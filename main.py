from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import random
from typing import List, Optional
import os
from dotenv import load_dotenv, set_key

import models, database, agents
import sqlalchemy
from sqlalchemy import text
from pydantic import BaseModel
from logger import logger
import json

def run_profiling_background_task():
    logger.log_info("Starting Cognitive Background Task...")
    db = database.SessionLocal()
    try:
        user_profile = db.query(models.UserProfile).first()
        if not user_profile:
            logger.log_info("No UserProfile found. Creating default guest profile...")
            user_profile = models.UserProfile(name="Guest User", primary_goals="General Learning")
            db.add(user_profile)
            db.commit()
            db.refresh(user_profile)
            
        if not user_profile.cognitive_profile:
            logger.log_info("No CognitiveProfile found. Creating default empty profile...")
            cp = models.CognitiveProfile(user_id=user_profile.id, cognitive_data_json="{}", interests_json="[]")
            db.add(cp)
            db.commit()
            db.refresh(user_profile)
            
        logger.log_process_start("Semantic Vectorization", "Checking for un-embedded learning logs")
        # 1. Update Vectors for any un-embedded logs (Asynchronous generation)
        unembedded_logs = db.query(models.LearningEventLog).filter(models.LearningEventLog.vector_embedding_json == None).all()
        if unembedded_logs:
            logger.log_info(f"Found {len(unembedded_logs)} un-embedded logs. Extracting embeddings via embedding-001...")
            embedder = agents.get_embeddings_model()
            for log in unembedded_logs:
                text_to_embed = f"Event: {log.event_type} | Course: {log.course_title} | Session: {log.session_title} | Duration: {log.study_duration_seconds}s | Details: {log.raw_interaction_text or ''}"
                try:
                    vector = embedder.embed_query(text_to_embed)
                    log.vector_embedding_json = json.dumps(vector)
                    
                    logger.log_ai_call(
                        step_name="Semantic Vectorization",
                        model_name=embedder.model if hasattr(embedder, 'model') else "OllamaEmbeddings",
                        system_prompt="Generate vector embedding for the following learning log event.",
                        user_input=text_to_embed,
                        result=f"Vector generated with {len(vector)} dimensions. Sample: {str(vector[:3])}..."
                    )
                    
                    logger.log_success(f"Generated semantic vector for event '{log.session_title}'")
                except Exception as e:
                    logger.log_error(f"Vector embedding failed for log {log.id}: {str(e)}")
            db.commit()
            logger.log_success("All pending logs have been vectorized successfully.")
        else:
            logger.log_info("All logs are already vectorized. No new embeddings required.")
        logger.log_process_end("Semantic Vectorization", 0)
            
        cog_profile = user_profile.cognitive_profile
        
        logger.log_process_start("Cognitive Profiling Pipeline", "Extracting cognitive traits and conceptual knowledge increments")
        # Get recent logs (increased to 30 to include all recent chat interactions during the session)
        recent_logs = db.query(models.LearningEventLog).filter(models.LearningEventLog.user_id == user_profile.id).order_by(models.LearningEventLog.timestamp.desc()).limit(30).all()
        logs_str = "\n".join([f"- {l.event_type} | Course: {l.course_title} | Session: {l.session_title} | Dur: {l.study_duration_seconds}s | Extra: {l.raw_interaction_text}" for l in recent_logs])
        
        # Profile strings
        existing_nodes = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id).all()
        existing_nodes_str = ", ".join([n.concept for n in existing_nodes]) if existing_nodes else "None"
        
        profile_str = f"Name: {user_profile.name}, Age: {user_profile.age}, Goal: {user_profile.primary_goals}"
        current_state_str = f"Velocity: {cog_profile.global_learning_velocity}, Attention: {cog_profile.attention_span_minutes}m\nData: {cog_profile.cognitive_data_json}\nInterests: {cog_profile.interests_json}\nExisting Knowledge Nodes (MUST REUSE EXACT NAMES if possible): {existing_nodes_str}"
        
        updated_data = agents.run_cognitive_profiler(profile_str, current_state_str, logs_str)
        if updated_data:
            cog_profile.global_learning_velocity = updated_data.global_learning_velocity
            cog_profile.attention_span_minutes = updated_data.attention_span_minutes
            cog_profile.retention_index = updated_data.retention_index
            
            cognitive_data_dict = {
                "learning_style": {
                    "hands_on": updated_data.ls_hands_on,
                    "visual": updated_data.ls_visual,
                    "theoretical": updated_data.ls_theoretical,
                    "self_directed": updated_data.ls_self_directed
                },
                "personality_traits": {
                    "persistence": updated_data.pt_persistence,
                    "patience_with_errors": updated_data.pt_patience,
                    "learning_curiosity": updated_data.pt_curiosity,
                    "preferred_session_length": updated_data.pt_session_length
                }
            }
            cog_profile.cognitive_data_json = json.dumps(cognitive_data_dict, ensure_ascii=False)
            cog_profile.interests_json = json.dumps(updated_data.new_interests, ensure_ascii=False)
            
            # Save new rich fields
            cog_profile.learning_style_summary = updated_data.learning_style_summary
            cog_profile.personality_summary = updated_data.personality_summary
            cog_profile.strength_areas_json = json.dumps(updated_data.strength_areas, ensure_ascii=False)
            cog_profile.recommended_topics_json = json.dumps(updated_data.recommended_topics, ensure_ascii=False)
            
            logger.log_info(f"AI Profiler successfully returned {len(updated_data.updated_knowledge_nodes)} knowledge concept increments.")
            for kn_update in updated_data.updated_knowledge_nodes:
                node = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id, models.KnowledgeNode.concept == kn_update.concept).first()
                if not node:
                    node = models.KnowledgeNode(user_id=user_profile.id, concept=kn_update.concept, category=kn_update.category, mastery_score=kn_update.mastery_score_delta, confidence_level=kn_update.confidence_score)
                    db.add(node)
                    logger.log_success(f"Registered new node: {kn_update.concept} ({kn_update.mastery_score_delta*100:.1f}%)")
                else:
                    old_score = node.mastery_score
                    node.mastery_score = min(1.0, node.mastery_score + kn_update.mastery_score_delta)
                    node.confidence_level = kn_update.confidence_score
                    logger.log_success(f"Updated node '{kn_update.concept}': {old_score*100:.1f}% -> {node.mastery_score*100:.1f}%")
                    
            db.commit()
            logger.log_success("All cognitive states and knowledge bases have been updated securely.")
        else:
            logger.log_error("Profiler returned None. AI failed to return valid schema.")
        logger.log_process_end("Cognitive Profiling Pipeline", 0)
    except Exception as e:
        logger.log_error(f"Background profiling failed: {str(e)}")
    finally:
        db.close()


# --- Database Migrations ---
def run_migrations():
    logger.log_info("Running database migrations...")
    engine = database.engine
    with engine.connect() as conn:
        # Create Cognitive Profiler and User Profile tables safely
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                age VARCHAR,
                education_level VARCHAR,
                background_experience TEXT,
                primary_goals TEXT,
                additional_info TEXT,
                created_at VARCHAR
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cognitive_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                global_learning_velocity FLOAT DEFAULT 1.0,
                attention_span_minutes INTEGER DEFAULT 25,
                retention_index FLOAT DEFAULT 0.8,
                cognitive_data_json TEXT,
                interests_json TEXT,
                FOREIGN KEY(user_id) REFERENCES user_profiles(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                concept VARCHAR,
                category VARCHAR,
                mastery_score FLOAT DEFAULT 0.0,
                confidence_level FLOAT DEFAULT 0.0,
                last_tested_at VARCHAR,
                FOREIGN KEY(user_id) REFERENCES user_profiles(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS learning_event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp VARCHAR,
                event_type VARCHAR,
                course_title VARCHAR,
                session_title VARCHAR,
                study_duration_seconds INTEGER,
                raw_interaction_text TEXT,
                vector_embedding_json TEXT,
                FOREIGN KEY(user_id) REFERENCES user_profiles(id)
            )
        """))
        
        # Ensure 'name' exists in user_profiles in case it was created without it
        try:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN name VARCHAR"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN age VARCHAR"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN education_level VARCHAR"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN background_experience TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN primary_goals TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN additional_info TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN created_at VARCHAR"))
        except Exception:
            pass
        
        # New CognitiveProfile columns
        for col_name, col_def in [
            ("recommended_topics_json", "TEXT DEFAULT '[]'"),
            ("learning_style_summary", "TEXT"),
            ("strength_areas_json", "TEXT DEFAULT '[]'"),
            ("personality_summary", "TEXT"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE cognitive_profiles ADD COLUMN {col_name} {col_def}"))
                conn.commit()
            except Exception:
                pass

        # Columns to add to courses
        course_columns = [
            ("short_title", "VARCHAR"),
            ("level", "VARCHAR"),
            ("hours", "INTEGER"),
            ("sessions", "INTEGER"),
            ("chat_summary", "TEXT"),
            ("color", "VARCHAR"),
            ("cover_image", "VARCHAR")
        ]
        for col_name, col_type in course_columns:
            try:
                conn.execute(text(f"ALTER TABLE courses ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                logger.log_success(f"Added {col_name} column to courses table")
            except Exception:
                pass

        # Columns to add to outline_items
        outline_columns = [
            ("study_time", "INTEGER DEFAULT 0"),
            ("chapter", "VARCHAR"),
            ("completed_at", "VARCHAR")
        ]
        for col_name, col_type in outline_columns:
            try:
                conn.execute(text(f"ALTER TABLE outline_items ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                logger.log_success(f"Added {col_name} column to outline_items table")
            except Exception:
                pass

        # Create daily_activity table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS daily_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date VARCHAR(255),
                study_time INTEGER DEFAULT 0
            )
        """))
        try:
            conn.execute(text("CREATE INDEX ix_daily_activity_date ON daily_activity (date)"))
        except Exception:
            pass

        # Create knowledge_insights table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                created_at VARCHAR(255)
            )
        """))

        # Create user_settings table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255),
                age VARCHAR(50),
                education VARCHAR(255),
                background_experience TEXT,
                additional_info TEXT,
                gemini_api_key VARCHAR(255),
                gemini_model VARCHAR(255)
            )
        """))

        conn.commit()
    logger.log_success("Database migrations complete")

run_migrations()
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for API ---
class SettingsSchema(BaseModel):
    google_api_key: Optional[str] = None
    model_name: Optional[str] = None
    name: Optional[str] = None
    age: Optional[str] = None
    education: Optional[str] = None
    background_experience: Optional[str] = None
    additional_info: Optional[str] = None

class OutlineItemCreate(BaseModel):
    title: str
    description: str

class OutlineChapterCreate(BaseModel):
    title: str
    description: str
    items: List[OutlineItemCreate]

class CourseCreate(BaseModel):
    short_title: str
    description: str
    level: str
    hours: int
    sessions: int
    outline: List[OutlineChapterCreate]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class CoachChatRequest(BaseModel):
    message: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    course_id: int
    item_id: int

class ChatHistoryResponse(BaseModel):
    role: str
    content: str

class OutlineItemOut(BaseModel):
    id: int
    title: str
    chapter: Optional[str]
    is_completed: bool
    content: Optional[str]
    study_time: int = 0

    class Config:
        from_attributes = True # updated for pydantic v2

class CourseOut(BaseModel):
    id: int
    title: str
    short_title: Optional[str]
    description: Optional[str]
    level: Optional[str]
    hours: Optional[int]
    sessions: Optional[int]
    progress: float
    color: Optional[str] = "purple"
    cover_image: Optional[str] = None
    items: List[OutlineItemOut]

    class Config:
        from_attributes = True # updated for pydantic v2

# --- API Endpoints ---

@app.get("/settings")
def get_settings(db: Session = Depends(database.get_db)):
    load_dotenv(override=True)
    env_settings = {
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        "model_name": os.getenv("GENERATOR_MODEL_NAME", "gemini-flash-latest")
    }
    
    user_settings = db.query(models.UserSettings).first()
    if user_settings:
        return {
            **env_settings,
            "name": user_settings.name or "",
            "age": user_settings.age or "",
            "education": user_settings.education or "",
            "background_experience": user_settings.background_experience or "",
            "additional_info": user_settings.additional_info or ""
        }
    return {
        **env_settings,
        "name": "", "age": "", "education": "", "background_experience": "", "additional_info": ""
    }

@app.post("/settings")
def update_settings(settings: SettingsSchema, db: Session = Depends(database.get_db)):
    env_file = ".env"
    if not os.path.exists(env_file):
        open(env_file, 'w').close()
    
    if settings.google_api_key is not None:
        set_key(env_file, "GOOGLE_API_KEY", settings.google_api_key)
    if settings.model_name is not None:
        set_key(env_file, "GENERATOR_MODEL_NAME", settings.model_name)
        set_key(env_file, "MAIN_MODEL_NAME", settings.model_name)
        set_key(env_file, "COACH_MODEL_NAME", settings.model_name)
        
    user_settings = db.query(models.UserSettings).first()
    if not user_settings:
        user_settings = models.UserSettings()
        db.add(user_settings)
        
    user_profile = db.query(models.UserProfile).first()
    if not user_profile:
        user_profile = models.UserProfile()
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)
        cog_profile = models.CognitiveProfile(user_id=user_profile.id)
        db.add(cog_profile)
        
    if settings.name is not None:
        user_settings.name = settings.name
        user_profile.name = settings.name
    if settings.age is not None:
        user_settings.age = settings.age
        user_profile.age = settings.age
    if settings.education is not None:
        user_settings.education = settings.education
        user_profile.education_level = settings.education
    if settings.background_experience is not None:
        user_settings.background_experience = settings.background_experience
        user_profile.background_experience = settings.background_experience
    if settings.additional_info is not None:
        user_settings.additional_info = settings.additional_info
        user_profile.additional_info = settings.additional_info
    if settings.google_api_key is not None:
        user_settings.gemini_api_key = settings.google_api_key
    if settings.model_name is not None:
        user_settings.gemini_model = settings.model_name
        
    db.commit()
    
    return {"status": "success"}


@app.post("/chat/course-generator")
def chat_course_generator(request: ChatRequest, db: Session = Depends(database.get_db)):
    logger.log_info("API Endpoint: /chat/course-generator hit")
    
    user_settings = db.query(models.UserSettings).first()
    user_info = ""
    if user_settings:
        user_info = f"Name: {user_settings.name or 'N/A'}\nAge: {user_settings.age or 'N/A'}\nEducation: {user_settings.education or 'N/A'}\nExperience: {user_settings.background_experience or 'N/A'}\nAdditional Info: {user_settings.additional_info or 'N/A'}"
        
    # Convert Pydantic models to dicts for the agent
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    result = agents.chat_course_generator(messages, user_info)
    return result

@app.get("/courses/{course_id}/chat-history", response_model=List[ChatHistoryResponse])
def get_course_chat_history(course_id: int, db: Session = Depends(database.get_db)):
    history = db.query(models.CourseChatMessage).filter(models.CourseChatMessage.course_id == course_id).order_by(models.CourseChatMessage.id).all()
    return [{"role": msg.role, "content": msg.content} for msg in history]

@app.post("/chat/coach")
def chat_coach(request: CoachChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    logger.log_info(f"API Endpoint: /chat/coach hit for course {request.course_id}, item {request.item_id}")
    course = db.query(models.Course).filter(models.Course.id == request.course_id).first()
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == request.item_id).first()
    
    if not course or not item:
        raise HTTPException(status_code=404, detail="Course or Item not found")
        
    user_input = request.message
    if not user_input and request.messages:
        user_input = request.messages[-1].content
        
    # Save user message
    user_msg = models.CourseChatMessage(course_id=course.id, role="user", content=user_input or "")
    db.add(user_msg)
    
    # Log Learning Event and Trigger AI Profiler
    user_profile = db.query(models.UserProfile).first()
    if user_profile:
        event = models.LearningEventLog(
            user_id=user_profile.id,
            event_type="smart_coach_interaction",
            course_title=course.title,
            session_title=item.title,
            raw_interaction_text=f"User asked: {user_input}"
        )
        db.add(event)
        # We no longer trigger the heavy background task on every single chat message.
        # It will be triggered once the session is completed.
        
    db.commit()

    # Get history for context
    history_msgs = db.query(models.CourseChatMessage).filter(models.CourseChatMessage.course_id == course.id).order_by(models.CourseChatMessage.id).all()
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in history_msgs]

    outline_titles = [i.title for i in sorted(course.items, key=lambda x: x.order)]
    
    user_settings = db.query(models.UserSettings).first()
    user_info = ""
    if user_settings:
        user_info = f"Name: {user_settings.name or 'N/A'}\nAge: {user_settings.age or 'N/A'}\nEducation: {user_settings.education or 'N/A'}\nExperience: {user_settings.background_experience or 'N/A'}\nAdditional Info: {user_settings.additional_info or 'N/A'}"
        
    # Build semantic memory dynamically
    logs = db.query(models.LearningEventLog).filter(models.LearningEventLog.vector_embedding_json != None).all()
    logs_with_vectors = []
    for log in logs:
        try:
            logs_with_vectors.append({
                "title": f"{log.course_title} - {log.session_title}",
                "text": f"Event: {log.event_type} | Data: {log.raw_interaction_text or f'Studied for {log.study_duration_seconds}s'}",
                "vector": json.loads(log.vector_embedding_json)
            })
        except:
            pass
            
    semantic_memory_context = ""
    if logs_with_vectors:
        semantic_memory_context = agents.semantic_search_logs(user_input, logs_with_vectors)

    generator = agents.chat_coach_stream(
        messages=messages_dict,
        course_title=course.title,
        course_description=course.description or "",
        outline_titles=outline_titles,
        current_session_title=item.title,
        current_session_content=item.content or "",
        chat_summary=course.chat_summary,
        user_info=user_info,
        semantic_memory_context=semantic_memory_context
    )
    
    def stream_wrapper():
        full_response = ""
        for chunk in generator:
            full_response += chunk
            yield chunk
            
        # Save assistant message after streaming completes
        assistant_msg = models.CourseChatMessage(course_id=course.id, role="assistant", content=full_response)
        db.add(assistant_msg)
        db.commit()

        # Execute conversation history summarizing (Langchain strategy)
        try:
            unsummarized_msgs = db.query(models.CourseChatMessage).filter(
                models.CourseChatMessage.course_id == course.id,
                models.CourseChatMessage.is_summarized == False
            ).order_by(models.CourseChatMessage.id).all()
            
            # Summarize older context, keep recent unsummarized
            if len(unsummarized_msgs) > 10:
                msgs_to_summarize = unsummarized_msgs[:-6]
                messages_dict_to_summarize = [{"role": msg.role, "content": msg.content} for msg in msgs_to_summarize]
                
                logger.log_info(f"Triggering background summarization for {len(msgs_to_summarize)} old messages...")
                
                new_summary = agents.generate_history_summary(messages_dict_to_summarize, course.chat_summary)
                course.chat_summary = new_summary
                
                for msg in msgs_to_summarize:
                    msg.is_summarized = True
                    
                db.commit()
                logger.log_success(f"History summarization complete. New summary saved for course {course.id}")
        except Exception as e:
            logger.log_error(f"Error during background summarization: {str(e)}")

    return StreamingResponse(stream_wrapper(), media_type="text/plain")

@app.post("/courses/")
def create_course(course: CourseCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    logger.log_process_start("Database Operation", f"Creating new course: {course.short_title}")
    # 1. Save Course to DB
    db_course = models.Course(
        title=course.short_title,
        short_title=course.short_title,
        description=course.description,
        level=course.level,
        hours=course.hours,
        sessions=course.sessions
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    # 2. Save Outline Items to DB
    order = 0
    for chapter in course.outline:
        for item in chapter.items:
            db_item = models.OutlineItem(
                course_id=db_course.id,
                chapter=chapter.title,
                title=item.title,
                order=order,
                is_completed=False,
                content=None,
                study_time=0
            )
            db.add(db_item)
            order += 1

    db.commit()
    logger.log_success(f"Successfully saved course '{course.short_title}' and its items to DB")

    # 3. Log Learning Event for course creation and trigger background optimizer
    user_profile = db.query(models.UserProfile).first()
    if user_profile:
        event = models.LearningEventLog(
            user_id=user_profile.id,
            event_type="course_created",
            course_title=db_course.title,
            session_title="ایجاد دوره جدید",
            raw_interaction_text=(
                f"کاربر دوره جدیدی به نام '{db_course.title}' ایجاد کرد. "
                f"توضیحات دوره: '{db_course.description or 'ندارد'}' | سطح دوره: '{db_course.level or 'نامشخص'}'. "
                f"این دوره شامل {order} جلسه آموزشی است که به برنامه درسی افزوده شد."
            )
        )
        db.add(event)
        db.commit()
        
        # Trigger dynamic background optimizer
        background_tasks.add_task(run_profiling_background_task)
        logger.log_success("Triggered AI profiler optimization task for newly generated course.")

    return db_course

@app.get("/courses/", response_model=List[CourseOut])
def list_courses(db: Session = Depends(database.get_db)):
    courses = db.query(models.Course).all()
    results = []
    for course in courses:
        completed = [i for i in course.items if i.is_completed]
        progress = (len(completed) / len(course.items) * 100) if course.items else 0

        results.append({
            "id": course.id,
            "title": course.title,
            "short_title": course.short_title,
            "description": course.description,
            "level": course.level,
            "hours": course.hours,
            "sessions": course.sessions,
            "progress": progress,
            "color": course.color or "purple",
            "cover_image": course.cover_image,
            "items": sorted(course.items, key=lambda x: x.order)
        })
    return results

@app.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    completed = [i for i in course.items if i.is_completed]
    progress = (len(completed) / len(course.items) * 100) if course.items else 0
    return {
        "id": course.id,
        "title": course.title,
        "short_title": course.short_title,
        "description": course.description,
        "level": course.level,
        "hours": course.hours,
        "sessions": course.sessions,
        "progress": progress,
        "color": course.color or "purple",
        "cover_image": course.cover_image,
        "items": sorted(course.items, key=lambda x: x.order)
    }

@app.get("/daily-micro-courses")
def get_daily_micro_courses(course_ids: Optional[str] = None, count: int = 1, exclude_ids: Optional[str] = None, db: Session = Depends(database.get_db)):
    courses_query = db.query(models.Course)
    if course_ids:
        ids = [int(id) for id in course_ids.split(',') if id.strip().isdigit()]
        if ids:
            courses_query = courses_query.filter(models.Course.id.in_(ids))
    courses = courses_query.all()
    
    excluded = set()
    if exclude_ids:
        excluded = {int(id) for id in exclude_ids.split(',') if id.strip().isdigit()}
    
    daily_items = []
    
    # We can use today's date as a seed so it remains consistent for the day
    from datetime import date
    import random
    seed = date.today().toordinal()
    rng = random.Random(seed)
    
    for course in courses:
        items = list(course.items)
        rng.shuffle(items)
        
        # Select items that are not completed and not already loaded
        valid_items = [i for i in items if not i.is_completed and i.id not in excluded]
        selected = valid_items[:count]
        
        for item in selected:
            daily_items.append({
                "course_id": course.id,
                "course_title": course.title,
                "course_color": course.color,
                "item_id": item.id,
                "item_title": item.title,
                "chapter": item.chapter,
                "content": item.content,
                "is_completed": item.is_completed
            })
            
    return daily_items


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    color: Optional[str] = None

@app.patch("/courses/{course_id}")
def update_course(course_id: int, update_data: CourseUpdate, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if update_data.title is not None:
        course.title = update_data.title
    if update_data.color is not None:
        course.color = update_data.color
        
    db.commit()
    db.refresh(course)
    logger.log_success(f"Updated course {course_id}")
    return course

@app.post("/courses/{course_id}/cover")
async def upload_course_cover(course_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    os.makedirs("static/images/covers", exist_ok=True)
    file_extension = file.filename.split(".")[-1]
    file_path = f"static/images/covers/{course_id}.{file_extension}"
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    image_url = f"/assets/images/covers/{course_id}.{file_extension}"
    course.cover_image = image_url
    db.commit()
    db.refresh(course)
    
    logger.log_success(f"Uploaded cover image for course {course_id}")
    return course

@app.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Delete associated items first
    db.query(models.OutlineItem).filter(models.OutlineItem.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    logger.log_info(f"Deleted course ID: {course_id}")
    return {"status": "success"}

@app.post("/courses/{course_id}/generate-micro")
def generate_random_micro(course_id: int, db: Session = Depends(database.get_db)):
    logger.log_info(f"API Endpoint: Request to generate random micro-course for course {course_id}")
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    remaining_items = [i for i in course.items if not i.is_completed]
    if not remaining_items:
        raise HTTPException(status_code=400, detail="Course already completed")

    selected_item = random.choice(remaining_items)
    
    # Get all item titles for context
    full_outline = [i.title for i in sorted(course.items, key=lambda x: x.order)]
    
    user_settings = db.query(models.UserSettings).first()
    user_info = ""
    if user_settings:
        user_info = f"Name: {user_settings.name or 'N/A'}\nAge: {user_settings.age or 'N/A'}\nEducation: {user_settings.education or 'N/A'}\nExperience: {user_settings.background_experience or 'N/A'}\nAdditional Info: {user_settings.additional_info or 'N/A'}"

    # Generate content using Agent
    content = agents.get_content(
        subject=course.title, 
        item_title=selected_item.title,
        course_description=course.description,
        full_outline=full_outline,
        user_info=user_info
    )

    selected_item.content = content
    db.commit()

    return selected_item

@app.post("/items/{item_id}/complete")
def complete_item(item_id: int, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_completed = True
    from datetime import datetime
    item.completed_at = datetime.now().isoformat()
    
    # Log Learning Event and Trigger AI Profiler
    user_profile = db.query(models.UserProfile).first()
    if user_profile:
        event = models.LearningEventLog(
            user_id=user_profile.id,
            event_type="session_complete",
            course_title=item.course.title if item.course else "Unknown",
            session_title=item.title,
            study_duration_seconds=item.study_time
        )
        db.add(event)
        background_tasks.add_task(run_profiling_background_task)
        
    db.commit()
    logger.log_success(f"Item {item_id} marked as complete and profiler triggered")
    return {"status": "success"}

class StudyTimeUpdate(BaseModel):
    seconds: int

@app.post("/items/{item_id}/study-time")
def update_study_time(item_id: int, data: StudyTimeUpdate, db: Session = Depends(database.get_db)):
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.study_time += data.seconds

    # Update Daily Activity
    from datetime import date
    today = date.today().isoformat()
    daily = db.query(models.DailyActivity).filter(models.DailyActivity.date == today).first()
    if not daily:
        daily = models.DailyActivity(date=today, study_time=data.seconds)
        db.add(daily)
    else:
        daily.study_time += data.seconds

    db.commit()
    return {"status": "success", "total_study_time": item.study_time}

@app.post("/items/{item_id}/set-study-time")
def set_study_time(item_id: int, data: StudyTimeUpdate, db: Session = Depends(database.get_db)):
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    diff = data.seconds - item.study_time
    item.study_time = data.seconds

    # Update Daily Activity with the difference
    from datetime import date
    today = date.today().isoformat()
    daily = db.query(models.DailyActivity).filter(models.DailyActivity.date == today).first()
    if not daily:
        daily = models.DailyActivity(date=today, study_time=max(0, diff))
        db.add(daily)
    else:
        daily.study_time = max(0, daily.study_time + diff)

    db.commit()
    return {"status": "success", "total_study_time": item.study_time}


@app.get("/stats")
def get_stats(db: Session = Depends(database.get_db)):
    total_courses = db.query(models.Course).count()
    completed_items = db.query(models.OutlineItem).filter(models.OutlineItem.is_completed == True).all()

    total_sessions = db.query(models.OutlineItem).count()
    total_completed_sessions = len(completed_items)

    total_study_time = db.query(sqlalchemy.func.sum(models.OutlineItem.study_time)).scalar() or 0

    # Calculate completed courses
    all_courses = db.query(models.Course).all()
    completed_courses_count = 0
    for course in all_courses:
        if course.items and all(item.is_completed for item in course.items):
            completed_courses_count += 1

    # Recent completed sessions
    recent_completed = []
    # Sort by completed_at if available, else by id
    sorted_completed = sorted(completed_items, key=lambda x: (x.completed_at or '', x.id))
    for item in sorted_completed[-20:]: # Last 20
        recent_completed.append({
            "id": item.id,
            "title": item.title,
            "course_id": item.course_id,
            "course_title": item.course.title,
            "study_time": item.study_time,
            "completed_at": item.completed_at
        })

    # Activity Data (Last 365 days)
    from datetime import date, timedelta
    start_date = (date.today() - timedelta(days=364)).isoformat()
    
    # Query all daily activities in the range
    daily_activities = db.query(models.DailyActivity).filter(models.DailyActivity.date >= start_date).all()
    activity_map = {d.date: d.study_time for d in daily_activities}
    
    # Group completed items by date
    completed_items_by_date = {}
    for item in completed_items:
        if hasattr(item, 'completed_at') and item.completed_at:
            date_str = item.completed_at.split('T')[0]
            if date_str not in completed_items_by_date:
                completed_items_by_date[date_str] = []
            completed_items_by_date[date_str].append(item.title)
    
    activity_data = []
    for i in range(364, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        study_time = activity_map.get(d, 0)
        sessions = completed_items_by_date.get(d, [])
        
        # Only add to activity_data if within last 7 days or has some activity to keep frontend array manageable
        # Wait, the frontend wants to zoom out to 365 days, so we must return all 365 days.
        activity_data.append({
            "date": d,
            "minutes": study_time // 60,
            "completed_sessions": sessions
        })

    # Fetch Cognitive Profile Data
    user_profile = db.query(models.UserProfile).first()
    cognitive_profile = None
    user_info = None
    knowledge_nodes = []
    
    if user_profile:
        user_info = {
            "name": user_profile.name,
            "age": user_profile.age,
            "education_level": user_profile.education_level,
            "background_experience": user_profile.background_experience,
            "primary_goals": user_profile.primary_goals,
            "additional_info": user_profile.additional_info
        }
        if user_profile.cognitive_profile:
            import json
            cp = user_profile.cognitive_profile
            cognitive_profile = {
                "global_learning_velocity": cp.global_learning_velocity,
                "attention_span_minutes": cp.attention_span_minutes,
                "retention_index": cp.retention_index,
                "cognitive_data": json.loads(cp.cognitive_data_json) if cp.cognitive_data_json else {},
                "interests": json.loads(cp.interests_json) if cp.interests_json else [],
                "learning_style_summary": cp.learning_style_summary or "",
                "personality_summary": cp.personality_summary or "",
                "strength_areas": json.loads(cp.strength_areas_json) if cp.strength_areas_json else [],
                "recommended_topics": json.loads(cp.recommended_topics_json) if cp.recommended_topics_json else [],
            }
        
        # Fetch knowledge nodes grid
        nodes = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id).order_by(models.KnowledgeNode.mastery_score.desc()).all()
        for n in nodes:
            knowledge_nodes.append({
                "concept": n.concept,
                "category": n.category,
                "mastery_score": n.mastery_score,
                "confidence_level": n.confidence_level
            })

    return {
        "total_courses": total_courses,
        "completed_courses": completed_courses_count,
        "total_sessions": total_sessions,
        "total_completed_sessions": total_completed_sessions,
        "total_study_time": total_study_time,
        "recent_completed": recent_completed,
        "activity_data": activity_data,
        "cognitive_profile": cognitive_profile,
        "user_info": user_info,
        "knowledge_nodes": knowledge_nodes
    }

@app.post("/profile/rebuild")
def rebuild_profile(db: Session = Depends(database.get_db)):
    logger.log_process_start("Full Profile Rebuild", "Aggregating all historical user data to rebuild knowledge bases")
    
    try:
        # 1. Ensure user profile exists
        user_profile = db.query(models.UserProfile).first()
        if not user_profile:
            user_settings = db.query(models.UserSettings).first()
            name = user_settings.name if user_settings else "کاربر"
            bg = user_settings.background_experience if user_settings else ""
            user_profile = models.UserProfile(name=name, background_experience=bg, primary_goals="یادگیری و توسعه فردی")
            db.add(user_profile)
            db.commit()
            db.refresh(user_profile)
            logger.log_success(f"Created UserProfile for: {name}")

        # 2. Sync settings -> profile
        user_settings = db.query(models.UserSettings).first()
        if user_settings:
            user_profile.name = user_settings.name or user_profile.name
            user_profile.age = user_settings.age or user_profile.age
            user_profile.education_level = user_settings.education or user_profile.education_level
            user_profile.background_experience = user_settings.background_experience or user_profile.background_experience
            db.commit()
            logger.log_success("Synced UserSettings -> UserProfile")

        # 3. Ensure cognitive profile exists
        if not user_profile.cognitive_profile:
            cp = models.CognitiveProfile(user_id=user_profile.id, cognitive_data_json="{}", interests_json="[]",
                                          recommended_topics_json="[]", strength_areas_json="[]")
            db.add(cp)
            db.commit()
            db.refresh(user_profile)

        # 4. Delete old nodes to rebuild fresh
        deleted = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id).delete()
        db.commit()
        logger.log_info(f"Cleared {deleted} old knowledge nodes for fresh rebuild.")

        # 5. Gather ALL historical data
        all_courses = db.query(models.Course).all()
        
        # Course info aggregation
        courses_info = []
        for c in all_courses:
            total_study_time = sum(item.study_time for item in c.items)
            session_count = len(c.items)
            outline_titles = [item.title for item in sorted(c.items, key=lambda x: x.order)]
            outline_str = ", ".join(outline_titles) if outline_titles else "فاقد سرفصل"
            courses_info.append(
                f"- دوره: '{c.title}' | سطح: '{c.level or 'نامشخص'}' | توضیحات: '{c.description or ''}' | "
                f"کل زمان مطالعه دوره: {total_study_time} ثانیه | تعداد کل جلسات: {session_count} | "
                f"سرفصل‌های کل دوره: [{outline_str}]"
            )
        courses_str = "\n".join(courses_info) if courses_info else "هیچ دوره‌ای ثبت نشده است."

        # Outline item aggregation
        completed_items = db.query(models.OutlineItem).filter(models.OutlineItem.is_completed == True).all()
        
        sessions_info = []
        for item in completed_items:
            sessions_info.append(
                f"- جلسه سرفصل تکمیل‌شده: '{item.title}' | دوره: '{item.course.title if item.course else 'نامشخص'}' | زمان مطالعه: {item.study_time} ثانیه"
            )
        sessions_str = "\n".join(sessions_info) if sessions_info else "هیچ سرفصل تکمیل‌شده‌ای وجود ندارد."

        # Course chats aggregation
        all_chats = db.query(models.CourseChatMessage).all()
        chats_info = []
        for chat in all_chats:
            role_fa = "مربی هوشمند" if chat.role == "assistant" else "کاربر"
            course_title = chat.course.title if chat.course else "نامشخص"
            chats_info.append(
                f"- [{role_fa}] در دوره '{course_title}': {chat.content}"
            )
        chats_str = "\n".join(chats_info) if chats_info else "هیچ گفتگویی ثبت نشده است."

        # Learning Event logs aggregation
        all_logs = db.query(models.LearningEventLog).filter(models.LearningEventLog.user_id == user_profile.id).all()
        logs_info = []
        for log in all_logs:
            logs_info.append(
                f"- رویداد: '{log.event_type}' | دوره: '{log.course_title or ''}' | جلسه: '{log.session_title or ''}' | زمان مطالعه: {log.study_duration_seconds} ثانیه | جزئیات تعامل: {log.raw_interaction_text or ''}"
            )
        logs_str = "\n".join(logs_info) if logs_info else "لاگ رویداد آموزشی یافت نشد."

        # Compile final history block
        profile_str = (
            f"نام: {user_profile.name or 'کاربر'}, سن: {user_profile.age or 'نامشخص'}, "
            f"تحصیلات: {user_profile.education_level or 'نامشخص'}, "
            f"پیش‌زمینه: {user_profile.background_experience or ''}, "
            f"اهداف: {user_profile.primary_goals or 'یادگیری و توسعه فردی'}"
        )
        
        cog_profile = user_profile.cognitive_profile
        # Clear cognitive profile items to prevent anchoring bias during a manual rebuild/refresh
        current_state_str = "وضعیت شناختی قبلی وجود ندارد. سرعت یادگیری، تمرکز، و شاخص حفظ اطلاعات را کاملاً از نو بر اساس لاگ‌ها و سرفصل‌های تکمیل‌شده از نو دقیقاً محاسبه کنید."

        super_history_str = f"""
=== دوره‌های کاربر (User Courses) ===
{courses_str}

=== وضعیت سرفصل‌ها و جلسات تکمیل‌شده (Completed Outline Items) ===
{sessions_str}

=== گفتگوها با مربی هوشمند (Smart Coach Chats) ===
{chats_str}

=== لاگ رویدادهای آموزشی (Learning Event Logs) ===
{logs_str}
"""

        # Verbose terminal logging
        logger.log_info("=" * 70)
        logger.log_info("🚨 COMPREHENSIVE REBUILD INITIATED 🚨")
        logger.log_info(f"User Profile Info:\n{profile_str}")
        logger.log_info(f"Current State:\n{current_state_str}")
        logger.log_info(f"Aggregated Courses: {len(all_courses)}")
        logger.log_info(f"Aggregated Completed Sessions: {len(completed_items)}")
        logger.log_info(f"Aggregated Chats: {len(all_chats)}")
        logger.log_info(f"Aggregated Event Logs: {len(all_logs)}")
        logger.log_info("-" * 70)
        logger.log_info("📜 FULL HISTORICAL TEXT COMPILED FOR AI:")
        logger.log_info(super_history_str.strip())
        logger.log_info("=" * 70)

        # 6. Call AI cognitive profiler
        updated_data = agents.run_cognitive_profiler(profile_str, current_state_str, super_history_str)

        if not updated_data:
            logger.log_error("Profiler returned None. AI Rebuild Failed.")
            raise HTTPException(status_code=500, detail="AI profiler failed to generate cognitive profile.")

        # 7. Save rebuilt cognitive profile
        cog_profile.global_learning_velocity = updated_data.global_learning_velocity
        cog_profile.attention_span_minutes = updated_data.attention_span_minutes
        cog_profile.retention_index = updated_data.retention_index
        
        cognitive_data_dict = {
            "learning_style": {
                "hands_on": updated_data.ls_hands_on,
                "visual": updated_data.ls_visual,
                "theoretical": updated_data.ls_theoretical,
                "self_directed": updated_data.ls_self_directed
            },
            "personality_traits": {
                "persistence": updated_data.pt_persistence,
                "patience_with_errors": updated_data.pt_patience,
                "learning_curiosity": updated_data.pt_curiosity,
                "preferred_session_length": updated_data.pt_session_length
            }
        }
        cog_profile.cognitive_data_json = json.dumps(cognitive_data_dict, ensure_ascii=False)
        cog_profile.interests_json = json.dumps(updated_data.new_interests, ensure_ascii=False)
        cog_profile.learning_style_summary = updated_data.learning_style_summary
        cog_profile.personality_summary = updated_data.personality_summary
        cog_profile.strength_areas_json = json.dumps(updated_data.strength_areas, ensure_ascii=False)
        cog_profile.recommended_topics_json = json.dumps(updated_data.recommended_topics, ensure_ascii=False)

        logger.log_success(f"Saved rebuilt cognitive profile. Got {len(updated_data.updated_knowledge_nodes)} knowledge nodes.")
        
        # 8. Register rebuilt knowledge nodes
        for kn in updated_data.updated_knowledge_nodes:
            node = models.KnowledgeNode(
                user_id=user_profile.id,
                concept=kn.concept,
                category=kn.category,
                mastery_score=min(1.0, kn.mastery_score_delta),
                confidence_level=kn.confidence_score
            )
            db.add(node)
            logger.log_success(f"  ✦ {kn.concept} ({kn.category}) — {kn.mastery_score_delta*100:.0f}%")

        db.commit()
        logger.log_success("=== Complete Rebuild Sync Complete! All widgets refreshed! ===")
        
        return {"status": "success", "message": "Knowledge base rebuilt successfully."}

    except Exception as e:
        import traceback
        logger.log_error(f"Manual rebuild failed: {str(e)}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")

@app.post("/generate-insight")
def generate_insight(db: Session = Depends(database.get_db)):
    completed_items = db.query(models.OutlineItem).filter(models.OutlineItem.is_completed == True).all()

    completed_sessions_data = [
        {"course_title": item.course.title, "item_title": item.title}
        for item in completed_items
    ]

    insight_content = agents.generate_knowledge_insight(completed_sessions_data)

    from datetime import datetime
    new_insight = models.KnowledgeInsight(
        content=insight_content,
        created_at=datetime.now().isoformat()
    )
    db.add(new_insight)
    db.commit()
    db.refresh(new_insight)

    return new_insight

@app.get("/insights")
def get_insights(db: Session = Depends(database.get_db)):
    insights = db.query(models.KnowledgeInsight).order_by(models.KnowledgeInsight.id.desc()).all()
    return insights

@app.post("/items/{item_id}/generate")
def generate_specific_micro(item_id: int, db: Session = Depends(database.get_db)):
    logger.log_info(f"API Endpoint: Request to generate specific micro-course for item {item_id}")
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    course = item.course
    # Get all item titles for context
    full_outline = [i.title for i in sorted(course.items, key=lambda x: x.order)]
    
    user_settings = db.query(models.UserSettings).first()
    user_info = ""
    if user_settings:
        user_info = f"Name: {user_settings.name or 'N/A'}\nAge: {user_settings.age or 'N/A'}\nEducation: {user_settings.education or 'N/A'}\nExperience: {user_settings.background_experience or 'N/A'}\nAdditional Info: {user_settings.additional_info or 'N/A'}"

    content = agents.get_content(
        subject=course.title, 
        item_title=item.title,
        course_description=course.description,
        full_outline=full_outline,
        user_info=user_info
    )

    item.content = content
    db.commit()

    return item

# --- Static Frontend Serving ---
import os
# Ensure static directory exists
os.makedirs("static", exist_ok=True)
app.mount("/assets", StaticFiles(directory="static"), name="assets")

@app.get("/{full_path:path}")
def serve_react_app(full_path: str):
    return FileResponse("static/index.html")
