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
- Beautiful colorful terminal logging with Rich

Run:
    python course_coach_bot.py
"""

import json
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

GEMINI_API_KEY = "AIzaSyDZLcdWEYGtvlmcDrPSaZS1VxMIjOAFOcI"

MODEL_NAME = "gemini-flash-lite-latest"

DEBUG_LOGS = True
FULL_PROMPT_LOGS = True
SHOW_FULL_STATE = True
SHOW_MODEL_OUTPUT = True

MAX_RECENT_MESSAGES = 10
KEEP_RECENT_MESSAGES = 6


# ============================================================
# 2. Rich logger setup
# ============================================================

rich_traceback_install(show_locals=False)

console = Console()


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

    def info(self, title: str, message: str, style: str = "cyan") -> None:
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

    def warning(self, title: str, message: str) -> None:
        if not self.enabled:
            return

        console.print(
            Panel(
                message,
                title=f"[bold yellow]{title}[/]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    def success(self, title: str, message: str) -> None:
        if not self.enabled:
            return

        console.print(
            Panel(
                message,
                title=f"[bold green]{title}[/]",
                border_style="green",
                padding=(1, 2),
            )
        )

    def error(self, title: str, error: Exception) -> None:
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

    def json(self, title: str, data: Any, style: str = "blue") -> None:
        if not self.enabled:
            return

        try:
            formatted = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        except Exception:
            formatted = str(data)

        syntax = Syntax(
            formatted,
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

    def prompt(self, title: str, prompt_text: str) -> None:
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

    def node_start(self, node_name: str, state: Dict[str, Any]) -> None:
        if not self.enabled:
            return

        self.rule(f"NODE START: {node_name}", "bold cyan")

        summary_table = Table(
            title=f"Node Input Summary — {node_name}",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
        )

        summary_table.add_column("Key", style="bold")
        summary_table.add_column("Value", overflow="fold")

        summary_table.add_row("Time", self.time())
        summary_table.add_row("Turn Count", str(state.get("turn_count", 0)))
        summary_table.add_row("Ready To Generate", str(state.get("ready_to_generate", False)))
        summary_table.add_row("Has Course Outline", str(bool(state.get("course_outline"))))
        summary_table.add_row("Recent Messages", str(len(state.get("recent_messages", []))))
        summary_table.add_row("Summary Exists", str(bool(state.get("conversation_summary"))))

        console.print(summary_table)

        if self.show_full_state:
            self.json(f"Full State Input — {node_name}", state, style="cyan")

    def node_end(self, node_name: str, result: Dict[str, Any]) -> None:
        if not self.enabled:
            return

        self.json(f"Node Output — {node_name}", result, style="green")
        self.rule(f"NODE END: {node_name}", "bold green")

    def model_call(self, title: str, prompt_text: str) -> None:
        if not self.enabled:
            return

        self.info(
            title=f"MODEL CALL: {title}",
            message=f"Model: {MODEL_NAME}\nPrompt logging: {self.full_prompts}",
            style="magenta",
        )

        self.prompt(f"Prompt — {title}", prompt_text)

    def model_output(self, title: str, output: Any) -> None:
        if not self.enabled or not self.show_model_output:
            return

        self.json(f"Model Output — {title}", output, style="green")


logger = DebugLogger(
    enabled=DEBUG_LOGS,
    full_prompts=FULL_PROMPT_LOGS,
    show_full_state=SHOW_FULL_STATE,
    show_model_output=SHOW_MODEL_OUTPUT,
)


# ============================================================
# 3. Gemini model setup
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
# 4. Structured data models
# ============================================================

class ProfilePatch(BaseModel):
    """
    Partial update to the user/course profile.
    """

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
    """
    Model decision for one conversational turn.
    """

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


decision_model = structured_llm.with_structured_output(CoachDecision)


# ============================================================
# 5. LangGraph state
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
# 6. Utility functions
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


def merge_profile(profile: Dict[str, Any], patch: ProfilePatch) -> Dict[str, Any]:
    """
    Merge new structured profile info into existing profile.
    """

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
# 7. Node: add user message
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
# 8. Router: summarize or continue
# ============================================================

def should_summarize_history(state: CoachState) -> str:
    recent_messages = state.get("recent_messages", [])

    logger.info(
        title="ROUTER: should_summarize_history",
        message=(
            f"Recent messages: {len(recent_messages)}\n"
            f"Max allowed before summary: {MAX_RECENT_MESSAGES}\n"
            f"Decision: {'summarize_history' if len(recent_messages) > MAX_RECENT_MESSAGES else 'coach_turn'}"
        ),
        style="yellow",
    )

    if len(recent_messages) > MAX_RECENT_MESSAGES:
        return "summarize_history"

    return "coach_turn"


# ============================================================
# 9. Node: summarize history
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

    logger.model_call("summarize_history", prompt)

    try:
        response = llm.invoke(prompt)
        new_summary = response.content.strip()

        logger.model_output(
            "summarize_history",
            {
                "summary": new_summary,
                "usage_metadata": getattr(response, "usage_metadata", None),
            },
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
# 10. Node: conversational coach turn
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

    logger.model_call("coach_turn", prompt)

    try:
        decision: CoachDecision = decision_model.invoke(prompt)

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

        logger.model_output(
            "coach_turn",
            {
                "decision": decision.model_dump(),
                "updated_profile": updated_profile,
            },
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
# 11. Router: generate course or wait
# ============================================================

def should_generate_course(state: CoachState) -> str:
    ready = state.get("ready_to_generate") is True
    has_outline = bool(state.get("course_outline"))

    decision = "generate_course_outline" if ready and not has_outline else "append_assistant_message"

    logger.info(
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
# 12. Node: generate final course outline
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

    logger.model_call("generate_course_outline", prompt)

    try:
        response = llm.invoke(prompt)
        outline = response.content.strip()

        logger.model_output(
            "generate_course_outline",
            {
                "outline": outline,
                "usage_metadata": getattr(response, "usage_metadata", None),
            },
        )

    except Exception as error:
        logger.error("generate_course_outline failed", error)

        outline = (
            "I had an issue generating the full course outline. "
            "Please check your Gemini API key, model name, and package versions."
        )

    result: CoachState = {
        "course_outline": outline,
        "assistant_message": outline,
        "ready_to_generate": True,
    }

    logger.node_end("generate_course_outline", result)
    return result


# ============================================================
# 13. Node: append assistant message
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
# 14. Build graph
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
# 15. CLI app
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


def main():
    if GEMINI_API_KEY == "PASTE_YOUR_NEW_GEMINI_API_KEY_HERE":
        console.print(
            Panel(
                "You must paste your Gemini API key into GEMINI_API_KEY before running.",
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

    # First assistant message generated dynamically.
    state["user_message"] = ""
    state = graph.invoke(state)

    console.print(
        Panel(
            state.get("assistant_message", ""),
            title="[bold green]Coach[/]",
            border_style="green",
            padding=(1, 2),
        )
    )

    while True:
        user_input = console.input("[bold cyan]You:[/] ").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            console.print(
                Panel(
                    "Goodbye.",
                    title="[bold green]Coach[/]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
            break

        state["user_message"] = user_input
        state = graph.invoke(state)

        console.print(
            Panel(
                state.get("assistant_message", ""),
                title="[bold green]Coach[/]",
                border_style="green",
                padding=(1, 2),
            )
        )

        if state.get("course_outline"):
            console.print(
                Panel(
                    "Course outline generated successfully.",
                    title="[bold bright_green]DONE[/]",
                    border_style="bright_green",
                    padding=(1, 2),
                )
            )
            break


if __name__ == "__main__":
    main()