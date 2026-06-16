"""
course_coach_bot.py

Fully conversational AI course-generator coach bot.

Features:
- LangGraph workflow
- Gemini through LangChain Google GenAI
- Fully conversational / no fixed question templates
- Uses previous conversation history
- Summarizes older history to save tokens
- Generates customized course outline
- Colorful structured terminal logging with Rich
- Tracks AI calls per user question
- Tracks total AI calls
- Tracks token usage when available
- Fixes Gemini response.content list problem

Run:
    python course_coach_bot.py
"""

import json
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.traceback import install as rich_traceback_install


# ============================================================
# 1. Configuration
# ============================================================

GEMINI_API_KEY = "AIzaSyB1C6OyENmBaHgbmE3nj57LPyyQb_SFG5A"

MODEL_NAME = "gemini-flash-lite-latest"

DEBUG_LOGS = True
FULL_PROMPT_LOGS = True
SHOW_FULL_STATE = True
SHOW_MODEL_OUTPUT = True

MAX_RECENT_MESSAGES = 10
KEEP_RECENT_MESSAGES = 6


# ============================================================
# 2. Rich console setup
# ============================================================

rich_traceback_install(show_locals=False)
console = Console()


# ============================================================
# 3. Text / token helpers
# ============================================================

def approx_tokens(text: str) -> int:
    """
    Rough token estimate.
    Good enough for terminal debugging.
    Real token usage is shown when the model returns usage_metadata.
    """
    if not text:
        return 0

    return max(1, len(text) // 4)


def safe_json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(data)


def message_content_to_text(content: Any) -> str:
    """
    Converts LangChain/Gemini message content safely into plain text.

    Fixes this error:
        AttributeError: 'list' object has no attribute 'strip'

    Because Gemini may return:
        response.content = "text"

    Or:
        response.content = [
            {"type": "text", "text": "..."},
            ...
        ]
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


def normalize_usage_metadata(usage: Any) -> Dict[str, Any]:
    """
    Normalizes token usage from LangChain responses.
    Different providers may use slightly different keys.
    """

    if not usage:
        return {}

    if not isinstance(usage, dict):
        try:
            usage = dict(usage)
        except Exception:
            return {"raw_usage_metadata": str(usage)}

    normalized = {
        "input_tokens": usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or usage.get("prompt_token_count"),
        "output_tokens": usage.get("output_tokens")
        or usage.get("completion_tokens")
        or usage.get("candidates_token_count"),
        "total_tokens": usage.get("total_tokens")
        or usage.get("total_token_count"),
        "raw": usage,
    }

    return normalized


# ============================================================
# 4. Debug logger
# ============================================================

class DebugLogger:
    """
    Colorful structured logger for terminal debugging.
    """

    def __init__(
        self,
        enabled: bool = True,
        full_prompts: bool = True,
        show_full_state: bool = True,
        show_model_output: bool = True,
    ):
        self.enabled = enabled
        self.full_prompts = full_prompts
        self.show_full_state = show_full_state
        self.show_model_output = show_model_output

    def time(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def rule(self, title: str, style: str = "bold cyan") -> None:
        if not self.enabled:
            return

        console.rule(f"[{style}]{title}[/]", style=style)

    def panel(
        self,
        title: str,
        message: str,
        style: str = "cyan",
    ) -> None:
        if not self.enabled:
            return

        console.print(
            Panel(
                message,
                title=f"[bold {style}]{title}[/]",
                border_style=style,
                padding=(1, 2),
            )
        )

    def json_panel(
        self,
        title: str,
        data: Any,
        style: str = "blue",
    ) -> None:
        if not self.enabled:
            return

        syntax = Syntax(
            safe_json(data),
            "json",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
        )

        console.print(
            Panel(
                syntax,
                title=f"[bold {style}]{title}[/]",
                border_style=style,
                padding=(1, 2),
            )
        )

    def prompt_panel(
        self,
        title: str,
        prompt_text: str,
    ) -> None:
        if not self.enabled or not self.full_prompts:
            return

        syntax = Syntax(
            prompt_text,
            "markdown",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )

        console.print(
            Panel(
                syntax,
                title=f"[bold magenta]{title}[/]",
                border_style="magenta",
                padding=(1, 2),
            )
        )

    def error(
        self,
        title: str,
        error: Exception,
    ) -> None:
        if not self.enabled:
            return

        error_text = f"{str(error)}\n\n{traceback.format_exc()}"

        console.print(
            Panel(
                error_text,
                title=f"[bold red]{title}[/]",
                border_style="red",
                padding=(1, 2),
            )
        )

    def node_start(
        self,
        node_name: str,
        state: Dict[str, Any],
    ) -> None:
        if not self.enabled:
            return

        self.rule(f"NODE START: {node_name}", "bold cyan")

        table = Table(
            title=f"Node Input Summary — {node_name}",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
        )

        table.add_column("Key", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("Time", self.time())
        table.add_row("Turn Count", str(state.get("turn_count", 0)))
        table.add_row("Ready To Generate", str(state.get("ready_to_generate", False)))
        table.add_row("Has Course Outline", str(bool(state.get("course_outline"))))
        table.add_row("Recent Messages", str(len(state.get("recent_messages", []))))
        table.add_row("Summary Exists", str(bool(state.get("conversation_summary"))))
        table.add_row("Current Turn AI Calls", str(ai_tracker.current_turn_call_count))
        table.add_row("Total AI Calls", str(ai_tracker.total_ai_calls))

        console.print(table)

        if self.show_full_state:
            self.json_panel(
                f"Full State Input — {node_name}",
                state,
                style="cyan",
            )

    def node_end(
        self,
        node_name: str,
        result: Dict[str, Any],
    ) -> None:
        if not self.enabled:
            return

        self.json_panel(
            f"Node Output — {node_name}",
            result,
            style="green",
        )

        self.rule(f"NODE END: {node_name}", "bold green")

    def ai_call_start(
        self,
        record: Dict[str, Any],
        prompt_text: str,
    ) -> None:
        if not self.enabled:
            return

        table = Table(
            title=f"AI CALL START — #{record['total_call_number']}",
            show_header=True,
            header_style="bold magenta",
            border_style="magenta",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("Time", record["started_at"])
        table.add_row("Node", record["node"])
        table.add_row("Purpose", record["purpose"])
        table.add_row("Model", record["model"])
        table.add_row("AI Call In This Question", str(record["turn_call_number"]))
        table.add_row("Total AI Call Number", str(record["total_call_number"]))
        table.add_row("Prompt Characters", str(record["prompt_chars"]))
        table.add_row("Approx Input Tokens", str(record["approx_input_tokens"]))

        console.print(table)

        if self.full_prompts:
            self.prompt_panel(
                f"Prompt — AI Call #{record['total_call_number']} — {record['node']}",
                prompt_text,
            )

    def ai_call_end(
        self,
        record: Dict[str, Any],
        output_text: str,
        usage_metadata: Dict[str, Any],
    ) -> None:
        if not self.enabled:
            return

        table = Table(
            title=f"AI CALL END — #{record['total_call_number']}",
            show_header=True,
            header_style="bold green",
            border_style="green",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("Node", record["node"])
        table.add_row("Purpose", record["purpose"])
        table.add_row("Duration Seconds", f"{record['duration_seconds']:.2f}")
        table.add_row("Output Characters", str(record["output_chars"]))
        table.add_row("Approx Output Tokens", str(record["approx_output_tokens"]))

        if usage_metadata:
            table.add_row("Real Input Tokens", str(usage_metadata.get("input_tokens")))
            table.add_row("Real Output Tokens", str(usage_metadata.get("output_tokens")))
            table.add_row("Real Total Tokens", str(usage_metadata.get("total_tokens")))
        else:
            table.add_row("Real Token Usage", "Not returned by model response")

        table.add_row("AI Calls This Question", str(ai_tracker.current_turn_call_count))
        table.add_row("Total AI Calls", str(ai_tracker.total_ai_calls))

        console.print(table)

        if self.show_model_output:
            self.json_panel(
                f"Output Preview — AI Call #{record['total_call_number']}",
                {
                    "output_text": output_text,
                    "usage_metadata": usage_metadata,
                },
                style="green",
            )

    def turn_start(
        self,
        turn_id: int,
        user_message: str,
    ) -> None:
        if not self.enabled:
            return

        self.rule(f"QUESTION START — Turn {turn_id}", "bold bright_blue")

        self.panel(
            title="User Question",
            message=user_message if user_message else "[initial assistant greeting]",
            style="bright_blue",
        )

    def turn_end(
        self,
        turn_id: int,
    ) -> None:
        if not self.enabled:
            return

        table = Table(
            title=f"QUESTION SUMMARY — Turn {turn_id}",
            show_header=True,
            header_style="bold bright_blue",
            border_style="bright_blue",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", overflow="fold")

        table.add_row("AI Calls In This Question", str(ai_tracker.current_turn_call_count))
        table.add_row("Total AI Calls So Far", str(ai_tracker.total_ai_calls))
        table.add_row("Approx Input Tokens This Question", str(ai_tracker.current_turn_approx_input_tokens))
        table.add_row("Approx Output Tokens This Question", str(ai_tracker.current_turn_approx_output_tokens))
        table.add_row("Real Input Tokens This Question", str(ai_tracker.current_turn_real_input_tokens))
        table.add_row("Real Output Tokens This Question", str(ai_tracker.current_turn_real_output_tokens))
        table.add_row("Real Total Tokens This Question", str(ai_tracker.current_turn_real_total_tokens))
        table.add_row("Duration Seconds", f"{ai_tracker.current_turn_duration_seconds:.2f}")

        console.print(table)

        self.rule(f"QUESTION END — Turn {turn_id}", "bold bright_blue")


logger = DebugLogger(
    enabled=DEBUG_LOGS,
    full_prompts=FULL_PROMPT_LOGS,
    show_full_state=SHOW_FULL_STATE,
    show_model_output=SHOW_MODEL_OUTPUT,
)


# ============================================================
# 5. AI call tracker
# ============================================================

class AICallTracker:
    """
    Tracks:
    - total AI calls
    - AI calls per user question
    - estimated token usage
    - real token usage when returned
    """

    def __init__(self):
        self.total_ai_calls = 0

        self.current_turn_id = 0
        self.current_turn_call_count = 0
        self.current_turn_started_at = 0.0
        self.current_turn_duration_seconds = 0.0

        self.current_turn_approx_input_tokens = 0
        self.current_turn_approx_output_tokens = 0

        self.current_turn_real_input_tokens = 0
        self.current_turn_real_output_tokens = 0
        self.current_turn_real_total_tokens = 0

    def start_turn(
        self,
        turn_id: int,
        user_message: str,
    ) -> None:
        self.current_turn_id = turn_id
        self.current_turn_call_count = 0
        self.current_turn_started_at = time.perf_counter()
        self.current_turn_duration_seconds = 0.0

        self.current_turn_approx_input_tokens = 0
        self.current_turn_approx_output_tokens = 0

        self.current_turn_real_input_tokens = 0
        self.current_turn_real_output_tokens = 0
        self.current_turn_real_total_tokens = 0

        logger.turn_start(turn_id, user_message)

    def begin_call(
        self,
        node: str,
        purpose: str,
        prompt_text: str,
    ) -> Dict[str, Any]:
        self.total_ai_calls += 1
        self.current_turn_call_count += 1

        prompt_chars = len(prompt_text)
        prompt_tokens = approx_tokens(prompt_text)

        self.current_turn_approx_input_tokens += prompt_tokens

        record = {
            "node": node,
            "purpose": purpose,
            "model": MODEL_NAME,
            "started_at": datetime.now().strftime("%H:%M:%S"),
            "start_perf": time.perf_counter(),
            "turn_call_number": self.current_turn_call_count,
            "total_call_number": self.total_ai_calls,
            "prompt_chars": prompt_chars,
            "approx_input_tokens": prompt_tokens,
        }

        logger.ai_call_start(record, prompt_text)

        return record

    def end_call(
        self,
        record: Dict[str, Any],
        output_text: str,
        usage_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        duration = time.perf_counter() - record["start_perf"]

        output_chars = len(output_text or "")
        output_tokens = approx_tokens(output_text or "")

        self.current_turn_approx_output_tokens += output_tokens

        usage_metadata = usage_metadata or {}

        real_input = usage_metadata.get("input_tokens")
        real_output = usage_metadata.get("output_tokens")
        real_total = usage_metadata.get("total_tokens")

        if isinstance(real_input, int):
            self.current_turn_real_input_tokens += real_input

        if isinstance(real_output, int):
            self.current_turn_real_output_tokens += real_output

        if isinstance(real_total, int):
            self.current_turn_real_total_tokens += real_total

        record["duration_seconds"] = duration
        record["output_chars"] = output_chars
        record["approx_output_tokens"] = output_tokens

        logger.ai_call_end(record, output_text, usage_metadata)

    def end_turn(self) -> None:
        self.current_turn_duration_seconds = time.perf_counter() - self.current_turn_started_at
        logger.turn_end(self.current_turn_id)


ai_tracker = AICallTracker()


# ============================================================
# 6. Gemini model setup
# ============================================================

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0.2,
    api_key=GEMINI_API_KEY,
)

structured_llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0,
    api_key=GEMINI_API_KEY,
)


# ============================================================
# 7. Structured data models
# ============================================================

class ProfilePatch(BaseModel):
    course_topic: Optional[str] = Field(
        None,
        description="Main course topic or skill."
    )

    desired_outcome: Optional[str] = Field(
        None,
        description="The practical outcome the learner should achieve."
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

    business_context: Optional[str] = Field(
        None,
        description="Relevant professional or business context."
    )

    time_available: Optional[str] = Field(
        None,
        description="Available time, duration, deadline, weekly hours, etc."
    )

    preferred_format: Optional[str] = Field(
        None,
        description="Preferred course format."
    )

    language: Optional[str] = Field(
        None,
        description="Preferred course language."
    )

    constraints: Optional[List[str]] = Field(
        None,
        description="Important constraints."
    )

    must_include: Optional[List[str]] = Field(
        None,
        description="Things the course must include."
    )

    must_avoid: Optional[List[str]] = Field(
        None,
        description="Things the course should avoid."
    )


class CoachDecision(BaseModel):
    profile_patch: ProfilePatch = Field(
        default_factory=ProfilePatch,
        description="New information learned from this turn."
    )

    missing_information: List[str] = Field(
        default_factory=list,
        description="Important missing information before course generation."
    )

    ready_to_generate: bool = Field(
        False,
        description="Whether enough information exists to generate the course."
    )

    assistant_message: str = Field(
        ...,
        description="The exact assistant message to show the user."
    )

    debug_notes: str = Field(
        "",
        description="Brief explanation of the decision."
    )


# Try to keep raw structured model response for usage_metadata.
# If your installed LangChain version does not support include_raw,
# the code falls back safely.
try:
    decision_model = structured_llm.with_structured_output(
        CoachDecision,
        include_raw=True,
    )
    STRUCTURED_INCLUDE_RAW = True
except TypeError:
    decision_model = structured_llm.with_structured_output(CoachDecision)
    STRUCTURED_INCLUDE_RAW = False


# ============================================================
# 8. LangGraph state
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
# 9. Model call wrappers
# ============================================================

def call_llm_text(
    node: str,
    purpose: str,
    prompt: str,
) -> str:
    """
    Calls normal Gemini model and safely converts content to text.
    """

    record = ai_tracker.begin_call(
        node=node,
        purpose=purpose,
        prompt_text=prompt,
    )

    response = llm.invoke(prompt)

    output_text = message_content_to_text(response.content)

    usage_metadata = normalize_usage_metadata(
        getattr(response, "usage_metadata", None)
    )

    ai_tracker.end_call(
        record=record,
        output_text=output_text,
        usage_metadata=usage_metadata,
    )

    return output_text


def call_llm_structured_decision(
    node: str,
    purpose: str,
    prompt: str,
) -> CoachDecision:
    """
    Calls structured Gemini model.

    Uses include_raw=True when available so we can log usage_metadata.
    """

    record = ai_tracker.begin_call(
        node=node,
        purpose=purpose,
        prompt_text=prompt,
    )

    result = decision_model.invoke(prompt)

    usage_metadata: Dict[str, Any] = {}
    output_for_log: Any = result

    if STRUCTURED_INCLUDE_RAW and isinstance(result, dict):
        parsed = result.get("parsed")
        raw = result.get("raw")
        parsing_error = result.get("parsing_error")

        if parsing_error:
            raise RuntimeError(f"Structured parsing error: {parsing_error}")

        if not isinstance(parsed, CoachDecision):
            raise RuntimeError("Structured model did not return CoachDecision.")

        decision = parsed

        usage_metadata = normalize_usage_metadata(
            getattr(raw, "usage_metadata", None)
        )

        output_for_log = {
            "parsed": decision.model_dump(),
            "raw_content": message_content_to_text(getattr(raw, "content", "")),
            "usage_metadata": usage_metadata,
        }

    else:
        if not isinstance(result, CoachDecision):
            raise RuntimeError("Structured model did not return CoachDecision.")

        decision = result
        output_for_log = decision.model_dump()

    ai_tracker.end_call(
        record=record,
        output_text=safe_json(output_for_log),
        usage_metadata=usage_metadata,
    )

    return decision


# ============================================================
# 10. Utility functions
# ============================================================

def is_useful_value(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str) and not value.strip():
        return False

    if isinstance(value, list) and len(value) == 0:
        return False

    return True


def merge_lists(old: List[str], new: List[str]) -> List[str]:
    merged = list(old)

    for item in new:
        clean_item = str(item).strip()

        if clean_item and clean_item not in merged:
            merged.append(clean_item)

    return merged


def merge_profile(
    profile: Dict[str, Any],
    patch: ProfilePatch,
) -> Dict[str, Any]:
    updated = dict(profile)
    patch_dict = patch.model_dump(exclude_none=True)

    list_fields = {
        "constraints",
        "must_include",
        "must_avoid",
    }

    for key, value in patch_dict.items():
        if not is_useful_value(value):
            continue

        if key in list_fields:
            old_value = updated.get(key, [])

            if not isinstance(old_value, list):
                old_value = [str(old_value)]

            if isinstance(value, list):
                updated[key] = merge_lists(old_value, value)
            else:
                updated[key] = merge_lists(old_value, [str(value)])
        else:
            updated[key] = value

    return updated


def append_message(
    messages: List[Dict[str, str]],
    role: str,
    content: str,
) -> List[Dict[str, str]]:
    if not content or not content.strip():
        return messages

    new_messages = list(messages)

    new_messages.append(
        {
            "role": role,
            "content": content.strip(),
        }
    )

    return new_messages


# ============================================================
# 11. Node: add user message
# ============================================================

def add_user_message(state: CoachState) -> CoachState:
    logger.node_start("add_user_message", state)

    user_message = state.get("user_message", "").strip()
    recent_messages = state.get("recent_messages", [])
    turn_count = state.get("turn_count", 0)

    if user_message:
        recent_messages = append_message(
            recent_messages,
            "user",
            user_message,
        )
        turn_count += 1

    result: CoachState = {
        "recent_messages": recent_messages,
        "turn_count": turn_count,
    }

    logger.node_end("add_user_message", result)
    return result


# ============================================================
# 12. Router: summarize or continue
# ============================================================

def should_summarize_history(state: CoachState) -> str:
    recent_messages = state.get("recent_messages", [])

    decision = (
        "summarize_history"
        if len(recent_messages) > MAX_RECENT_MESSAGES
        else "coach_turn"
    )

    logger.panel(
        title="ROUTER: should_summarize_history",
        message=(
            f"Recent messages: {len(recent_messages)}\n"
            f"Max allowed before summary: {MAX_RECENT_MESSAGES}\n"
            f"Decision: {decision}"
        ),
        style="yellow",
    )

    return decision


# ============================================================
# 13. Node: summarize history
# ============================================================

def summarize_history(state: CoachState) -> CoachState:
    logger.node_start("summarize_history", state)

    recent_messages = state.get("recent_messages", [])
    old_summary = state.get("conversation_summary", "")

    messages_to_summarize = recent_messages[:-KEEP_RECENT_MESSAGES]
    messages_to_keep = recent_messages[-KEEP_RECENT_MESSAGES:]

    prompt = f"""
You are summarizing a conversation for an AI course-generator coach bot.

Goal:
Create a compact but useful memory summary.

Rules:
- Preserve user goals, preferences, constraints, decisions, and course requirements.
- Preserve important personal needs.
- Preserve course direction already agreed.
- Remove small talk and repeated information.
- Keep it concise but useful.
- Do not invent information.

Previous summary:
{old_summary}

Older messages to merge into summary:
{json.dumps(messages_to_summarize, ensure_ascii=False, indent=2)}

Return only the updated summary text.
"""

    try:
        new_summary = call_llm_text(
            node="summarize_history",
            purpose="summarize older conversation history",
            prompt=prompt,
        )

    except Exception as error:
        logger.error("summarize_history failed", error)
        new_summary = old_summary

    result: CoachState = {
        "conversation_summary": new_summary,
        "recent_messages": messages_to_keep,
    }

    logger.node_end("summarize_history", result)
    return result


# ============================================================
# 14. Node: conversational coach turn
# ============================================================

def coach_turn(state: CoachState) -> CoachState:
    logger.node_start("coach_turn", state)

    profile = state.get("profile", {})
    recent_messages = state.get("recent_messages", [])
    conversation_summary = state.get("conversation_summary", "")
    turn_count = state.get("turn_count", 0)

    prompt = f"""
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
- If enough information exists, set ready_to_generate=true.
- If not enough information exists, set ready_to_generate=false and ask the next best custom question.
- Your assistant_message must be the exact message shown to the user.
- Keep assistant_message helpful, friendly, practical, and natural.
- Do not mention JSON, schema, extraction, or internal process to the user.

When is enough information collected?
You can generate the course when you understand most of these:
- Course topic
- Desired outcome
- Target learner
- Current level
- Personal needs or customization needs
- Time available or course duration
- Preferred format
- Language
- Constraints or must-have requirements

You do NOT need every field perfectly filled.
Use judgment.

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

    try:
        decision = call_llm_structured_decision(
            node="coach_turn",
            purpose="understand user, update profile, decide next response",
            prompt=prompt,
        )

        updated_profile = merge_profile(
            profile,
            decision.profile_patch,
        )

        result: CoachState = {
            "profile": updated_profile,
            "missing_information": decision.missing_information,
            "ready_to_generate": decision.ready_to_generate,
            "assistant_message": decision.assistant_message,
        }

        logger.json_panel(
            "Coach Decision Parsed",
            {
                "decision": decision.model_dump(),
                "updated_profile": updated_profile,
            },
            style="bright_green",
        )

    except Exception as error:
        logger.error("coach_turn structured decision failed", error)

        result = {
            "assistant_message": (
                "I understood. To customize the course properly, tell me a bit more about "
                "what result you want the learner to achieve and who exactly this course is for."
            ),
            "ready_to_generate": False,
            "missing_information": [
                "desired outcome",
                "target learner",
            ],
        }

    logger.node_end("coach_turn", result)
    return result


# ============================================================
# 15. Router: generate course or wait
# ============================================================

def should_generate_course(state: CoachState) -> str:
    ready = state.get("ready_to_generate") is True
    has_outline = bool(state.get("course_outline"))

    decision = (
        "generate_course_outline"
        if ready and not has_outline
        else "append_assistant_message"
    )

    logger.panel(
        title="ROUTER: should_generate_course",
        message=(
            f"Ready to generate: {ready}\n"
            f"Already has outline: {has_outline}\n"
            f"Decision: {decision}"
        ),
        style="yellow",
    )

    return decision


# ============================================================
# 16. Node: generate final course outline
# ============================================================

def generate_course_outline(state: CoachState) -> CoachState:
    logger.node_start("generate_course_outline", state)

    profile = state.get("profile", {})
    conversation_summary = state.get("conversation_summary", "")
    recent_messages = state.get("recent_messages", [])

    prompt = f"""
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

Output requirements:
- Make it practical and customized.
- Avoid generic course structure.
- Adapt to the user's personal needs, current level, available time, preferred format, and goals.
- Include a strong course title.
- Include a clear promise.
- Include target learner description.
- Include course format.
- Include module-by-module outline.
- Include lessons inside each module.
- Include exercises and tasks.
- Include checkpoints.
- Include a final project.
- Include suggested schedule.
- Include success metrics.
- Include next steps after the course.

Use this format:

# Course Title

## Course Promise

## Best For

## Course Format

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

## Suggested Schedule

## Success Metrics

## After Finishing This Course
"""

    try:
        outline = call_llm_text(
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
        logger.error("generate_course_outline failed", error)

        # Important:
        # Do NOT set course_outline here.
        # Otherwise the app will incorrectly say DONE.
        result = {
            "assistant_message": (
                "I had an issue generating the full course outline. "
                "The model response was not valid text. The app did not mark the course as generated. "
                "Please try again."
            ),
            "ready_to_generate": False,
        }

    logger.node_end("generate_course_outline", result)
    return result


# ============================================================
# 17. Node: append assistant message
# ============================================================

def append_assistant_message(state: CoachState) -> CoachState:
    logger.node_start("append_assistant_message", state)

    assistant_message = state.get("assistant_message", "").strip()
    recent_messages = state.get("recent_messages", [])

    recent_messages = append_message(
        recent_messages,
        "assistant",
        assistant_message,
    )

    result: CoachState = {
        "recent_messages": recent_messages,
    }

    logger.node_end("append_assistant_message", result)
    return result


# ============================================================
# 18. Build graph
# ============================================================

def build_graph():
    builder = StateGraph(CoachState)

    builder.add_node("add_user_message", add_user_message)
    builder.add_node("summarize_history", summarize_history)
    builder.add_node("coach_turn", coach_turn)
    builder.add_node("generate_course_outline", generate_course_outline)
    builder.add_node("append_assistant_message", append_assistant_message)

    builder.add_edge(START, "add_user_message")

    builder.add_conditional_edges(
        "add_user_message",
        should_summarize_history,
        {
            "summarize_history": "summarize_history",
            "coach_turn": "coach_turn",
        },
    )

    builder.add_edge("summarize_history", "coach_turn")

    builder.add_conditional_edges(
        "coach_turn",
        should_generate_course,
        {
            "generate_course_outline": "generate_course_outline",
            "append_assistant_message": "append_assistant_message",
        },
    )

    builder.add_edge("generate_course_outline", "append_assistant_message")
    builder.add_edge("append_assistant_message", END)

    return builder.compile()


# ============================================================
# 19. CLI UI
# ============================================================

def print_app_header() -> None:
    header = Table.grid(expand=True)
    header.add_column(justify="center")

    title = Text("AI Course Coach Bot", style="bold white")
    subtitle = Text(
        f"Model: {MODEL_NAME} | Logging: {'ON' if DEBUG_LOGS else 'OFF'}",
        style="cyan",
    )

    header.add_row(title)
    header.add_row(subtitle)

    console.print(
        Panel(
            header,
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def print_coach_message(message: str) -> None:
    console.print(
        Panel(
            message,
            title="[bold green]Coach[/]",
            border_style="green",
            padding=(1, 2),
        )
    )


def main():
    if GEMINI_API_KEY == "PASTE_YOUR_NEW_GEMINI_API_KEY_HERE":
        console.print(
            Panel(
                "Paste your Gemini API key into GEMINI_API_KEY before running.",
                title="[bold red]Missing API Key[/]",
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

    print_app_header()

    console.print(
        Panel(
            "Type [bold]exit[/], [bold]quit[/], or [bold]q[/] to stop.",
            title="[bold green]Ready[/]",
            border_style="green",
            padding=(1, 2),
        )
    )

    # Initial assistant greeting.
    ai_tracker.start_turn(
        turn_id=0,
        user_message="[initial assistant greeting]",
    )

    state["user_message"] = ""
    state = graph.invoke(state)

    ai_tracker.end_turn()

    print_coach_message(state.get("assistant_message", ""))

    while True:
        user_input = console.input("[bold cyan]You:[/] ").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            print_coach_message("Goodbye.")
            break

        next_turn_id = state.get("turn_count", 0) + 1

        ai_tracker.start_turn(
            turn_id=next_turn_id,
            user_message=user_input,
        )

        state["user_message"] = user_input
        state = graph.invoke(state)

        ai_tracker.end_turn()

        print_coach_message(state.get("assistant_message", ""))

        if state.get("course_outline"):
            console.print(
                Panel(
                    (
                        "Course outline generated successfully.\n\n"
                        f"Total AI calls in this session: {ai_tracker.total_ai_calls}"
                    ),
                    title="[bold bright_green]DONE[/]",
                    border_style="bright_green",
                    padding=(1, 2),
                )
            )
            break


if __name__ == "__main__":
    main()