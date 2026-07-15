import random
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app import models, database
from app.logger import logger
from app.schemas import StudyTimeUpdate
from app.services import agent_service
from app.services.profile_service import run_profiling_background_task
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.post("/items/{item_id}/complete")
def complete_item(
    item_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Marks a syllabus lesson as completed and schedules cognitive profiling updates."""
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item or not item.course or item.course.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_completed = True
    item.completed_at = datetime.now().isoformat()
    
    # Log learning event and trigger AI dynamic profiler
    user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if user_profile:
        event = models.LearningEventLog(
            user_id=user_profile.id,
            event_type="session_complete",
            course_title=item.course.title if item.course else "Unknown",
            session_title=item.title,
            study_duration_seconds=item.study_time
        )
        db.add(event)
        
        # Dispatch asynchronous profiler updates
        background_tasks.add_task(run_profiling_background_task, current_user.id)
        
    db.commit()
    logger.log_success(f"Item {item_id} marked as complete and profiler triggered")
    return {"status": "success"}

@router.post("/items/{item_id}/study-time")
def update_study_time(
    item_id: int,
    data: StudyTimeUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Adds a duration delta in seconds to outline items and daily tracker aggregates."""
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item or not item.course or item.course.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    item.study_time += data.seconds

    # Update Daily activity heatmap record
    today = date.today().isoformat()
    daily = db.query(models.DailyActivity).filter(
        models.DailyActivity.user_id == current_user.id,
        models.DailyActivity.date == today
    ).first()
    if not daily:
        daily = models.DailyActivity(user_id=current_user.id, date=today, study_time=data.seconds)
        db.add(daily)
    else:
        daily.study_time += data.seconds

    db.commit()
    return {"status": "success", "total_study_time": item.study_time}

@router.post("/items/{item_id}/set-study-time")
def set_study_time(
    item_id: int,
    data: StudyTimeUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Directly sets absolute study times and increments daily differences."""
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item or not item.course or item.course.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    diff = data.seconds - item.study_time
    item.study_time = data.seconds

    # Update Daily activity aggregates with the difference
    today = date.today().isoformat()
    daily = db.query(models.DailyActivity).filter(
        models.DailyActivity.user_id == current_user.id,
        models.DailyActivity.date == today
    ).first()
    if not daily:
        daily = models.DailyActivity(user_id=current_user.id, date=today, study_time=max(0, diff))
        db.add(daily)
    else:
        daily.study_time = max(0, daily.study_time + diff)

    db.commit()
    return {"status": "success", "total_study_time": item.study_time}
@router.post("/items/{item_id}/generate")
def generate_specific_micro(
    item_id: int,
    generate_cover: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Instructs the dynamic content agent to write detailed lesson text for a specific outline item."""
    logger.log_info(f"API Endpoint: Request to generate specific micro-course for item {item_id} (generate_cover: {generate_cover})")
    item = db.query(models.OutlineItem).filter(models.OutlineItem.id == item_id).first()
    if not item or not item.course or item.course.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    import json

    course = item.course
    full_outline = [i.title for i in sorted(course.items, key=lambda x: x.order)]
    
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

    try:
        item_lo = json.loads(item.learning_objectives) if item.learning_objectives else []
    except Exception:
        item_lo = []
    try:
        item_kc = json.loads(item.key_concepts) if item.key_concepts else []
    except Exception:
        item_kc = []

    content = agent_service.get_content(
        subject=course.title,
        item_title=item.title,
        course_description=course.description,
        full_outline=full_outline,
        user_info=user_info,
        course_level=course.level,
        course_goal=course.course_goal,
        learning_outcomes=learning_outcomes,
        prerequisites=prerequisites,
        target_user=course.target_user_summary,
        detailed_outline=detailed_outline,
        session_description=item.description,
        session_learning_objectives=item_lo,
        session_key_concepts=item_kc,
        api_key=user_api_key,
        content_model=user_content_model
    )

    if generate_cover:
        logger.log_info(f"Requesting AI image generation for session cover: {item.title}")
        try:
            import os
            context_text = f"This is a session titled '{item.title}' in the course '{course.title}' which covers: {course.description or ''}"
            visual_prompt = agent_service.generate_prompt_for_image(item.title, context_text, api_key=user_api_key, content_model=user_content_model)
            img_bytes = agent_service.generate_image_cover(visual_prompt, api_key=user_image_api_key or user_api_key, image_model=user_image_model)
            if img_bytes:
                os.makedirs("static/images/sessions", exist_ok=True)
                file_path = f"static/images/sessions/{item.id}.jpg"
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                
                img_url = f"/assets/images/sessions/{item.id}.jpg"
                content = f"![{item.title}]({img_url})\n\n{content}"
                logger.log_success(f"Successfully generated and embedded session cover for session {item.id}")
            else:
                logger.log_error("Could not generate AI session cover (image bytes empty)")
        except Exception as img_err:
            logger.log_error(f"Error generating AI session cover: {str(img_err)}")

    item.content = content
    db.commit()
    db.refresh(item)
    return item
@router.get("/daily-micro-courses")
def get_daily_micro_courses(
    course_ids: Optional[str] = None,
    count: int = 1,
    exclude_ids: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Selects a set of suggested uncompleted sessions.
    Uses daily ordinal seeding so recommendations remain consistent for the user throughout the day.
    """
    courses_query = db.query(models.Course).filter(models.Course.user_id == current_user.id)
    if course_ids:
        ids = [int(cid) for cid in course_ids.split(',') if cid.strip().isdigit()]
        if ids:
            courses_query = courses_query.filter(models.Course.id.in_(ids))
    courses = courses_query.all()
    
    excluded = set()
    if exclude_ids:
        excluded = {int(eid) for eid in exclude_ids.split(',') if eid.strip().isdigit()}
    
    daily_items = []
    
    # Establish ordinal day seed for stability
    seed = date.today().toordinal()
    rng = random.Random(seed)
    
    for course in courses:
        items = list(course.items)
        rng.shuffle(items)
        
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
