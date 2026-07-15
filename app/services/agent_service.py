import os
import time
import math
import json
from typing import List, Optional, Generator, Dict, Any, TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END

from app import prompts
from app.logger import logger
from app.schemas import (
    OutlineItemSchema,
    OutlineChapterSchema,
    CourseOutlineSchema,
    CourseGenerationSchema,
    ChatAgentResponse,
    ProfilerUpdateSchema,
    IncrementalProfilerUpdateSchema
)

# ==========================================
# 1. LLM ENGINE INSTANTIATIONS
# ==========================================

def get_generator_llm() -> ChatGoogleGenerativeAI:
    """Instantiates a dedicated LLM for course curriculum outlining (creative)."""
    load_dotenv(override=True)
    return ChatGoogleGenerativeAI(
        model=os.getenv("GENERATOR_MODEL_NAME", "gemini-flash-latest"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.75,
    )

def get_content_llm() -> ChatGoogleGenerativeAI:
    """Instantiates a dedicated LLM for session/lesson content writing."""
    load_dotenv(override=True)
    return ChatGoogleGenerativeAI(
        model=os.getenv("MAIN_MODEL_NAME", "gemini-flash-latest"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7,
    )

def get_coach_llm() -> ChatGoogleGenerativeAI:
    """Instantiates a dedicated, low-temperature LLM for the conversational coach."""
    load_dotenv(override=True)
    return ChatGoogleGenerativeAI(
        model=os.getenv("COACH_MODEL_NAME", "gemini-flash-lite-latest"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.5,
    )


# ==========================================
# 2. CORE ONE-SHOT GENERATIONS
# ==========================================

def get_outline(subject: str) -> List[OutlineChapterSchema]:
    """
    Generates a detailed chapter-by-chapter outline for a given subject.
    Utilizes Pydantic structured output parsing.
    """
    logger.log_process_start("Outline Generation", f"Generating outline for subject: {subject}")
    start_time = time.time()
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.OUTLINE_GENERATOR_PROMPT),
        ("human", "Please generate the course outline now."),
    ])
    
    # Standard LangChain chain composition using the pipe operator
    chain = prompt_template | get_content_llm().with_structured_output(CourseOutlineSchema, method="json_schema")
    result = chain.invoke({"subject": subject})
    
    logger.log_ai_call(
        step_name="Outline Generation Node",
        model_name=get_content_llm().model,
        system_prompt=prompts.OUTLINE_GENERATOR_PROMPT,
        user_input=f"Subject: {subject}\nRequest: Please generate the course outline now.",
        result=result.model_dump_json(indent=2)
    )
    
    logger.log_info(f"Generated {len(result.items)} chapters for the outline.")
    logger.log_process_end("Outline Generation", time.time() - start_time)
    
    return result.items

def get_content(
    subject: str,
    item_title: str,
    course_description: str = "",
    full_outline: List[str] = None,
    user_info: str = "",
    course_level: Optional[str] = None,
    course_goal: Optional[str] = None,
    learning_outcomes: Optional[List[str]] = None,
    prerequisites: Optional[List[str]] = None,
    target_user: Optional[str] = None,
    detailed_outline: Optional[List[dict]] = None,
    session_description: Optional[str] = None,
    session_learning_objectives: Optional[List[str]] = None,
    session_key_concepts: Optional[List[str]] = None
) -> str:
    """
    Writes comprehensive, rich Markdown text for an individual syllabus session.
    Provides detailed context to ensure consistency.
    """
    # 1. Build compact outline: chapter titles + session titles only (no per-session details)
    detailed_outline_str = ""
    if detailed_outline:
        chapters = {}
        for item in detailed_outline:
            ch = item.get("chapter") or "سایر"
            if ch not in chapters:
                chapters[ch] = []
            chapters[ch].append(item)

        for ch_title, ch_items in chapters.items():
            detailed_outline_str += f"\n- Chapter: {ch_title}\n"
            for item in ch_items:
                title = item.get("title", "")
                marker = " ◀ [CURRENT SESSION]" if title == item_title else ""
                detailed_outline_str += f"  * {title}{marker}\n"
    else:
        detailed_outline_str = "\n".join([f"- {t}" for t in (full_outline or [])]) if full_outline else "Not provided"

    # 2. Build course details metadata
    course_details_str = f"""Course Details:
- Title: {subject}
- Level: {course_level or 'Not specified'}
- Goal: {course_goal or 'Not specified'}
- Target User: {target_user or 'Not specified'}
"""
    if learning_outcomes:
        course_details_str += f"- Learning Outcomes:\n" + "\n".join([f"  * {o}" for o in learning_outcomes]) + "\n"
    if prerequisites:
        course_details_str += f"- Prerequisites:\n" + "\n".join([f"  * {p}" for p in prerequisites]) + "\n"

    logger.log_process_start("Content Generation", f"Generating lesson: '{item_title}' for course '{subject}'")
    start_time = time.time()

    user_prompt_template = """Please write the full session content now.

Session Details:
- Title: {item_title}
- Description: {session_description}
- Learning Objectives: {session_learning_objectives}
- Key Concepts: {session_key_concepts}

{course_details_str}

Course Context/Description:
{course_desc}

Course Outline (titles only for context):
{outline_context}
"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.CONTENT_GENERATOR_PROMPT),
        ("human", user_prompt_template),
    ])
    
    chain = prompt_template | get_content_llm()
    
    invoke_args = {
        "item_title": item_title,
        "session_description": session_description or "Not provided",
        "session_learning_objectives": ", ".join(session_learning_objectives) if session_learning_objectives else "Not provided",
        "session_key_concepts": ", ".join(session_key_concepts) if session_key_concepts else "Not provided",
        "course_details_str": course_details_str,
        "course_desc": course_description,
        "outline_context": detailed_outline_str,
        "user_info": user_info or "Not provided"
    }
    
    result = chain.invoke(invoke_args)
    content = result.content
    
    # Handle list part format edge cases returned by the model
    if isinstance(content, list):
        content = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in content])

    rendered_system_prompt = prompts.CONTENT_GENERATOR_PROMPT.format(
        user_info=user_info or "Not provided"
    )
    rendered_user_prompt = user_prompt_template.format(**invoke_args)
    variables_block = (
        f"[TEMPLATE VARIABLES]\n"
        f"  item_title       : {item_title}\n"
        f"  subject (course) : {subject}\n"
        f"  course_level     : {course_level or 'Not specified'}\n"
        f"  course_goal      : {course_goal or 'Not specified'}\n"
        f"  target_user      : {target_user or 'Not specified'}\n"
        f"  course_desc      : {course_description or 'Not provided'}\n"
        f"  user_info        : {user_info or 'Not provided'}\n"
        f"  learning_outcomes: {learning_outcomes or []}\n"
        f"  prerequisites    : {prerequisites or []}\n"
        f"\n[RENDERED USER PROMPT]\n{rendered_user_prompt}"
    )
    logger.log_ai_call(
        step_name="Lesson Content Generation",
        model_name=get_content_llm().model,
        system_prompt=rendered_system_prompt,
        user_input=variables_block,
        result=content
    )
    
    logger.log_process_end("Content Generation", time.time() - start_time)
    return content


# ==========================================
# 3. CHAT & AGENT FLOWS
# ==========================================

def generate_history_summary(messages: List[dict], current_summary: str = None) -> str:
    """Progressively condenses conversation logs into short summary blocks to conserve tokens."""
    if not messages:
        return current_summary or ""
        
    chat_history_str = ""
    for msg in messages:
        role = "User" if msg["role"] == "user" else "AI"
        chat_history_str += f"{role}: {msg['content']}\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Progressively summarize the lines of conversation provided, adding onto the previous summary returning a new summary."),
        ("user", "Current summary:\n{current_summary}\n\nNew lines of conversation:\n{new_lines}\n\nNew summary:")
    ])
    
    chain = prompt | get_generator_llm()
    res = chain.invoke({
        "current_summary": current_summary or "No summary yet.",
        "new_lines": chat_history_str
    })
    
    summary_content = res.content
    if isinstance(summary_content, list):
        summary_content = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in summary_content])
    
    logger.log_ai_call(
        step_name="Background History Summarization",
        model_name=get_generator_llm().model,
        system_prompt="Progressively summarize the lines of conversation provided...",
        user_input=f"Previous Summary:\n{current_summary or 'None'}\n\nNew Lines:\n{chat_history_str}",
        result=summary_content
    )
    
    return summary_content

def parse_data_url(data_url: str):
    """
    Parses a data URL (e.g. 'data:audio/mp3;base64,...') to extract 
    the raw base64 data and mime type.
    """
    if isinstance(data_url, str) and data_url.startswith("data:"):
        try:
            header, base64_data = data_url.split(";base64,", 1)
            mime_type = header.split("data:", 1)[1]
            return base64_data, mime_type
        except Exception:
            pass
    return data_url, None

# --- Profile Patch and Coach Decision Schemas ---
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

    course_level: Optional[str] = Field(
        None,
        description="Desired course level to generate (e.g., beginner, intermediate, advanced)."
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
            "These suggestions  should be accepted by the user."
        ),
    )

class CoachDecision(BaseModel):
    profile_patch: ProfilePatch = Field(
        default_factory=ProfilePatch,
        description="Delta update patch containing ONLY fields that are newly discovered, updated, or changed in this turn. Leave all other fields None."
    )
    missing_information: List[str] = Field(default_factory=list)
    ready_to_generate: bool = False
    assistant_message: str
    debug_notes: str = ""

class ConversationProfileExtraction(BaseModel):
    profile: ProfilePatch = Field(description="The profile details collected so far from the user's statements in the history.")
    conversation_summary: str = Field(description="A concise summary of the conversation history so far.")

class CoachState(TypedDict, total=False):
    user_message: Any  # Can be str or content list for multimodal
    profile: Dict[str, Any]
    recent_messages: List[Dict[str, str]]
    conversation_summary: str
    assistant_message: str
    missing_information: List[str]
    ready_to_generate: bool
    course_outline: Optional[CourseGenerationSchema]
    turn_count: int
    
    # Custom context fields:
    user_info: str
    selected_level: str
    selected_duration: str
    selected_learning_style: str


def merge_profile(profile: dict, patch: ProfilePatch) -> dict:
    updated = dict(profile)
    patch_data = patch.model_dump(exclude_none=True)
    
    list_fields = {"rules", "suggested_topics"}
    
    for key, value in patch_data.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, list) and not value:
            continue
            
        if key in list_fields:
            old_value = updated.get(key, [])
            old_list = old_value if isinstance(old_value, list) else [str(old_value)]
            new_list = value if isinstance(value, list) else [str(value)]
            
            merged = list(old_list)
            for item in new_list:
                item = str(item).strip()
                if item and item not in merged:
                    merged.append(item)
            updated[key] = merged
        else:
            updated[key] = value
    return updated


def build_coach_prompt(state: CoachState) -> str:
    profile = state.get("profile", {})
    conversation_summary = state.get("conversation_summary", "")
    user_info = state.get("user_info", "Not provided")
    selected_level = state.get("selected_level", "هوشمند")
    selected_duration = state.get("selected_duration", "هوشمند")
    selected_learning_style = state.get("selected_learning_style", "هوشمند")
    
    return prompts.COURSE_COACH_PROMPT.format(
        user_info=user_info,
        profile_json=json.dumps(profile, ensure_ascii=False, indent=2),
        conversation_summary=conversation_summary or "No summary yet.",
        selected_level=selected_level,
        selected_duration=selected_duration,
        selected_learning_style=selected_learning_style
    )


def format_course_outline_to_markdown(course: CourseGenerationSchema) -> str:
    md = f"# 🎓 {course.title}\n\n"
    
    md += f"## 📋 مشخصات دوره\n"
    md += f"- 🔹 **عنوان کوتاه:** {course.short_title}\n"
    md += f"- 📶 **سطح دوره:** {course.level}\n"
    md += f"- ⏱️ **مدت زمان تخمینی:** {course.total_estimated_hours} ساعت\n"
    md += f"- 👥 **مخاطب هدف:** {course.target_user_summary}\n"
    md += f"- 🎯 **هدف اصلی:** {course.course_goal}\n\n"
    
    md += f"## 📝 توضیحات دوره\n>{course.course_description}\n\n"
    
    if course.learning_outcomes:
        md += f"## 🏆 دستاوردهای یادگیری\n"
        for outcome in course.learning_outcomes:
            md += f"- ✔️ {outcome}\n"
        md += "\n"
        
    if course.prerequisites:
        md += f"## 🛑 پیش‌نیازها\n"
        for prereq in course.prerequisites:
            md += f"- 📌 {prereq}\n"
        md += "\n"
        
    md += f"## 📚 برنامه درسی (سرفصل‌ها)\n\n"
    for ch_idx, ch in enumerate(course.chapters, 1):
        md += f"### 📂 فصل {ch_idx}: {ch.title}\n"
        md += f"> 💡 *{ch.description}*\n\n"
        for s_idx, s in enumerate(ch.sessions, 1):
            md += f"#### 🔹 جلسه {s_idx}: {s.title}\n"
            md += f"- 📖 **توضیح:** {s.description}\n"
            if s.learning_objectives:
                objectives_str = "، ".join(s.learning_objectives)
                md += f"- 🎯 **اهداف یادگیری:** {objectives_str}\n"
            if s.key_concepts:
                concepts_str = "، ".join(s.key_concepts)
                md += f"- 🔑 **مفاهیم کلیدی:** {concepts_str}\n\n"
                
    return md


# --- Graph Node Functions ---

def add_user_message_node(state: CoachState) -> CoachState:
    user_message = state.get("user_message")
    messages = state.get("recent_messages", [])
    turn_count = state.get("turn_count", 0)
    
    # Format message for storing in history
    display_content = ""
    if isinstance(user_message, str):
        display_content = user_message
    elif isinstance(user_message, list):
        for part in user_message:
            if isinstance(part, dict) and part.get("type") == "text":
                display_content = part.get("text", "")
        if not display_content:
            display_content = "[محتوای چندرسانه‌ای]"
            
    if user_message:
        messages = list(messages)
        messages.append({"role": "user", "content": display_content})
        turn_count += 1
        
    return {
        "recent_messages": messages,
        "turn_count": turn_count,
    }


def coach_turn_node(state: CoachState) -> CoachState:
    logger.log_info("Node: coach_turn | Running diagnostic coach step")
    prompt = build_coach_prompt(state)
    
    recent_messages = state.get("recent_messages", [])
    history_messages = recent_messages[:-1] if (recent_messages and recent_messages[-1]["role"] == "user") else recent_messages
    
    messages_formatted = []
    history_log_str = ""
    for msg in history_messages:
        role = msg["role"]
        content = msg["content"]
        history_log_str += f"[{role}]: {content}\n"
        if role == "user":
            messages_formatted.append(HumanMessage(content=content))
        else:
            messages_formatted.append(AIMessage(content=content))
            
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=prompt),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{user_input}")
    ])
    
    try:
        structured_llm = get_coach_llm().with_structured_output(CoachDecision, method="json_schema")
        chain = prompt_template | structured_llm
        
        user_message = state.get("user_message")
        
        decision = chain.invoke({
            "history": messages_formatted,
            "user_input": user_message
        })
        
        logger.log_ai_call(
            step_name="Coach Turn Node",
            model_name=get_coach_llm().model,
            system_prompt=prompt,
            user_input=f"--- Message History ---\n{history_log_str}\n--- Latest User Message ---\n{user_message}",
            result=decision.model_dump_json(indent=2)
        )
        
        updated_profile = merge_profile(state.get("profile", {}), decision.profile_patch)
        
        logger.log_success(f"Node: coach_turn | Successfully completed turn. Ready to generate: {decision.ready_to_generate}")
        
        return {
            "profile": updated_profile,
            "conversation_summary": state.get("conversation_summary", ""),
            "missing_information": decision.missing_information,
            "ready_to_generate": decision.ready_to_generate,
            "assistant_message": decision.assistant_message
        }
    except Exception as e:
        logger.log_error(f"Error in coach_turn_node: {str(e)}")
        return {
            "assistant_message": "پوزش می‌خواهم، مشکلی در پردازش درخواست شما رخ داد. لطفاً دوباره تلاش کنید.",
            "ready_to_generate": False
        }


def generate_course_outline_node(state: CoachState) -> CoachState:
    logger.log_info("Node: generate_course_outline | Generating finalized course curriculum")
    profile = state.get("profile", {})
    conversation_summary = state.get("conversation_summary", "")
    user_info = state.get("user_info", "Not provided")
    
    if not profile or not profile.get("course_topic"):
        logger.log_error("Outline Generation Blocked: Missing full profile patch!")
        return {
            "assistant_message": "متأسفانه به دلیل نداشتن اطلاعات کافی در پروفایل، ساخت سرفصل‌های دوره ممکن نیست. لطفاً اطلاعات موضوع دوره را در چت تکمیل کنید.",
            "ready_to_generate": False
        }
        
    prompt = prompts.COURSE_OUTLINE_PROMPT.format(
        profile_json=json.dumps(profile, ensure_ascii=False, indent=2),
        conversation_summary=conversation_summary or "No summary yet.",
        user_info=user_info
    )
    
    try:
        structured_llm = get_generator_llm().with_structured_output(CourseGenerationSchema, method="json_schema")
        course_outline = structured_llm.invoke(prompt)
        
        logger.log_ai_call(
            step_name="Generate Course Outline Node",
            model_name=get_generator_llm().model,
            system_prompt=prompts.COURSE_OUTLINE_PROMPT,
            user_input=f"Profile Details JSON:\n{json.dumps(profile, ensure_ascii=False, indent=2)}\n\nConversation Summary:\n{conversation_summary}\n\nUser Profile Info:\n{user_info}",
            result=course_outline.model_dump_json(indent=2)
        )
        
        markdown_preview = format_course_outline_to_markdown(course_outline)
        
        logger.log_success(f"Node: generate_course_outline | Outline generated: '{course_outline.title}' with {len(course_outline.chapters)} chapters")
        
        return {
            "course_outline": course_outline,
            "assistant_message": markdown_preview,
            "ready_to_generate": True
        }
    except Exception as e:
        logger.log_error(f"Error in generate_course_outline_node: {str(e)}")
        return {
            "assistant_message": "متأسفانه خطایی در تولید سرفصل‌های دوره پیش آمد. لطفاً دوباره درخواست خود را ارسال کنید.",
            "ready_to_generate": False
        }


def append_assistant_message_node(state: CoachState) -> CoachState:
    logger.log_info("Node: append_assistant_message | Saving assistant reply to recent messages")
    messages = state.get("recent_messages", [])
    assistant_message = state.get("assistant_message", "")
    if assistant_message:
        messages = list(messages)
        messages.append({"role": "assistant", "content": assistant_message})
    return {
        "recent_messages": messages
    }


def route_after_coach_turn(state: CoachState) -> str:
    ready = state.get("ready_to_generate") is True
    has_outline = state.get("course_outline") is not None
    if ready and not has_outline:
        logger.log_info("Routing conditional edge: route_after_coach_turn | Ready to generate. Routing to: generate_course_outline")
        return "generate_course_outline"
    logger.log_info(f"Routing conditional edge: route_after_coach_turn | Ready={ready}, HasOutline={has_outline} -> Routing to: append_assistant_message")
    return "append_assistant_message"


def summarize_history_node(state: CoachState) -> CoachState:
    logger.log_info("Node: summarize_history | Condensing older conversation history")
    messages = state.get("recent_messages", [])
    old_summary = state.get("conversation_summary", "")
    
    keep_messages_count = 6
    if len(messages) <= keep_messages_count:
        return {}
        
    to_summarize = messages[:-keep_messages_count]
    to_keep = messages[-keep_messages_count:]
    
    prompt = prompts.COURSE_SUMMARY_PROMPT.format(
        old_summary=old_summary or "No summary yet.",
        messages_to_summarize=json.dumps(to_summarize, ensure_ascii=False, indent=2)
    )
    
    try:
        res = get_generator_llm().invoke(prompt)
        summary_text = res.content
        if isinstance(summary_text, list):
            summary_text = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in summary_text])
        summary_text = summary_text.strip()
        
        logger.log_ai_call(
            step_name="Graph History Summarizer Node",
            model_name=get_generator_llm().model,
            system_prompt=prompts.COURSE_SUMMARY_PROMPT,
            user_input=f"Old Summary:\n{old_summary}\n\nMessages to Summarize:\n{json.dumps(to_summarize, ensure_ascii=False, indent=2)}",
            result=summary_text
        )
        
        return {
            "conversation_summary": summary_text,
            "recent_messages": to_keep
        }
    except Exception as e:
        logger.log_error(f"Error in summarize_history_node: {str(e)}")
        return {
            "conversation_summary": old_summary,
            "recent_messages": messages
        }


def route_after_add_user_message(state: CoachState) -> str:
    messages = state.get("recent_messages", [])
    if len(messages) > 10:
        logger.log_info(f"Routing conditional edge: route_after_add_user_message | Messages count {len(messages)} > 10 -> Routing to: summarize_history")
        return "summarize_history"
    logger.log_info(f"Routing conditional edge: route_after_add_user_message | Messages count {len(messages)} <= 10 -> Routing to: coach_turn")
    return "coach_turn"


def build_course_generator_graph():
    graph = StateGraph(CoachState)
    
    graph.add_node("add_user_message", add_user_message_node)
    graph.add_node("summarize_history", summarize_history_node)
    graph.add_node("coach_turn", coach_turn_node)
    graph.add_node("generate_course_outline", generate_course_outline_node)
    graph.add_node("append_assistant_message", append_assistant_message_node)
    
    graph.add_edge(START, "add_user_message")
    
    graph.add_conditional_edges(
        "add_user_message",
        route_after_add_user_message,
        {
            "summarize_history": "summarize_history",
            "coach_turn": "coach_turn"
        }
    )
    
    graph.add_edge("summarize_history", "coach_turn")
    
    graph.add_conditional_edges(
        "coach_turn",
        route_after_coach_turn,
        {
            "generate_course_outline": "generate_course_outline",
            "append_assistant_message": "append_assistant_message"
        }
    )
    
    graph.add_edge("generate_course_outline", "append_assistant_message")
    graph.add_edge("append_assistant_message", END)
    
    return graph.compile()


def chat_course_generator(
    messages: List[dict],
    user_info: str = "",
    level: Optional[str] = None,
    duration_sessions: Optional[int] = None,
    learning_style: Optional[str] = None,
    conversation_summary: Optional[str] = None,
    profile: Optional[dict] = None
) -> ChatAgentResponse:
    """
    Guides the user through dynamic, diagnostic chat turns to refine course outlines.
    Implements a structured LangGraph state workflow.
    """
    level_map = {
        "beginner": "مقدماتی",
        "intermediate": "متوسط",
        "advanced": "پیشرفته",
        "beginner_to_intermediate": "مقدماتی تا متوسط",
        "default": "انتخاب هوشمند",
    }
    pref_level = level_map.get(level.lower(), level) if level else "انتخاب هوشمند"
    pref_duration = f"{duration_sessions} جلسه" if duration_sessions and duration_sessions > 0 else "انتخاب هوشمند"
    
    style_map = {
        "text": "متنی با مثال‌های کد",
        "video": "ویدئوهای آموزشی",
        "exercises": "پروژه‌های عملی و تمرین",
        "projects": "پروژه‌های عملی و تمرین",
        "practical": "پروژه‌های عملی و تمرین",
        "coaching": "همراه با مربیگری",
        "default": "انتخاب هوشمند",
    }
    pref_learning_style = style_map.get(learning_style.lower(), learning_style) if learning_style else "انتخاب هوشمند"
    
    logger.log_process_start("Chat Course Generator", "Restructured LangGraph course generation workflow")
    start_time = time.time()
    
    if not messages:
        logger.log_process_end("Chat Course Generator", time.time() - start_time)
        return ChatAgentResponse(
            is_complete=False,
            chat_response="سلام! من بلو هستم، دستیار هوشمند شما برای طراحی دوره‌های آموزشی شخصی‌سازی شده. چه موضوعی را دوست دارید یاد بگیرید؟",
            course_data=None,
            conversation_summary="",
            profile={}
        )
        
    last_msg = messages[-1]
    last_role = last_msg.get("role", "user")
    content = last_msg.get("content", "")
    images = last_msg.get("images") or []
    audio = last_msg.get("audio") or []
    
    latest_user_content = ""
    if last_role == "user":
        if images or audio:
            content_list = []
            if content:
                content_list.append({"type": "text", "text": content})
            else:
                media_types = []
                if images: media_types.append("تصویر")
                if audio: media_types.append("فایل صوتی")
                content_list.append({"type": "text", "text": f"محتوای چندرسانه‌ای ارسال شد ({', '.join(media_types)})"})
            
            for img in images:
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
            
            for aud in audio:
                base64_data, mime_type = parse_data_url(aud)
                if not mime_type:
                     mime_type = "audio/mp3"
                content_list.append({
                    "type": "input_audio",
                    "input_audio": {
                        "data": base64_data,
                        "mime_type": mime_type
                    }
                })
            latest_user_content = content_list
        else:
            latest_user_content = content
            
    previous_messages = messages[:-1] if last_role == "user" else messages
    
    # Initialize profile with client-passed profile or empty dict
    accumulated_profile = profile or {}
    
    # Pre-populate profile with pre-selected preferences if set (and not "انتخاب هوشمند")
    if pref_level != "انتخاب هوشمند":
        accumulated_profile["course_level"] = pref_level
    if pref_duration != "انتخاب هوشمند":
        accumulated_profile["course_duration"] = pref_duration
    if pref_learning_style != "انتخاب هوشمند":
        accumulated_profile["preferred_format"] = pref_learning_style
        
    initial_state = {
        "user_message": latest_user_content,
        "profile": accumulated_profile,
        "recent_messages": [{"role": m["role"], "content": m.get("content") or ""} for m in previous_messages],
        "conversation_summary": conversation_summary or "",
        "turn_count": len(previous_messages) // 2,
        "ready_to_generate": False,
        "course_outline": None,
        
        "user_info": user_info,
        "selected_level": pref_level,
        "selected_duration": pref_duration,
        "selected_learning_style": pref_learning_style
    }
    
    # Format the accumulated profile as a nice string or dict list
    profile_summary = ""
    for k_pref, v_pref in initial_state["profile"].items():
        if v_pref:
            profile_summary += f"    • {k_pref}: {v_pref}\n"
    if not profile_summary:
        profile_summary = "    • (No profile fields extracted yet)\n"
        
    logger.log_info(f"Chat Course Generator | Starting LangGraph workflow:")
    logger.log_info(f"  - User message: {latest_user_content}")
    logger.log_info(f"  - Trimmed Turn Count: {initial_state['turn_count']}")
    logger.log_info(f"  - Level Pref: {initial_state['selected_level']}")
    logger.log_info(f"  - Duration Pref: {initial_state['selected_duration']}")
    logger.log_info(f"  - Learning Style Pref: {initial_state['selected_learning_style']}")
    
    from rich.panel import Panel
    from rich.text import Text
    from app.logger import console
    console.print(Panel(
        Text(f"Turn Count: {initial_state['turn_count']}\n"
             f"User Message: {latest_user_content}\n"
             f"Pre-selected preferences:\n"
             f"  - Level: {initial_state['selected_level']}\n"
             f"  - Duration: {initial_state['selected_duration']}\n"
             f"  - Learning Style: {initial_state['selected_learning_style']}\n\n"
             f"Accumulated profile patch till now:\n{profile_summary}", style="white"),
        title="[bold yellow]📋 CURRENT ACCUMULATED PROFILE[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    ))
    
    try:
        graph = build_course_generator_graph()
        final_state = graph.invoke(initial_state)
        
        result = ChatAgentResponse(
            is_complete=final_state.get("ready_to_generate", False),
            chat_response=final_state.get("assistant_message"),
            course_data=final_state.get("course_outline"),
            conversation_summary=final_state.get("conversation_summary", ""),
            profile=final_state.get("profile", {})
        )
        logger.log_success("Chat Course Generator | LangGraph workflow executed successfully")
    except Exception as e:
        logger.log_error(f"Failed to execute Course Generator Graph: {str(e)}")
        result = ChatAgentResponse(
            is_complete=False,
            chat_response="متأسفانه در پردازش پیام خطایی رخ داد. لطفاً دوباره پیام خود را ارسال کنید.",
            course_data=None,
            conversation_summary=current_summary,
            profile=accumulated_profile
        )
        
    logger.log_process_end("Chat Course Generator", time.time() - start_time)
    return result


def chat_coach_stream(
    messages: List[dict],
    course_title: str,
    course_description: str,
    outline_titles: List[str],
    current_session_title: str,
    current_session_content: str,
    chat_summary: Optional[str] = None,
    user_info: str = "",
    semantic_memory_context: str = "",
    detailed_outline: Optional[List[dict]] = None,
    course_level: Optional[str] = None,
    course_goal: Optional[str] = None,
    learning_outcomes: Optional[List[str]] = None,
    prerequisites: Optional[List[str]] = None,
    target_user: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Initiates a streaming chat coach conversation.
    Limits memory to the last 10 turns for efficient token caching.
    """
    logger.log_process_start("Smart Coach Agent", "Generating streaming response")
    
    # Build summarized outline context (only chapter name and session titles)
    outline_context = ""
    if detailed_outline:
        chapters = {}
        # Keep items sorted by order
        sorted_items = sorted(detailed_outline, key=lambda x: x.get("order", 0))
        for item in sorted_items:
            ch = item.get("chapter") or "سایر"
            if ch not in chapters:
                chapters[ch] = []
            chapters[ch].append(item.get("title"))
            
        for ch_title, sessions in chapters.items():
            outline_context += f"\n- Chapter: {ch_title}\n"
            for s_title in sessions:
                outline_context += f"  * Session: {s_title}\n"
    else:
        outline_context = "\n".join([f"- {title}" for title in outline_titles]) if outline_titles else "No outline available."
        
    # Build course details metadata
    course_details_str = f"""- Title: {course_title}
- Description: {course_description}
- Level: {course_level or 'Not specified'}
- Goal: {course_goal or 'Not specified'}
- Target User: {target_user or 'Not specified'}
"""
    if learning_outcomes:
        course_details_str += f"- Learning Outcomes:\n" + "\n".join([f"  * {o}" for o in learning_outcomes]) + "\n"
    if prerequisites:
        course_details_str += f"- Prerequisites:\n" + "\n".join([f"  * {p}" for p in prerequisites]) + "\n"

    system_prompt = prompts.SMART_COACH_SYSTEM_PROMPT.format(
        course_details_context=course_details_str,
        outline_context=outline_context,
        current_session_title=current_session_title,
        current_session_content=current_session_content or "No content available yet.",
        chat_summary_context=f"\n[PREVIOUS CONVERSATION SUMMARY]:\n{chat_summary}\n" if chat_summary else "",
        user_info=user_info,
        semantic_memory_context=semantic_memory_context
    )
    
    langchain_history = []
    full_conversation_log = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        role_label = "USER" if role == "user" else "ASSISTANT"
        full_conversation_log += f"\n[{role_label}]: {content}\n"
        
        if role == "user":
            langchain_history.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_history.append(AIMessage(content=content))
            
    # Apply standard sliding-window memory slicing (last 10 turns)
    if len(langchain_history) > 10:
        langchain_history = langchain_history[-10:]
        
    # Ensure starting with a UserMessage for Gemini requirements
    if langchain_history and langchain_history[0].type == "ai":
        langchain_history = langchain_history[1:]
            
    logger.log_process_start("AI Coach Stream", "Handling coach chat interaction")
    start_time = time.time()
    
    full_response_content = ""
    logger.log_ai_stream_start("AI Smart Coach", get_coach_llm().model)
    
    try:
        messages_to_send = [SystemMessage(content=system_prompt)] + langchain_history
        for chunk in get_coach_llm().stream(messages_to_send):
            content = chunk.content
            if isinstance(content, list):
                content = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in content])
            
            full_response_content += content
            yield content
            
        logger.log_ai_call(
            step_name="AI Smart Coach (Stream Finished)",
            model_name=get_coach_llm().model,
            system_prompt=system_prompt,
            user_input=full_conversation_log.strip(),
            result=full_response_content
        )
            
    except Exception as e:
        logger.log_error(f"Error in AI Coach Stream: {str(e)}")
        if "getaddrinfo failed" in str(e) or "ConnectError" in str(e):
            yield "خطا در اتصال به سرویس هوش مصنوعی. لطفا وضعیت اینترنت یا پروکسی خود را بررسی کنید. 🌐❌"
        else:
            yield f"متأسفانه خطایی رخ داد: {str(e)} ⚠️"
        
    logger.log_process_end("AI Coach Stream", time.time() - start_time)

def generate_knowledge_insight(completed_sessions: List[dict]) -> str:
    """Analyzes historical progress and prints highly engaging educational reflection insights (Farsi)."""
    if not completed_sessions:
        return "You haven't completed any sessions yet. Start your learning journey to see your insights here! 🚀"

    sessions_info = "\n".join([f"- Course: {s['course_title']}, Session: {s['item_title']}" for s in completed_sessions])

    logger.log_process_start("Knowledge Insight Generation", f"Generating insight for {len(completed_sessions)} sessions")
    start_time = time.time()

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.KNOWLEDGE_INSIGHT_PROMPT),
        ("human", "Please analyze my progress and give me my knowledge insight."),
    ])

    chain = prompt_template | get_content_llm()
    result = chain.invoke({"completed_sessions_info": sessions_info})

    content = result.content
    if isinstance(content, list):
        content = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in content])

    logger.log_process_end("Knowledge Insight Generation", time.time() - start_time)
    return content

def run_cognitive_profiler(user_profile: str, current_state: str, recent_logs: str) -> Optional[ProfilerUpdateSchema]:
    """Analyzes learner traits and conceptual mastery, updating the user graph (Farsi summaries)."""
    logger.log_process_start("Cognitive Profiler Agent", "Analyzing event logs for double-loop learning")
    start_time = time.time()

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.COGNITIVE_PROFILER_SYSTEM_PROMPT),
        ("human", "User Profile:\n{user_profile}\n\nCurrent Cognitive State:\n{current_state}\n\nRecent Logs:\n{recent_logs}\n\nProvide the updated profile JSON now."),
    ])

    try:
        llm = get_generator_llm()
        structured_llm = llm.with_structured_output(ProfilerUpdateSchema, method="json_schema")
        chain = prompt_template | structured_llm
        
        user_input_formatted = f"User Profile:\n{user_profile}\n\nCurrent Cognitive State:\n{current_state}\n\nRecent Logs:\n{recent_logs}\n\nProvide the updated profile JSON now."
        
        result = chain.invoke({
            "user_profile": user_profile,
            "current_state": current_state,
            "recent_logs": recent_logs
        })
        
        logger.log_ai_call(
            step_name="Cognitive Profiler Agent",
            model_name=llm.model,
            system_prompt=prompts.COGNITIVE_PROFILER_SYSTEM_PROMPT,
            user_input=user_input_formatted,
            result=result.model_dump_json(indent=2) if result else "None"
        )
        
        logger.log_success("Cognitive Profiler Agent generated a new dynamic profile")
        logger.log_process_end("Cognitive Profiler Agent", time.time() - start_time)
        return result
    except Exception as e:
        logger.log_error(f"Error in Cognitive Profiler Agent: {str(e)}")
        logger.log_process_end("Cognitive Profiler Agent", time.time() - start_time)
        return None

def run_incremental_cognitive_profiler(user_profile: str, current_state: str, current_nodes: str, new_event: str) -> Optional[IncrementalProfilerUpdateSchema]:
    """Analyzes a single new learning event context to selectively append/refine cognitive details and concept masteries."""
    logger.log_process_start("Incremental Profiler Agent", "Evaluating single learning event delta")
    start_time = time.time()

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.INCREMENTAL_COGNITIVE_PROFILER_SYSTEM_PROMPT),
        ("human", "User Biographical Profile:\n{user_profile}\n\nCurrent Cognitive Profile:\n{current_state}\n\nCurrent Knowledge Graph Nodes:\n{current_nodes}\n\nNEW Learning Event Details:\n{new_event}\n\nProvide the delta updates JSON now."),
    ])

    try:
        llm = get_generator_llm()
        structured_llm = llm.with_structured_output(IncrementalProfilerUpdateSchema, method="json_schema")
        chain = prompt_template | structured_llm
        
        user_input_formatted = f"User Biographical Profile:\n{user_profile}\n\nCurrent Cognitive Profile:\n{current_state}\n\nCurrent Knowledge Graph Nodes:\n{current_nodes}\n\nNEW Learning Event Details:\n{new_event}"
        
        result = chain.invoke({
            "user_profile": user_profile,
            "current_state": current_state,
            "current_nodes": current_nodes,
            "new_event": new_event
        })
        
        logger.log_ai_call(
            step_name="Incremental Profiler Agent",
            model_name=llm.model,
            system_prompt=prompts.INCREMENTAL_COGNITIVE_PROFILER_SYSTEM_PROMPT,
            user_input=user_input_formatted,
            result=result.model_dump_json(indent=2) if result else "None"
        )
        
        logger.log_success("Incremental Profiler Agent returned a structured delta update")
        logger.log_process_end("Incremental Profiler Agent", time.time() - start_time)
        return result
    except Exception as e:
        logger.log_error(f"Error in Incremental Profiler Agent: {str(e)}")
        logger.log_process_end("Incremental Profiler Agent", time.time() - start_time)
        return None

# ==========================================
# 4. IMAGE GENERATION SERVICES
# ==========================================

def generate_prompt_for_image(note_title: str, content_context: str) -> str:
    """
    Uses the content LLM and the IMAGE_SYSTEM_INSTRUCTION to translate course/session content
    into a concrete visual prompt description for the Imagen model.
    """
    logger.log_process_start("Image Prompt Translation", f"Creating visual prompt for: {note_title}")
    
    # Replace note_title dynamically in the system instruction template
    system_prompt = prompts.IMAGE_SYSTEM_INSTRUCTION.replace("{note_title}", note_title).replace("note_title", note_title)
    
    user_prompt = f"""Based on the following content context, please write a single English prompt description for generating a cover image.
Title: {note_title}
Content Context:
{content_context}

Output ONLY the final image generation prompt in English, with no quotes or introduction, and ensure you include the requested technical details at the end.
"""

    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    
    chain = prompt_template | get_generator_llm()
    result = chain.invoke({})
    prompt = result.content
    if isinstance(prompt, list):
        prompt = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in prompt])
    
    prompt = prompt.strip()
    logger.log_info(f"Generated visual prompt: {prompt}")
    logger.log_process_end("Image Prompt Translation", 0)
    return prompt

def generate_image_cover(prompt_text: str) -> Optional[bytes]:
    """
    Generates a 16:9 cover image using the Google image generation model.
    Utilizes the new google-genai library and streams the generated content.
    """
    from google import genai
    from google.genai import types
    from dotenv import load_dotenv

    load_dotenv(override=True)
    api_key = os.getenv("GOOGLE_IMAGE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.log_error("Image Generation: GOOGLE_IMAGE_API_KEY, GOOGLE_API_KEY or GEMINI_API_KEY is not set.")
        return None

    # Load model name from .env, defaulting to 'gemini-2.5-flash-image'
    model_name = os.getenv("IMAGE_MODEL_NAME", "gemini-2.5-flash-image")

    logger.log_process_start("AI Image Generation", f"Generating image with model '{model_name}' and prompt: {prompt_text[:100]}...")
    start_time = time.time()

    try:
        client = genai.Client(api_key=api_key)
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt_text),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )

        img_data = b""
        for chunk in client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.parts is None:
                continue
            for part in chunk.parts:
                if part.inline_data and part.inline_data.data:
                    img_data += part.inline_data.data
                else:
                    if text := part.text:
                        logger.log_info(f"Image Gen Text Chunk: {text}")

        if img_data:
            logger.log_success(f"Successfully generated image cover ({len(img_data)} bytes)")
            logger.log_process_end("AI Image Generation", time.time() - start_time)
            return img_data
        else:
            logger.log_error("Image Generation failed: No image data returned from model stream.")
            
    except Exception as e:
        logger.log_error(f"Error in Image Generation: {str(e)}")

    logger.log_process_end("AI Image Generation", time.time() - start_time)
    return None

