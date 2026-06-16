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
    ProfilerUpdateSchema
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

def get_content(subject: str, item_title: str, course_description: str = "", full_outline: List[str] = None, user_info: str = "") -> str:
    """
    Writes comprehensive, rich Markdown text for an individual syllabus session.
    Provides detailed context to ensure consistency.
    """
    outline_context = "\n".join([f"- {t}" for t in (full_outline or [])]) if full_outline else "Not provided"
    
    logger.log_process_start("Content Generation", f"Generating lesson: '{item_title}' for course '{subject}'")
    start_time = time.time()

    user_prompt_template = """Please write the full session content now.

Session Details:
- this session Title: {item_title}
- Course: {subject}

Course Context:
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
        "subject": subject,
        "course_desc": course_description,
        "outline_context": outline_context,
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

def chat_course_generator(messages: List[dict], user_info: str = "") -> ChatAgentResponse:
    """
    Guides the user through dynamic, diagnostic chat steps to refine curriculum needs.
    Uses structured outputs parsing.
    """
    system_prompt = prompts.COURSE_GENERATOR_SYSTEM_PROMPT.format(user_info=user_info)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
    ])
    
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
    semantic_memory_context: str = ""
) -> Generator[str, None, None]:
    """
    Initiates a streaming chat coach conversation.
    Limits memory to the last 10 turns for efficient token caching.
    """
    logger.log_process_start("Smart Coach Agent", "Generating streaming response")
    outline_context = "\n".join([f"- {title}" for title in outline_titles])
    
    system_prompt = prompts.SMART_COACH_SYSTEM_PROMPT.format(
        course_title=course_title,
        course_description=course_description,
        outline_context=outline_context,
        current_session_title=current_session_title,
        current_session_content=current_session_content or "No content available yet.",
        chat_summary_context=f"\n[PREVIOUS CONVERSATION SUMMARY]:\n{chat_summary}\n" if chat_summary else "",
        user_info=user_info,
        semantic_memory_context=semantic_memory_context
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
        chain = prompt_template | get_coach_llm()
        for chunk in chain.stream({"history": langchain_history}):
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
    Generates a 16:9 cover image using Google's Imagen 4 model.
    Returns the raw bytes of the generated image if successful, otherwise None.
    """
    import requests
    import base64
    
    load_dotenv(override=True)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.log_error("Image Generation: GOOGLE_API_KEY is not set.")
        return None

    # Call the Imagen 4 predict endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [
            {
                "prompt": prompt_text
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9",
            "outputMimeType": "image/jpeg"
        }
    }

    logger.log_process_start("AI Image Generation", f"Generating image with prompt: {prompt_text[:100]}...")
    start_time = time.time()
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            res_json = response.json()
            if "predictions" in res_json and len(res_json["predictions"]) > 0:
                pred = res_json["predictions"][0]
                if "bytesBase64Encoded" in pred:
                    img_bytes = base64.b64decode(pred["bytesBase64Encoded"])
                    logger.log_success(f"Successfully generated image cover ({len(img_bytes)} bytes)")
                    logger.log_process_end("AI Image Generation", time.time() - start_time)
                    return img_bytes
                
            logger.log_error(f"Image Generation response format invalid: {response.text[:500]}")
        else:
            logger.log_error(f"Image Generation failed (HTTP {response.status_code}): {response.text[:1000]}")
            
    except Exception as e:
        logger.log_error(f"Error in Image Generation: {str(e)}")
        
    logger.log_process_end("AI Image Generation", time.time() - start_time)
    return None

