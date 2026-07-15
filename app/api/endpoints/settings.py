from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, database
from app.schemas import SettingsSchema
from app.api.endpoints.auth import get_current_user

router = APIRouter()

DEFAULTS = {
    "content_model":        "gemini-flash-latest",
    "coach_model":          "gemini-flash-latest",
    "knowledge_model":      "gemini-flash-lite-latest",
    "image_model":          "gemini-2.5-flash-image",
    "auto_generate_covers": False,
}


def _get_or_create_settings(db: Session, user: models.User) -> models.UserSettings:
    us = db.query(models.UserSettings).filter(models.UserSettings.user_id == user.id).first()
    if not us:
        us = models.UserSettings(user_id=user.id, name=user.username)
        db.add(us)
        db.commit()
        db.refresh(us)
    return us


@router.get("/settings/api-key-status")
def api_key_status(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Returns whether the current user has a Gemini API key configured."""
    us = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    has_key = bool(us and us.gemini_api_key and us.gemini_api_key.strip())
    return {"has_api_key": has_key}


@router.get("/settings")
def get_settings(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Returns all per-user settings from DB (never from .env)."""
    us = _get_or_create_settings(db, current_user)
    return {
        "google_api_key":        us.gemini_api_key or "",
        "image_api_key":         us.image_api_key or "",
        "content_model":         us.content_model   or DEFAULTS["content_model"],
        "coach_model":           us.coach_model     or DEFAULTS["coach_model"],
        "knowledge_model":       us.knowledge_model or DEFAULTS["knowledge_model"],
        "image_model":           us.image_model     or DEFAULTS["image_model"],
        "auto_generate_covers":  us.auto_generate_covers if us.auto_generate_covers is not None else DEFAULTS["auto_generate_covers"],
        "name":                  us.name or "",
        "age":                   us.age or "",
        "education":             us.education or "",
        "background_experience": us.background_experience or "",
        "additional_info":       us.additional_info or "",
    }


@router.post("/settings")
def update_settings(
    settings_data: SettingsSchema,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Saves all settings per-user in DB. Nothing is written to .env."""
    us = _get_or_create_settings(db, current_user)

    user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not user_profile:
        user_profile = models.UserProfile(user_id=current_user.id)
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)
        db.add(models.CognitiveProfile(user_id=user_profile.id))

    if settings_data.google_api_key is not None:
        us.gemini_api_key = settings_data.google_api_key
    if settings_data.image_api_key is not None:
        us.image_api_key = settings_data.image_api_key
    if settings_data.content_model is not None:
        us.content_model = settings_data.content_model
    if settings_data.coach_model is not None:
        us.coach_model = settings_data.coach_model
    if settings_data.knowledge_model is not None:
        us.knowledge_model = settings_data.knowledge_model
    if settings_data.image_model is not None:
        us.image_model = settings_data.image_model
    if settings_data.auto_generate_covers is not None:
        us.auto_generate_covers = settings_data.auto_generate_covers
    if settings_data.name is not None:
        us.name = settings_data.name
        user_profile.name = settings_data.name
    if settings_data.age is not None:
        us.age = settings_data.age
        user_profile.age = settings_data.age
    if settings_data.education is not None:
        us.education = settings_data.education
        user_profile.education_level = settings_data.education
    if settings_data.background_experience is not None:
        us.background_experience = settings_data.background_experience
        user_profile.background_experience = settings_data.background_experience
    if settings_data.additional_info is not None:
        us.additional_info = settings_data.additional_info
        user_profile.additional_info = settings_data.additional_info

    db.commit()
    return {"status": "success"}
