from pydantic import BaseModel, Field
from typing import List, Optional
from app import prompts

# ==========================================
# 1. AI AGENTS & STRUCTURED OUTPUT SCHEMAS
# ==========================================

class OutlineItemSchema(BaseModel):
    """Syllabus session detail."""
    session_id: str = Field(description=prompts.OUTLINE_ITEM_SESSION_ID)
    title: str = Field(description=prompts.OUTLINE_ITEM_TITLE)
    description: str = Field(description=prompts.OUTLINE_ITEM_DESCRIPTION)
    learning_objectives: List[str] = Field(description=prompts.OUTLINE_ITEM_LEARNING_OBJECTIVES)
    key_concepts: List[str] = Field(description=prompts.OUTLINE_ITEM_KEY_CONCEPTS)


class OutlineChapterSchema(BaseModel):
    """Syllabus chapter mapping multiple sessions."""
    chapter_id: str = Field(description=prompts.OUTLINE_CHAPTER_ID)
    title: str = Field(description=prompts.OUTLINE_CHAPTER_TITLE)
    description: str = Field(description=prompts.OUTLINE_CHAPTER_DESCRIPTION)
    sessions: List[OutlineItemSchema] = Field(description=prompts.OUTLINE_CHAPTER_SESSIONS)


class CourseOutlineSchema(BaseModel):
    """Full course chapter mapping."""
    items: List[OutlineChapterSchema]


class CourseGenerationSchema(BaseModel):
    """Full details of a newly generated AI course curriculum."""
    title: str = Field(description=prompts.COURSE_GEN_TITLE)
    short_title: str = Field(description=prompts.COURSE_GEN_SHORT_TITLE)
    level: str = Field(description=prompts.COURSE_GEN_LEVEL)
    total_estimated_hours: int = Field(description=prompts.COURSE_GEN_HOURS)
    target_user_summary: str = Field(description=prompts.COURSE_GEN_USER_SUMMARY)
    course_goal: str = Field(description=prompts.COURSE_GEN_GOAL)
    course_description: str = Field(description=prompts.COURSE_GEN_DESCRIPTION)
    learning_outcomes: List[str] = Field(description=prompts.COURSE_GEN_OUTCOMES)
    prerequisites: List[str] = Field(description=prompts.COURSE_GEN_PREREQS)
    chapters: List[OutlineChapterSchema] = Field(description=prompts.COURSE_GEN_CHAPTERS)


class ChatAgentResponse(BaseModel):
    """Dynamic output determining chat diagnostic loop status."""
    is_complete: bool = Field(description=prompts.CHAT_RESPONSE_COMPLETE)
    chat_response: Optional[str] = Field(description=prompts.CHAT_RESPONSE_TEXT)
    course_data: Optional[CourseGenerationSchema] = Field(description=prompts.CHAT_RESPONSE_COURSE_DATA)
    conversation_summary: Optional[str] = None
    profile: Optional[dict] = None


class KnowledgeNodeUpdateSchema(BaseModel):
    """Representing updates to individual concepts inside user's master graph on full rebuild."""
    concept: str = Field(description=prompts.KNOWLEDGE_NODE_CONCEPT)
    category: str = Field(description=prompts.KNOWLEDGE_NODE_CATEGORY)
    mastery_score_delta: float = Field(description=prompts.KNOWLEDGE_NODE_MASTERY_SCORE)
    prerequisites: Optional[List[str]] = Field(default=[], description=prompts.KNOWLEDGE_NODE_PREREQS)
    difficulty_level: str = Field(default="مقدماتی", description=prompts.KNOWLEDGE_NODE_DIFFICULTY)
    key_terms: List[str] = Field(default=[], description=prompts.KNOWLEDGE_NODE_KEY_TERMS)


class ProfilerUpdateSchema(BaseModel):
    """Detailed structural response returned by the Cognitive Profiler Agent on full rebuild."""
    global_learning_velocity: float = Field(description=prompts.PROFILER_VELOCITY)
    ls_hands_on: float = Field(default=0.0, description=prompts.PROFILER_HANDS_ON)
    ls_visual: float = Field(default=0.0, description=prompts.PROFILER_VISUAL)
    ls_theoretical: float = Field(default=0.0, description=prompts.PROFILER_THEORETICAL)
    ls_self_directed: float = Field(default=0.0, description=prompts.PROFILER_SELF_DIRECTED)
    learning_style_summary: str = Field(default="", description=prompts.PROFILER_STYLE_SUMMARY)
    personality_summary: str = Field(default="", description=prompts.PROFILER_PERSONALITY_SUMMARY)
    strength_areas: List[str] = Field(default=[], description=prompts.PROFILER_STRENGTHS)
    interests: List[str] = Field(default=[], description=prompts.PROFILER_INTERESTS)
    recommended_topics: List[str] = Field(default=[], description=prompts.PROFILER_RECOMMENDATIONS)
    updated_knowledge_nodes: List[KnowledgeNodeUpdateSchema] = Field(description=prompts.PROFILER_NODES)


class IncrementalKnowledgeNodeSchema(BaseModel):
    """Representing an incremental addition or refinement to a concept node on incremental sync."""
    concept: str = Field(description=prompts.INCREMENTAL_NODE_CONCEPT)
    category: str = Field(description=prompts.INCREMENTAL_NODE_CATEGORY)
    action: str = Field(description=prompts.INCREMENTAL_NODE_ACTION)
    mastery_score_delta: float = Field(default=0.0, description=prompts.INCREMENTAL_NODE_MASTERY)
    prerequisites: Optional[List[str]] = Field(default=[], description=prompts.INCREMENTAL_NODE_PREREQS)
    difficulty_level: str = Field(default="مقدماتی", description=prompts.INCREMENTAL_NODE_DIFFICULTY)
    key_terms: List[str] = Field(default=[], description=prompts.INCREMENTAL_NODE_KEY_TERMS)


class IncrementalProfilerUpdateSchema(BaseModel):
    """Sleek, lightweight schema returned by the Incremental Profiler Agent for delta updates on incremental sync."""
    should_update_cognitive_profile: bool = Field(description=prompts.INCREMENTAL_PROFILER_SHOULD_UPDATE)
    global_learning_velocity: Optional[float] = Field(default=None, description=prompts.INCREMENTAL_PROFILER_VELOCITY)
    learning_style_summary_update: Optional[str] = Field(default=None, description=prompts.INCREMENTAL_PROFILER_STYLE_SUMMARY)
    personality_summary_update: Optional[str] = Field(default=None, description=prompts.INCREMENTAL_PROFILER_PERSONALITY_SUMMARY)
    strength_areas: Optional[List[str]] = Field(default=None, description=prompts.INCREMENTAL_PROFILER_STRENGTHS)
    interests: Optional[List[str]] = Field(default=None, description=prompts.INCREMENTAL_PROFILER_INTERESTS)
    recommended_topics: Optional[List[str]] = Field(default=None, description=prompts.INCREMENTAL_PROFILER_RECOMMENDATIONS)
    updated_knowledge_nodes: List[IncrementalKnowledgeNodeSchema] = Field(default=[], description=prompts.INCREMENTAL_PROFILER_NODES)


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
