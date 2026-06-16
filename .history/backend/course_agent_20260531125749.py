# course_agent.py

import os
import re
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END


# ============================================================
# 0. CONFIG
# ============================================================

load_dotenv()
console = Console()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY. Add it to .env as GOOGLE_API_KEY=...")

MODEL_NAME = "gemini-3.1-flash-lite"

AI_COST_MODE = "cheap"
# cheap    = only 1 AI call: final course generation
# balanced = static parsing + final course generation. Same as cheap now.
# smart    = reserved for future optional AI extraction

ENABLE_LOGGING = True


llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2,
)


# ============================================================
# 1. LOGGING
# ============================================================

def log_step(name: str, msg: str = ""):
    if ENABLE_LOGGING:
        console.print(f"[bold cyan]▶ {name}[/bold cyan] [dim]{msg}[/dim]")


def log_ok(msg: str):
    if ENABLE_LOGGING:
        console.print(f"[bold green]✓[/bold green] {msg}")


def log_skip(msg: str):
    if ENABLE_LOGGING:
        console.print(f"[bold blue]↳[/bold blue] [dim]{msg}[/dim]")


def log_warn(msg: str):
    if ENABLE_LOGGING:
        console.print(f"[bold yellow]•[/bold yellow] {msg}")


def log_ai(msg: str):
    if ENABLE_LOGGING:
        console.print(f"[bold magenta]AI CALL[/bold magenta] [dim]{msg}[/dim]")


def log_progress(turn: int, brief: Dict[str, Any]):
    required = [
        "topic",
        "course_direction",
        "user_goal",
        "target_outcome",
        "current_level",
        "background_context",
        "preferred_style",
        "preferred_depth",
        "available_time_per_day_minutes",
        "total_course_duration_hours",
        "desired_session_length_minutes",
        "preferred_language",
    ]

    done = 0
    for key in required:
        value = brief.get(key)
        if value not in [None, "", [], 0, 0.0]:
            done += 1

    percent = int(done / len(required) * 100)
    bar_len = 24
    fill = int(bar_len * percent / 100)
    bar = "█" * fill + "░" * (bar_len - fill)

    color = "red"
    if percent >= 45:
        color = "yellow"
    if percent >= 75:
        color = "green"

    console.print(
        f"[bold {color}]Brief[/bold {color}] "
        f"[{color}]{bar}[/{color}] {percent}% "
        f"[dim]| user turn {turn}/4[/dim]"
    )


# ============================================================
# 2. SCHEMAS
# ============================================================

CourseLevel = Literal[
    "absolute_beginner",
    "beginner",
    "intermediate",
    "advanced",
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

PreferredDepth = Literal[
    "simple",
    "balanced",
    "deep",
    "expert",
]

Status = Literal[
    "collecting",
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
    turn_index: int
    course_brief: Dict[str, Any]
    pending_options: List[Dict[str, Any]]
    generated_course: Optional[Dict[str, Any]]
    status: Status
    saved_path: Optional[str]
    ai_call_count: int


course_llm = llm.with_structured_output(GeneratedCourse)


# ============================================================
# 3. LOCAL PARSING HELPERS — NO AI
# ============================================================

def clean_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text or None


def brief_obj(state: CourseBuilderState) -> CourseBrief:
    return CourseBrief(**state["course_brief"])


def is_number_choice(text: str) -> Optional[int]:
    text = text.strip()
    if re.fullmatch(r"[1-3]", text):
        return int(text)
    return None


def normalize_topic(text: str) -> str:
    text = clean_text(text) or ""
    text = re.sub(r"^(i want to learn|i wanna learn|learn|teach me|course about)\s+", "", text, flags=re.I)
    return clean_text(text) or text


def detect_level(text: str) -> Optional[CourseLevel]:
    t = text.lower()

    if any(x in t for x in ["absolute beginner", "complete beginner", "zero knowledge", "know nothing", "i know nothing", "no background"]):
        return "absolute_beginner"
    if "beginner" in t or "basic" in t or "new to" in t:
        return "beginner"
    if "intermediate" in t:
        return "intermediate"
    if "advanced" in t:
        return "advanced"
    if "expert" in t or "professional" in t:
        return "expert"

    return None


def detect_style(text: str) -> Optional[PreferredStyle]:
    t = text.lower()

    if any(x in t for x in ["step by step", "step-by-step", "step_by_step"]):
        return "step_by_step"
    if any(x in t for x in ["project based", "project-based", "project_based", "project"]):
        return "project_based"
    if "practical" in t or "hands-on" in t or "hands on" in t:
        return "practical"
    if "visual" in t or "diagram" in t:
        return "visual"
    if "conceptual" in t or "theory" in t or "theoretical" in t:
        return "conceptual"
    if "mixed" in t or "mix" in t:
        return "mixed"

    return None


def detect_depth(text: str) -> Optional[PreferredDepth]:
    t = text.lower()

    if "simple" in t or "easy" in t or "light" in t:
        return "simple"
    if "balanced" in t or "normal" in t:
        return "balanced"
    if "deep" in t or "detailed" in t:
        return "deep"
    if "expert" in t or "professional" in t:
        return "expert"

    return None


def detect_language(text: str) -> Optional[str]:
    t = text.lower()

    if re.search(r"\b(en|english)\b", t):
        return "en"
    if re.search(r"\b(fa|farsi|persian)\b", t):
        return "fa"
    if re.search(r"\b(es|spanish)\b", t):
        return "es"
    if re.search(r"\b(ar|arabic)\b", t):
        return "ar"

    return None


def detect_daily_minutes(text: str) -> Optional[int]:
    t = text.lower()

    patterns = [
        r"(\d+)\s*(min|mins|minute|minutes)\s*(/|per)?\s*(day|daily)",
        r"(\d+)\s*(min|mins|minute|minutes)\s*a\s*day",
        r"daily\s*(\d+)\s*(min|mins|minute|minutes)",
    ]

    for p in patterns:
        m = re.search(p, t)
        if m:
            return int(m.group(1))

    return None


def detect_session_minutes(text: str) -> Optional[int]:
    t = text.lower()

    patterns = [
        r"(\d+)\s*(min|mins|minute|minutes)\s*(session|sessions)",
        r"session[s]?\s*(of)?\s*(\d+)\s*(min|mins|minute|minutes)",
    ]

    for p in patterns:
        m = re.search(p, t)
        if m:
            nums = re.findall(r"\d+", m.group(0))
            if nums:
                return int(nums[0])

    return None


def detect_total_hours(text: str) -> Optional[float]:
    t = text.lower()

    patterns = [
        r"(\d+(?:\.\d+)?)\s*(total\s*)?(hour|hours|hr|hrs)",
        r"(\d+(?:\.\d+)?)\s*h\b",
    ]

    for p in patterns:
        m = re.search(p, t)
        if m:
            return float(m.group(1))

    return None


def detect_constraints(text: str) -> Dict[str, List[str]]:
    t = text.lower()

    result = {
        "must_include": [],
        "must_avoid": [],
        "constraints": [],
    }

    include_match = re.search(r"(include|must include|cover)\s*:\s*([^.;]+)", text, re.I)
    if include_match:
        result["must_include"] = [x.strip() for x in re.split(r",|and", include_match.group(2)) if x.strip()]

    avoid_match = re.search(r"(avoid|must avoid|do not include|don't include)\s*:\s*([^.;]+)", text, re.I)
    if avoid_match:
        result["must_avoid"] = [x.strip() for x in re.split(r",|and", avoid_match.group(2)) if x.strip()]

    if any(x in t for x in ["no constraints", "no constraint", "nothing specific", "none"]):
        result["constraints"] = ["No specific constraints"]

    return result


def local_update_brief(state: CourseBuilderState) -> CourseBuilderState:
    """
    Main zero-token parser.
    Updates CourseBrief based on user turn.
    """

    text = clean_text(state["user_message"]) or ""
    lower = text.lower()
    turn = state["turn_index"]
    brief = brief_obj(state)

    log_step("local_parser", "zero-token extraction")

    # 1. Numeric selection for pending options
    selected = is_number_choice(text)
    if selected and state.get("pending_options"):
        matched = next((x for x in state["pending_options"] if int(x["id"]) == selected), None)
        if matched:
            brief.course_direction = matched["title"]
            state["pending_options"] = []
            log_ok(f"Selected focus option {selected}: {matched['title']}")

    # 2. Custom short focus if options are pending
    elif state.get("pending_options") and len(text.split()) <= 8:
        brief.course_direction = text
        state["pending_options"] = []
        log_ok(f"Custom focus accepted: {text}")

    # 3. Turn 1: topic
    elif turn == 1 and not brief.topic:
        brief.topic = normalize_topic(text)
        log_ok(f"Topic set: {brief.topic}")

    # 4. General extraction from any text
    level = detect_level(text)
    if level:
        brief.current_level = level
        if level == "absolute_beginner" and not brief.background_context:
            brief.background_context = "No prior knowledge"
        log_ok(f"Level: {level}")

    style = detect_style(text)
    if style:
        brief.preferred_style = style
        log_ok(f"Style: {style}")

    depth = detect_depth(text)
    if depth:
        brief.preferred_depth = depth
        log_ok(f"Depth: {depth}")

    lang = detect_language(text)
    if lang:
        brief.preferred_language = lang
        log_ok(f"Language: {lang}")

    daily = detect_daily_minutes(text)
    if daily:
        brief.available_time_per_day_minutes = daily
        log_ok(f"Daily minutes: {daily}")

    session_minutes = detect_session_minutes(text)
    if session_minutes:
        brief.desired_session_length_minutes = session_minutes
        log_ok(f"Session minutes: {session_minutes}")

    hours = detect_total_hours(text)
    if hours:
        brief.total_course_duration_hours = hours
        log_ok(f"Total hours: {hours}")

    constraints = detect_constraints(text)
    if constraints["must_include"]:
        brief.must_include = list(dict.fromkeys(brief.must_include + constraints["must_include"]))
        log_ok("Must-include captured")
    if constraints["must_avoid"]:
        brief.must_avoid = list(dict.fromkeys(brief.must_avoid + constraints["must_avoid"]))
        log_ok("Must-avoid captured")
    if constraints["constraints"]:
        brief.constraints = list(dict.fromkeys(brief.constraints + constraints["constraints"]))
        log_ok("Constraints captured")

    # 5. Turn-specific grouped meaning
    # Turn 3 normally collects goal + outcome + background
    if turn == 3:
        if not brief.user_goal:
            brief.user_goal = text
            log_ok("Goal captured from turn 3")
        if not brief.target_outcome:
            brief.target_outcome = text
            log_ok("Outcome captured from turn 3")
        if not brief.background_context:
            if any(x in lower for x in ["know", "background", "nothing", "beginner", "experience"]):
                brief.background_context = text
                log_ok("Background captured from turn 3")

    # If user gives strong goal/outcome in any turn
    if any(x in lower for x in ["i want to", "my goal", "so i can", "by the end", "i need to"]):
        if not brief.user_goal:
            brief.user_goal = text
            log_ok("Goal captured")
        if not brief.target_outcome and any(x in lower for x in ["by the end", "able to", "so i can"]):
            brief.target_outcome = text
            log_ok("Outcome captured")

    state["course_brief"] = brief.model_dump()
    return state


def create_static_options(topic: str) -> List[Dict[str, Any]]:
    """
    Zero-token focus options.
    """

    topic_clean = clean_text(topic) or "Topic"

    return [
        {
            "id": 1,
            "title": f"{topic_clean} Fundamentals",
            "description": "Core ideas, terms, and foundations.",
        },
        {
            "id": 2,
            "title": f"Practical {topic_clean}",
            "description": "Real use, examples, and exercises.",
        },
        {
            "id": 3,
            "title": f"Deep {topic_clean}",
            "description": "Detailed theory and advanced structure.",
        },
    ]


def fill_defaults(brief: CourseBrief) -> CourseBrief:
    """
    Final safe completion.
    This keeps max 4 user messages.
    """

    data = brief.model_dump()

    topic = data.get("topic") or "the selected topic"

    if not data.get("course_direction"):
        data["course_direction"] = f"{topic} Fundamentals"

    if not data.get("user_goal"):
        data["user_goal"] = f"Learn {topic} clearly and efficiently"

    if not data.get("target_outcome"):
        data["target_outcome"] = f"Understand and apply the core ideas of {topic}"

    if not data.get("current_level"):
        data["current_level"] = "beginner"

    if not data.get("background_context"):
        data["background_context"] = "No specific background provided"

    if not data.get("use_case"):
        data["use_case"] = "personal learning"

    if not data.get("preferred_style"):
        data["preferred_style"] = "step_by_step"

    if not data.get("preferred_depth"):
        data["preferred_depth"] = "balanced"

    if not data.get("available_time_per_day_minutes"):
        data["available_time_per_day_minutes"] = 20

    if not data.get("total_course_duration_hours"):
        data["total_course_duration_hours"] = 6

    if not data.get("desired_session_length_minutes"):
        data["desired_session_length_minutes"] = 15

    if not data.get("preferred_language"):
        data["preferred_language"] = "en"

    return CourseBrief(**data)


def readiness_score(brief: CourseBrief) -> float:
    data = brief.model_dump()
    required = [
        "topic",
        "course_direction",
        "user_goal",
        "target_outcome",
        "current_level",
        "background_context",
        "preferred_style",
        "preferred_depth",
        "available_time_per_day_minutes",
        "total_course_duration_hours",
        "desired_session_length_minutes",
        "preferred_language",
    ]

    done = sum(1 for key in required if data.get(key) not in [None, "", [], 0, 0.0])
    return done / len(required)


def should_generate(state: CourseBuilderState) -> bool:
    brief = brief_obj(state)

    if state["turn_index"] >= 4:
        return True

    if readiness_score(brief) >= 0.9:
        return True

    return False


def next_question(state: CourseBuilderState) -> str:
    turn = state["turn_index"]
    brief = brief_obj(state)

    if turn == 0:
        return "What topic do you want to learn?"

    if turn == 1:
        if state.get("pending_options"):
            lines = [
                f"{x['id']}) {x['title']} — {x['description']}"
                for x in state["pending_options"]
            ]
            return (
                "Choose the focus:\n"
                + "\n".join(lines)
                + "\n\nReply with 1, 2, 3, or write your own focus."
            )

        return (
            "What is your goal and current level?\n"
            "Example: I want to use it personally; I am beginner."
        )

    if turn == 2:
        return (
            "What should you be able to do by the end, and what background do you have?\n"
            "Example: read my own chart; I know nothing."
        )

    if turn == 3:
        return (
            "Choose format: style, depth, time, language.\n"
            "Example: step_by_step, balanced, 20 min/day, 6 hours, 15 min sessions, en."
        )

    return "Generating now."


def save_course(course: Dict[str, Any]) -> str:
    os.makedirs("generated_courses", exist_ok=True)

    title = course.get("title", "course")
    safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "_", title).strip("_")
    path = f"generated_courses/{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(path, "w", encoding="utf-8") as file:
        json.dump(course, file, ensure_ascii=False, indent=2)

    return path


def course_summary(course: Dict[str, Any]) -> str:
    chapters = course.get("chapters", [])
    sessions = sum(len(ch.get("sessions", [])) for ch in chapters)

    return (
        "Done. I generated your course.\n"
        f"Title: {course.get('title')}\n"
        f"Level: {course.get('level')}\n"
        f"Hours: {course.get('total_estimated_hours')}\n"
        f"Chapters: {len(chapters)} | Sessions: {sessions}\n\n"
        "Type /save to save JSON or /brief to inspect the final brief."
    )


# ============================================================
# 4. LANGGRAPH NODES
# ============================================================

def initialize_node(state: CourseBuilderState) -> CourseBuilderState:
    log_step("initialize", f"turn={state['turn_index']}/4")
    if not state.get("course_brief"):
        state["course_brief"] = CourseBrief().model_dump()
    return state


def parse_message_node(state: CourseBuilderState) -> CourseBuilderState:
    log_step("parse_message", "local parser only / zero AI tokens")
    state = local_update_brief(state)
    return state


def static_options_node(state: CourseBuilderState) -> CourseBuilderState:
    log_step("static_options", "checking if focus options are needed")

    brief = brief_obj(state)

    if (
        state["turn_index"] == 1
        and brief.topic
        and not brief.course_direction
        and not state.get("pending_options")
    ):
        state["pending_options"] = create_static_options(brief.topic)
        log_ok("Static focus options created / no AI call")
    else:
        log_skip("No options needed")

    return state


def route_node(state: CourseBuilderState) -> CourseBuilderState:
    log_step("route", "deciding ask or generate")

    brief = brief_obj(state)
    log_progress(state["turn_index"], brief.model_dump())

    if should_generate(state):
        state["status"] = "ready"
        log_ok("Ready for final generation")
    else:
        state["status"] = "collecting"
        state["assistant_message"] = next_question(state)

    return state


def generate_course_node(state: CourseBuilderState) -> CourseBuilderState:
    log_step("generate_course", "final generation")
    log_ai("Generating structured course JSON")

    brief = brief_obj(state)
    brief = fill_defaults(brief)
    state["course_brief"] = brief.model_dump()

    course_id = str(uuid.uuid4())

    prompt = f"""
You are Blue, an expert AI course architect for a micro-learning platform.

Generate a personalized course outline from the CourseBrief.

Critical rules:
- Return only structured data matching the schema.
- Use exact course_id: {course_id}
- Stay strictly on topic and course_direction.
- Do not add unrelated domains.
- Respect total_course_duration_hours.
- Respect desired_session_length_minutes.
- Build clear chapters and short micro-sessions.
- Each session must be useful, focused, and ordered logically.
- Include practical tasks where useful.
- Include a final project only if it supports the user's outcome.
- Keep it efficient, not bloated.

CourseBrief:
{json.dumps(brief.model_dump(), ensure_ascii=False, indent=2)}
"""

    course = course_llm.invoke(prompt)

    state["ai_call_count"] += 1
    state["generated_course"] = course.model_dump()
    state["assistant_message"] = course_summary(state["generated_course"])
    state["status"] = "generated"

    log_ok(f"Course generated | total AI calls: {state['ai_call_count']}")
    return state


# ============================================================
# 5. GRAPH
# ============================================================

def route_after_route_node(state: CourseBuilderState) -> str:
    if state["status"] == "ready":
        return "generate_course"
    return END


def build_graph():
    graph = StateGraph(CourseBuilderState)

    graph.add_node("initialize", initialize_node)
    graph.add_node("parse_message", parse_message_node)
    graph.add_node("static_options", static_options_node)
    graph.add_node("route", route_node)
    graph.add_node("generate_course", generate_course_node)

    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "parse_message")
    graph.add_edge("parse_message", "static_options")
    graph.add_edge("static_options", "route")

    graph.add_conditional_edges(
        "route",
        route_after_route_node,
        {
            "generate_course": "generate_course",
            END: END,
        },
    )

    graph.add_edge("generate_course", END)

    return graph.compile()


course_graph = build_graph()


# ============================================================
# 6. SESSION
# ============================================================

class CourseBuilderSession:
    def __init__(self, user_id: str):
        self.state: CourseBuilderState = {
            "user_id": user_id,
            "conversation_id": str(uuid.uuid4()),
            "user_message": "",
            "assistant_message": "",
            "turn_index": 0,
            "course_brief": CourseBrief().model_dump(),
            "pending_options": [],
            "generated_course": None,
            "status": "collecting",
            "saved_path": None,
            "ai_call_count": 0,
        }

    def intro(self) -> str:
        return next_question(self.state)

    def send(self, text: str) -> str:
        if self.state["status"] == "generated":
            return "Course already generated. Type /save, /brief, or /reset."

        self.state["turn_index"] += 1
        self.state["user_message"] = text

        result = course_graph.invoke(self.state)
        self.state.update(result)

        return self.state["assistant_message"]

    def save(self) -> str:
        if not self.state.get("generated_course"):
            return "No generated course yet."

        path = save_course(self.state["generated_course"])
        self.state["saved_path"] = path
        self.state["status"] = "saved"

        return f"Saved: {path}"

    def reset(self) -> str:
        self.__init__(self.state["user_id"])
        return self.intro()

    def show_brief(self):
        brief = self.state["course_brief"]

        table = Table(title="Course Brief", header_style="bold cyan")
        table.add_column("Field", style="bold")
        table.add_column("Value")

        for key, value in brief.items():
            if isinstance(value, list):
                display = ", ".join(value) if value else "-"
            else:
                display = str(value) if value not in [None, "", 0, 0.0] else "-"

            style = "green" if display != "-" else "yellow"
            table.add_row(key, f"[{style}]{display}[/{style}]")

        console.print(table)
        console.print(f"[dim]AI calls used:[/dim] [bold magenta]{self.state['ai_call_count']}[/bold magenta]")


# ============================================================
# 7. CLI
# ============================================================

def print_blue(text: str):
    console.print(
        Panel(
            text,
            title="[bold blue]Blue[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
    )


def print_help():
    console.print(
        Panel(
            "/brief    show current brief\n"
            "/save     save generated course JSON\n"
            "/reset    restart\n"
            "/exit     quit",
            title="Commands",
            border_style="cyan",
        )
    )


def run_cli():
    console.print(
        Panel(
            "[bold blue]Blue Learn Low-API Course Builder[/bold blue]\n"
            "[dim]Max 4 user answers. Static options. Local parsing. Only final course uses AI.[/dim]",
            border_style="blue",
        )
    )

    print_help()

    session = CourseBuilderSession(user_id="demo_user")
    print_blue(session.intro())

    while True:
        user = console.input("\n[bold green]You:[/bold green] ").strip()

        if not user:
            continue

        cmd = user.lower()

        if cmd in ["/exit", "exit", "quit"]:
            print_blue("Goodbye.")
            break

        if cmd == "/brief":
            session.show_brief()
            continue

        if cmd == "/save":
            print_blue(session.save())
            continue

        if cmd == "/reset":
            print_blue(session.reset())
            continue

        response = session.send(user)
        print_blue(response)


if __name__ == "__main__":
    run_cli()