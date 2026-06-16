"""
course_coach_bot.py

Conversational AI course-generator coach.

Main features:
- LangGraph workflow
- Gemini via LangChain Google GenAI
- Conversational course discovery
- Compact memory: profile + recent messages + summary
- Dynamic follow-up questions, no fixed question templates
- Suggested topics step before final course generation
- User can accept/reject suggested topics
- Final customized course generation
- Rich colorful logging
- AI call count per user question
- Token usage logging when available
- Safe Gemini response parsing for string/list content

Run:
    python course_coach_bot.py
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.traceback import install as install_rich_traceback

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END


# ============================================================
# 1. App configuration
# ============================================================

@dataclass
class Settings:
    api_key: str = "AIzaSyB1C6OyENmBaHgbmE3nj57LPyyQb_SFG5A"
    model: str = "gemini-flash-lite-latest"

    debug_logs: bool = True
    full_prompt_logs: bool = True
    show_full_state: bool = True
    show_model_output: bool = True

    max_recent_messages: int = 10
    keep_recent_messages: int = 6


CFG = Settings()


# ============================================================
# 2. Console and formatting helpers
# ============================================================

install_rich_traceback(show_locals=False)
console = Console()


def safe_json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(data)


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def message_content_to_text(content: Any) -> str:
    """
    Safely converts Gemini/LangChain response.content to text.

    Fixes:
        AttributeError: 'list' object has no attribute 'strip'
    """

    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: List[str] = []

        for item in content:
            if item is None:
                continue

            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
                elif isinstance(item.get("data"), str):
                    parts.append(item["data"])
                else:
                    parts.append(safe_json(item))

            else:
                parts.append(str(item))

        return "\n".join(parts).strip()

    return str(content).strip()


def normalize_usage(usage: Any) -> Dict[str, Any]:
    """
    Normalizes token usage metadata from model response.
    """

    if not usage:
        return {}

    if not isinstance(usage, dict):
        try:
            usage = dict(usage)
        except Exception:
            return {"raw": str(usage)}

    return {
        "input_tokens": (
            usage.get("input_tokens")
            or usage.get("prompt_tokens")
            or usage.get("prompt_token_count")
        ),
        "output_tokens": (
            usage.get("output_tokens")
            or usage.get("completion_tokens")
            or usage.get("candidates_token_count")
        ),
        "total_tokens": (
            usage.get("total_tokens")
            or usage.get("total_token_count")
        ),
        "raw": usage,
    }


# ============================================================
# 3. AI call statistics
# ============================================================

@dataclass
class AICallStats:
    total_calls: int = 0
    turn_id: int = 0
    turn_calls: int = 0
    turn_started_at: float = 0.0
    turn_duration: float = 0.0

    approx_input_tokens: int = 0
    approx_output_tokens: int = 0

    real_input_tokens: int = 0
    real_output_tokens: int = 0
    real_total_tokens: int = 0

    def start_turn(self, turn_id: int) -> None:
        self.turn_id = turn_id
        self.turn_calls = 0
        self.turn_started_at = time.perf_counter()
        self.turn_duration = 0.0

        self.approx_input_tokens = 0
        self.approx_output_tokens = 0

        self.real_input_tokens = 0
        self.real_output_tokens = 0
        self.real_total_tokens = 0

    def start_call(self, node: str, purpose: str, prompt: str) -> Dict[str, Any]:
        self.total_calls += 1
        self.turn_calls += 1

        prompt_tokens = approx_tokens(prompt)
        self.approx_input_tokens += prompt_tokens

        return {
            "node": node,
            "purpose": purpose,
            "model": CFG.model,
            "started_at": now(),
            "started_perf": time.perf_counter(),
            "turn_call_number": self.turn_calls,
            "total_call_number": self.total_calls,
            "prompt_chars": len(prompt),
            "approx_input_tokens": prompt_tokens,
        }

    def finish_call(
        self,
        record: Dict[str, Any],
        output_text: str,
        usage: Dict[str, Any],
    ) -> Dict[str, Any]:
        duration = time.perf_counter() - record["started_perf"]
        output_tokens = approx_tokens(output_text)

        self.approx_output_tokens += output_tokens

        input_tokens = usage.get("input_tokens")
        output_tokens_real = usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")

        if isinstance(input_tokens, int):
            self.real_input_tokens += input_tokens

        if isinstance(output_tokens_real, int):
            self.real_output_tokens += output_tokens_real

        if isinstance(total_tokens, int):
            self.real_total_tokens += total_tokens

        record.update(
            {
                "duration_seconds": duration,
                "output_chars": len(output_text or ""),
                "approx_output_tokens": output_tokens,
            }
        )

        return record

    def finish_turn(self) -> None:
        self.turn_duration = time.perf_counter() - self.turn_started_at


stats = AICallStats()


# ============================================================
# 4. Rich logger
# ============================================================

class Logger:
    def __init__(self, settings: Settings):
        self.cfg = settings

    def enabled(self) -> bool:
        return self.cfg.debug_logs

    def rule(self, title: str, style: str = "bold cyan") -> None:
        if self.enabled():
            console.rule(f"[{style}]{title}[/]", style=style)

    def panel(self, title: str, message: str, style: str = "cyan") -> None:
        if not self.enabled():
            return

        console.print(
            Panel(
                message,
                title=f"[bold {style}]{title}[/]",
                border_style=style,
                padding=(1, 2),
            )
        )

    def json(self, title: str, data: Any, style: str = "blue") -> None:
        if not self.enabled():
            return

        console.print(
            Panel(
                Syntax(
                    safe_json(data),
                    "json",
                    theme="monokai",
                    word_wrap=True,
                ),
                title=f"[bold {style}]{title}[/]",
                border_style=style,
                padding=(1, 2),
            )
        )

    def prompt(self, title: str, prompt: str) -> None:
        if not self.enabled() or not self.cfg.full_prompt_logs:
            return

        console.print(
            Panel(
                Syntax(
                    prompt,
                    "markdown",
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True,
                ),
                title=f"[bold magenta]{title}[/]",
                border_style="magenta",
                padding=(1, 2),
            )
        )

    def error(self, title: str, error: Exception) -> None:
        if not self.enabled():
            return

        console.print(
            Panel(
                f"{str(error)}\n\n{traceback.format_exc()}",
                title=f"[bold red]{title}[/]",
                border_style="red",
                padding=(1, 2),
            )
        )

    def node_start(self, node: str, state: Dict[str, Any]) -> None:
        if not self.enabled():
            return

        self.rule(f"NODE START: {node}", "bold cyan")

        table = Table(
            title=f"Node input summary — {node}",
            header_style="bold cyan",
            border_style="cyan",
        )

        table.add_column("Key", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("Time", now())
        table.add_row("Turn count", str(state.get("turn_count", 0)))
        table.add_row("Ready to generate", str(state.get("ready_to_generate", False)))
        table.add_row("Has course outline", str(bool(state.get("course_outline"))))
        table.add_row("Recent messages", str(len(state.get("recent_messages", []))))
        table.add_row("Summary exists", str(bool(state.get("conversation_summary"))))
        table.add_row("AI calls this turn", str(stats.turn_calls))
        table.add_row("Total AI calls", str(stats.total_calls))

        console.print(table)

        if self.cfg.show_full_state:
            self.json(f"Full state input — {node}", state, "cyan")

    def node_end(self, node: str, result: Dict[str, Any]) -> None:
        if not self.enabled():
            return

        self.json(f"Node output — {node}", result, "green")
        self.rule(f"NODE END: {node}", "bold green")

    def call_start(self, record: Dict[str, Any], prompt: str) -> None:
        if not self.enabled():
            return

        table = Table(
            title=f"AI call start — #{record['total_call_number']}",
            header_style="bold magenta",
            border_style="magenta",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("Time", record["started_at"])
        table.add_row("Node", record["node"])
        table.add_row("Purpose", record["purpose"])
        table.add_row("Model", record["model"])
        table.add_row("AI call in this question", str(record["turn_call_number"]))
        table.add_row("Total AI call number", str(record["total_call_number"]))
        table.add_row("Prompt characters", str(record["prompt_chars"]))
        table.add_row("Approx input tokens", str(record["approx_input_tokens"]))

        console.print(table)

        self.prompt(
            f"Prompt — AI call #{record['total_call_number']} — {record['node']}",
            prompt,
        )

    def call_end(
        self,
        record: Dict[str, Any],
        output_text: str,
        usage: Dict[str, Any],
    ) -> None:
        if not self.enabled():
            return

        table = Table(
            title=f"AI call end — #{record['total_call_number']}",
            header_style="bold green",
            border_style="green",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("Node", record["node"])
        table.add_row("Purpose", record["purpose"])
        table.add_row("Duration seconds", f"{record['duration_seconds']:.2f}")
        table.add_row("Output characters", str(record["output_chars"]))
        table.add_row("Approx output tokens", str(record["approx_output_tokens"]))

        if usage:
            table.add_row("Real input tokens", str(usage.get("input_tokens")))
            table.add_row("Real output tokens", str(usage.get("output_tokens")))
            table.add_row("Real total tokens", str(usage.get("total_tokens")))
        else:
            table.add_row("Real token usage", "Not returned")

        table.add_row("AI calls this question", str(stats.turn_calls))
        table.add_row("Total AI calls", str(stats.total_calls))

        console.print(table)

        if self.cfg.show_model_output:
            self.json(
                f"Output preview — AI call #{record['total_call_number']}",
                {
                    "output_text": output_text,
                    "usage_metadata": usage,
                },
                "green",
            )

    def turn_start(self, turn_id: int, user_message: str) -> None:
        if not self.enabled():
            return

        self.rule(f"QUESTION START — Turn {turn_id}", "bold bright_blue")
        self.panel(
            "User question",
            user_message or "[initial assistant greeting]",
            "bright_blue",
        )

    def turn_end(self) -> None:
        if not self.enabled():
            return

        table = Table(
            title=f"Question summary — Turn {stats.turn_id}",
            header_style="bold bright_blue",
            border_style="bright_blue",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("AI calls in this question", str(stats.turn_calls))
        table.add_row("Total AI calls so far", str(stats.total_calls))
        table.add_row("Approx input tokens", str(stats.approx_input_tokens))
        table.add_row("Approx output tokens", str(stats.approx_output_tokens))
        table.add_row("Real input tokens", str(stats.real_input_tokens))
        table.add_row("Real output tokens", str(stats.real_output_tokens))
        table.add_row("Real total tokens", str(stats.real_total_tokens))
        table.add_row("Duration seconds", f"{stats.turn_duration:.2f}")

        console.print(table)
        self.rule(f"QUESTION END — Turn {stats.turn_id}", "bold bright_blue")


log = Logger(CFG)


# ============================================================
# 5. Gemini models
# ============================================================

llm = ChatGoogleGenerativeAI(
    model=CFG.model,
    temperature=0.2,
    api_key=CFG.api_key,
)

structured_llm = ChatGoogleGenerativeAI(
    model=CFG.model,
    temperature=0,
    api_key=CFG.api_key,
)


# ============================================================
# 6. Structured output schemas
# ============================================================

class ProfilePatch(BaseModel):
    course_topic: Optional[str] = Field(
        None,
        description="Main course topic or skill."
    )

    course_topic_description: Optional[str] = Field(
        None,
        description=(
            "Full descriptive information about the course topic. "
            "This clarifies the exact meaning, scope, angle, and boundaries of the course topic."
        ),
    )

    course_goals_and_outcomes: Optional[str] = Field(
        None,
        description=(
            "The user's goal and intent for this course, plus the outcomes "
            "they want the learner to achieve."
        ),
    )

    target_learner: Optional[str] = Field(
        None,
        description="Who the course is for."
    )

    current_level: Optional[str] = Field(
        None,
        description="Current learner level."
    )

    personal_needs: Optional[str] = Field(
        None,
        description="Personal needs, learning style, challenges, or preferences."
    )

    course_duration: Optional[str] = Field(
        None,
        description=(
            "How long the course should be, how many sessions/modules it should have, "
            "or the expected learning timeline."
        ),
    )

    preferred_format: Optional[str] = Field(
        None,
        description="Preferred course format: text, video, exercises, projects, coaching, etc."
    )

    rules: Optional[List[str]] = Field(
        None,
        description=(
            "Rules, important tips, must-follow principles, course requirements, "
            "and important guidance about how this course should be designed."
        ),
    )

    suggested_topics: Optional[List[str]] = Field(
        None,
        description=(
            "Personalized related topics suggested by the chatbot to improve the course. "
            "These are suggestions first and should be accepted or rejected by the user."
        ),
    )

    accepted_suggested_topics: Optional[List[str]] = Field(
        None,
        description=(
            "Suggested topics that the user accepted and wants to include in the course."
        ),
    )

    suggested_topics_decision: Optional[str] = Field(
        None,
        description=(
            "User decision about suggested topics. "
            "Use one of: not_suggested, pending, accepted, accepted_some, rejected."
        ),
    )


class CoachDecision(BaseModel):
    profile_patch: ProfilePatch = Field(default_factory=ProfilePatch)
    missing_information: List[str] = Field(default_factory=list)
    ready_to_generate: bool = False
    assistant_message: str
    debug_notes: str = ""


try:
    decision_chain = structured_llm.with_structured_output(
        CoachDecision,
        include_raw=True,
    )
    DECISION_INCLUDE_RAW = True
except TypeError:
    decision_chain = structured_llm.with_structured_output(CoachDecision)
    DECISION_INCLUDE_RAW = False


# ============================================================
# 7. LangGraph state
# ============================================================

class CoachState(TypedDict, total=False):
    user_message: str
    profile: Dict[str, Any]
    recent_messages: List[Dict[str, str]]
    conversation_summary: str
    assistant_message: str
    missing_information: List[str]
    ready_to_generate: bool
    course_outline: str
    turn_count: int


# ============================================================
# 8. Model call wrappers
# ============================================================

def call_text(node: str, purpose: str, prompt: str) -> str:
    record = stats.start_call(node, purpose, prompt)
    log.call_start(record, prompt)

    response = llm.invoke(prompt)

    output_text = message_content_to_text(response.content)
    usage = normalize_usage(getattr(response, "usage_metadata", None))
    final_record = stats.finish_call(record, output_text, usage)

    log.call_end(final_record, output_text, usage)

    return output_text


def call_decision(node: str, purpose: str, prompt: str) -> CoachDecision:
    record = stats.start_call(node, purpose, prompt)
    log.call_start(record, prompt)

    result = decision_chain.invoke(prompt)

    usage: Dict[str, Any] = {}
    output_for_log: Any = result

    if DECISION_INCLUDE_RAW and isinstance(result, dict):
        if result.get("parsing_error"):
            raise RuntimeError(f"Structured parsing error: {result['parsing_error']}")

        parsed = result.get("parsed")
        raw = result.get("raw")

        if isinstance(parsed, CoachDecision):
            decision = parsed
        elif isinstance(parsed, dict):
            decision = CoachDecision.model_validate(parsed)
        else:
            raise RuntimeError("Structured model did not return CoachDecision.")

        usage = normalize_usage(getattr(raw, "usage_metadata", None))
        output_for_log = {
            "parsed": decision.model_dump(),
            "raw_content": message_content_to_text(getattr(raw, "content", "")),
            "usage_metadata": usage,
        }

    else:
        if isinstance(result, CoachDecision):
            decision = result
        elif isinstance(result, dict):
            decision = CoachDecision.model_validate(result)
        else:
            raise RuntimeError("Structured model did not return CoachDecision.")

        output_for_log = decision.model_dump()

    output_text = safe_json(output_for_log)
    final_record = stats.finish_call(record, output_text, usage)

    log.call_end(final_record, output_text, usage)

    return decision


# ============================================================
# 9. Profile and message utilities
# ============================================================

def useful(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str) and not value.strip():
        return False

    if isinstance(value, list) and not value:
        return False

    return True


def merge_unique(old: List[str], new: List[str]) -> List[str]:
    result = list(old)

    for item in new:
        item = str(item).strip()

        if item and item not in result:
            result.append(item)

    return result


def merge_profile(profile: Dict[str, Any], patch: ProfilePatch) -> Dict[str, Any]:
    updated = dict(profile)
    patch_data = patch.model_dump(exclude_none=True)

    list_fields = {
        "rules",
        "suggested_topics",
        "accepted_suggested_topics",
    }

    for key, value in patch_data.items():
        if not useful(value):
            continue

        if key in list_fields:
            old_value = updated.get(key, [])
            old_list = old_value if isinstance(old_value, list) else [str(old_value)]
            new_list = value if isinstance(value, list) else [str(value)]
            updated[key] = merge_unique(old_list, new_list)
        else:
            updated[key] = value

    return updated


def add_message(
    messages: List[Dict[str, str]],
    role: str,
    content: str,
) -> List[Dict[str, str]]:
    if not content or not content.strip():
        return messages

    return [
        *messages,
        {
            "role": role,
            "content": content.strip(),
        },
    ]


# ============================================================
# 10. Prompt builders
# ============================================================

def build_summary_prompt(
    old_summary: str,
    messages_to_summarize: List[Dict[str, str]],
) -> str:
    return f"""
You are summarizing a conversation for an AI course-generator coach bot.

Goal:
Create a compact but useful memory summary.

Rules:
- Preserve user goals, preferences, decisions, and course requirements.
- Preserve the course topic and course topic description.
- Preserve course goals and outcomes.
- Preserve current learner level and target learner.
- Preserve personal needs.
- Preserve course duration and number of sessions/modules if mentioned.
- Preserve preferred format.
- Preserve course rules and important tips.
- Preserve suggested topics and whether the user accepted or rejected them.
- Remove small talk and repeated information.
- Keep it concise but useful.
- Do not invent information.

Previous summary:
{old_summary}

Older messages to merge into summary:
{json.dumps(messages_to_summarize, ensure_ascii=False, indent=2)}

Return only the updated summary text.
"""


def build_coach_prompt(state: CoachState) -> str:
    profile = state.get("profile", {})
    recent_messages = state.get("recent_messages", [])
    conversation_summary = state.get("conversation_summary", "")
    turn_count = state.get("turn_count", 0)

    return f"""
You are an expert AI course creation coach.

Your job:
Help the user step by step to design the best possible course based on their exact needs.

Important behavior:
- Be fully conversational and interactive.
- Do NOT use fixed or generic question templates.
- Ask natural, customized follow-up questions based on the user's previous answers.
- Use the previous conversation summary and recent messages.
- Do not ignore previous conversation history.
- Do not ask for information the user already gave.
- Ask at most 1 or 2 focused questions per turn.
- If the user gives many details, acknowledge them briefly and move forward.
- If the user is unclear, ask a clarifying question.
- If enough information exists but suggested topics have not been suggested yet, suggest personalized related topics first.
- Before generating the final course, the user must accept or reject the suggested topics.
- If the user accepts all suggested topics, set suggested_topics_decision to "accepted".
- If the user accepts only some, set suggested_topics_decision to "accepted_some" and fill accepted_suggested_topics.
- If the user rejects the suggestions, set suggested_topics_decision to "rejected".
- If suggestions were just made and the user has not answered yet, set suggested_topics_decision to "pending".
- Set ready_to_generate=true only after the user accepts or rejects the suggested topics.
- Your assistant_message must be the exact message shown to the user.
- Keep assistant_message helpful, friendly, practical, and natural.
- Do not mention JSON, schema, extraction, or internal process to the user.

Profile fields you should maintain:
- course_topic
- course_topic_description
- course_goals_and_outcomes
- target_learner
- current_level
- personal_needs
- course_duration
- preferred_format
- rules
- suggested_topics
- accepted_suggested_topics
- suggested_topics_decision

When is enough information collected?
You can move to the suggested-topics step when you understand most of these:
- Course topic
- Descriptive clarification of the course topic
- Course goals and outcomes
- Target learner
- Current level
- Personal needs
- Course duration / number of sessions / timeline
- Preferred format
- Important rules or tips about the course

Suggested topics step:
- When enough information is collected and suggested_topics is empty, suggest 3 to 7 highly personalized, efficient, related topics that could improve this course.
- These topics should be optional.
- Ask the user to accept all, reject all, or choose specific ones.
- Do not generate the final course in the same turn you first suggest these topics.

Generation readiness:
- If suggested topics are pending, ready_to_generate must be false.
- If user accepts all, accepts some, or rejects all, ready_to_generate can be true.
- If important core information is still missing, ready_to_generate must be false.

Current structured profile:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Conversation summary:
{conversation_summary}

Recent messages:
{json.dumps(recent_messages, ensure_ascii=False, indent=2)}

Turn number:
{turn_count}

Return a structured CoachDecision.
"""


def build_outline_prompt(state: CoachState) -> str:
    profile = state.get("profile", {})
    recent_messages = state.get("recent_messages", [])
    conversation_summary = state.get("conversation_summary", "")

    return f"""
You are an expert instructional designer, curriculum strategist, and personal learning coach.

Create a highly customized course outline based on everything known about the user.

Use:
1. The structured profile
2. The conversation summary
3. The recent conversation

Do not ask more questions.
Generate the course now.

Structured profile:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Conversation summary:
{conversation_summary}

Recent messages:
{json.dumps(recent_messages, ensure_ascii=False, indent=2)}

Important profile meaning:
- course_topic: the main course topic
- course_topic_description: full clarification of the topic, scope, angle, and boundaries
- course_goals_and_outcomes: the user's intention and expected learner outcomes
- course_duration: how long the course should be and how many sessions/modules it should have
- rules: important course design rules, requirements, and tips
- suggested_topics: topics suggested by the chatbot
- accepted_suggested_topics: suggested topics the user accepted
- suggested_topics_decision: accepted, accepted_some, rejected, or pending

Suggested topics handling:
- If suggested_topics_decision is "accepted", include the suggested topics naturally in the course.
- If suggested_topics_decision is "accepted_some", include only accepted_suggested_topics.
- If suggested_topics_decision is "rejected", do not force suggested topics into the course.
- If accepted_suggested_topics exists, treat those as approved course content.
- Do not include rejected suggestions as required modules.

Output requirements:
- Make it practical and customized.
- Avoid generic course structure.
- Adapt to the user's personal needs, current level, course duration, preferred format, goals, and rules.
- Include a strong course title.
- Include a clear course promise.
- Include a clear course topic description.
- Include target learner description.
- Include course goals and outcomes.
- Include course format.
- Include course duration and session/module logic.
- Include module-by-module outline.
- Include lessons inside each module.
- Include exercises and tasks.
- Include checkpoints.
- Include final project.
- Include success metrics.
- Include next steps after the course.

Use this format:

# Course Title

## Course Promise

## Course Topic Description

## Best For

## Course Goals and Outcomes

## Course Format

## Course Duration

## Course Rules and Important Tips

## Course Roadmap

### Module 1: ...
Purpose:
Lessons:
1.
2.
3.
Practice:
Checkpoint:

### Module 2: ...
Purpose:
Lessons:
1.
2.
3.
Practice:
Checkpoint:

## Final Project

## Success Metrics

## After Finishing This Course
"""


# ============================================================
# 11. Graph nodes
# ============================================================

def add_user_message(state: CoachState) -> CoachState:
    log.node_start("add_user_message", state)

    user_message = state.get("user_message", "").strip()
    messages = state.get("recent_messages", [])
    turn_count = state.get("turn_count", 0)

    if user_message:
        messages = add_message(messages, "user", user_message)
        turn_count += 1

    result: CoachState = {
        "recent_messages": messages,
        "turn_count": turn_count,
    }

    log.node_end("add_user_message", result)
    return result


def summarize_history(state: CoachState) -> CoachState:
    log.node_start("summarize_history", state)

    messages = state.get("recent_messages", [])
    old_summary = state.get("conversation_summary", "")

    to_summarize = messages[:-CFG.keep_recent_messages]
    to_keep = messages[-CFG.keep_recent_messages:]

    prompt = build_summary_prompt(old_summary, to_summarize)

    try:
        summary = call_text(
            node="summarize_history",
            purpose="summarize older conversation history",
            prompt=prompt,
        )

        result: CoachState = {
            "conversation_summary": summary,
            "recent_messages": to_keep,
        }

    except Exception as error:
        log.error("summarize_history failed", error)

        result = {
            "conversation_summary": old_summary,
            "recent_messages": messages,
        }

    log.node_end("summarize_history", result)
    return result


def coach_turn(state: CoachState) -> CoachState:
    log.node_start("coach_turn", state)

    prompt = build_coach_prompt(state)

    try:
        decision = call_decision(
            node="coach_turn",
            purpose="understand user, update profile, suggest topics, decide next response",
            prompt=prompt,
        )

        profile = merge_profile(
            state.get("profile", {}),
            decision.profile_patch,
        )

        result: CoachState = {
            "profile": profile,
            "missing_information": decision.missing_information,
            "ready_to_generate": decision.ready_to_generate,
            "assistant_message": decision.assistant_message,
        }

        log.json(
            "Parsed coach decision",
            {
                "decision": decision.model_dump(),
                "updated_profile": profile,
            },
            "bright_green",
        )

    except Exception as error:
        log.error("coach_turn failed", error)

        result = {
            "assistant_message": (
                "I understood. To customize the course properly, tell me more about "
                "the course topic, the goal of the course, and who this course is for."
            ),
            "ready_to_generate": False,
            "missing_information": [
                "course topic description",
                "course goals and outcomes",
                "target learner",
            ],
        }

    log.node_end("coach_turn", result)
    return result


def generate_course_outline(state: CoachState) -> CoachState:
    log.node_start("generate_course_outline", state)

    prompt = build_outline_prompt(state)

    try:
        outline = call_text(
            node="generate_course_outline",
            purpose="generate final customized course outline",
            prompt=prompt,
        )

        if not outline:
            raise RuntimeError("Gemini returned an empty course outline.")

        result: CoachState = {
            "course_outline": outline,
            "assistant_message": outline,
            "ready_to_generate": True,
        }

    except Exception as error:
        log.error("generate_course_outline failed", error)

        result = {
            "assistant_message": (
                "I had an issue generating the full course outline. "
                "The model response was not valid text. The course was not marked as generated. "
                "Please try again."
            ),
            "ready_to_generate": False,
        }

    log.node_end("generate_course_outline", result)
    return result


def append_assistant_message(state: CoachState) -> CoachState:
    log.node_start("append_assistant_message", state)

    messages = add_message(
        state.get("recent_messages", []),
        "assistant",
        state.get("assistant_message", ""),
    )

    result: CoachState = {
        "recent_messages": messages,
    }

    log.node_end("append_assistant_message", result)
    return result


# ============================================================
# 12. Graph routers
# ============================================================

def route_after_user_message(state: CoachState) -> str:
    messages = state.get("recent_messages", [])

    decision = (
        "summarize_history"
        if len(messages) > CFG.max_recent_messages
        else "coach_turn"
    )

    log.panel(
        "Router: after user message",
        (
            f"Recent messages: {len(messages)}\n"
            f"Max before summary: {CFG.max_recent_messages}\n"
            f"Decision: {decision}"
        ),
        "yellow",
    )

    return decision


def route_after_coach_turn(state: CoachState) -> str:
    ready = state.get("ready_to_generate") is True
    has_outline = bool(state.get("course_outline"))

    decision = (
        "generate_course_outline"
        if ready and not has_outline
        else "append_assistant_message"
    )

    log.panel(
        "Router: after coach turn",
        (
            f"Ready to generate: {ready}\n"
            f"Has outline: {has_outline}\n"
            f"Decision: {decision}"
        ),
        "yellow",
    )

    return decision


# ============================================================
# 13. Graph builder
# ============================================================

def build_graph():
    graph = StateGraph(CoachState)

    graph.add_node("add_user_message", add_user_message)
    graph.add_node("summarize_history", summarize_history)
    graph.add_node("coach_turn", coach_turn)
    graph.add_node("generate_course_outline", generate_course_outline)
    graph.add_node("append_assistant_message", append_assistant_message)

    graph.add_edge(START, "add_user_message")

    graph.add_conditional_edges(
        "add_user_message",
        route_after_user_message,
        {
            "summarize_history": "summarize_history",
            "coach_turn": "coach_turn",
        },
    )

    graph.add_edge("summarize_history", "coach_turn")

    graph.add_conditional_edges(
        "coach_turn",
        route_after_coach_turn,
        {
            "generate_course_outline": "generate_course_outline",
            "append_assistant_message": "append_assistant_message",
        },
    )

    graph.add_edge("generate_course_outline", "append_assistant_message")
    graph.add_edge("append_assistant_message", END)

    return graph.compile()


# ============================================================
# 14. CLI interface
# ============================================================

def print_header() -> None:
    grid = Table.grid(expand=True)
    grid.add_column(justify="center")
    grid.add_row(Text("AI Course Coach Bot", style="bold white"))
    grid.add_row(Text(f"Model: {CFG.model} | Logging: {'ON' if CFG.debug_logs else 'OFF'}", style="cyan"))

    console.print(
        Panel(
            grid,
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def print_coach(message: str) -> None:
    console.print(
        Panel(
            message,
            title="[bold green]Coach[/]",
            border_style="green",
            padding=(1, 2),
        )
    )


def run_turn(
    graph,
    state: CoachState,
    user_message: str,
    turn_id: int,
) -> CoachState:
    stats.start_turn(turn_id)
    log.turn_start(turn_id, user_message)

    state["user_message"] = user_message
    state = graph.invoke(state)

    stats.finish_turn()
    log.turn_end()

    return state


def main() -> None:
    if CFG.api_key == "PASTE_YOUR_NEW_GEMINI_API_KEY_HERE":
        console.print(
            Panel(
                "Paste your Gemini API key into CFG.api_key before running.",
                title="[bold red]Missing API key[/]",
                border_style="red",
                padding=(1, 2),
            )
        )
        return

    graph = build_graph()

    state: CoachState = {
        "profile": {},
        "recent_messages": [],
        "conversation_summary": "",
        "turn_count": 0,
        "ready_to_generate": False,
    }

    print_header()

    console.print(
        Panel(
            "Type [bold]exit[/], [bold]quit[/], or [bold]q[/] to stop.",
            title="[bold green]Ready[/]",
            border_style="green",
            padding=(1, 2),
        )
    )

    state = run_turn(
        graph=graph,
        state=state,
        user_message="",
        turn_id=0,
    )

    print_coach(state.get("assistant_message", ""))

    while True:
        user_input = console.input("[bold cyan]You:[/] ").strip()

        if user_input.lower() in {"exit", "quit", "q"}:
            print_coach("Goodbye.")
            break

        next_turn_id = state.get("turn_count", 0) + 1

        state = run_turn(
            graph=graph,
            state=state,
            user_message=user_input,
            turn_id=next_turn_id,
        )

        print_coach(state.get("assistant_message", ""))

        if state.get("course_outline"):
            console.print(
                Panel(
                    (
                        "Course outline generated successfully.\n\n"
                        f"Total AI calls in this session: {stats.total_calls}"
                    ),
                    title="[bold bright_green]DONE[/]",
                    border_style="bright_green",
                    padding=(1, 2),
                )
            )
            break


if __name__ == "__main__":
    main()