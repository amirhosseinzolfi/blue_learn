import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv, set_key

from app import models, database
from app.schemas import SettingsSchema
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/settings")
def get_settings(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieves current application settings from .env configurations and user_settings table."""
    load_dotenv(override=True)
    env_settings = {
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        "model_name": os.getenv("GENERATOR_MODEL_NAME", "gemini-flash-latest"),
        "google_image_api_key": os.getenv("GOOGLE_IMAGE_API_KEY", ""),
        "image_model_name": os.getenv("IMAGE_MODEL_NAME", "gemini-2.5-flash-image"),
        "auto_generate_session_covers": os.getenv("AUTO_GENERATE_SESSION_COVERS", "false").lower() == "true"
    }
    
    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    if not user_settings:
        user_settings = models.UserSettings(user_id=current_user.id, name=current_user.username)
        db.add(user_settings)
        db.commit()
        db.refresh(user_settings)
        
    return {
        **env_settings,
        "name": user_settings.name or "",
        "age": user_settings.age or "",
        "education": user_settings.education or "",
        "background_experience": user_settings.background_experience or "",
        "additional_info": user_settings.additional_info or ""
    }

@router.post("/settings")
def update_settings(
    settings_data: SettingsSchema,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Saves updated parameters to both local .env files and user settings tables."""
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            pass
    
    if settings_data.google_api_key is not None:
        set_key(env_file, "GOOGLE_API_KEY", settings_data.google_api_key)
    if settings_data.model_name is not None:
        set_key(env_file, "GENERATOR_MODEL_NAME", settings_data.model_name)
        set_key(env_file, "MAIN_MODEL_NAME", settings_data.model_name)
        set_key(env_file, "COACH_MODEL_NAME", settings_data.model_name)
    if settings_data.google_image_api_key is not None:
        set_key(env_file, "GOOGLE_IMAGE_API_KEY", settings_data.google_image_api_key)
    if settings_data.image_model_name is not None:
        set_key(env_file, "IMAGE_MODEL_NAME", settings_data.image_model_name)
    if settings_data.auto_generate_session_covers is not None:
        val_str = "true" if settings_data.auto_generate_session_covers else "false"
        set_key(env_file, "AUTO_GENERATE_SESSION_COVERS", val_str)
        
    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    if not user_settings:
        user_settings = models.UserSettings(user_id=current_user.id)
        db.add(user_settings)
        
    user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not user_profile:
        user_profile = models.UserProfile(user_id=current_user.id)
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)
        
        cog_profile = models.CognitiveProfile(user_id=user_profile.id)
        db.add(cog_profile)
        
    if settings_data.name is not None:
        user_settings.name = settings_data.name
        user_profile.name = settings_data.name
    if settings_data.age is not None:
        user_settings.age = settings_data.age
        user_profile.age = settings_data.age
    if settings_data.education is not None:
        user_settings.education = settings_data.education
        user_profile.education_level = settings_data.education
    if settings_data.background_experience is not None:
        user_settings.background_experience = settings_data.background_experience
        user_profile.background_experience = settings_data.background_experience
    if settings_data.additional_info is not None:
        user_settings.additional_info = settings_data.additional_info
        user_profile.additional_info = settings_data.additional_info
    if settings_data.google_api_key is not None:
        user_settings.gemini_api_key = settings_data.google_api_key
    if settings_data.model_name is not None:
        user_settings.gemini_model = settings_data.model_name
        
    db.commit()
    return {"status": "success"}
