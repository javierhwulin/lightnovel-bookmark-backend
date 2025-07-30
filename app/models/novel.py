from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.db.session import Base

class LightNovel(Base):
    __tablename__ = "novels"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    cover_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="ongoing")
    genres = Column(String, nullable=True)  # JSON string of genres
    source_url = Column(String, nullable=True)
    
    # New fields for chapter/volume tracking and raw status
    total_chapters = Column(Integer, nullable=True, default=0)
    total_volumes = Column(Integer, nullable=True, default=0)
    content_type = Column(String, nullable=True, default="unknown")  # 'chapters', 'volumes', or 'unknown'
    raw_status = Column(Text, nullable=True)  # Raw "Status in COO" text from NovelUpdates
    
    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")
    
class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    number = Column(Float, nullable=False)  # Allow decimal chapters like 1.5
    title = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    
    novel = relationship("LightNovel", back_populates="chapters")