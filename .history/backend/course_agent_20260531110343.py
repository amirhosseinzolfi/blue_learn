# blue_learn_course_builder_agent.py

import os
import json
import uuid
from typing import Optional, List, Literal, TypedDict, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END


# ============================================================
# 0. ENV + MODEL
# ============================================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY is missing. Add it to your .env file or environment variables."
    )

MODEL_NAME = "gemini-2.5-flash-lite"

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=GOOGLE_API_KEY,
)


# ============================================================
# 1. DATA MODELS
# ============================================================

CourseLevel = Literal[
    "absolute_beginner",
    "beginner",
    "intermediate",
    "advanced",
    "expert"
]

PreferredDepth = Literal[
    "simple",
    "balanced",
    "deep",
    "expert"
]

PreferredStyle = Literal[
    "conceptual",
    "practical",
    "project_based",
    "visual",
    "step_by_step",
    "mixed"
]

CourseStatus = Literal[
    "collecting_info",
    "suggesting_direction",
    "ready_to_generate",
    "course_generated",
    "approved",
    "saved"
]


class CourseBrief(BaseModel):
    topic: Optional[str] = None
    user_goal: Optional[str] = None
    target_outcome: Optional[str] = None
    current_level: Optional[CourseLevel] = None
    background_context: Optional[str] = None
    preferred_depth: Optional[PreferredDepth] = None
    preferred_style: Optional[PreferredStyle] = None
    available_time_per_day_minutes: Optional[int] = None
    total_course_duration_hours: Optional[float] = None
    desired_session_length_minutes: Optional[int] = None
    preferred_language: Optional[str] = None
    use_case: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    must_include: List[str] = Field(default_factory=list)
    must_avoid: List[str] = Field(default_factory=list)


class ExtractedCourseInfo(BaseModel):
    topic: Optional[str] = None
    user_goal: Optional[str] = None
    target_outcome: Optional[str] = None
    current_level: Optional[CourseLevel] = None
    background_context: Optional[str] = None
    preferred_depth: Optional[PreferredDepth] = None
    preferred_style: Optional[PreferredStyle] = None
    available_time_per_day_minutes: Optional[int] = None
    total_course_duration_hours: Optional[float] = None
    desired_session_length_minutes: Optional[int] = None
    preferred_language: Optional[str] = None
    use_case: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    must_include: List[str] = Field(default_factory=list)
    must_avoid: List[str] = Field(default_factory=list)

    user_is_unsure: bool = False
    needs_suggestion: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class BriefEvaluation(BaseModel):
    readiness_score: float = Field(ge=0.0, le=1.0)
    can_generate: bool
    missing_fields: List[str] = Field(default_factory=list)
    next_best_question: Optional[str] = None
    reason: str


class CourseDirectionOption(BaseModel):
    title: str
    description: str
    best_for: str
    difficulty: str


class SuggestedDirections(BaseModel):
    options: List[CourseDirectionOption]
    recommended_option_title: str
    recommendation_reason: str
    follow_up_question: str


class CourseSession(BaseModel):
    session_id: str
    title: str
    description: str
    learning_objectives: List[str]
    estimated_minutes: int
    difficulty: Literal["easy", "medium", "hard"]
    key_concepts: List[str]
    practice_task: Optional[str] = None


class CourseChapter(BaseModel):
    chapter_id: str
    title: str
    description: str
    sessions: List[CourseSession]


class FinalProject(BaseModel):
    title: str
    description: str
    deliverables: List[str]


class GeneratedCourse(BaseModel):
    course_id: str
    title: str
    subtitle: str
    level: str
    total_estimated_hours: float
    recommended_duration_days: int
    session_length_minutes: int
    language: str
    target_user_summary: str
    course_goal: str
    course_description: str
    learning_outcomes: List[str]
    prerequisites: List[str]
    chapters: List[CourseChapter]
    final_project: Optional[FinalProject] = None
    recommended_pace: str


class CourseBuilderState(TypedDict):
    user_id: str
    conversation_id: str
    user_message: str
    assistant_message: Optional[str]
    user_learning_profile: Dict[str, Any]
    course_brief: Dict[str, Any]
    missing_fields: List[str]
    readiness_score: float
    can_generate: bool
    suggested_options: List[Dict[str, Any]]
    generated_course: Optional[Dict[str, Any]]
    status: CourseStatus


# ============================================================
# 2. DEMO USER PROFILE
# Replace this with your real DB-loaded user profile.
# ============================================================

DEMO_USER_PROFILE = {
    "basic_profile": {
        "display_name": "User",
        "preferred_language": "en",
        "background_summary": "Building an AI-powered micro-learning platform.",
        "current_learning_goal": "Learn how to build AI agents and personalized learning systems."
    },
    "learning_preferences": {
        "preferred_depth": "deep",
        "preferred_style": "project_based",
        "preferred_session_length_minutes": 20,
        "daily_learning_capacity_minutes": 30,
        "preferred_examples": ["real_world", "code", "startup", "product"]
    },
    "knowledge_mastery": {
        "known_domains": ["Python", "FastAPI", "AI product design"],
        "weak_areas": ["LangGraph production workflows", "agent memory architecture"]
    }
}


# ============================================================
# 3. HELPERS
# ============================================================

def to_course_brief(data: Dict[str, Any]) -> CourseBrief:
    return CourseBrief(**data)


def merge_brief(current: CourseBrief, extracted: ExtractedCourseInfo) -> CourseBrief:
    """
    Deterministic merge:
    - Explicit new values replace empty old values.
    - Existing values are kept unless the user clearly gave a new value.
    - Lists are merged/deduplicated.
    """

    current_data = current.model_dump()
    extracted_data = extracted.model_dump()

    scalar_fields = [
        "topic",
        "user_goal",
        "target_outcome",
        "current_level",
        "background_context",
        "preferred_depth",
        "preferred_style",
        "available_time_per_day_minutes",
        "total_course_duration_hours",
        "desired_session_length_minutes",
        "preferred_language",
        "use_case",
    ]

    for field in scalar_fields:
        new_value = extracted_data.get(field)
        if new_value is not None:
            current_data[field] = new_value

    list_fields = ["constraints", "must_include", "must_avoid"]
    for field in list_fields:
        existing = current_data.get(field, []) or []
        new_items = extracted_data.get(field, []) or []
        merged = list(dict.fromkeys(existing + new_items))
        current_data[field] = merged

    return CourseBrief(**current_data)


def apply_profile_defaults(brief: CourseBrief, profile: Dict[str, Any]) -> CourseBrief:
    """
    Use the existing user profile to fill weak defaults.
    Do not override explicit user choices.
    """

    data = brief.model_dump()

    learning_prefs = profile.get("learning_preferences", {})
    basic_profile = profile.get("basic_profile", {})

    if not data.get("preferred_language"):
        data["preferred_language"] = basic_profile.get("preferred_language", "en")

    if not data.get("preferred_depth"):
        data["preferred_depth"] = learning_prefs.get("preferred_depth", "balanced")

    if not data.get("preferred_style"):
        data["preferred_style"] = learning_prefs.get("preferred_style", "mixed")

    if not data.get("desired_session_length_minutes"):
        data["desired_session_length_minutes"] = learning_prefs.get(
            "preferred_session_length_minutes",
            20
        )

    if not data.get("available_time_per_day_minutes"):
        data["available_time_per_day_minutes"] = learning_prefs.get(
            "daily_learning_capacity_minutes",
            30
        )

    return CourseBrief(**data)


def format_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


# ============================================================
# 4. STRUCTURED LLM CHAINS
# ============================================================

extractor_llm = llm.with_structured_output(ExtractedCourseInfo)
evaluator_llm = llm.with_structured_output(BriefEvaluation)
suggestion_llm = llm.with_structured_output(SuggestedDirections)
course_generator_llm = llm.with_structured_output(GeneratedCourse)


# ============================================================
# 5. LANGGRAPH NODES
# ============================================================

def load_user_profile_node(state: CourseBuilderState) -> CourseBuilderState:
    """
    In production:
    - Load user profile from PostgreSQL.
    - Load active learning goals.
    - Load weak concepts / known domains.
    """

    if not state.get("user_learning_profile"):
        state["user_learning_profile"] = DEMO_USER_PROFILE

    if not state.get("course_brief"):
        empty_brief = CourseBrief()
        empty_brief = apply_profile_defaults(empty_brief, state["user_learning_profile"])
        state["course_brief"] = empty_brief.model_dump()

    return state


def analyze_user_message_node(state: CourseBuilderState) -> CourseBuilderState:
    brief = to_course_brief(state["course_brief"])
    profile = state["user_learning_profile"]
    user_message = state["user_message"]

    prompt = f"""
You are Blue, an expert AI course designer for a personalized micro-learning platform.

Your job in this step:
Extract course requirements from the user's latest message.

Important rules:
- Do NOT generate the course.
- Only extract fields that are explicitly stated or strongly implied.
- If the user is vague or unsure, set needs_suggestion=true.
- If the user says they do not know what direction to choose, set user_is_unsure=true.
- Keep extracted fields concise and useful.
- Match values to the allowed schema.

Current course brief:
{format_json(brief.model_dump())}

User learning profile:
{format_json(profile)}

Latest user message:
{user_message}
"""

    extracted = extractor_llm.invoke(prompt)

    updated_brief = merge_brief(brief, extracted)
    updated_brief = apply_profile_defaults(updated_brief, profile)

    state["course_brief"] = updated_brief.model_dump()

    if extracted.needs_suggestion or extracted.user_is_unsure:
        state["status"] = "suggesting_direction"
    else:
        state["status"] = "collecting_info"

    return state


def evaluate_brief_node(state: CourseBuilderState) -> CourseBuilderState:
    brief = to_course_brief(state["course_brief"])
    profile = state["user_learning_profile"]

    prompt = f"""
You are evaluating whether a personalized course brief is ready for course generation.

A course can be generated only when the assistant knows enough to create a useful, personalized, efficient course.

Required fields:
- topic
- user_goal or target_outcome
- current_level
- preferred_style
- available_time_per_day_minutes or total_course_duration_hours
- desired_session_length_minutes
- preferred_language

Optional but useful:
- background_context
- use_case
- must_include
- must_avoid
- constraints

Scoring:
- 0.00 to 0.50: not ready
- 0.51 to 0.75: partially ready, ask one strong question
- 0.76 to 0.90: ready with minor assumptions
- 0.91 to 1.00: fully ready

Rules:
- Ask only ONE next best question.
- If the missing field can be reasonably inferred from the user profile, do not ask it.
- Prefer action-oriented questions.
- Do not generate the course here.

Course brief:
{format_json(brief.model_dump())}

User profile:
{format_json(profile)}
"""

    evaluation = evaluator_llm.invoke(prompt)

    state["readiness_score"] = evaluation.readiness_score
    state["can_generate"] = evaluation.can_generate
    state["missing_fields"] = evaluation.missing_fields

    if evaluation.can_generate:
        state["status"] = "ready_to_generate"
        state["assistant_message"] = (
            "I have enough information to generate your personalized course outline now."
        )
    else:
        state["status"] = "collecting_info"
        state["assistant_message"] = evaluation.next_best_question

    return state


def suggest_direction_node(state: CourseBuilderState) -> CourseBuilderState:
    brief = to_course_brief(state["course_brief"])
    profile = state["user_learning_profile"]

    prompt = f"""
You are Blue, an expert AI course designer.

The user is vague or unsure. Suggest 3 strong course directions based on:
- User message
- Current course brief
- User learning profile
- Likely practical value for the user

Rules:
- Do not generate the final course.
- Suggest clear course direction options.
- Recommend one option.
- End with one follow-up question asking the user to choose or refine.

Course brief:
{format_json(brief.model_dump())}

User profile:
{format_json(profile)}

Latest user message:
{state["user_message"]}
"""

    suggestions = suggestion_llm.invoke(prompt)

    state["suggested_options"] = [opt.model_dump() for opt in suggestions.options]

    options_text = "\n".join(
        [
            f"{i + 1}. {opt.title}\n   {opt.description}\n   Best for: {opt.best_for}\n   Difficulty: {opt.difficulty}"
            for i, opt in enumerate(suggestions.options)
        ]
    )

    state["assistant_message"] = (
        f"I can help you choose the strongest direction.\n\n"
        f"{options_text}\n\n"
        f"My recommendation: {suggestions.recommended_option_title}\n"
        f"Reason: {suggestions.recommendation_reason}\n\n"
        f"{suggestions.follow_up_question}"
    )

    state["status"] = "suggesting_direction"
    return state


def generate_course_outline_node(state: CourseBuilderState) -> CourseBuilderState:
    brief = to_course_brief(state["course_brief"])
    profile = state["user_learning_profile"]

    course_id = str(uuid.uuid4())

    prompt = f"""
You are Blue, an elite AI course architect for a personalized micro-learning platform.

Generate a complete personalized course outline.

Important rules:
- Return only structured data according to the schema.
- The course must be personalized to the user's goal, level, background, time, and preferred learning style.
- Use micro-sessions.
- Each session should be focused, practical, and self-contained.
- The course should be realistic for the requested total time.
- If total_course_duration_hours is missing, infer a reasonable total duration from the topic and available time.
- Make the course efficient, not bloated.
- Include practical tasks.
- Include a final project when appropriate.
- Course ID must be: {course_id}
- Create unique chapter_id and session_id values.

Course brief:
{format_json(brief.model_dump())}

User learning profile:
{format_json(profile)}
"""

    course = course_generator_llm.invoke(prompt)

    state["generated_course"] = course.model_dump()
    state["status"] = "course_generated"

    state["assistant_message"] = (
        "I generated your personalized course outline.\n\n"
        f"{format_json(course.model_dump())}"
    )

    return state


# ============================================================
# 6. ROUTING LOGIC
# ============================================================

def route_after_analysis(state: CourseBuilderState) -> str:
    if state["status"] == "suggesting_direction":
        return "suggest_direction"
    return "evaluate_brief"


def route_after_evaluation(state: CourseBuilderState) -> str:
    if state["can_generate"]:
        return "generate_course_outline"
    return END


# ============================================================
# 7. BUILD LANGGRAPH
# ============================================================

def build_course_builder_graph():
    graph = StateGraph(CourseBuilderState)

    graph.add_node("load_user_profile", load_user_profile_node)
    graph.add_node("analyze_user_message", analyze_user_message_node)
    graph.add_node("evaluate_brief", evaluate_brief_node)
    graph.add_node("suggest_direction", suggest_direction_node)
    graph.add_node("generate_course_outline", generate_course_outline_node)

    graph.add_edge(START, "load_user_profile")
    graph.add_edge("load_user_profile", "analyze_user_message")

    graph.add_conditional_edges(
        "analyze_user_message",
        route_after_analysis,
        {
            "suggest_direction": "suggest_direction",
            "evaluate_brief": "evaluate_brief",
        },
    )

    graph.add_edge("suggest_direction", END)

    graph.add_conditional_edges(
        "evaluate_brief",
        route_after_evaluation,
        {
            "generate_course_outline": "generate_course_outline",
            END: END,
        },
    )

    graph.add_edge("generate_course_outline", END)

    return graph.compile()


course_builder_app = build_course_builder_graph()


# ============================================================
# 8. CONVERSATION MANAGER
# ============================================================

class CourseBuilderSession:
    """
    Simple in-memory session manager for local testing.

    In production:
    - Store state in PostgreSQL.
    - Use LangGraph checkpointer.
    - Save CourseBrief after every turn.
    """

    def __init__(self, user_id: str):
        self.state: CourseBuilderState = {
            "user_id": user_id,
            "conversation_id": str(uuid.uuid4()),
            "user_message": "",
            "assistant_message": None,
            "user_learning_profile": DEMO_USER_PROFILE,
            "course_brief": CourseBrief().model_dump(),
            "missing_fields": [],
            "readiness_score": 0.0,
            "can_generate": False,
            "suggested_options": [],
            "generated_course": None,
            "status": "collecting_info",
        }

    def send(self, user_message: str) -> str:
        self.state["user_message"] = user_message

        result = course_builder_app.invoke(self.state)

        # Persist updated state
        self.state.update(result)

        return self.state.get("assistant_message") or ""

    def approve_and_save(self):
        """
        Placeholder save function.

        In production:
        - Save course to courses table
        - Save chapters
        - Save sessions
        - Trigger learning event: COURSE_CREATED
        - Trigger profile updater agent
        """

        if not self.state.get("generated_course"):
            return {
                "saved": False,
                "message": "No generated course exists yet."
            }

        self.state["status"] = "saved"

        return {
            "saved": True,
            "course": self.state["generated_course"]
        }


# ============================================================
# 9. CLI DEMO
# ============================================================

def run_cli_demo():
    print("\nBlue Learn Course Builder Agent")
    print("Type 'exit' to quit.")
    print("Type 'save' after a course is generated to save it.")
    print("-" * 60)

    session = CourseBuilderSession(user_id="demo_user")

    opening = (
        "Hi, I’m Blue. Tell me what you want to learn, and I’ll help you turn it "
        "into a personalized course. You can start simple, for example: "
        "'I want to learn LangGraph for building AI agents.'"
    )

    print(f"\nBlue: {opening}")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("\nBlue: Goodbye.")
            break

        if user_input.lower() == "save":
            result = session.approve_and_save()
            print("\nBlue:")
            print(format_json(result))
            continue

        response = session.send(user_input)
        print("\nBlue:")
        print(response)

        if session.state.get("generated_course"):
            print("\nYou can type 'save' to save this course.")


if __name__ == "__main__":
    run_cli_demo()