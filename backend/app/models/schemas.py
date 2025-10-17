"""
Pydantic Schemas
Request/Response models for API validation
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user data response"""
    id: UUID
    email: str
    tier: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# ============================================================================
# User Preference Schemas
# ============================================================================

class TopicPreferences(BaseModel):
    """Schema for hierarchical topic preferences"""
    history: Optional[Dict[str, float]] = Field(default_factory=dict)
    culture: Optional[Dict[str, float]] = Field(default_factory=dict)
    nature: Optional[Dict[str, float]] = Field(default_factory=dict)
    architecture: Optional[Dict[str, float]] = Field(default_factory=dict)
    food: Optional[Dict[str, float]] = Field(default_factory=dict)
    arts: Optional[Dict[str, float]] = Field(default_factory=dict)
    science: Optional[Dict[str, float]] = Field(default_factory=dict)
    folklore: Optional[Dict[str, float]] = Field(default_factory=dict)
    geography: Optional[Dict[str, float]] = Field(default_factory=dict)
    society: Optional[Dict[str, float]] = Field(default_factory=dict)


class ContextualPreferences(BaseModel):
    """Schema for contextual preferences"""
    time_of_day: Optional[Dict[str, Any]] = Field(default_factory=dict)
    day_of_week: Optional[Dict[str, Any]] = Field(default_factory=dict)
    device_type: Optional[Dict[str, Any]] = Field(default_factory=dict)
    location_context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserPreferenceCreate(BaseModel):
    """Schema for creating user preferences"""
    topic_preferences: TopicPreferences = Field(default_factory=TopicPreferences)
    depth_preference: int = Field(default=3, ge=1, le=6)
    surprise_tolerance: int = Field(default=3, ge=1, le=6)
    contextual_preferences: Optional[ContextualPreferences] = Field(default_factory=ContextualPreferences)


class UserPreferenceUpdate(BaseModel):
    """Schema for updating user preferences"""
    topic_preferences: Optional[TopicPreferences] = None
    depth_preference: Optional[int] = Field(None, ge=1, le=6)
    surprise_tolerance: Optional[int] = Field(None, ge=1, le=6)
    contextual_preferences: Optional[ContextualPreferences] = None


class UserPreferenceResponse(BaseModel):
    """Schema for user preference response"""
    id: UUID
    user_id: UUID
    topic_preferences: Dict[str, Any]
    depth_preference: int
    surprise_tolerance: int
    contextual_preferences: Optional[Dict[str, Any]] = None
    preference_version: int
    last_updated: datetime
    
    model_config = {"from_attributes": True}


# ============================================================================
# User Behavior Schemas
# ============================================================================

class BehaviorData(BaseModel):
    """Schema for behavior tracking data"""
    playback_speed: Optional[float] = None
    pause_count: Optional[int] = None
    skip_count: Optional[int] = None
    replay_segments: Optional[List[Dict[str, float]]] = None
    completion_percentage: Optional[float] = None
    engagement_score: Optional[float] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class UserBehaviorCreate(BaseModel):
    """Schema for creating behavior record"""
    session_id: str
    podcast_id: Optional[str] = None
    behavior_data: BehaviorData
    device_type: Optional[str] = None
    location_context: Optional[str] = None


class UserBehaviorResponse(BaseModel):
    """Schema for behavior response"""
    id: UUID
    user_id: UUID
    session_id: str
    podcast_id: Optional[str] = None
    behavior_data: Dict[str, Any]
    device_type: Optional[str] = None
    location_context: Optional[str] = None
    timestamp: datetime
    
    model_config = {"from_attributes": True}


# ============================================================================
# Content Metadata Schemas
# ============================================================================

class ContentMetadataCreate(BaseModel):
    """Schema for creating content metadata"""
    location_id: str
    content_type: str = Field(..., pattern="^(base|standout|topic-specific)$")
    source_apis: List[str]
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    content_hash: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class ContentMetadataResponse(BaseModel):
    """Schema for content metadata response"""
    id: UUID
    location_id: str
    content_type: str
    source_apis: List[str]
    quality_score: Optional[float] = None
    content_hash: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int
    last_accessed: datetime
    
    model_config = {"from_attributes": True}


# ============================================================================
# Health Check Schemas
# ============================================================================

class HealthCheck(BaseModel):
    """Schema for health check response"""
    status: str
    version: str
    environment: str
    database: str
    redis: str
    timestamp: datetime


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
