"""
Podcast Schemas
Pydantic models for podcast API requests and responses
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, validator


class PodcastCreate(BaseModel):
    """Request schema for creating a new podcast"""
    location: str = Field(..., description="Location name or coordinates")
    podcast_type: str = Field(default="base", description="Type of podcast (base, standout, topic, personalized)")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences for generation")
    
    @validator('podcast_type')
    def validate_podcast_type(cls, v):
        valid_types = ['base', 'standout', 'topic', 'personalized']
        if v not in valid_types:
            raise ValueError(f'podcast_type must be one of: {", ".join(valid_types)}')
        return v


class GenerationStatusResponse(BaseModel):
    """Response schema for generation status"""
    job_id: UUID
    status: str  # processing, completed, failed
    message: str
    podcast_id: Optional[UUID] = None
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    
    class Config:
        from_attributes = True


class PodcastResponse(BaseModel):
    """Response schema for podcast details"""
    id: UUID
    user_id: UUID
    location: str
    podcast_type: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    script_content: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    podcast_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress_percentage: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PodcastListItem(BaseModel):
    """Response schema for podcast in list view (excludes script_content)"""
    id: UUID
    user_id: UUID
    location: str
    podcast_type: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    progress_percentage: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PodcastListResponse(BaseModel):
    """Response schema for podcast list"""
    podcasts: List[PodcastListItem]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class PodcastMetadata(BaseModel):
    """Metadata for podcast"""
    location_details: Optional[Dict[str, Any]] = None
    content_sources: Optional[List[str]] = None
    generation_time_seconds: Optional[float] = None
    quality_score: Optional[float] = None
    word_count: Optional[int] = None
    
    class Config:
        from_attributes = True
