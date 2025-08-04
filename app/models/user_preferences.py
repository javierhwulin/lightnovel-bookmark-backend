"""
User Preferences database models
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.session import Base


class UserPreferences(Base):
    """
    User preferences for novels - tracks reading status, favorites, progress, etc.
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False, unique=True)
    user_status = Column(String, nullable=True)  # reading, completed, on_hold, dropped, plan_to_read
    is_favorite = Column(Boolean, default=False, nullable=False)
    current_chapter = Column(Float, nullable=True)  # Support decimal chapters like 1.5
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    personal_notes = Column(Text, nullable=True)
    date_started = Column(Date, nullable=True)
    date_completed = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to novel
    novel = relationship("LightNovel", backref="user_preferences")


class ReadingSession(Base):
    """
    Track individual reading sessions for analytics and time tracking
    """
    __tablename__ = "reading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    chapter_number = Column(Float, nullable=False)  # Support decimal chapters
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_minutes = Column(Integer, nullable=True)  # Duration in minutes
    
    # Additional metadata
    ended_at = Column(DateTime, nullable=True)
    device_type = Column(String, nullable=True)  # web, mobile, etc.
    
    # Relationships
    novel = relationship("LightNovel", backref="reading_sessions") 