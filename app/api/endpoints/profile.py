import json
import sqlalchemy
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, database
from app.logger import logger
from app.services import agent_service, profile_service
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/stats")
def get_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves global user analytics:
    - Overall course completion numbers and durations.
    - Last 20 completed sessions.
    - 365-day learning heatmap activity dataset.
    - Static user bio details and dynamic cognitive velocity/retention coefficients.
    - Full conceptual mastery node records.
    """
    total_courses = db.query(models.Course).filter(models.Course.user_id == current_user.id).count()
    completed_items = db.query(models.OutlineItem).join(models.Course).filter(
        models.Course.user_id == current_user.id,
        models.OutlineItem.is_completed == True
    ).all()

    total_sessions = db.query(models.OutlineItem).join(models.Course).filter(
        models.Course.user_id == current_user.id
    ).count()
    total_completed_sessions = len(completed_items)

    total_study_time = db.query(sqlalchemy.func.sum(models.OutlineItem.study_time)).join(models.Course).filter(
        models.Course.user_id == current_user.id
    ).scalar() or 0

    # Calculate completed courses
    all_courses = db.query(models.Course).filter(models.Course.user_id == current_user.id).all()
    completed_courses_count = 0
    for course in all_courses:
        if course.items and all(item.is_completed for item in course.items):
            completed_courses_count += 1

    # Recent completed sessions
    recent_completed = []
    sorted_completed = sorted(completed_items, key=lambda x: (x.completed_at or '', x.id))
    for item in sorted_completed[-20:]:  # Last 20
        recent_completed.append({
            "id": item.id,
            "title": item.title,
            "course_id": item.course_id,
            "course_title": item.course.title if item.course else "Unknown",
            "study_time": item.study_time,
            "completed_at": item.completed_at
        })

    # Activity Heatmap Data (Last 365 days)
    start_date = (date.today() - timedelta(days=364)).isoformat()
    daily_activities = db.query(models.DailyActivity).filter(
        models.DailyActivity.user_id == current_user.id,
        models.DailyActivity.date >= start_date
    ).all()
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
        
        activity_data.append({
            "date": d,
            "minutes": study_time // 60,
            "completed_sessions": sessions
        })

    # Fetch Cognitive Profile Data
    user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
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
        
        # Fetch knowledge nodes grid sorted descending by mastery score
        nodes = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id).order_by(models.KnowledgeNode.mastery_score.desc()).all()
        for n in nodes:
            prereqs = []
            difficulty_level = "مقدماتی"
            key_terms = []
            if n.dependencies_json:
                try:
                    dep_data = json.loads(n.dependencies_json)
                    if isinstance(dep_data, dict):
                        prereqs = dep_data.get("prerequisites", [])
                        difficulty_level = dep_data.get("difficulty_level", "مقدماتی")
                        key_terms = dep_data.get("key_terms", [])
                except Exception:
                    pass
            knowledge_nodes.append({
                "concept": n.concept,
                "category": n.category,
                "mastery_score": n.mastery_score,
                "confidence_level": n.confidence_level,
                "prerequisites": prereqs,
                "difficulty_level": difficulty_level,
                "key_terms": key_terms
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

@router.post("/profile/rebuild")
def rebuild_profile(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Triggers the full, historical double-loop cognitive rebuild service."""
    try:
        result = profile_service.rebuild_user_cognitive_profile(db, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-insight")
def generate_insight(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Analyzes completed lessons and inserts a fresh reflection insight (Farsi) into database."""
    completed_items = db.query(models.OutlineItem).join(models.Course).filter(
        models.Course.user_id == current_user.id,
        models.OutlineItem.is_completed == True
    ).all()

    completed_sessions_data = [
        {"course_title": item.course.title if item.course else "Unknown", "item_title": item.title}
        for item in completed_items
    ]

    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    user_api_key = user_settings.gemini_api_key if user_settings else None
    user_content_model = user_settings.content_model if user_settings else None

    insight_content = agent_service.generate_knowledge_insight(completed_sessions_data, api_key=user_api_key, content_model=user_content_model)

    new_insight = models.KnowledgeInsight(
        user_id=current_user.id,
        content=insight_content,
        created_at=datetime.now().isoformat()
    )
    db.add(new_insight)
    db.commit()
    db.refresh(new_insight)
    return new_insight

@router.get("/insights")
def get_insights(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieves all past reflective insights logged in descending order."""
    insights = db.query(models.KnowledgeInsight).filter(
        models.KnowledgeInsight.user_id == current_user.id
    ).order_by(models.KnowledgeInsight.id.desc()).all()
    return insights
