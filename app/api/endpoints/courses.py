import os
import random
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile
from sqlalchemy.orm import Session

from app import models, database
from app.logger import logger
from app.schemas import CourseCreate, CourseOut, CourseUpdate
from app.services import agent_service
from app.services.profile_service import run_profiling_background_task
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.post("/courses/", response_model=CourseOut)
def create_course(
    course: CourseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Creates a new AI-outlined course, saves syllabus chapters, and triggers the profiling optimizer."""
    logger.log_process_start("Database Operation", f"Creating new course: {course.short_title}")
    
    import json
    
    # 1. Save Course to DB
    db_course = models.Course(
        user_id=current_user.id,
        title=course.title,
        short_title=course.short_title,
        description=course.course_description,
        course_description=course.course_description,
        level=course.level,
        hours=course.total_estimated_hours,
        total_estimated_hours=course.total_estimated_hours,
        sessions=sum(len(ch.sessions) for ch in course.chapters),
        target_user_summary=course.target_user_summary,
        course_goal=course.course_goal,
        learning_outcomes=json.dumps(course.learning_outcomes),
        prerequisites=json.dumps(course.prerequisites)
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    # 2. Save Outline Items to DB
    order = 0
    for chapter in course.chapters:
        for session in chapter.sessions:
            db_item = models.OutlineItem(
                course_id=db_course.id,
                session_id=session.session_id,
                chapter=chapter.title,
                chapter_id=chapter.chapter_id,
                title=session.title,
                description=session.description,
                learning_objectives=json.dumps(session.learning_objectives),
                key_concepts=json.dumps(session.key_concepts),
                order=order,
                is_completed=False,
                content=None,
                study_time=0
            )
            db.add(db_item)
            order += 1

    db.commit()
    db.refresh(db_course)
    logger.log_success(f"Successfully saved course '{course.short_title}' and its items to DB")

    # Check if AI cover generation is requested
    if course.generate_cover:
        logger.log_info(f"Requesting AI image generation for course cover: {db_course.title}")
        try:
            _us = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
            _api_key = _us.gemini_api_key if _us else None
            outline_context = "\n".join([f"- {ch.title}: " + ", ".join([s.title for s in ch.sessions]) for ch in course.chapters])
            context_text = f"Description: {course.course_description or ''}\nOutline:\n{outline_context}"
            
            visual_prompt = agent_service.generate_prompt_for_image(db_course.title, context_text, api_key=_api_key, content_model=_us.content_model if _us else None)
            
            img_bytes = agent_service.generate_image_cover(visual_prompt, api_key=(_us.image_api_key or _api_key) if _us else _api_key, image_model=_us.image_model if _us else None)
            if img_bytes:
                os.makedirs("static/images/covers", exist_ok=True)
                file_path = f"static/images/covers/{db_course.id}.jpg"
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                
                db_course.cover_image = f"/assets/images/covers/{db_course.id}.jpg"
                db.commit()
                db.refresh(db_course)
                logger.log_success(f"Successfully generated and saved AI cover image for course {db_course.id}")
            else:
                logger.log_error("Could not generate AI cover image (image bytes empty)")
        except Exception as img_err:
            logger.log_error(f"Error generating AI cover image: {str(img_err)}")

    # 3. Log Learning Event and trigger dynamic background profiler thread
    user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if user_profile:
        event = models.LearningEventLog(
            user_id=user_profile.id,
            event_type="course_created",
            course_title=db_course.title,
            session_title="ایجاد دوره جدید",
            raw_interaction_text=(
                f"کاربر دوره جدیدی به نام '{db_course.title}' ایجاد کرد. "
                f"توضیحات دوره: '{db_course.course_description or 'ندارد'}' | سطح دوره: '{db_course.level or 'نامشخص'}'. "
                f"این دوره شامل {order} جلسه آموزشی است که به برنامه درسی افزوده شد."
            ),
            is_profiled=False
        )
        db.add(event)
        db.commit()
        logger.log_success("Saved learning event for newly generated course. Profiling will run in the next batch or nightly.")

    # Format return to match CourseOut pydantic schema
    completed = [i for i in db_course.items if i.is_completed]
    progress = (len(completed) / len(db_course.items) * 100) if db_course.items else 0
    
    # Parse JSON fields for items
    items_with_parsed_json = []
    for item in sorted(db_course.items, key=lambda x: x.order):
        item_dict = {
            "id": item.id,
            "session_id": item.session_id,
            "title": item.title,
            "chapter": item.chapter,
            "chapter_id": item.chapter_id,
            "description": item.description,
            "learning_objectives": json.loads(item.learning_objectives) if item.learning_objectives else [],
            "key_concepts": json.loads(item.key_concepts) if item.key_concepts else [],
            "order": item.order,
            "is_completed": item.is_completed,
            "content": item.content,
            "study_time": item.study_time
        }
        items_with_parsed_json.append(item_dict)
    
    return {
        "id": db_course.id,
        "title": db_course.title,
        "short_title": db_course.short_title,
        "description": db_course.description,
        "course_description": db_course.course_description,
        "level": db_course.level,
        "hours": db_course.hours,
        "total_estimated_hours": db_course.total_estimated_hours,
        "sessions": db_course.sessions,
        "target_user_summary": db_course.target_user_summary,
        "course_goal": db_course.course_goal,
        "learning_outcomes": json.loads(db_course.learning_outcomes) if db_course.learning_outcomes else [],
        "prerequisites": json.loads(db_course.prerequisites) if db_course.prerequisites else [],
        "progress": progress,
        "color": db_course.color or "purple",
        "cover_image": db_course.cover_image,
        "is_published": db_course.is_published,
        "published_at": db_course.published_at.isoformat() if db_course.published_at else None,
        "source_course_id": db_course.source_course_id,
        "items": items_with_parsed_json
    }

@router.get("/courses/", response_model=List[CourseOut])
def list_courses(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Lists all available courses and aggregates completion progresses."""
    import json
    courses = db.query(models.Course).filter(models.Course.user_id == current_user.id).all()
    results = []
    for course in courses:
        completed = [i for i in course.items if i.is_completed]
        progress = (len(completed) / len(course.items) * 100) if course.items else 0
        
        # Parse JSON fields for items
        items_with_parsed_json = []
        for item in sorted(course.items, key=lambda x: x.order):
            item_dict = {
                "id": item.id,
                "session_id": item.session_id,
                "title": item.title,
                "chapter": item.chapter,
                "chapter_id": item.chapter_id,
                "description": item.description,
                "learning_objectives": json.loads(item.learning_objectives) if item.learning_objectives else [],
                "key_concepts": json.loads(item.key_concepts) if item.key_concepts else [],
                "order": item.order,
                "is_completed": item.is_completed,
                "content": item.content,
                "study_time": item.study_time
            }
            items_with_parsed_json.append(item_dict)

        results.append({
            "id": course.id,
            "title": course.title,
            "short_title": course.short_title,
            "description": course.description,
            "course_description": course.course_description,
            "level": course.level,
            "hours": course.hours,
            "total_estimated_hours": course.total_estimated_hours,
            "sessions": course.sessions,
            "target_user_summary": course.target_user_summary,
            "course_goal": course.course_goal,
            "learning_outcomes": json.loads(course.learning_outcomes) if course.learning_outcomes else [],
            "prerequisites": json.loads(course.prerequisites) if course.prerequisites else [],
            "progress": progress,
            "color": course.color or "purple",
            "cover_image": course.cover_image,
            "is_published": course.is_published,
            "published_at": course.published_at.isoformat() if course.published_at else None,
            "source_course_id": course.source_course_id,
            "items": items_with_parsed_json
        })
    return results

@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieves metadata and full syllabus details of a single course."""
    import json
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    completed = [i for i in course.items if i.is_completed]
    progress = (len(completed) / len(course.items) * 100) if course.items else 0
    
    # Parse JSON fields for items
    items_with_parsed_json = []
    for item in sorted(course.items, key=lambda x: x.order):
        item_dict = {
            "id": item.id,
            "session_id": item.session_id,
            "title": item.title,
            "chapter": item.chapter,
            "chapter_id": item.chapter_id,
            "description": item.description,
            "learning_objectives": json.loads(item.learning_objectives) if item.learning_objectives else [],
            "key_concepts": json.loads(item.key_concepts) if item.key_concepts else [],
            "order": item.order,
            "is_completed": item.is_completed,
            "content": item.content,
            "study_time": item.study_time
        }
        items_with_parsed_json.append(item_dict)
    
    return {
        "id": course.id,
        "title": course.title,
        "short_title": course.short_title,
        "description": course.description,
        "course_description": course.course_description,
        "level": course.level,
        "hours": course.hours,
        "total_estimated_hours": course.total_estimated_hours,
        "sessions": course.sessions,
        "target_user_summary": course.target_user_summary,
        "course_goal": course.course_goal,
        "learning_outcomes": json.loads(course.learning_outcomes) if course.learning_outcomes else [],
        "prerequisites": json.loads(course.prerequisites) if course.prerequisites else [],
        "progress": progress,
        "color": course.color or "purple",
        "cover_image": course.cover_image,
        "is_published": course.is_published,
        "published_at": course.published_at.isoformat() if course.published_at else None,
        "source_course_id": course.source_course_id,
        "items": items_with_parsed_json
    }

@router.patch("/courses/{course_id}")
def update_course(
    course_id: int,
    update_data: CourseUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Updates basic details (e.g. title, theme color) of an existing course."""
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
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

@router.post("/courses/{course_id}/cover")
async def upload_course_cover(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Saves custom cover images to static resources and updates course parameters."""
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
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

@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Deletes a course and all associated lessons/chats."""
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.query(models.OutlineItem).filter(models.OutlineItem.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    logger.log_info(f"Deleted course ID: {course_id}")
    return {"status": "success"}

@router.post("/courses/{course_id}/generate-micro")
def generate_random_micro(
    course_id: int,
    generate_cover: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Selects a random uncompleted session from a course and calls the agent to write its content."""
    logger.log_info(f"API Endpoint: Request to generate random micro-course for course {course_id} (generate_cover: {generate_cover})")
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    remaining_items = [i for i in course.items if not i.is_completed]
    if not remaining_items:
        raise HTTPException(status_code=400, detail="Course already completed")

    selected_item = random.choice(remaining_items)
    full_outline = [i.title for i in sorted(course.items, key=lambda x: x.order)]
    
    import json
    
    # Extract detailed outline
    detailed_outline = []
    for i in sorted(course.items, key=lambda x: x.order):
        try:
            lo = json.loads(i.learning_objectives) if i.learning_objectives else []
        except Exception:
            lo = []
        try:
            kc = json.loads(i.key_concepts) if i.key_concepts else []
        except Exception:
            kc = []
        detailed_outline.append({
            "title": i.title,
            "chapter": i.chapter,
            "description": i.description,
            "learning_objectives": lo,
            "key_concepts": kc
        })
        
    try:
        learning_outcomes = json.loads(course.learning_outcomes) if course.learning_outcomes else []
    except Exception:
        learning_outcomes = []
        
    try:
        prerequisites = json.loads(course.prerequisites) if course.prerequisites else []
    except Exception:
        prerequisites = []

    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    user_info = ""
    user_api_key = None
    user_content_model = None
    user_image_model = None
    user_image_api_key = None
    if user_settings:
        user_info = f"Name: {user_settings.name or 'N/A'}\nAge: {user_settings.age or 'N/A'}\nEducation: {user_settings.education or 'N/A'}\nExperience: {user_settings.background_experience or 'N/A'}\nAdditional Info: {user_settings.additional_info or 'N/A'}"
        user_api_key = user_settings.gemini_api_key
        user_content_model = user_settings.content_model
        user_image_model = user_settings.image_model
        user_image_api_key = user_settings.image_api_key

    # Generate content using dynamic agent service
    try:
        selected_lo = json.loads(selected_item.learning_objectives) if selected_item.learning_objectives else []
    except Exception:
        selected_lo = []
    try:
        selected_kc = json.loads(selected_item.key_concepts) if selected_item.key_concepts else []
    except Exception:
        selected_kc = []

    content = agent_service.get_content(
        subject=course.title,
        item_title=selected_item.title,
        course_description=course.description,
        full_outline=full_outline,
        user_info=user_info,
        course_level=course.level,
        course_goal=course.course_goal,
        learning_outcomes=learning_outcomes,
        prerequisites=prerequisites,
        target_user=course.target_user_summary,
        detailed_outline=detailed_outline,
        session_description=selected_item.description,
        session_learning_objectives=selected_lo,
        session_key_concepts=selected_kc,
        api_key=user_api_key,
        content_model=user_content_model
    )

    if generate_cover:
        logger.log_info(f"Requesting AI image generation for session cover: {selected_item.title}")
        try:
            context_text = f"This is a session titled '{selected_item.title}' in the course '{course.title}' which covers: {course.description or ''}"
            visual_prompt = agent_service.generate_prompt_for_image(selected_item.title, context_text, api_key=user_api_key, content_model=user_content_model)
            img_bytes = agent_service.generate_image_cover(visual_prompt, api_key=user_image_api_key or user_api_key, image_model=user_image_model)
            if img_bytes:
                os.makedirs("static/images/sessions", exist_ok=True)
                file_path = f"static/images/sessions/{selected_item.id}.jpg"
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                
                img_url = f"/assets/images/sessions/{selected_item.id}.jpg"
                content = f"![{selected_item.title}]({img_url})\n\n{content}"
                logger.log_success(f"Successfully generated and embedded session cover for session {selected_item.id}")
            else:
                logger.log_error("Could not generate AI session cover (image bytes empty)")
        except Exception as img_err:
            logger.log_error(f"Error generating AI session cover: {str(img_err)}")

    selected_item.content = content
    db.commit()
    db.refresh(selected_item)
    return selected_item
