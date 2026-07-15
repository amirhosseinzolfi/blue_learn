import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(override=True)

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./backend/learning_app.db")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
