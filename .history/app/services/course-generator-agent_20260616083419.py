"""
course_coach_bot.py

Fully conversational AI course-generator coach bot.

Features:
- Uses LangGraph for stateful workflow.
- Uses Gemini through LangChain Google GenAI.
- Fully conversational and interactive.
- Does NOT use fixed/prebuilt question templates.
- Uses previous conversation history.
- Summarizes older conversation history to reduce token usage.
- Extracts and updates structured user/course profile.
- Generates a customized course outline when enough information is collected.
- Includes detailed readable terminal logging for debugging.

Run:
    python course_coach_bot.py
"""

import os
import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END


# ============================================================
# 1. Environment and configuration
# ============================================================

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

DEBUG_LOGS = os.getenv("DEBUG_LOGS", "true").lower() == "true"
FULL_PROMPT_LOGS = os.getenv("FULL_PROMPT_LOGS", "true").lower() == "true"

MAX_RECENT_MESSAGES = int(os.getenv("MAX_RECENT_MESSAGES", "10"))
KEEP_RECENT_MESSAGES = int(os.getenv("KEEP_RECENT_MESSAGES", "6"))

if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError(
        "Missing GOOGLE_API_KEY or GEMINI_API_KEY. Add one of them to your .env file."
    )


# ============================================================
# 2. Logging helpers
# ============================================================

def now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def to_pretty_json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(data)


def log_block(title: str, content: Any = None) -> None:
    """
    Readable terminal logging.
    Shows every important process, state, prompt, and output.
    """

    if not DEBUG_LOGS:
        return

    print("\n" + "=" * 100)
    print(f"[{now_time()}] {title}")
    print("-" * 100)

    if content is not None:
        if isinstance(content, (dict, list)):
            print(to_pretty_json(content))
        else:
            print(str(content))

    print("=" * 100 + "\n")


def log_error(title: str, error: Exception) -> None:
    if not DEBUG_LOGS:
        return

    print("\n" + "!" * 100)
    print(f"[{now_time()}] ERROR: {title}")
    print("-" * 100)
    print(str(error))
    print(traceback.format_exc())
    print("!" * 100 + "\n")


# ============================================================
# 3. Gemini model setup
# ============================================================

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0.2,
)

structured_llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0,
)


# ============================================================
# 4. Structured data models
# ============================================================

class ProfilePatch(BaseModel):
    """
    Partial update to the course/user profile.
    The model should only fill fields that are clearly understood from conversation.
    """

    course_topic: Optional[str] = Field(
        None,
        description="The main course topic or skill the user wants to build."
    )

    desired_outcome: Optional[str] = Field(
        None,
        description="The final practical outcome the user wants from the course."
    )

    target_learner: Optional[str] = Field(
        None,
        description="Who the course is for. Could be the user, their clients, employees, beginners, etc."
    )

    current_level: Optional[str] = Field(
        None,
        description="Current knowledge level of the learner."
    )

    personal_needs: Optional[str] = Field(
        None,
        description="Personal needs, learning style, challenges, goals, limitations, or preferences."
    )

    business_context: Optional[str] = Field(
        None,
        description="Relevant business or professional context, if any."
    )

    time_available: Optional[str] = Field(
        None,
        description="Available time, deadline, duration, weekly hours, or learning schedule."
    )

    preferred_format: Optional[str] = Field(
        None,
        description="Preferred course format: videos, text, tasks, project-based, coaching, quizzes, etc."
    )

    language: Optional[str] = Field(
        None,
        description="Preferred language for the course."
    )

    constraints: Optional[List[str]] = Field(
        None,
        description="Important constraints, must-have items, must-avoid items, tools, budget, platform, etc."
    )

    must_include: Optional[List[str]] = Field(
        None,
        description="Topics, examples, tools, or sections the course must include."
    )

    must_avoid: Optional[List[str]] = Field(
        None,
        description="Topics, methods, styles, or formats the course should avoid."
    )


class CoachDecision(BaseModel):
    """
    The conversational coach's decision for this turn.
    """

    profile_patch: ProfilePatch = Field(
        default_factory=ProfilePatch,
        description="New profile information learned from this turn."
    )

    missing_information: List[str] = Field(
        default_factory=list,
        description="Important missing details still needed before generating a high-quality course."
    )

    ready_to_generate: bool = Field(
        False,
        description="True only when enough information exists to generate a useful customized course."
    )

    assistant_message: str = Field(
        ...,
        description="The exact conversational message to show the user now."
    )

    debug_notes: str = Field(
        "",
        description="Brief explanation of why this response was chosen."
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
    Merge structured profile patch into existing profile.

    Rules:
    - Only overwrite normal string fields if the new value is useful.
    - For list fields, merge instead of replacing.
    """

    updated = dict(profile)
    patch_dict = patch.model_dump(exclude_none=True)

    list_fields = {"constraints", "must_include", "must_avoid"}

    for key, value in patch_dict.items():
        if not is_useful_value(value):
            continue

        if key in list_fields:
            old_list = updated.get(key, [])
            if not isinstance(old_list, list):
                old_list = [str(old_list)]

            if isinstance(value, list):
                updated[key] = merge_lists(old_list, value)
            else:
                updated[key] = merge_lists(old_list, [str(value)])
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
# 7. Node: add user message to short-term history
# ============================================================

def add_user_message(state: CoachState) -> CoachState:
    log_block("NODE START: add_user_message", state)

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

    log_block("NODE END: add_user_message", result)
    return result


# ============================================================
# 8. Router: summarize or continue
# ============================================================

def should_summarize_history(state: CoachState) -> str:
    recent_messages = state.get("recent_messages", [])

    if len(recent_messages) > MAX_RECENT_MESSAGES:
        return "summarize_history"

    return "coach_turn"


# ============================================================
# 9. Node: summarize older conversation history
# ============================================================

def summarize_history(state: CoachState) -> CoachState:
    """
    Compress older conversation into a compact summary.

    Token optimization:
    - Keep only recent messages raw.
    - Move older messages into a short but useful summary.
    """

    log_block("NODE START: summarize_history", state)

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
- Preserve any important personal needs.
- Preserve any course direction already agreed.
- Remove small talk and repeated information.
- Keep it concise but complete enough for future turns.
- Do not invent information.

Previous summary:
{old_summary}

Older messages to merge into summary:
{json.dumps(messages_to_summarize, ensure_ascii=False, indent=2)}

Return only the updated summary text.
"""

    if FULL_PROMPT_LOGS:
        log_block("PROMPT: summarize_history", prompt)

    try:
        response = llm.invoke(prompt)
        new_summary = response.content.strip()

        log_block(
            "MODEL OUTPUT: summarize_history",
            {
                "summary": new_summary,
                "usage_metadata": getattr(response, "usage_metadata", None),
            },
        )

    except Exception as error:
        log_error("summarize_history failed", error)
        new_summary = old_summary

    result: CoachState = {
        "conversation_summary": new_summary,
        "recent_messages": messages_to_keep,
    }

    log_block("NODE END: summarize_history", result)
    return result


# ============================================================
# 10. Node: fully conversational coach turn
# ============================================================

def coach_turn(state: CoachState) -> CoachState:
    """
    Main conversational intelligence node.

    This replaces fixed question templates.

    It does three jobs in one LLM call:
    1. Understand conversation.
    2. Update profile.
    3. Decide the best next assistant response.
    """

    log_block("NODE START: coach_turn", state)

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
- Keep assistant_message helpful, friendly, and practical.
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

    if FULL_PROMPT_LOGS:
        log_block("PROMPT: coach_turn", prompt)

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

        log_block(
            "MODEL OUTPUT: coach_turn",
            {
                "decision": decision.model_dump(),
                "updated_profile": updated_profile,
            },
        )

    except Exception as error:
        log_error("coach_turn structured decision failed", error)

        fallback_message = (
            "I understood. To customize the course properly, tell me a bit more about "
            "what result you want the learner to achieve and who exactly this course is for."
        )

        result = {
            "assistant_message": fallback_message,
            "ready_to_generate": False,
            "missing_information": [
                "desired outcome",
                "target learner",
            ],
        }

    log_block("NODE END: coach_turn", result)
    return result


# ============================================================
# 11. Router: generate course or end turn
# ============================================================

def should_generate_course(state: CoachState) -> str:
    if state.get("ready_to_generate") is True and not state.get("course_outline"):
        return "generate_course_outline"

    return "append_assistant_message"


# ============================================================
# 12. Node: generate final customized course outline
# ============================================================

def generate_course_outline(state: CoachState) -> CoachState:
    """
    Generate the final course outline.
    Uses structured profile + summarized history + recent messages.
    """

    log_block("NODE START: generate_course_outline", state)

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

    if FULL_PROMPT_LOGS:
        log_block("PROMPT: generate_course_outline", prompt)

    try:
        response = llm.invoke(prompt)
        outline = response.content.strip()

        log_block(
            "MODEL OUTPUT: generate_course_outline",
            {
                "outline": outline,
                "usage_metadata": getattr(response, "usage_metadata", None),
            },
        )

    except Exception as error:
        log_error("generate_course_outline failed", error)

        outline = (
            "I had an issue generating the full course outline. "
            "Please try again or check your Gemini model/API configuration."
        )

    result: CoachState = {
        "course_outline": outline,
        "assistant_message": outline,
        "ready_to_generate": True,
    }

    log_block("NODE END: generate_course_outline", result)
    return result


# ============================================================
# 13. Node: append assistant message to recent history
# ============================================================

def append_assistant_message(state: CoachState) -> CoachState:
    """
    Store assistant response in recent history so future turns use it.
    """

    log_block("NODE START: append_assistant_message", state)

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

    log_block("NODE END: append_assistant_message", result)
    return result


# ============================================================
# 14. Build LangGraph
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

    graph = builder.compile()

    return graph


# ============================================================
# 15. CLI chat app
# ============================================================

def main():
    graph = build_graph()

    state: CoachState = {
        "profile": {},
        "recent_messages": [],
        "conversation_summary": "",
        "turn_count": 0,
        "ready_to_generate": False,
    }

    print("\n" + "=" * 100)
    print("AI Course Coach Bot")
    print(f"Model: {MODEL_NAME}")
    print("Type 'exit' to quit.")
    print("=" * 100 + "\n")

    # First assistant message generated dynamically by model.
    state["user_message"] = ""
    state = graph.invoke(state)

    print(f"\nCoach:\n{state.get('assistant_message', '')}\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nCoach: Goodbye.\n")
            break

        state["user_message"] = user_input

        state = graph.invoke(state)

        print(f"\nCoach:\n{state.get('assistant_message', '')}\n")

        if state.get("course_outline"):
            print("\n" + "=" * 100)
            print("COURSE OUTLINE GENERATED")
            print("=" * 100 + "\n")
            break


if __name__ == "__main__":
    main()