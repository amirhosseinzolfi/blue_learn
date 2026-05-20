import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    short_title = Column(String, nullable=True)
    description = Column(String)
    level = Column(String, nullable=True)
    hours = Column(Integer, nullable=True)
    sessions = Column(Integer, nullable=True)
    chat_summary = Column(Text, nullable=True)
    color = Column(String, nullable=True, default="purple")
    cover_image = Column(String, nullable=True)

    items = relationship("OutlineItem", back_populates="course", cascade="all, delete-orphan")
    chat_messages = relationship("CourseChatMessage", back_populates="course", cascade="all, delete-orphan", order_by="CourseChatMessage.id")

class CourseChatMessage(Base):
    __tablename__ = "course_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    role = Column(String)
    content = Column(Text)
    is_summarized = Column(Boolean, default=False)

    course = relationship("Course", back_populates="chat_messages")

class OutlineItem(Base):
    __tablename__ = "outline_items"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    chapter = Column(String, nullable=True)
    title = Column(String)
    order = Column(Integer)
    is_completed = Column(Boolean, default=False)
    content = Column(Text, nullable=True)
    study_time = Column(Integer, default=0) # in seconds
    completed_at = Column(String, nullable=True) # ISO format string

    course = relationship("Course", back_populates="items")

class DailyActivity(Base):
    __tablename__ = "daily_activity"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True) # YYYY-MM-DD
    study_time = Column(Integer, default=0) # in seconds

class KnowledgeInsight(Base):
    __tablename__ = "knowledge_insights"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(String) # For simplicity using string, but could be DateTime

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    age = Column(String, nullable=True)
    education = Column(String, nullable=True)
    background_experience = Column(Text, nullable=True)
    additional_info = Column(Text, nullable=True)
    gemini_api_key = Column(String, nullable=True)
    gemini_model = Column(String, nullable=True)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    age = Column(String, nullable=True)
    education_level = Column(String, nullable=True)
    background_experience = Column(Text, nullable=True)
    primary_goals = Column(Text, nullable=True)
    additional_info = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    cognitive_profile = relationship("CognitiveProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    knowledge_nodes = relationship("KnowledgeNode", back_populates="user", cascade="all, delete-orphan")
    learning_events = relationship("LearningEventLog", back_populates="user", cascade="all, delete-orphan")

class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True)
    
    global_learning_velocity = Column(Float, default=1.0)
    attention_span_minutes = Column(Integer, default=25)
    retention_index = Column(Float, default=0.8)
    
    cognitive_data_json = Column(Text, default='{}') 
    interests_json = Column(Text, default='[]')
    recommended_topics_json = Column(Text, default='[]')
    learning_style_summary = Column(Text, nullable=True)
    strength_areas_json = Column(Text, default='[]')
    personality_summary = Column(Text, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("UserProfile", back_populates="cognitive_profile")

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    
    concept = Column(String, index=True)
    category = Column(String, index=True)
    
    mastery_score = Column(Float, default=0.0) 
    confidence_level = Column(Float, default=0.5) 
    
    dependencies_json = Column(Text, default='{}')
    
    first_encountered = Column(DateTime, default=datetime.datetime.utcnow)
    last_tested = Column(DateTime, nullable=True)

    user = relationship("UserProfile", back_populates="knowledge_nodes")

class LearningEventLog(Base):
    __tablename__ = "learning_event_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    
    event_type = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    course_title = Column(String, nullable=True)
    session_title = Column(String, nullable=True)
    study_duration_seconds = Column(Integer, default=0)
    
    raw_interaction_text = Column(Text, nullable=True)
    vector_embedding_json = Column(Text, nullable=True) 

    user = relationship("UserProfile", back_populates="learning_events")
