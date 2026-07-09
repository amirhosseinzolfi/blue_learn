import os
import hashlib
import secrets
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.logger import logger

def hash_password(password: str) -> str:
    """Securely hash a password using standard PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hashed value securely."""
    try:
        parts = hashed.split('$')
        if len(parts) != 2:
            return False
        salt, key_hex = parts[0], parts[1]
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

# SQLite Connection Configuration
# We allow checking the same thread since SQLite is local and FastAPI runs multi-threaded.
engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency yield database sessions securely, cleaning up connections upon completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations():
    """
    Executes raw schema upgrades and ensures newer columns exist in the SQLite database.
    This acts as a lightweight, robust migration manager since Alembic is not used.
    """
    logger.log_info("Running database migrations...")
    try:
        with engine.connect() as conn:
            # 1. Create tables if they do not exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR UNIQUE,
                    password_hash VARCHAR
                )
            """))

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
            
            # 2. Add dynamic columns if tables were created with older versions
            # User Profiles Columns
            for col in ["name", "age", "education_level", "background_experience", "primary_goals", "additional_info", "created_at"]:
                try:
                    conn.execute(text(f"ALTER TABLE user_profiles ADD COLUMN {col} VARCHAR"))
                    conn.commit()
                except Exception:
                    pass

            # Cognitive Profile Columns
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

            # Course Columns
            course_columns = [
                ("short_title", "VARCHAR"),
                ("description", "VARCHAR"),
                ("level", "VARCHAR"),
                ("hours", "INTEGER"),
                ("sessions", "INTEGER"),
                ("chat_summary", "TEXT"),
                ("color", "VARCHAR"),
                ("cover_image", "VARCHAR"),
                ("is_published", "BOOLEAN DEFAULT 0"),
                ("published_at", "DATETIME"),
                ("source_course_id", "INTEGER")
            ]
            for col_name, col_type in course_columns:
                try:
                    conn.execute(text(f"ALTER TABLE courses ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.log_success(f"Added {col_name} column to courses table")
                except Exception:
                    pass

            # Create course_enrollments table if not exists — tracks global enrollments
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS course_enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    source_course_id INTEGER,
                    cloned_course_id INTEGER,
                    enrolled_at VARCHAR
                )
            """))
            try:
                conn.execute(text("CREATE INDEX ix_course_enrollments_user_id ON course_enrollments (user_id)"))
                conn.execute(text("CREATE INDEX ix_course_enrollments_source_course_id ON course_enrollments (source_course_id)"))
                conn.commit()
            except Exception:
                pass

            # Create course_ratings table if not exists — user star ratings on global courses
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS course_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    course_id INTEGER,
                    rating INTEGER,
                    created_at VARCHAR
                )
            """))
            try:
                conn.execute(text("CREATE INDEX ix_course_ratings_user_id ON course_ratings (user_id)"))
                conn.execute(text("CREATE INDEX ix_course_ratings_course_id ON course_ratings (course_id)"))
                conn.commit()
            except Exception:
                pass

            # Outline Items Columns
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

            # Create daily_activity table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS daily_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date VARCHAR(255),
                    study_time INTEGER DEFAULT 0
                )
            """))
            try:
                conn.execute(text("CREATE INDEX ix_daily_activity_date ON daily_activity (date)"))
                conn.commit()
            except Exception:
                pass

            # Create knowledge_insights table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    created_at VARCHAR(255)
                )
            """))

            # Create user_settings table if not exists
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

            # Add user_id column dynamically to user-specific tables if they do not exist
            for table in ["user_profiles", "user_settings", "courses", "daily_activity", "knowledge_insights"]:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER"))
                    conn.commit()
                except Exception:
                    pass

            # Seed default user amir and assign existing orphaned records to him
            res = conn.execute(text("SELECT id FROM users WHERE username = 'amir'")).fetchone()
            if not res:
                hashed = hash_password("amir")
                # Try to insert amir with ID 1 so he maps to existing profiles
                id_check = conn.execute(text("SELECT id FROM users WHERE id = 1")).fetchone()
                if not id_check:
                    conn.execute(text("INSERT INTO users (id, username, password_hash) VALUES (1, 'amir', :pwd)"), {"pwd": hashed})
                else:
                    conn.execute(text("INSERT INTO users (username, password_hash) VALUES ('amir', :pwd)"), {"pwd": hashed})
                conn.commit()
                logger.log_success("Created default user amir (pass: amir)")
                
                # Assign all existing records (where user_id is null) to amir
                for table in ["user_profiles", "user_settings", "courses", "daily_activity", "knowledge_insights"]:
                    try:
                        conn.execute(text(f"UPDATE {table} SET user_id = 1 WHERE user_id IS NULL"))
                        conn.commit()
                        logger.log_success(f"Assigned existing records in {table} to user amir (ID 1)")
                    except Exception as err:
                        logger.log_error(f"Failed to assign records in {table}: {str(err)}")

            conn.commit()
        logger.log_success("Database migrations complete")
    except Exception as e:
        logger.log_error(f"Migration processing error: {str(e)}")
