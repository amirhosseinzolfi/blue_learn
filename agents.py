import os
import time
import json
import math
from typing import List, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

import prompts
from logger import logger

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
load_dotenv()

# --- Dedicated LLM for Course Generator Agent (creative curriculum design) ---
def get_generator_llm():
    load_dotenv(override=True)
    return ChatGoogleGenerativeAI(
        model=os.getenv("GENERATOR_MODEL_NAME", "gemini-flash-latest"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.75,
    )

def get_embeddings_model():
    return OllamaEmbeddings(model="nomic-embed-text-v2-moe:latest")

# --- Dedicated LLM for Content Generation (lesson writing) ---
def get_content_llm():
    load_dotenv(override=True)
    return ChatGoogleGenerativeAI(
        model=os.getenv("MAIN_MODEL_NAME", "gemini-flash-latest"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7,
    )

# --- Dedicated LLM for AI Coach (streaming, lower temperature for consistency) ---
def get_coach_llm():
    load_dotenv(override=True)
    return ChatGoogleGenerativeAI(
        model=os.getenv("COACH_MODEL_NAME", "gemini-flash-lite-latest"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.5,
    )

# ==========================================
# 2. PYDANTIC SCHEMAS (STRUCTURED OUTPUT)
# ==========================================
# These schemas enforce the JSON structure that the LLM must return.
# They act as the strict interface between the AI's natural language and the app's backend.

class OutlineItemSchema(BaseModel):
    title: str = Field(description="Title of the micro-course session")
    description: str = Field(description="Brief description of what will be covered in this session")

class OutlineChapterSchema(BaseModel):
    title: str = Field(description="Title of the main chapter")
    description: str = Field(description="Brief description of the chapter")
    items: List[OutlineItemSchema] = Field(description="Sessions within this chapter")

class CourseOutlineSchema(BaseModel):
    items: List[OutlineChapterSchema]

class CourseGenerationSchema(BaseModel):
    short_title: str = Field(description="Most efficient proper  short title for the course in 3 upto 6 word")
    level: str = Field(description="Level of the course in Persian, e.g., مبتدی, متوسط, پیشرفته")
    hours: int = Field(description="Estimated hours to complete")
    sessions: int = Field(description="Number of sessions")
    description: str = Field(description="Course proper detail explanation overview in one paragraph")
    outline: List[OutlineChapterSchema] = Field(description="Detailed list of chapters and their micro-courses")

class ChatAgentResponse(BaseModel):
    is_complete: bool = Field(description="Set to true if you have gathered enough information to generate the course. False if you still need to ask the user questions.")
    chat_response: Optional[str] = Field(description="If is_complete is false, this is the question you ask the user. If is_complete is true, this can be empty.")
    course_data: Optional[CourseGenerationSchema] = Field(description="If is_complete is true, this contains the full generated course data.")

class KnowledgeNodeUpdateSchema(BaseModel):
    concept: str = Field(description="Name of the concept, e.g., SQL Joins")
    category: str = Field(description="Category of the concept")
    mastery_score_delta: float = Field(description="Change in mastery score from 0.0 to 1.0")
    confidence_score: float = Field(description="Confidence of AI in this evaluation from 0.0 to 1.0")

class ProfilerUpdateSchema(BaseModel):
    global_learning_velocity: float = Field(description="Speed coefficient from 0.5 to 2.0")
    attention_span_minutes: int = Field(description="Adjusted average session time")
    retention_index: float = Field(description="Memory decay indicator from 0.0 to 1.0")
    ls_hands_on: float = Field(default=0.0, description="Learning style ratio for hands_on")
    ls_visual: float = Field(default=0.0, description="Learning style ratio for visual")
    ls_theoretical: float = Field(default=0.0, description="Learning style ratio for theoretical")
    ls_self_directed: float = Field(default=0.0, description="Learning style ratio for self_directed")
    pt_persistence: str = Field(default="", description="Personality trait persistence")
    pt_patience: str = Field(default="", description="Personality trait patience_with_errors")
    pt_curiosity: str = Field(default="", description="Personality trait learning_curiosity")
    pt_session_length: str = Field(default="", description="Personality trait preferred_session_length")
    learning_style_summary: str = Field(default="", description="Persian narrative of how the user learns best")
    personality_summary: str = Field(default="", description="Persian narrative of the user's learner personality")
    strength_areas: List[str] = Field(default=[], description="Persian list of top subject domains")
    new_interests: List[str] = Field(default=[], description="Persian list of newly discovered interests")
    recommended_topics: List[str] = Field(default=[], description="Persian list of recommended next topics")
    updated_knowledge_nodes: List[KnowledgeNodeUpdateSchema] = Field(description="Updates to the knowledge graph")

# ==========================================
# 3. CORE GENERATION FUNCTIONS
# ==========================================
# These functions handle direct, one-shot generations (like writing an outline or a lesson).
# We use direct LangChain invocation here instead of LangGraph since these are single-step tasks.

def get_outline(subject: str) -> List[OutlineItemSchema]:
    """
    Generates a detailed outline of micro-courses for a given subject.
    Uses structured output to guarantee a list of titles and descriptions.
    """
    logger.log_process_start("Outline Generation", f"Generating outline for subject: {subject}")
    start_time = time.time()
    
    # Use ChatPromptTemplate for standard LangChain pattern
    # NOTE: Google GenAI requires at least one human/user message in `contents`.
    # We add a minimal human turn after the system prompt to satisfy this requirement.
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.OUTLINE_GENERATOR_PROMPT),
        ("human", "Please generate the course outline now."),
    ])
    
    # Bind the schema and create the chain
    chain = prompt_template | get_content_llm().with_structured_output(CourseOutlineSchema)
    result = chain.invoke({"subject": subject})
    
    # Log the full structured result as a string for visibility
    logger.log_info(f"Generated {len(result.items)} chapters for the outline.")
    
    logger.log_process_end("Outline Generation", time.time() - start_time)
    
    return result.items

def get_content(subject: str, item_title: str, course_description: str = "", full_outline: List[str] = None, user_info: str = "") -> str:
    """
    Generates the actual Markdown content for a specific lesson/session.
    Provides the LLM with the broader course context to maintain consistency.
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

    # Use ChatPromptTemplate for standard LangChain pattern
    # NOTE: Google GenAI requires at least one human/user message in `contents`.
    # We add a minimal human turn after the system prompt to satisfy this requirement.
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
    
    # Handle edge case where content might be returned as a list of dicts/strings
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
# 4. CHAT & CONVERSATIONAL AGENTS
# ==========================================
# These functions handle multi-turn conversations with the user.

def generate_history_summary(messages: List[dict], current_summary: str = None) -> str:
    """Uses LLM to summarize a batch of messages, appending to the current summary."""
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
    Acts as a consultant to gather requirements from the user before building a course.
    Returns structured data that dictates whether to keep chatting or proceed to generation.
    """
    # Use ChatPromptTemplate for standard LangChain message handling
    system_prompt = prompts.COURSE_GENERATOR_SYSTEM_PROMPT.format(user_info=user_info)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
    ])
    
    # Convert dict messages to LangChain message objects
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
    
    # Create the chain using the pipe operator
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

def chat_coach_stream(messages: List[dict], course_title: str, course_description: str, outline_titles: List[str], current_session_title: str, current_session_content: str, chat_summary: Optional[str] = None, user_info: str = "", semantic_memory_context: str = ""):
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
    # Use ChatPromptTemplate for standard LangChain message handling
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
    ])
    
    # Convert dict messages to LangChain message objects
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
            
    # Apply efficient conversation history method (Short Memory optimization)
    # We keep the last 10 messages to keep context window small and efficient
    if len(langchain_history) > 10:
        langchain_history = langchain_history[-10:]
        
    # Ensure the first message in history is a user message for Gemini compatibility
    if langchain_history and langchain_history[0].type == "ai":
        langchain_history = langchain_history[1:]
            
    logger.log_process_start("AI Coach Stream", "Handling coach chat interaction")
    start_time = time.time()
    
    # Stream the chunks directly to the caller (FastAPI StreamingResponse)
    full_response_content = ""
    logger.log_ai_stream_start("AI Smart Coach", get_coach_llm().model)
    
    try:
        # Invoke the chain in streaming mode
        chain = prompt_template | get_coach_llm()
        for chunk in chain.stream({"history": langchain_history}):
            content = chunk.content
            if isinstance(content, list):
                # Handle cases where content is a list of parts
                content = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in content])
            
            full_response_content += content
            yield content
            
        # Log the full exchange after streaming completes
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
    """
    Analyzes completed sessions and generates a motivational knowledge insight.
    """
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
    """
    Analyzes recent learning events and returns a structured JSON update for the Cognitive Profile.
    """
    logger.log_process_start("Cognitive Profiler Agent", "Analyzing event logs for double-loop learning")
    start_time = time.time()

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts.COGNITIVE_PROFILER_SYSTEM_PROMPT),
        ("human", "User Profile:\n{user_profile}\n\nCurrent Cognitive State:\n{current_state}\n\nRecent Logs:\n{recent_logs}\n\nProvide the updated profile JSON now."),
    ])

    try:
        # We use the main generative model for complex analysis
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

def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Mathematical standard vector similarity calculation."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0: return 0.0
    return dot_product / (mag1 * mag2)

def semantic_search_logs(query: str, logs_with_vectors: List[dict], top_k: int = 3) -> str:
    """
    Standard lightweight LangChain semantic search.
    Embeds the user's query and compares it to all past embedded logs.
    """
    logger.log_process_start("Semantic Vector Search", f"Searching past memories for: '{query}'")
    start_time = time.time()
    
    try:
        embedder = get_embeddings_model()
        query_vector = embedder.embed_query(query)
        
        scored_logs = []
        for log in logs_with_vectors:
            if not log.get('vector'): continue
            similarity = calculate_cosine_similarity(query_vector, log['vector'])
            scored_logs.append((similarity, log))
            
        # Sort by highest similarity (most relevant)
        scored_logs.sort(key=lambda x: x[0], reverse=True)
        top_logs = scored_logs[:top_k]
        
        context_str = ""
        logger.log_info("--- Top Semantic Memory Results ---")
        for idx, (score, log) in enumerate(top_logs):
            logger.log_info(f"Memory {idx+1} [Score: {score:.3f}]: {log['title']}")
            if score > 0.65: # Threshold to ensure relevance
                context_str += f"- Past Session '{log['title']}': {log['text']}\n"
                
        logger.log_process_end("Semantic Vector Search", time.time() - start_time)
        return context_str if context_str else "No highly relevant past memories found."
    except Exception as e:
        logger.log_error(f"Semantic Search Failed: {str(e)}")
        return "Memory retrieval unavailable."
