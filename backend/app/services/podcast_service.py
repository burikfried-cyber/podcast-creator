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
from app.services.content.content_aggregator import content_aggregator
from app.services.content.hierarchical_collector import hierarchical_collector
from app.services.content.question_detector import question_detector
from app.services.research.deep_research_service import deep_research_service
from app.services.narrative.enhanced_podcast_generator import enhanced_podcast_generator
from app.services.audio.audio_service import audio_service
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
            
            # Step 1: Gather content from all sources with hierarchical collection (30%)
            log_step(1, "Gathering multi-level content from Wikipedia, Wikidata, GeoNames, and Location services", "RUNNING")
            user_preferences = podcast.podcast_metadata or {}
            content_data = await self._gather_content(podcast.location, user_preferences)
            podcast.progress_percentage = 30
            await self.db.commit()
            
            # Log hierarchical collection results
            hierarchical_meta = content_data.get('hierarchical_metadata', {})
            levels_collected = hierarchical_meta.get('levels_collected', 1)
            context = hierarchical_meta.get('context_preference', 'balanced')
            log_step(1, f"Content gathering complete - {levels_collected} geographic levels collected ({context})", "DONE")
            
            # Step 2: Generate script with enhanced generator (60%)
            log_step(2, "Generating podcast script with Enhanced Perplexity AI (CLEAR framework)", "RUNNING")
            user_profile = self._create_user_profile(podcast.user_id, podcast.podcast_metadata or {})
            podcast_type_enum = self._get_podcast_type_enum(podcast.podcast_type)
            
            # Get target duration from metadata or default to 10 minutes
            target_duration = (podcast.podcast_metadata or {}).get('duration_minutes', 10)
            
            # Use enhanced generator with CLEAR framework
            result = await enhanced_podcast_generator.generate_information_rich_script(
                content_data=content_data,
                podcast_type=podcast_type_enum.value,
                target_duration=target_duration,
                user_preferences=podcast.podcast_metadata
            )
            
            if not result.get('success'):
                error_msg = result.get('generation_metadata', {}).get('error', 'Script generation failed validation')
                log_step(2, f"Script generation FAILED: {error_msg}", "ERROR")
                # Log quality metrics for debugging
                quality_metrics = result.get('quality_metrics', {})
                logger.warning("script_generation_failed", metrics=quality_metrics)
                raise Exception(error_msg)
            
            podcast.progress_percentage = 60
            await self.db.commit()
            
            # Log generation metadata
            gen_metadata = result.get('generation_metadata', {})
            quality_metrics = result.get('quality_metrics', {})
            log_step(2, f"Script generation complete - {gen_metadata.get('attempts', 1)} attempts, {gen_metadata.get('generation_time', 0):.1f}s", "DONE")
            
            # Step 3: Extract script details (70%)
            log_step(3, "Extracting script details and metadata", "RUNNING")
            logger.info("extracting_script_details", podcast_id=podcast_id)
            
            script_text = result.get('script')
            if not script_text:
                log_step(3, "No script in result", "ERROR")
                raise Exception("No script in generation result")
            
            # Build title and description
            is_question = content_data.get('is_question', False)
            if is_question:
                podcast.title = f"Research: {content_data.get('location', 'Unknown')[:100]}"
                podcast.description = content_data.get('description', '')[:500]
            else:
                podcast.title = content_data.get('title', f"Podcast about {podcast.location}")
                podcast.description = content_data.get('description', '')[:500]
            
            podcast.script_content = script_text
            
            # Calculate duration from word count (150 words/minute)
            word_count = gen_metadata.get('actual_word_count', len(script_text.split()))
            podcast.duration_seconds = int((word_count / 150) * 60)
            
            # Use validation score as quality score
            quality_score = 1.0 if quality_metrics.get('passes_validation') else 0.7
            
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
            
            # Step 4: Generate audio with Google Cloud TTS (90%)
            log_step(4, "Generating audio with Google Cloud TTS", "RUNNING")
            
            # Determine user tier (free vs premium)
            user_tier = (podcast.podcast_metadata or {}).get('user_tier', 'free')
            
            try:
                # Generate audio using Google TTS
                audio_result = await audio_service.generate_podcast_audio(
                    script_text=script_text,
                    podcast_id=str(podcast.id),
                    user_tier=user_tier,
                    speaking_rate=1.0,
                    pitch=0.0
                )
                
                if audio_result.get('success'):
                    # Update podcast with audio details
                    podcast.audio_url = audio_result['audio_url']
                    podcast.duration_seconds = audio_result['duration_seconds']
                    
                    # Add audio metadata
                    podcast.podcast_metadata = {
                        **(podcast.podcast_metadata or {}),
                        'audio_generation': {
                            'file_size_mb': audio_result.get('file_size_mb', 0),
                            'generation_time': audio_result.get('generation_time', 0),
                            'synthesis_time': audio_result.get('synthesis_time', 0),
                            'cost_estimate': audio_result.get('cost_estimate', 0),
                            'voice_name': audio_result.get('voice_name', ''),
                            'voice_type': audio_result.get('voice_type', '')
                        }
                    }
                    
                    log_step(4, f"Audio generated: {audio_result.get('file_size_mb', 0):.2f}MB, {audio_result.get('duration_seconds', 0)}s", "DONE")
                    logger.info("audio_generation_success",
                               podcast_id=podcast_id,
                               duration=audio_result['duration_seconds'],
                               cost=audio_result.get('cost_estimate', 0))
                else:
                    # Audio generation failed, but continue without audio
                    error_msg = audio_result.get('error', 'Unknown error')
                    log_step(4, f"Audio generation failed: {error_msg} (continuing without audio)", "WARNING")
                    logger.warning("audio_generation_failed_continuing",
                                 podcast_id=podcast_id,
                                 error=error_msg)
                    
            except Exception as e:
                # Handle audio generation errors gracefully
                log_step(4, f"Audio generation error: {str(e)} (continuing without audio)", "WARNING")
                logger.warning("audio_generation_error",
                             podcast_id=podcast_id,
                             error=str(e))
            
            podcast.progress_percentage = 90
            await self.db.commit()
            log_step(4, "Audio step complete", "DONE")
            
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
    
    async def _gather_content(self, location: str, user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Gather content using question detection and routing.
        Routes to deep research for questions, hierarchical collection for locations.
        """
        logger.info("gathering_content_with_routing", input=location[:100])
        
        # Phase 1C: Detect if input is a question
        detection = question_detector.is_question(location)
        
        if detection["is_question"]:
            # Question path: Use deep research
            logger.info("question_detected", 
                       question_type=detection.get("question_type"),
                       confidence=detection.get("confidence"))
            
            return await self._gather_research_content(location, user_preferences, detection)
        else:
            # Location path: Use hierarchical collector
            logger.info("location_detected", location=location)
            return await self._gather_location_content(location, user_preferences)
    
    async def _gather_research_content(
        self, 
        question: str, 
        user_preferences: Optional[Dict[str, Any]], 
        detection: Dict
    ) -> Dict[str, Any]:
        """
        Gather content for question-based research.
        Uses deep research service + optional location context.
        """
        depth_level = user_preferences.get("depth_preference", 3) if user_preferences else 3
        
        # Conduct deep research
        research_result = await deep_research_service.research_question(
            question,
            depth_level=depth_level
        )
        
        # Check if location was extracted from question
        extracted_location = detection.get("extracted_location")
        location_context = None
        
        if extracted_location:
            logger.info("location_extracted_from_question", location=extracted_location)
            try:
                # Get location context to enrich research
                location_context = await hierarchical_collector.collect_hierarchical_content(
                    extracted_location,
                    user_preferences
                )
            except Exception as e:
                logger.warning("location_context_failed", error=str(e))
        
        # Build content data structure
        return {
            'id': question,
            'location': question,
            'title': f"Research: {question[:100]}",
            'description': research_result.get("overview", ""),
            'content': research_result.get("comprehensive_answer", ""),
            'sources': [s.get("url", s.get("source", "Unknown")) for s in research_result.get("sources", [])],
            # Phase 1C: Deep research data
            'is_question': True,
            'question_type': detection.get("question_type"),
            'research_result': research_result,
            'key_findings': research_result.get("key_findings", []),
            'detailed_explanation': research_result.get("detailed_explanation", ""),
            'conclusion': research_result.get("conclusion", ""),
            'confidence': research_result.get("confidence", 0.0),
            'research_time': research_result.get("research_time", 0.0),
            # Optional location context
            'extracted_location': extracted_location,
            'location_context': location_context,
            # Metadata
            'collection_metadata': {
                'method': 'deep_research',
                'depth_level': depth_level,
                'has_location_context': location_context is not None
            }
        }
    
    async def _gather_location_content(
        self,
        location: str,
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Gather content for location-based podcasts.
        Uses hierarchical collector for multi-level geographic context.
        """
        # Use hierarchical collector for multi-level content collection
        hierarchical_content = await hierarchical_collector.collect_hierarchical_content(
            location,
            user_preferences
        )
        
        # Extract primary content for backward compatibility
        primary_content = hierarchical_content.get('primary_content', {})
        aggregated = primary_content
        
        # Extract data from aggregated sources
        wikipedia_data = aggregated.get('sources', {}).get('wikipedia', {})
        wikidata_data = aggregated.get('sources', {}).get('wikidata', {})
        geonames_data = aggregated.get('sources', {}).get('geonames', {})
        location_data = aggregated.get('sources', {}).get('location', {})
        
        # Get interesting facts from Wikipedia (backward compatibility)
        interesting_facts = []
        if wikipedia_data:
            interesting_facts = await self.wikipedia.get_interesting_facts(wikipedia_data)
        
        # Log collection results
        metadata = aggregated.get('collection_metadata', {})
        hierarchical_meta = hierarchical_content.get('collection_metadata', {})
        
        logger.info("hierarchical_content_gathered",
                   location=location,
                   levels_collected=hierarchical_meta.get('levels_collected'),
                   context=hierarchical_content.get('context_preference'),
                   sources_successful=metadata.get('sources_successful'))
        
        # Return backward-compatible structure with enhancements
        return {
            'id': location,
            'location': location,
            'title': wikipedia_data.get('title', location),
            'description': wikipedia_data.get('summary', f"Information about {location}"),
            'wiki_content': wikipedia_data,
            'interesting_facts': interesting_facts,
            'location_details': location_data,
            'content': f"This is a podcast about {location}. It covers the history, culture, and interesting facts about this location.",
            'sources': ['wikipedia', 'wikidata', 'geonames', 'location'],
            # Phase 1A: Multi-source aggregated content
            'aggregated_content': aggregated,
            'hierarchy': aggregated.get('hierarchy', {}),
            'structured_facts': aggregated.get('structured_facts', []),
            'geographic_context': aggregated.get('geographic_context', {}),
            'quality_scores': aggregated.get('quality_scores', {}),
            'collection_metadata': metadata,
            # Phase 1B: Hierarchical multi-level content
            'hierarchical_content': hierarchical_content,
            'content_levels': hierarchical_content.get('content_levels', {}),
            'content_weights': hierarchical_content.get('content_weights', {}),
            'context_preference': hierarchical_content.get('context_preference', 'balanced'),
            'hierarchical_metadata': hierarchical_meta
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
