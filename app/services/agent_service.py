import os
import time
import math
from typing import List, Optional, Generator
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
    chain = prompt_template | get_content_llm().with_structured_output(CourseOutlineSchema)
    result = chain.invoke({"subject": subject})
    
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
    detailed_outline: Optional[List[dict]] = None
) -> str:
    """
    Writes comprehensive, rich Markdown text for an individual syllabus session.
    Provides detailed context to ensure consistency.
    """
    # 1. Build detailed outline string
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
                detailed_outline_str += f"  * Session: {item.get('title')}\n"
                if item.get("description"):
                    detailed_outline_str += f"    Description: {item.get('description')}\n"
                if item.get("learning_objectives"):
                    detailed_outline_str += f"    Learning Objectives: {', '.join(item.get('learning_objectives'))}\n"
                if item.get("key_concepts"):
                    detailed_outline_str += f"    Key Concepts: {', '.join(item.get('key_concepts'))}\n"
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
- this session Title: {item_title}

{course_details_str}

Course Context/Description:
{course_desc}

Course Outline:
{outline_context}
"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.CONTENT_GENERATOR_PROMPT),
        ("human", user_prompt_template),
    ])
    
    chain = prompt_template | get_content_llm()
    
    invoke_args = {
        "item_title": item_title,
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
        
    logger.log_ai_call(
        step_name="Lesson Content Generation",
        model_name=get_content_llm().model,
        system_prompt=prompts.CONTENT_GENERATOR_PROMPT,
        user_input=user_prompt_template.format(**invoke_args),
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

def chat_course_generator(
    messages: List[dict],
    user_info: str = "",
    level: Optional[str] = None,
    duration_sessions: Optional[int] = None,
    learning_style: Optional[str] = None
) -> ChatAgentResponse:
    """
    Guides the user through dynamic, diagnostic chat steps to refine curriculum needs.
    Uses structured outputs parsing and supports pre-selected preferences & multimodal input.
    """
    # Format preferences
    pref_level = level if level and level != "default" else "انتخاب هوشمند (تعیین توسط هوش مصنوعی)"
    pref_duration = f"{duration_sessions}" if duration_sessions and duration_sessions > 0 else "انتخاب هوشمند (تعیین توسط هوش مصنوعی)"
    pref_learning_style = learning_style if learning_style and learning_style != "default" else "انتخاب هوشمند (تعیین توسط هوش مصنوعی)"
    
    system_prompt = prompts.COURSE_GENERATOR_SYSTEM_PROMPT.format(
        user_info=user_info,
        selected_level=pref_level,
        selected_duration=pref_duration,
        selected_learning_style=pref_learning_style
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
    ])
    
    langchain_history = []
    full_conversation_log = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        images = msg.get("images") or []
        audio = msg.get("audio") or []
        role_label = "USER" if role == "user" else "ASSISTANT"
        
        # Log basic text content or multimedia info
        multimedia_info = ""
        if images:
            multimedia_info += f" [{len(images)} Image(s) Attached]"
        if audio:
            multimedia_info += f" [{len(audio)} Audio(s) Attached]"
        full_conversation_log += f"\n[{role_label}]: {content or ''}{multimedia_info}\n"
        
        if role == "user":
            if images or audio:
                content_list = []
                if content:
                    content_list.append({"type": "text", "text": content})
                else:
                    # Provide a fallback text description if user sent media with no text
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
                        mime_type = "audio/mp3"  # default fallback
                    content_list.append({
                        "type": "input_audio",
                        "input_audio": {
                            "data": base64_data,
                            "mime_type": mime_type
                        }
                    })
                langchain_history.append(HumanMessage(content=content_list))
            else:
                langchain_history.append(HumanMessage(content=content or ""))
        elif role == "assistant":
            langchain_history.append(AIMessage(content=content or ""))

    logger.log_process_start("Chat Course Generator", "Handling incoming chat messages")
    start_time = time.time()
    
    chain = prompt_template | get_generator_llm().with_structured_output(ChatAgentResponse)
    result = chain.invoke({"history": langchain_history})
    
    logger.log_ai_call(
        step_name="Course Generator Assistant",
        model_name=get_generator_llm().model,
        system_prompt=system_prompt,
        user_input=full_conversation_log.strip(),
        result=result.model_dump_json(indent=2)
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
        structured_llm = llm.with_structured_output(ProfilerUpdateSchema)
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
        structured_llm = llm.with_structured_output(IncrementalProfilerUpdateSchema)
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
        ("system", system_prompt),
        ("human", user_prompt),
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

