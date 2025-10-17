"""
User Preferences Endpoints
Manage user content preferences
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.user import User, UserPreference
from app.models.schemas import (
    UserPreferenceCreate,
    UserPreferenceUpdate,
    UserPreferenceResponse
)
from app.middleware.auth import get_current_active_user
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.post("", response_model=UserPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_preferences(
    preferences: UserPreferenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserPreferenceResponse:
    """
    Create user preferences
    
    Args:
        preferences: Preference data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created preferences
    """
    # Check if preferences already exist
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preferences already exist. Use PUT to update."
        )
    
    # Create preferences
    new_prefs = UserPreference(
        user_id=current_user.id,
        topic_preferences=preferences.topic_preferences.model_dump(),
        depth_preference=preferences.depth_preference,
        surprise_tolerance=preferences.surprise_tolerance,
        contextual_preferences=preferences.contextual_preferences.model_dump() if preferences.contextual_preferences else {}
    )
    
    db.add(new_prefs)
    await db.commit()
    await db.refresh(new_prefs)
    
    logger.info("Preferences created", user_id=str(current_user.id))
    
    return new_prefs


@router.get("", response_model=UserPreferenceResponse)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserPreferenceResponse:
    """
    Get user preferences
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        User preferences
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
    
    return preferences


@router.put("", response_model=UserPreferenceResponse)
async def update_preferences(
    preferences: UserPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserPreferenceResponse:
    """
    Update user preferences
    
    Args:
        preferences: Updated preference data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated preferences
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found. Use POST to create."
        )
    
    # Update fields
    if preferences.topic_preferences is not None:
        existing.topic_preferences = preferences.topic_preferences.model_dump()
    if preferences.depth_preference is not None:
        existing.depth_preference = preferences.depth_preference
    if preferences.surprise_tolerance is not None:
        existing.surprise_tolerance = preferences.surprise_tolerance
    if preferences.contextual_preferences is not None:
        existing.contextual_preferences = preferences.contextual_preferences.model_dump()
    
    existing.preference_version += 1
    
    await db.commit()
    await db.refresh(existing)
    
    logger.info("Preferences updated", user_id=str(current_user.id))
    
    return existing


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete user preferences
    
    Args:
        current_user: Authenticated user
        db: Database session
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
    
    await db.delete(preferences)
    await db.commit()
    
    logger.info("Preferences deleted", user_id=str(current_user.id))
