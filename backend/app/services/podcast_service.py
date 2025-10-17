"""
Podcast Service
Business logic for podcast generation and management
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
import structlog
from datetime import datetime

from app.models.podcast import Podcast, PodcastStatus
from app.models.user import User
from app.services.narrative.podcast_generator import PodcastGenerator
from app.services.narrative.models import PodcastType, UserProfile
from app.services.content import WikipediaService, LocationService
from app.core.file_logging import log_section, log_step

logger = structlog.get_logger()


class PodcastService:
    """Service for podcast operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.generator = PodcastGenerator()
        self.wikipedia = WikipediaService()
        self.location_service = LocationService()
    
    async def create_podcast(
        self,
        user_id: UUID,
        location: str,
        podcast_type: str = "base",
        preferences: Optional[Dict[str, Any]] = None
    ) -> Podcast:
        """
        Create a new podcast record
        """
        podcast = Podcast(
            user_id=user_id,
            location=location,
            podcast_type=podcast_type,
            status=PodcastStatus.PENDING,
            podcast_metadata=preferences or {}
        )
        
        self.db.add(podcast)
        await self.db.commit()
        await self.db.refresh(podcast)
        
        logger.info("podcast_created",
                   podcast_id=podcast.id,
                   user_id=user_id,
                   location=location)
        
        return podcast
    
    async def generate_podcast_async(self, podcast_id: UUID):
        """
        Generate podcast content asynchronously
        This runs in the background
        """
        try:
            result = await self.db.execute(select(Podcast).filter(Podcast.id == podcast_id))
            podcast = result.scalar_one_or_none()
            
            if not podcast:
                logger.error("podcast_not_found", podcast_id=podcast_id)
                return
            
            log_section(f"PODCAST GENERATION: {podcast.location}")
            
            # Update status to processing
            podcast.status = PodcastStatus.PROCESSING
            podcast.progress_percentage = 10
            await self.db.commit()
            
            log_step(1, f"Starting generation for {podcast.location}", "STARTED")
            logger.info("podcast_generation_started", podcast_id=podcast_id, location=podcast.location)
            
            # Step 1: Gather content (30%)
            log_step(1, "Gathering content from Wikipedia and Location services", "RUNNING")
            content_data = await self._gather_content(podcast.location)
            podcast.progress_percentage = 30
            await self.db.commit()
            log_step(1, "Content gathering complete", "DONE")
            
            # Step 2: Generate script (60%)
            log_step(2, "Generating podcast script with Perplexity AI", "RUNNING")
            user_profile = self._create_user_profile(podcast.user_id, podcast.podcast_metadata or {})
            podcast_type_enum = self._get_podcast_type_enum(podcast.podcast_type)
            
            result = await self.generator.generate_podcast(
                content_data=content_data,
                podcast_type=podcast_type_enum,
                user_preferences=user_profile,
                quality_check=True
            )
            
            if not result.get('success'):
                error_msg = result.get('error', 'Unknown generation error')
                log_step(2, f"Script generation FAILED: {error_msg}", "ERROR")
                raise Exception(error_msg)
            
            podcast.progress_percentage = 60
            await self.db.commit()
            log_step(2, "Script generation complete", "DONE")
            
            # Step 3: Extract script details (70%)
            log_step(3, "Extracting script details and metadata", "RUNNING")
            logger.info("extracting_script_details", podcast_id=podcast_id)
            
            script = result.get('script')
            if not script:
                log_step(3, "No script in result", "ERROR")
                raise Exception("No script in generation result")
            
            podcast.title = getattr(script, 'title', f"Podcast about {podcast.location}")
            podcast.description = getattr(script, 'description', '')
            podcast.script_content = getattr(script, 'content', '')
            podcast.duration_seconds = getattr(script, 'estimated_duration_seconds', 600)
            
            # Extract quality score from quality report
            quality_report = result.get('quality_report')
            quality_score = getattr(quality_report, 'overall_score', None) if quality_report else None
            
            podcast.podcast_metadata = {
                **(podcast.podcast_metadata or {}),
                'quality_score': quality_score,
                'word_count': len(podcast.script_content.split()) if podcast.script_content else 0,
                'generation_metadata': result.get('metadata', {})
            }
            podcast.progress_percentage = 70
            await self.db.commit()
            log_step(3, f"Script extracted: {podcast.title}", "DONE")
            logger.info("script_details_extracted", podcast_id=podcast_id, title=podcast.title)
            
            # Step 4: Generate audio (90%)
            log_step(4, "Preparing audio generation (skipped for now)", "RUNNING")
            # TODO: Integrate audio generation service
            # For now, we'll skip audio generation
            # audio_url = await self._generate_audio(script.content)
            # podcast.audio_url = audio_url
            podcast.progress_percentage = 90
            await self.db.commit()
            log_step(4, "Audio preparation complete", "DONE")
            
            # Step 5: Complete (100%)
            log_step(5, "Finalizing podcast", "RUNNING")
            podcast.status = PodcastStatus.COMPLETED
            podcast.progress_percentage = 100
            podcast.completed_at = datetime.utcnow()
            await self.db.commit()
            log_step(5, "Podcast generation COMPLETE!", "DONE")
            
            log_section(f"SUCCESS: {podcast.title}")
            logger.info("podcast_generation_completed",
                       podcast_id=podcast_id,
                       duration=podcast.duration_seconds,
                       title=podcast.title)
            
        except Exception as e:
            log_section(f"ERROR: Podcast Generation Failed")
            logger.error("podcast_generation_failed",
                        podcast_id=podcast_id,
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Log full traceback
            import traceback
            logger.error("full_traceback", traceback=traceback.format_exc())
            
            podcast.status = PodcastStatus.FAILED
            podcast.error_message = str(e)
            await self.db.commit()
            
            log_section(f"FAILED: {str(e)}")
    
    async def _gather_content(self, location: str) -> Dict[str, Any]:
        """
        Gather real content about the location from Wikipedia and location services
        """
        logger.info("gathering_content", location=location)
        
        # Fetch real content from Wikipedia
        wiki_content = await self.wikipedia.get_location_content(location)
        interesting_facts = await self.wikipedia.get_interesting_facts(wiki_content)
        
        # Fetch location details
        location_details = await self.location_service.get_location_details(location)
        
        logger.info("content_gathered",
                   location=location,
                   wiki_title=wiki_content.get('title'),
                   facts_count=len(interesting_facts))
        
        return {
            'id': location,
            'location': location,
            'title': wiki_content.get('title', location),
            'description': wiki_content.get('summary', f"Information about {location}"),
            'wiki_content': wiki_content,
            'interesting_facts': interesting_facts,
            'location_details': location_details,
            'content': f"This is a podcast about {location}. It covers the history, culture, and interesting facts about this location.",
            'sources': ['mock_data']
        }
    
    def _create_user_profile(self, user_id: UUID, metadata: Dict[str, Any]) -> UserProfile:
        """Create user profile from metadata"""
        return UserProfile(
            user_id=str(user_id),
            surprise_tolerance=metadata.get('surprise_tolerance', 2),
            preferred_length=metadata.get('preferred_length', 'medium'),
            preferred_style=metadata.get('preferred_style', 'balanced'),
            preferred_pace=metadata.get('preferred_pace', 'moderate'),
            interests=metadata.get('interests', [])
        )
    
    def _get_podcast_type_enum(self, podcast_type: str) -> PodcastType:
        """Convert string to PodcastType enum"""
        type_map = {
            'base': PodcastType.BASE,
            'standout': PodcastType.STANDOUT,
            'topic': PodcastType.TOPIC,
            'personalized': PodcastType.PERSONALIZED
        }
        return type_map.get(podcast_type, PodcastType.BASE)
    
    async def get_podcast(self, podcast_id: UUID, user_id: UUID) -> Optional[Podcast]:
        """Get a podcast by ID (user must own it)"""
        result = await self.db.execute(
            select(Podcast).filter(
                and_(
                    Podcast.id == podcast_id,
                    Podcast.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_user_podcasts(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> List[Podcast]:
        """List user's podcasts with optional filtering"""
        # Load all columns
        query = select(Podcast).filter(Podcast.user_id == user_id)
        
        if status_filter:
            try:
                status_enum = PodcastStatus(status_filter)
                query = query.filter(Podcast.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        query = query.order_by(Podcast.created_at.desc()).offset(skip).limit(limit)
        
        logger.info("listing_podcasts", user_id=user_id, skip=skip, limit=limit, status_filter=status_filter)
        result = await self.db.execute(query)
        podcasts = list(result.scalars().all())
        
        logger.info("podcasts_listed", count=len(podcasts))
        
        return podcasts
    
    async def count_user_podcasts(
        self,
        user_id: UUID,
        status_filter: Optional[str] = None
    ) -> int:
        """Count user's podcasts"""
        from sqlalchemy import func
        query = select(func.count()).select_from(Podcast).filter(Podcast.user_id == user_id)
        
        if status_filter:
            try:
                status_enum = PodcastStatus(status_filter)
                query = query.filter(Podcast.status == status_enum)
            except ValueError:
                pass
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def delete_podcast(self, podcast_id: UUID, user_id: UUID) -> bool:
        """Delete a podcast"""
        podcast = await self.get_podcast(podcast_id, user_id)
        
        if not podcast:
            return False
        
        await self.db.delete(podcast)
        await self.db.commit()
        
        logger.info("podcast_deleted", podcast_id=podcast_id, user_id=user_id)
        return True
    
    async def reset_podcast_for_regeneration(self, podcast_id: UUID):
        """Reset podcast status for regeneration"""
        result = await self.db.execute(select(Podcast).filter(Podcast.id == podcast_id))
        podcast = result.scalar_one_or_none()
        
        if podcast:
            podcast.status = PodcastStatus.PENDING
            podcast.progress_percentage = 0
            podcast.error_message = None
            podcast.completed_at = None
            await self.db.commit()
