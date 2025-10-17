"""
Podcast API Endpoints
Handles podcast generation, retrieval, and management
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.base import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.podcast import Podcast, PodcastStatus
from app.schemas.podcast import (
    PodcastCreate,
    PodcastResponse,
    PodcastListResponse,
    GenerationStatusResponse
)
from app.services.podcast_service import PodcastService

logger = structlog.get_logger()
router = APIRouter(prefix="/podcasts", tags=["podcasts"])


async def _generate_podcast_background(podcast_id: UUID):
    """Background task wrapper that creates its own DB session"""
    from app.db.base import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        service = PodcastService(session)
        await service.generate_podcast_async(podcast_id=podcast_id)


@router.post("/generate", response_model=GenerationStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_podcast(
    podcast_data: PodcastCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new podcast based on location and preferences
    
    This endpoint starts the podcast generation process asynchronously.
    Use the returned job_id to check generation status.
    """
    logger.info("podcast_generation_requested",
                user_id=current_user.id,
                location=podcast_data.location)
    
    try:
        service = PodcastService(db)
        
        # Create podcast record
        podcast = await service.create_podcast(
            user_id=current_user.id,
            location=podcast_data.location,
            podcast_type=podcast_data.podcast_type,
            preferences=podcast_data.preferences
        )
        
        # Start generation in background with its own DB session
        background_tasks.add_task(
            _generate_podcast_background,
            podcast_id=podcast.id
        )
        
        logger.info("podcast_generation_started",
                   podcast_id=podcast.id,
                   user_id=current_user.id)
        
        return GenerationStatusResponse(
            job_id=str(podcast.id),
            status="processing",
            message="Podcast generation started",
            podcast_id=podcast.id
        )
        
    except Exception as e:
        logger.error("podcast_generation_failed",
                    user_id=current_user.id,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start podcast generation: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check the status of a podcast generation job
    """
    try:
        # Use a quick, non-blocking query
        from sqlalchemy import select
        from app.models.podcast import Podcast
        
        # Set a short timeout for this query
        result = await db.execute(
            select(Podcast).filter(
                Podcast.id == job_id,
                Podcast.user_id == current_user.id
            )
        )
        podcast = result.scalar_one_or_none()
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        logger.info("status_checked", 
                   job_id=job_id,
                   status=podcast.status.value,
                   progress=podcast.progress_percentage)
        
        return GenerationStatusResponse(
            job_id=job_id,
            status=podcast.status.value,
            message=podcast.error_message or "Generation in progress",
            podcast_id=podcast.id,
            progress=podcast.progress_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("status_check_failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check status: {str(e)}"
        )


@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific podcast by ID
    """
    try:
        service = PodcastService(db)
        podcast = await service.get_podcast(podcast_id, current_user.id)
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        # Log what we're returning
        logger.info("podcast_retrieved",
                   podcast_id=podcast_id,
                   has_title=bool(podcast.title),
                   has_script=bool(podcast.script_content),
                   script_length=len(podcast.script_content) if podcast.script_content else 0,
                   has_audio=bool(podcast.audio_url),
                   status=podcast.status.value)
        
        return PodcastResponse.model_validate(podcast)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_podcast_failed", podcast_id=podcast_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve podcast: {str(e)}"
        )


@router.get("/", response_model=PodcastListResponse)
async def list_podcasts(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's podcast library
    
    Query parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return
    - status_filter: Filter by status (completed, processing, failed)
    """
    try:
        service = PodcastService(db)
        podcasts = await service.list_user_podcasts(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status_filter=status_filter
        )
        
        total = await service.count_user_podcasts(
            user_id=current_user.id,
            status_filter=status_filter
        )
        
        from app.schemas.podcast import PodcastListItem
        
        return PodcastListResponse(
            podcasts=[PodcastListItem.model_validate(p) for p in podcasts],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        import traceback
        logger.error("list_podcasts_failed", 
                    user_id=current_user.id, 
                    error=str(e),
                    error_type=type(e).__name__,
                    traceback=traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve podcasts: {str(e)}"
        )


@router.delete("/{podcast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_podcast(
    podcast_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a podcast
    """
    try:
        service = PodcastService(db)
        success = await service.delete_podcast(podcast_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        logger.info("podcast_deleted", podcast_id=podcast_id, user_id=current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_podcast_failed", podcast_id=podcast_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete podcast: {str(e)}"
        )


@router.post("/{podcast_id}/regenerate", response_model=GenerationStatusResponse)
async def regenerate_podcast(
    podcast_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate an existing podcast with same parameters
    """
    try:
        service = PodcastService(db)
        podcast = await service.get_podcast(podcast_id, current_user.id)
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        # Reset podcast status
        await service.reset_podcast_for_regeneration(podcast_id)
        
        # Start generation in background
        background_tasks.add_task(
            service.generate_podcast_async,
            podcast_id=podcast_id
        )
        
        logger.info("podcast_regeneration_started",
                   podcast_id=podcast_id,
                   user_id=current_user.id)
        
        return GenerationStatusResponse(
            job_id=str(podcast_id),
            status="processing",
            message="Podcast regeneration started",
            podcast_id=podcast_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("regenerate_podcast_failed", podcast_id=podcast_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate podcast: {str(e)}"
        )
