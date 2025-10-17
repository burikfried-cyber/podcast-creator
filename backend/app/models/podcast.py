"""
Podcast Model
Database model for podcast records
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from app.db.base import Base
from app.db.types import UUID


class PodcastStatus(str, enum.Enum):
    """Podcast generation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Podcast(Base):
    """
    Podcast model for storing generated podcasts
    """
    __tablename__ = "podcasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Location and type
    location = Column(String(255), nullable=False)
    podcast_type = Column(String(50), nullable=False, default="base")  # base, standout, topic, personalized
    
    # Status tracking
    status = Column(SQLEnum(PodcastStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=PodcastStatus.PENDING, index=True)
    progress_percentage = Column(Integer, default=0)  # 0-100
    
    # Content
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    script_content = Column(Text, nullable=True)
    
    # Audio
    audio_url = Column(String(1000), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Metadata (renamed to avoid SQLAlchemy reserved name)
    podcast_metadata = Column(JSON, nullable=True)  # Additional data (preferences, quality scores, etc.)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="podcasts")
    
    def __repr__(self):
        return f"<Podcast(id={self.id}, location='{self.location}', status='{self.status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if podcast generation is completed"""
        return self.status == PodcastStatus.COMPLETED
    
    @property
    def is_processing(self) -> bool:
        """Check if podcast is currently being generated"""
        return self.status == PodcastStatus.PROCESSING
    
    @property
    def has_failed(self) -> bool:
        """Check if podcast generation failed"""
        return self.status == PodcastStatus.FAILED
