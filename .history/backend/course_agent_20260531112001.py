# blue_learn_strict_course_builder_agent.py

import os
import re
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END


# ============================================================
# 0. SETUP
# ============================================================

load_dotenv()

console = Console()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY. Add it to your .env file.")

MODEL_NAME = "gemini-2.5-flash-lite"

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2,
)


# ============================================================
# 1. TERMINAL LOGGING
# ============================================================

ENABLE_LOGGING = True


def log_node(name: str, message: str = ""):
    if not ENABLE_LOGGING:
        return
    console.print(f"[bold cyan]▶ {name}[/bold cyan] [dim]{message}[/dim]")


def log_success(message: str):
    if not ENABLE_LOGGING:
        return
    console.print(f"[bold green]✓[/bold green] {message}")


def log_warning(message: str):
    if not ENABLE_LOGGING:
        return
    console.print(f"[bold yellow]•[/bold yellow] {message}")


def log_error(message: str):
    if not ENABLE_LOGGING:
        return
    console.print(f"[bold red]✗[/bold red] {message}")


def log_progress(completed: int, total: int, missing: List[str]):
    if not ENABLE_LOGGING:
        return

    percent = int((completed / total) * 100) if total else 0
    bar_length = 24
    filled = int(bar_length * completed / total) if total else 0
    bar = "█" * filled + "░" * (bar_length - filled)

    color = "red"
    if percent >= 50:
        color = "yellow"
    if percent >= 85:
        color = "green"

    console.print(
        f"[bold {color}]Brief Progress:[/bold {color}] "
        f"[{color}]{bar}[/{color}] {completed}/{total} ({percent}%)"
    )

    if missing:
        console.print(f"[dim]Missing next:[/dim] [yellow]{missing[0]}[/yellow]")


def print_brief_table(brief: Dict[str, Any], missing: List[str]):
    table = Table(title="Course Brief Snapshot", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="dim")
    table.add_column("Value", overflow="fold")

    for key, value in brief.items():
        if key in ["must_include", "must_avoid", "constraints"]:
            display = ", ".join(value) if value else "-"
        else:
            display = str(value) if value not in [None, ""] else "-"

        style = "green" if key not in missing and display != "-" else "yellow"
        table.add_row(key, f"[{style}]{display}[/{style}]")

    console.print(table)


# ============================================================
# 2. SCHEMA
# ============================================================

CourseLevel = Literal[
    "absolute_beginner",
    "beginner",
    "intermediate",
    "advanced",
    "expert",
]

PreferredDepth = Literal[
    "simple",
    "balanced",
    "deep",
    "expert",
]

PreferredStyle = Literal[
    "conceptual",
    "practical",
    "project_based",
    "visual",
    "step_by_step",
    "mixed",
]

Status = Literal[
    "collecting",
    "suggesting",
    "ready",
    "generated",
    "saved",
]


class CourseBrief(BaseModel):
    topic: Optional[str] = None
    course_direction: Optional[str] = None
    user_goal: Optional[str] = None
    target_outcome: Optional[str] = None
    current_level: Optional[CourseLevel] = None
    background_context: Optional[str] = None
    use_case: Optional[str] = None
    preferred_style: Optional[PreferredStyle] = None
    preferred_depth: Optional[PreferredDepth] = None
    available_time_per_day_minutes: Optional[int] = None
    total_course_duration_hours: Optional[float] = None
    desired_session_length_minutes: Optional[int] = None
    preferred_language: Optional[str] = None
    must_include: List[str] = Field(default_factory=list)
    must_avoid: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    constraints_confirmed: bool = False


REQUIRED_FIELD_ORDER = [
    "topic",
    "course_direction",
    "user_goal",
    "target_outcome",
    "current_level",
    "background_context",
    "use_case",
    "preferred_style",
    "preferred_depth",
    "available_time_per_day_minutes",
    "total_course_duration_hours",
    "desired_session_length_minutes",
    "preferred_language",
    "constraints_confirmed",
]


class ExtractedCourseInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Optional[str] = None
    course_direction: Optional[str] = None
    user_goal: Optional[str] = None
    target_outcome: Optional[str] = None
    current_level: Optional[CourseLevel] = None
    background_context: Optional[str] = None
    use_case: Optional[str] = None
    preferred_style: Optional[PreferredStyle] = None
    preferred_depth: Optional[PreferredDepth] = None
    available_time_per_day_minutes: Optional[int] = None
    total_course_duration_hours: Optional[float] = None
    desired_session_length_minutes: Optional[int] = None
    preferred_language: Optional[str] = None
    must_include: List[str] = Field(default_factory=list)
    must_avoid: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    constraints_confirmed: Optional[bool] = None

    user_is_unsure: bool = False
    needs_direction_suggestions: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DirectionOption(BaseModel):
    title: str
    description: str


class DirectionSuggestions(BaseModel):
    options: List[DirectionOption] = Field(min_length=2, max_length=3)
    question: str


class CourseSession(BaseModel):
    session_id: str
    title: str
    description: str
    estimated_minutes: int
    difficulty: Literal["easy", "medium", "hard"]
    learning_objectives: List[str]
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
    assistant_message: str
    user_learning_profile: Dict[str, Any]
    course_brief: Dict[str, Any]
    missing_fields: List[str]
    completed_fields: List[str]
    readiness_score: float
    suggested_options: List[Dict[str, Any]]
    generated_course: Optional[Dict[str, Any]]
    status: Status
    last_saved_path: Optional[str]


# ============================================================
# 3. DEMO PROFILE
# Replace with DB-loaded profile in production.
# ============================================================

DEMO_USER_PROFILE = {
    "basic_profile": {
        "display_name": "User",
        "preferred_language": "en",
        "background_summary": "Building an AI-powered micro-learning platform.",
    },
    "learning_preferences": {
        "preferred_depth": "deep",
        "preferred_style": "project_based",
        "preferred_session_length_minutes": 20,
        "daily_learning_capacity_minutes": 30,
        "preferred_examples": ["real_world", "code", "product"],
    },
    "knowledge_mastery": {
        "known_domains": ["Python", "FastAPI", "AI product design"],
        "weak_areas": ["LangGraph production workflows", "agent memory architecture"],
    },
}


# ============================================================
# 4. STRUCTURED LLM MODELS
# ============================================================

extractor_llm = llm.with_structured_output(ExtractedCourseInfo)
suggestion_llm = llm.with_structured_output(DirectionSuggestions)
course_llm = llm.with_structured_output(GeneratedCourse)


# ============================================================
# 5. HELPERS
# ============================================================

def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def brief_from_state(state: CourseBuilderState) -> CourseBrief:
    return CourseBrief(**state["course_brief"])


def to_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def merge_brief(current: CourseBrief, extracted: ExtractedCourseInfo) -> CourseBrief:
    data = current.model_dump()
    new = extracted.model_dump()

    scalar_fields = [
        "topic",
        "course_direction",
        "user_goal",
        "target_outcome",
        "current_level",
        "background_context",
        "use_case",
        "preferred_style",
        "preferred_depth",
        "available_time_per_day_minutes",
        "total_course_duration_hours",
        "desired_session_length_minutes",
        "preferred_language",
    ]

    for field in scalar_fields:
        value = new.get(field)
        if isinstance(value, str):
            value = normalize_text(value)
        if value is not None:
            data[field] = value

    for field in ["must_include", "must_avoid", "constraints"]:
        existing = data.get(field, []) or []
        incoming = new.get(field, []) or []
        merged = []
        for item in existing + incoming:
            item = normalize_text(str(item))
            if item and item.lower() not in [x.lower() for x in merged]:
                merged.append(item)
        data[field] = merged

    if new.get("constraints_confirmed") is not None:
        data["constraints_confirmed"] = bool(new["constraints_confirmed"])

    return CourseBrief(**data)


def apply_safe_profile_defaults(brief: CourseBrief, profile: Dict[str, Any]) -> CourseBrief:
    """
    Very limited defaults.
    We do NOT auto-fill important learning intent fields.
    We only fill language/session preference if known.
    """

    data = brief.model_dump()
    basic = profile.get("basic_profile", {})
    prefs = profile.get("learning_preferences", {})

    if not data.get("preferred_language"):
        data["preferred_language"] = basic.get("preferred_language")

    if not data.get("desired_session_length_minutes"):
        data["desired_session_length_minutes"] = prefs.get("preferred_session_length_minutes")

    return CourseBrief(**data)


def is_filled(brief: CourseBrief, field: str) -> bool:
    value = getattr(brief, field)

    if field == "constraints_confirmed":
        return bool(value)

    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (int, float)):
        return value > 0

    if isinstance(value, list):
        return True

    return bool(value)


def evaluate_completeness(brief: CourseBrief) -> tuple[List[str], List[str], float]:
    missing = []
    completed = []

    for field in REQUIRED_FIELD_ORDER:
        if is_filled(brief, field):
            completed.append(field)
        else:
            missing.append(field)

    readiness = len(completed) / len(REQUIRED_FIELD_ORDER)
    return missing, completed, readiness


def field_label(field: str) -> str:
    labels = {
        "topic": "topic",
        "course_direction": "course focus",
        "user_goal": "main goal",
        "target_outcome": "final outcome",
        "current_level": "current level",
        "background_context": "background",
        "use_case": "use case",
        "preferred_style": "learning style",
        "preferred_depth": "depth",
        "available_time_per_day_minutes": "daily time",
        "total_course_duration_hours": "total course size",
        "desired_session_length_minutes": "session length",
        "preferred_language": "language",
        "constraints_confirmed": "must-include / avoid / constraints",
    }
    return labels.get(field, field)


def build_next_question(field: str, brief: CourseBrief) -> str:
    """
    Short, controlled, one-step questions.
    """

    questions = {
        "topic": (
            "What topic do you want to learn?"
        ),
        "course_direction": (
            f"For {brief.topic}, which focus do you want?\n"
            "Reply with a short phrase, like: fundamentals, practical use, advanced, project-based, or exam prep."
        ),
        "user_goal": (
            "Why do you want to learn this?"
        ),
        "target_outcome": (
            "By the end, what should you be able to do?"
        ),
        "current_level": (
            "What is your current level?\n"
            "Choose: absolute_beginner, beginner, intermediate, advanced, expert."
        ),
        "background_context": (
            "What background do you already have related to this topic?"
        ),
        "use_case": (
            "Where will you use this knowledge?"
        ),
        "preferred_style": (
            "How do you want to learn?\n"
            "Choose: conceptual, practical, project_based, visual, step_by_step, mixed."
        ),
        "preferred_depth": (
            "How deep should the course be?\n"
            "Choose: simple, balanced, deep, expert."
        ),
        "available_time_per_day_minutes": (
            "How many minutes per day can you study?"
        ),
        "total_course_duration_hours": (
            "How many total hours should the full course be?"
        ),
        "desired_session_length_minutes": (
            "How long should each micro-session be?"
        ),
        "preferred_language": (
            "What language should the course use? Example: en, fa, es."
        ),
        "constraints_confirmed": (
            "Any must-include, must-avoid, or constraints?\n"
            "Reply with them, or say: no constraints."
        ),
    }

    return questions.get(field, f"Please provide: {field_label(field)}.")


def detect_no_constraints(text: str) -> bool:
    t = text.lower().strip()
    patterns = [
        "no",
        "no constraint",
        "no constraints",
        "nothing",
        "none",
        "no must",
        "not really",
        "no avoid",
    ]
    return any(p == t or p in t for p in patterns)


def summarize_course(course: Dict[str, Any]) -> str:
    chapters = course.get("chapters", [])
    session_count = sum(len(ch.get("sessions", [])) for ch in chapters)

    return (
        f"Course generated.\n"
        f"Title: {course.get('title')}\n"
        f"Level: {course.get('level')}\n"
        f"Hours: {course.get('total_estimated_hours')}\n"
        f"Chapters: {len(chapters)}\n"
        f"Sessions: {session_count}\n"
        f"Type /save to save it, /brief to inspect the brief, or describe changes."
    )


def save_course_json(course: Dict[str, Any]) -> str:
    os.makedirs("generated_courses", exist_ok=True)
    safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "_", course.get("title", "course")).strip("_")
    filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join("generated_courses", filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(course, f, indent=2, ensure_ascii=False)

    return path


# ============================================================
# 6. LANGGRAPH NODES
# ============================================================

def load_profile_node(state: CourseBuilderState) -> CourseBuilderState:
    log_node("load_profile", "Loading user learning profile")

    if not state.get("user_learning_profile"):
        state["user_learning_profile"] = DEMO_USER_PROFILE

    if not state.get("course_brief"):
        brief = CourseBrief()
        brief = apply_safe_profile_defaults(brief, state["user_learning_profile"])
        state["course_brief"] = brief.model_dump()

    log_success("Profile loaded")
    return state


def extract_info_node(state: CourseBuilderState) -> CourseBuilderState:
    log_node("extract_info", "Extracting only explicit course brief data")

    user_message = state["user_message"]
    current_brief = brief_from_state(state)
    profile = state["user_learning_profile"]

    if detect_no_constraints(user_message):
        extracted = ExtractedCourseInfo(
            constraints_confirmed=True,
            confidence=1.0,
        )
    else:
        prompt = f"""
You are the information extractor for Blue Learn's strict course builder.

Task:
Extract only course-brief data from the latest user message.

Critical rules:
- Do NOT generate a course.
- Do NOT ask a question.
- Do NOT invent missing values.
- Only extract fields that are explicitly stated or very strongly implied.
- If the user gives a vague topic, set needs_direction_suggestions=true.
- If the user chooses from previous suggestions, extract course_direction.
- If user gives constraints, must_include, or must_avoid, extract them and set constraints_confirmed=true.
- If the user says there are no constraints, set constraints_confirmed=true.
- Keep values concise.

Allowed values:
current_level: absolute_beginner, beginner, intermediate, advanced, expert
preferred_style: conceptual, practical, project_based, visual, step_by_step, mixed
preferred_depth: simple, balanced, deep, expert

Current CourseBrief:
{to_json(current_brief.model_dump())}

User profile:
{to_json(profile)}

Latest user message:
{user_message}
"""
        extracted = extractor_llm.invoke(prompt)

    updated = merge_brief(current_brief, extracted)
    updated = apply_safe_profile_defaults(updated, profile)

    state["course_brief"] = updated.model_dump()

    changed = [
        k for k, v in extracted.model_dump().items()
        if v not in [None, [], False, 0.0]
    ]

    if changed:
        log_success(f"Extracted: {', '.join(changed)}")
    else:
        log_warning("No strong new fields extracted")

    if extracted.needs_direction_suggestions:
        state["status"] = "suggesting"
    else:
        state["status"] = "collecting"

    return state


def evaluate_brief_node(state: CourseBuilderState) -> CourseBuilderState:
    log_node("evaluate_brief", "Checking strict required fields")

    brief = brief_from_state(state)
    missing, completed, readiness = evaluate_completeness(brief)

    state["missing_fields"] = missing
    state["completed_fields"] = completed
    state["readiness_score"] = readiness

    log_progress(len(completed), len(REQUIRED_FIELD_ORDER), missing)

    if missing:
        state["status"] = "collecting"
    else:
        state["status"] = "ready"

    return state


def suggest_direction_node(state: CourseBuilderState) -> CourseBuilderState:
    log_node("suggest_direction", "User topic is vague, generating short options")

    brief = brief_from_state(state)
    profile = state["user_learning_profile"]

    prompt = f"""
You are Blue, a concise AI course designer.

The user gave a vague topic. Suggest 2-3 short course directions.

Rules:
- Be short.
- Each option title max 7 words.
- Each description max 18 words.
- Do not generate a course.
- Ask the user to choose one option or write their own focus.

CourseBrief:
{to_json(brief.model_dump())}

User profile:
{to_json(profile)}

Latest user message:
{state["user_message"]}
"""

    suggestions = suggestion_llm.invoke(prompt)

    state["suggested_options"] = [x.model_dump() for x in suggestions.options]

    lines = []
    for i, option in enumerate(suggestions.options, start=1):
        lines.append(f"{i}) {option.title} — {option.description}")

    state["assistant_message"] = (
        "Choose the course focus:\n"
        + "\n".join(lines)
        + "\n\n"
        + suggestions.question
    )

    log_success("Short direction options prepared")
    return state


def ask_next_question_node(state: CourseBuilderState) -> CourseBuilderState:
    log_node("ask_next_question", "Asking one short question")

    brief = brief_from_state(state)
    missing = state["missing_fields"]

    if not missing:
        state["assistant_message"] = "I have enough information. Type /generate to create the course."
        return state

    next_field = missing[0]
    question = build_next_question(next_field, brief)

    completed = len(state["completed_fields"])
    total = len(REQUIRED_FIELD_ORDER)

    state["assistant_message"] = (
        f"{question}\n\n"
        f"Progress: {completed}/{total} fields complete."
    )

    return state


def generate_course_node(state: CourseBuilderState) -> CourseBuilderState:
    log_node("generate_course", "Generating final structured course outline")

    brief = brief_from_state(state)
    missing, completed, readiness = evaluate_completeness(brief)

    if missing:
        log_warning("Generation blocked because brief is incomplete")
        state["missing_fields"] = missing
        state["completed_fields"] = completed
        state["readiness_score"] = readiness
        state["status"] = "collecting"
        state["assistant_message"] = (
            f"I cannot generate the course yet. Missing: {field_label(missing[0])}.\n"
            f"{build_next_question(missing[0], brief)}"
        )
        return state

    course_id = str(uuid.uuid4())

    prompt = f"""
You are Blue, an expert course architect for a micro-learning platform.

Generate a personalized course outline from the completed CourseBrief.

Strict rules:
- Return only valid structured data.
- Use the exact course_id: {course_id}
- Do not add unrelated topics.
- Respect total_course_duration_hours.
- Respect desired_session_length_minutes.
- Build micro-sessions.
- Sessions must be short, focused, and ordered logically.
- Make the course practical and efficient.
- Add practice tasks where useful.
- Include a final project only if it fits the user's goal.
- Keep the course realistic.

Completed CourseBrief:
{to_json(brief.model_dump())}

User learning profile:
{to_json(state["user_learning_profile"])}
"""

    course = course_llm.invoke(prompt)

    state["generated_course"] = course.model_dump()
    state["status"] = "generated"
    state["assistant_message"] = summarize_course(state["generated_course"])

    log_success("Course generated")
    return state


# ============================================================
# 7. ROUTING
# ============================================================

def route_after_extract(state: CourseBuilderState) -> str:
    if state["status"] == "suggesting":
        return "suggest_direction"
    return "evaluate_brief"


def route_after_evaluate(state: CourseBuilderState) -> str:
    if state["status"] == "ready":
        return "ready_message"
    return "ask_next_question"


def ready_message_node(state: CourseBuilderState) -> CourseBuilderState:
    log_node("ready_message", "Brief complete")

    state["assistant_message"] = (
        "Great. I have the full course brief.\n"
        "Type /generate to create the course outline, or /brief to review it."
    )
    return state


# ============================================================
# 8. BUILD GRAPH
# ============================================================

def build_graph():
    graph = StateGraph(CourseBuilderState)

    graph.add_node("load_profile", load_profile_node)
    graph.add_node("extract_info", extract_info_node)
    graph.add_node("evaluate_brief", evaluate_brief_node)
    graph.add_node("suggest_direction", suggest_direction_node)
    graph.add_node("ask_next_question", ask_next_question_node)
    graph.add_node("ready_message", ready_message_node)
    graph.add_node("generate_course", generate_course_node)

    graph.add_edge(START, "load_profile")
    graph.add_edge("load_profile", "extract_info")

    graph.add_conditional_edges(
        "extract_info",
        route_after_extract,
        {
            "suggest_direction": "suggest_direction",
            "evaluate_brief": "evaluate_brief",
        },
    )

    graph.add_edge("suggest_direction", END)

    graph.add_conditional_edges(
        "evaluate_brief",
        route_after_evaluate,
        {
            "ask_next_question": "ask_next_question",
            "ready_message": "ready_message",
        },
    )

    graph.add_edge("ask_next_question", END)
    graph.add_edge("ready_message", END)
    graph.add_edge("generate_course", END)

    return graph.compile()


course_builder_graph = build_graph()


# ============================================================
# 9. SESSION MANAGER
# ============================================================

class CourseBuilderSession:
    def __init__(self, user_id: str):
        initial_brief = CourseBrief()
        initial_brief = apply_safe_profile_defaults(initial_brief, DEMO_USER_PROFILE)

        self.state: CourseBuilderState = {
            "user_id": user_id,
            "conversation_id": str(uuid.uuid4()),
            "user_message": "",
            "assistant_message": "",
            "user_learning_profile": DEMO_USER_PROFILE,
            "course_brief": initial_brief.model_dump(),
            "missing_fields": REQUIRED_FIELD_ORDER.copy(),
            "completed_fields": [],
            "readiness_score": 0.0,
            "suggested_options": [],
            "generated_course": None,
            "status": "collecting",
            "last_saved_path": None,
        }

    def send(self, user_message: str) -> str:
        self.state["user_message"] = user_message
        result = course_builder_graph.invoke(self.state)
        self.state.update(result)
        return self.state["assistant_message"]

    def generate(self) -> str:
        result = generate_course_node(self.state)
        self.state.update(result)
        return self.state["assistant_message"]

    def save(self) -> str:
        if not self.state.get("generated_course"):
            return "No generated course to save yet."

        path = save_course_json(self.state["generated_course"])
        self.state["last_saved_path"] = path
        self.state["status"] = "saved"

        return f"Saved course JSON to: {path}"

    def show_brief(self):
        brief = brief_from_state(self.state)
        missing, completed, readiness = evaluate_completeness(brief)
        print_brief_table(brief.model_dump(), missing)
        log_progress(len(completed), len(REQUIRED_FIELD_ORDER), missing)

    def reset(self):
        self.__init__(self.state["user_id"])
        return "Session reset."


# ============================================================
# 10. CLI
# ============================================================

def print_blue(message: str):
    console.print(
        Panel(
            Text(message, style="white"),
            title="[bold blue]Blue[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
    )


def print_help():
    help_text = """
Commands:
/brief      Show current CourseBrief
/generate   Generate course only if brief is complete
/save       Save generated course JSON
/reset      Restart session
/exit       Quit
"""
    console.print(Panel(help_text.strip(), title="Commands", border_style="cyan"))


def run_cli():
    console.print(
        Panel(
            "[bold blue]Blue Learn Strict Course Builder[/bold blue]\n"
            "[dim]Short questions. Strict brief completion. No early generation.[/dim]",
            border_style="blue",
        )
    )

    print_help()

    session = CourseBuilderSession(user_id="demo_user")

    print_blue(
        "Hi, I’m Blue.\n"
        "What topic do you want to learn?"
    )

    while True:
        user_input = console.input("\n[bold green]You:[/bold green] ").strip()

        if not user_input:
            continue

        command = user_input.lower()

        if command in ["/exit", "exit", "quit"]:
            print_blue("Goodbye.")
            break

        if command == "/help":
            print_help()
            continue

        if command == "/brief":
            session.show_brief()
            continue

        if command == "/reset":
            print_blue(session.reset())
            continue

        if command == "/generate":
            response = session.generate()
            print_blue(response)
            continue

        if command == "/save":
            response = session.save()
            print_blue(response)
            continue

        response = session.send(user_input)
        print_blue(response)


if __name__ == "__main__":
    run_cli()