from pydantic import BaseModel, Field
from typing import List, Optional

# ==========================================
# 1. AI AGENTS & STRUCTURED OUTPUT SCHEMAS
# ==========================================

class OutlineItemSchema(BaseModel):
    """Syllabus session detail."""
    session_id: str = Field(description="Unique identifier for the session, e.g., s_1, s_2")
    title: str = Field(description="Title of the micro-course session")
    description: str = Field(description="Brief description of what will be covered in this session")
    learning_objectives: List[str] = Field(description="List of specific learning objectives for this session")
    key_concepts: List[str] = Field(description="List of key concepts covered in this session")

class OutlineChapterSchema(BaseModel):
    """Syllabus chapter mapping multiple sessions."""
    chapter_id: str = Field(description="Unique identifier for the chapter, e.g., ch_1, ch_2")
    title: str = Field(description="Title of the main chapter")
    description: str = Field(description="Brief description of the chapter")
    sessions: List[OutlineItemSchema] = Field(description="Sessions within this chapter")

class CourseOutlineSchema(BaseModel):
    """Full course chapter mapping."""
    items: List[OutlineChapterSchema]

class CourseGenerationSchema(BaseModel):
    """Full details of a newly generated AI course curriculum."""
    title: str = Field(description="Full course title")
    short_title: str = Field(description="Most efficient proper short title for the course in 3 upto 6 words")
    level: str = Field(description="Level of the course, e.g., beginner, intermediate, advanced, beginner_to_intermediate")
    total_estimated_hours: int = Field(description="Total estimated hours to complete the course")
    target_user_summary: str = Field(description="Brief summary of the target user for this course")
    course_goal: str = Field(description="Main goal or outcome of the course")
    course_description: str = Field(description="Detailed course description explaining what will be taught")
    learning_outcomes: List[str] = Field(description="List of key learning outcomes students will achieve")
    prerequisites: List[str] = Field(description="List of prerequisites needed before taking this course")
    chapters: List[OutlineChapterSchema] = Field(description="Detailed list of chapters and their sessions")

class ChatAgentResponse(BaseModel):
    """Dynamic output determining chat diagnostic loop status."""
    is_complete: bool = Field(description="Set to true if you have gathered enough information to generate the course. False if you still need to ask the user questions.")
    chat_response: Optional[str] = Field(description="If is_complete is false, this is the question you ask the user. If is_complete is true, this can be empty.")
    course_data: Optional[CourseGenerationSchema] = Field(description="If is_complete is true, this contains the full generated course data.")
    conversation_summary: Optional[str] = None
    profile: Optional[dict] = None

class KnowledgeNodeUpdateSchema(BaseModel):
    """Representing updates to individual concepts inside user's master graph."""
    concept: str = Field(description="Name of the concept, e.g., SQL Joins")
    category: str = Field(description="Category of the concept")
    mastery_score_delta: float = Field(description="Mastery score of the concept from 0.0 to 1.0. Start very low for newly studied concepts (e.g. 0.05 - 0.20). Maximum is 0.98.")
    confidence_score: float = Field(description="Confidence of AI in this evaluation from 0.0 to 1.0")
    prerequisites: Optional[List[str]] = Field(default=[], description="List of direct prerequisite concepts (exact names of other concepts) for this concept")
    difficulty_level: str = Field(default="مقدماتی", description="Difficulty level in Persian: choose strictly from: مقدماتی (Beginner), متوسط (Intermediate), پیشرفته (Advanced)")
    key_terms: List[str] = Field(default=[], description="List of 3-5 specific technical terms or subconcepts in Persian related to this domain")

class ProfilerUpdateSchema(BaseModel):
    """Detailed structural response returned by the Cognitive Profiler Agent."""
    global_learning_velocity: float = Field(description="Speed coefficient from 0.5 to 2.0")
    attention_span_minutes: int = Field(description="Adjusted average session time")
    retention_index: float = Field(description="Memory decay indicator from 0.0 to 1.0")
    ls_hands_on: float = Field(default=0.0, description="Learning style ratio for hands_on")
    ls_visual: float = Field(default=0.0, description="Learning style ratio for visual")
    ls_theoretical: float = Field(default=0.0, description="Learning style ratio for theoretical")
    ls_self_directed: float = Field(default=0.0, description="Learning style ratio for self_directed")
    pt_persistence: str = Field(default="", description="Personality trait persistence")
    pt_patience: str = Field(default="", description="Personality trait patience_with_errors")
    pt_curiosity: str = Field(default="", description="Personality trait learning_curiosity")
    pt_session_length: str = Field(default="", description="Personality trait preferred_session_length")
    learning_style_summary: str = Field(default="", description="Persian narrative of how the user learns best")
    personality_summary: str = Field(default="", description="Persian narrative of the user's learner personality")
    strength_areas: List[str] = Field(default=[], description="Persian list of top subject domains")
    new_interests: List[str] = Field(default=[], description="Persian list of newly discovered interests")
    recommended_topics: List[str] = Field(default=[], description="Persian list of recommended next topics")
    updated_knowledge_nodes: List[KnowledgeNodeUpdateSchema] = Field(description="Updates to the knowledge graph")


class IncrementalKnowledgeNodeSchema(BaseModel):
    """Representing an incremental addition or refinement to a concept node."""
    concept: str = Field(description="Name of the concept in Persian, e.g., برنامه‌نویسی پایتون")
    category: str = Field(description="Category of the concept in Persian")
    action: str = Field(description="Action to take: 'add' (if completely new concept) or 'refine' (if incrementing mastery/confidence)")
    mastery_score_delta: float = Field(default=0.0, description="Increment/change in mastery score (e.g., +0.02 to +0.10 based on study duration, strictly progressive)")
    confidence_score: float = Field(default=0.7, description="AI confidence score from 0.0 to 1.0")
    prerequisites: Optional[List[str]] = Field(default=[], description="List of direct prerequisite concept names (if any) for this concept")
    difficulty_level: str = Field(default="مقدماتی", description="Difficulty level in Persian: choose strictly from: مقدماتی (Beginner), متوسط (Intermediate), پیشرفته (Advanced)")
    key_terms: List[str] = Field(default=[], description="List of 3-5 specific technical terms or subconcepts in Persian related to this domain")


class IncrementalProfilerUpdateSchema(BaseModel):
    """Sleek, lightweight schema returned by the Incremental Profiler Agent for delta updates."""
    should_update_cognitive_profile: bool = Field(description="Set to true if cognitive metrics or summaries need refinement based on this event. False otherwise.")
    global_learning_velocity: Optional[float] = Field(default=None, description="New speed coefficient from 0.5 to 2.0 (if changed)")
    attention_span_minutes: Optional[int] = Field(default=None, description="New average session time in minutes (if changed)")
    retention_index: Optional[float] = Field(default=None, description="New retention index from 0.0 to 1.0 (if changed)")
    learning_style_summary_update: Optional[str] = Field(default=None, description="Refinement or addition to the Persian learning style description (if needed)")
    personality_summary_update: Optional[str] = Field(default=None, description="Refinement or addition to the Persian personality summary (if needed)")
    new_strength_areas: Optional[List[str]] = Field(default=[], description="New subject domains to append to user's strengths (Persian)")
    new_interests: Optional[List[str]] = Field(default=[], description="New interests to append to user's interests list (Persian)")
    new_recommended_topics: Optional[List[str]] = Field(default=[], description="New next topics to recommend (Persian)")
    updated_knowledge_nodes: List[IncrementalKnowledgeNodeSchema] = Field(default=[], description="List of concept additions or increments based on this learning event")



# ==========================================
# 2. HTTP ENDPOINTS INPUTS / OUTPUTS
# ==========================================

class SettingsSchema(BaseModel):
    """API payload for updating local client settings."""
    # API keys
    google_api_key: Optional[str] = None
    image_api_key: Optional[str] = None
    # Per-user model names
    content_model: Optional[str] = None
    coach_model: Optional[str] = None
    knowledge_model: Optional[str] = None
    image_model: Optional[str] = None
    # Feature flags
    auto_generate_covers: Optional[bool] = None
    # Profile fields
    name: Optional[str] = None
    age: Optional[str] = None
    education: Optional[str] = None
    background_experience: Optional[str] = None
    additional_info: Optional[str] = None

class OutlineItemCreate(BaseModel):
    """Syllabus item creation schema."""
    session_id: str
    title: str
    description: str
    learning_objectives: List[str]
    key_concepts: List[str]

class OutlineChapterCreate(BaseModel):
    """Syllabus chapter creation schema."""
    chapter_id: str
    title: str
    description: str
    sessions: List[OutlineItemCreate]

class CourseCreate(BaseModel):
    """API payload for manually inserting a dynamic course."""
    title: str
    short_title: str
    level: str
    total_estimated_hours: int
    target_user_summary: str
    course_goal: str
    course_description: str
    learning_outcomes: List[str]
    prerequisites: List[str]
    chapters: List[OutlineChapterCreate]
    generate_cover: Optional[bool] = False

class ChatMessage(BaseModel):
    """Single chat message format."""
    role: str
    content: Optional[str] = None
    images: Optional[List[str]] = None
    audio: Optional[List[str]] = None

class ChatRequest(BaseModel):
    """API payload for requesting a diagnostic course generation dialogue turn."""
    messages: List[ChatMessage]
    level: Optional[str] = None
    duration_sessions: Optional[int] = None
    learning_style: Optional[str] = None
    conversation_summary: Optional[str] = None
    profile: Optional[dict] = None

class CoachChatRequest(BaseModel):
    """API payload for posting coach session questions."""
    message: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    course_id: int
    item_id: int

class ChatHistoryResponse(BaseModel):
    """API payload returning single chat history message."""
    role: str
    content: str

class OutlineItemOut(BaseModel):
    """API serialization schema for OutlineItem."""
    id: int
    session_id: Optional[str] = None
    title: str
    chapter: Optional[str] = None
    chapter_id: Optional[str] = None
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    key_concepts: Optional[List[str]] = None
    is_completed: bool
    content: Optional[str] = None
    study_time: int = 0

    class Config:
        from_attributes = True

class CourseOut(BaseModel):
    """API serialization schema for Course details."""
    id: int
    title: str
    short_title: Optional[str] = None
    description: Optional[str] = None
    course_description: Optional[str] = None
    level: Optional[str] = None
    hours: Optional[int] = None
    total_estimated_hours: Optional[int] = None
    sessions: Optional[int] = None
    target_user_summary: Optional[str] = None
    course_goal: Optional[str] = None
    learning_outcomes: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    progress: float
    color: Optional[str] = "purple"
    cover_image: Optional[str] = None
    is_published: bool = False
    published_at: Optional[str] = None
    source_course_id: Optional[int] = None
    items: List[OutlineItemOut]

    class Config:
        from_attributes = True


class GlobalCourseOut(BaseModel):
    """Lightweight card data for the shared Global Courses catalog."""
    id: int
    title: str
    short_title: Optional[str] = None
    description: Optional[str] = None
    course_description: Optional[str] = None
    level: Optional[str] = None
    sessions: Optional[int] = None
    total_estimated_hours: Optional[int] = None
    target_user_summary: Optional[str] = None
    course_goal: Optional[str] = None
    learning_outcomes: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    color: Optional[str] = "purple"
    cover_image: Optional[str] = None
    author_name: Optional[str] = None
    published_at: Optional[str] = None
    enrollment_count: int = 0
    is_enrolled: bool = False
    avg_rating: float = 0.0
    rating_count: int = 0
    my_rating: Optional[int] = None
    items: Optional[List['GlobalOutlineItemOut']] = None


class GlobalOutlineItemOut(BaseModel):
    """Read-only outline item shown in the global course detail page."""
    id: int
    session_id: Optional[str] = None
    title: str
    chapter: Optional[str] = None
    chapter_id: Optional[str] = None
    description: Optional[str] = None
    order: int


class CourseRatingRequest(BaseModel):
    """API payload for submitting a 1–5 star rating on a global course."""
    rating: int

class StudyTimeUpdate(BaseModel):
    """API payload containing elapsed focus time additions."""
    seconds: int

class CourseUpdate(BaseModel):
    """API payload containing course patch changes."""
    title: Optional[str] = None
    color: Optional[str] = None
