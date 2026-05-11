from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import random
from typing import List, Optional
import os
from dotenv import load_dotenv, set_key

import models, database, agents
from pydantic import BaseModel
from logger import logger

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
def get_settings():
    load_dotenv(override=True)
    return {
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        "model_name": os.getenv("GENERATOR_MODEL_NAME", "gemini-flash-latest")
    }

@app.post("/settings")
def update_settings(settings: SettingsSchema):
    env_file = ".env"
    if not os.path.exists(env_file):
        open(env_file, 'w').close()
    
    if settings.google_api_key is not None:
        set_key(env_file, "GOOGLE_API_KEY", settings.google_api_key)
    if settings.model_name is not None:
        set_key(env_file, "GENERATOR_MODEL_NAME", settings.model_name)
        set_key(env_file, "MAIN_MODEL_NAME", settings.model_name)
        set_key(env_file, "COACH_MODEL_NAME", settings.model_name)
    
    return {"status": "success"}


@app.post("/chat/course-generator")
def chat_course_generator(request: ChatRequest):
    logger.log_info("API Endpoint: /chat/course-generator hit")
    # Convert Pydantic models to dicts for the agent
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    result = agents.chat_course_generator(messages)
    return result

@app.get("/courses/{course_id}/chat-history", response_model=List[ChatHistoryResponse])
def get_course_chat_history(course_id: int, db: Session = Depends(database.get_db)):
    history = db.query(models.CourseChatMessage).filter(models.CourseChatMessage.course_id == course_id).order_by(models.CourseChatMessage.id).all()
    return [{"role": msg.role, "content": msg.content} for msg in history]

@app.post("/chat/coach")
def chat_coach(request: CoachChatRequest, db: Session = Depends(database.get_db)):
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
    db.commit()

    # Get history for context
    history_msgs = db.query(models.CourseChatMessage).filter(models.CourseChatMessage.course_id == course.id).order_by(models.CourseChatMessage.id).all()
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in history_msgs]

    outline_titles = [i.title for i in sorted(course.items, key=lambda x: x.order)]
    
    generator = agents.chat_coach_stream(
        messages=messages_dict,
        course_title=course.title,
        course_description=course.description or "",
        outline_titles=outline_titles,
        current_session_title=item.title,
        current_session_content=item.content or "",
        chat_summary=course.chat_summary
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
def create_course(course: CourseCreate, db: Session = Depends(database.get_db)):
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
                content=None
            )
            db.add(db_item)
            order += 1

    db.commit()
    logger.log_success(f"Successfully saved course '{course.short_title}' and its items to DB")
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

    # Generate content using Agent
    content = agents.get_content(
        subject=course.title, 
        item_title=selected_item.title,
        course_description=course.description,
        full_outline=full_outline
    )

    selected_item.content = content
    db.commit()

    return selected_item

@app.post("/items/{item_id}/complete")
def complete_item(item_id: int, db: Session = Depends(database.get_db)):
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_completed = True
    db.commit()
    logger.log_success(f"Item {item_id} marked as complete")
    return {"status": "success"}

@app.post("/items/{item_id}/generate")
def generate_specific_micro(item_id: int, db: Session = Depends(database.get_db)):
    logger.log_info(f"API Endpoint: Request to generate specific micro-course for item {item_id}")
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    course = item.course
    # Get all item titles for context
    full_outline = [i.title for i in sorted(course.items, key=lambda x: x.order)]

    content = agents.get_content(
        subject=course.title, 
        item_title=item.title,
        course_description=course.description,
        full_outline=full_outline
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
