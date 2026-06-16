import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, database
from app.logger import logger
from app.schemas import ChatRequest, ChatHistoryResponse, CoachChatRequest
from app.services import agent_service, vector_service
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.post("/chat/course-generator")
def chat_course_generator_endpoint(
    request: ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Receives chat requirements diagnostic turns and returns structured outlining guidelines."""
    logger.log_info("API Endpoint: /chat/course-generator hit")
    
    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    user_info = ""
    if user_settings:
        user_info = f"Name: {user_settings.name or 'N/A'}\nAge: {user_settings.age or 'N/A'}\nEducation: {user_settings.education or 'N/A'}\nExperience: {user_settings.background_experience or 'N/A'}\nAdditional Info: {user_settings.additional_info or 'N/A'}"
        
    messages = [
        {
            "role": msg.role,
            "content": msg.content,
            "images": msg.images,
            "audio": msg.audio
        }
        for msg in request.messages
    ]
    result = agent_service.chat_course_generator(
        messages=messages,
        user_info=user_info,
        level=request.level,
        duration_sessions=request.duration_sessions,
        learning_style=request.learning_style
    )
    return result

@router.get("/courses/{course_id}/chat-history", response_model=List[ChatHistoryResponse])
def get_course_chat_history(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieves all chat transcripts logged for a specific course."""
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    history = db.query(models.CourseChatMessage).filter(models.CourseChatMessage.course_id == course_id).order_by(models.CourseChatMessage.id).all()
    return [{"role": msg.role, "content": msg.content} for msg in history]

@router.post("/chat/coach")
def chat_coach_endpoint(
    request: CoachChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Connects to the AI streaming coach.
    1. Saves user inputs to the database.
    2. Performs semantic retrieval across past event logs using Fallback Embeddings.
    3. Streams response chunks to client continuously.
    4. Triggers background thread summarization for older messages once streaming concludes.
    """
    logger.log_info(f"API Endpoint: /chat/coach hit for course {request.course_id}, item {request.item_id}")
    course = db.query(models.Course).filter(
        models.Course.id == request.course_id,
        models.Course.user_id == current_user.id
    ).first()
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == request.item_id).first()
    
    if not course or not item or item.course_id != course.id:
        raise HTTPException(status_code=404, detail="Course or Item not found")
        
    user_input = request.message
    if not user_input and request.messages:
        user_input = request.messages[-1].content
        
    # Save user message to database
    user_msg = models.CourseChatMessage(course_id=course.id, role="user", content=user_input or "")
    db.add(user_msg)
    
    # Log Learning Event
    user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if user_profile:
        event = models.LearningEventLog(
            user_id=user_profile.id,
            event_type="smart_coach_interaction",
            course_title=course.title,
            session_title=item.title,
            raw_interaction_text=f"User asked: {user_input}"
        )
        db.add(event)
        
    db.commit()

    # Aggregate full conversation histories for LLM context
    history_msgs = db.query(models.CourseChatMessage).filter(models.CourseChatMessage.course_id == course.id).order_by(models.CourseChatMessage.id).all()
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in history_msgs]

    outline_titles = [i.title for i in sorted(course.items, key=lambda x: x.order)]
    
    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    user_info = ""
    if user_settings:
        user_info = f"Name: {user_settings.name or 'N/A'}\nAge: {user_settings.age or 'N/A'}\nEducation: {user_settings.education or 'N/A'}\nExperience: {user_settings.background_experience or 'N/A'}\nAdditional Info: {user_settings.additional_info or 'N/A'}"
        
    # Build semantic memory vectors dynamically, scoped to current user profile
    semantic_memory_context = ""
    if user_profile and user_input:
        logs = db.query(models.LearningEventLog).filter(
            models.LearningEventLog.user_id == user_profile.id,
            models.LearningEventLog.vector_embedding_json != None
        ).all()
        logs_with_vectors = []
        for log in logs:
            try:
                logs_with_vectors.append({
                    "title": f"{log.course_title} - {log.session_title}",
                    "text": f"Event: {log.event_type} | Data: {log.raw_interaction_text or f'Studied for {log.study_duration_seconds}s'}",
                    "vector": json.loads(log.vector_embedding_json)
                })
            except Exception:
                pass
                
        if logs_with_vectors:
            semantic_memory_context = vector_service.semantic_search_logs(user_input, logs_with_vectors)

    # Compile course details and summarized outline context for coach
    try:
        learning_outcomes = json.loads(course.learning_outcomes) if course.learning_outcomes else []
    except Exception:
        learning_outcomes = []
        
    try:
        prerequisites = json.loads(course.prerequisites) if course.prerequisites else []
    except Exception:
        prerequisites = []

    detailed_outline = [
        {
            "chapter": i.chapter,
            "title": i.title,
            "order": i.order
        }
        for i in course.items
    ]

    # Initiate conversational generator stream
    generator = agent_service.chat_coach_stream(
        messages=messages_dict,
        course_title=course.title,
        course_description=course.description or "",
        outline_titles=outline_titles,
        current_session_title=item.title,
        current_session_content=item.content or "",
        chat_summary=course.chat_summary,
        user_info=user_info,
        semantic_memory_context=semantic_memory_context,
        detailed_outline=detailed_outline,
        course_level=course.level,
        course_goal=course.course_goal,
        learning_outcomes=learning_outcomes,
        prerequisites=prerequisites,
        target_user=course.target_user_summary
    )
    
    def stream_wrapper():
        full_response = ""
        for chunk in generator:
            full_response += chunk
            yield chunk
            
        # 1. Save assistant message after streaming completes
        db_session = database.SessionLocal()
        try:
            # We re-fetch items in the fresh connection to prevent cross-thread issues
            course_db = db_session.query(models.Course).filter(models.Course.id == course.id).first()
            assistant_msg = models.CourseChatMessage(course_id=course_db.id, role="assistant", content=full_response)
            db_session.add(assistant_msg)
            db_session.commit()

            # 2. Trigger history summarization logic if old unsummarized messages count exceeds 10
            unsummarized_msgs = db_session.query(models.CourseChatMessage).filter(
                models.CourseChatMessage.course_id == course_db.id,
                models.CourseChatMessage.is_summarized == False
            ).order_by(models.CourseChatMessage.id).all()
            
            if len(unsummarized_msgs) > 10:
                msgs_to_summarize = unsummarized_msgs[:-6]
                messages_dict_to_summarize = [{"role": msg.role, "content": msg.content} for msg in msgs_to_summarize]
                
                logger.log_info(f"Triggering background summarization for {len(msgs_to_summarize)} old messages...")
                new_summary = agent_service.generate_history_summary(messages_dict_to_summarize, course_db.chat_summary)
                course_db.chat_summary = new_summary
                
                for msg in msgs_to_summarize:
                    msg.is_summarized = True
                    
                db_session.commit()
                logger.log_success(f"History summarization complete. New summary saved for course {course_db.id}")
        except Exception as ex:
            logger.log_error(f"Error during stream wrapper database sync: {str(ex)}")
        finally:
            db_session.close()

    return StreamingResponse(stream_wrapper(), media_type="text/plain")
