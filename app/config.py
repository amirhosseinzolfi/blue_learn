import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Centralized configuration management for the Blue Learn backend.
    Uses pydantic-settings to bind env vars, with dynamic loading capabilities.
    """
    google_api_key: str = ""
    generator_model_name: str = "gemini-flash-latest"
    main_model_name: str = "gemini-flash-latest"
    coach_model_name: str = "gemini-flash-lite-latest"
    database_url: str = "sqlite:///./backend/learning_app.db"
    
    class Config:
        env_file = ".env"
        extra = "allow"

    @classmethod
    def load_dynamic_settings(cls):
        """Loads and returns fresh settings from the environment, ensuring .env updates are reflected."""
        load_dotenv(override=True)
        return cls(
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            generator_model_name=os.getenv("GENERATOR_MODEL_NAME", "gemini-flash-latest"),
            main_model_name=os.getenv("MAIN_MODEL_NAME", "gemini-flash-latest"),
            coach_model_name=os.getenv("COACH_MODEL_NAME", "gemini-flash-lite-latest"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./backend/learning_app.db")
        )

# Instantiate the global settings
settings = Settings.load_dynamic_settings()
