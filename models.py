from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
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

    course = relationship("Course", back_populates="items")
