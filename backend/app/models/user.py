"""
User Database Models
SQLAlchemy models for users, preferences, and behavior
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, DECIMAL, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import UUID, JSONB, ARRAY


class User(Base):
    """User model with authentication and tier information"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tier = Column(String(20), default="free", nullable=False)  # free, premium
    is_active = Column(Integer, default=1, nullable=False)
    is_verified = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    behavior = relationship("UserBehavior", back_populates="user", cascade="all, delete-orphan")
    podcasts = relationship("Podcast", back_populates="user", cascade="all, delete-orphan")
    
    # Phase 3: Advanced preference relationships
    topic_preferences = relationship("UserTopicPreference", back_populates="user", cascade="all, delete-orphan")
    depth_preference = relationship("UserDepthPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    surprise_preference = relationship("UserSurprisePreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    contextual_preferences = relationship("UserContextualPreference", back_populates="user", cascade="all, delete-orphan")
    learning_state = relationship("UserLearningState", back_populates="user", uselist=False, cascade="all, delete-orphan")
    behavioral_signals = relationship("UserBehavioralSignal", back_populates="user", cascade="all, delete-orphan")
    cold_start_data = relationship("UserColdStartData", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, tier={self.tier})>"


class UserPreference(Base):
    """User preferences for content personalization"""
    
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Topic preferences (hierarchical structure)
    topic_preferences = Column(JSONB, nullable=False, default=dict)
    
    # Depth preference (1-6 scale)
    depth_preference = Column(Integer, default=3, nullable=False)
    
    # Surprise tolerance (1-6 scale)
    surprise_tolerance = Column(Integer, default=3, nullable=False)
    
    # Contextual preferences (time, device, location context)
    contextual_preferences = Column(JSONB, nullable=True, default=dict)
    
    # Learning state
    preference_version = Column(Integer, default=1, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id}, depth={self.depth_preference}, surprise={self.surprise_tolerance})>"


class UserBehavior(Base):
    """User behavior tracking for ML-based personalization"""
    
    __tablename__ = "user_behavior"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    podcast_id = Column(String(255), nullable=True, index=True)
    
    # Behavior data (playback, engagement, completion, etc.)
    behavior_data = Column(JSONB, nullable=False)
    
    # Metadata
    device_type = Column(String(50), nullable=True)
    location_context = Column(String(255), nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="behavior")
    
    def __repr__(self) -> str:
        return f"<UserBehavior(user_id={self.user_id}, session={self.session_id}, timestamp={self.timestamp})>"


class ContentMetadata(Base):
    """Content metadata for caching and quality tracking"""
    
    __tablename__ = "content_metadata"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    location_id = Column(String(255), nullable=False, index=True)
    content_type = Column(String(50), nullable=False, index=True)  # base, standout, topic-specific
    
    # Source information
    source_apis = Column(ARRAY(Text), nullable=False)
    
    # Quality metrics
    quality_score = Column(DECIMAL(3, 2), nullable=True)
    
    # Content hash for deduplication
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Flexible metadata storage (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    content_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Cache management
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ContentMetadata(location_id={self.location_id}, type={self.content_type}, quality={self.quality_score})>"
