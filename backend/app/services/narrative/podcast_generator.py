"""
Unified Podcast Generator
Orchestrates all components to generate complete podcast scripts
"""
import asyncio
from typing import Dict, List, Any, Optional
import structlog

from .models import (
    PodcastType,
    PodcastScript,
    QualityReport,
    UserProfile
)
from .narrative_engine import NarrativeIntelligenceEngine
from .script_assembly import ScriptAssemblyEngine
from .quality_control import ContentQualityController

logger = structlog.get_logger()


class PodcastGenerator:
    """
    Unified podcast generator for all formats
    Orchestrates narrative construction, script assembly, and quality control
    """
    
    def __init__(self):
        self.narrative_engine = NarrativeIntelligenceEngine()
        self.script_assembler = ScriptAssemblyEngine()
        self.quality_controller = ContentQualityController()
    
    async def generate_podcast(
        self,
        content_data: Dict[str, Any],
        podcast_type: PodcastType,
        user_preferences: Optional[UserProfile] = None,
        quality_check: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete podcast script with optional quality check
        
        Args:
            content_data: Source content for podcast
            podcast_type: Type of podcast to generate
            user_preferences: User preferences for personalization
            quality_check: Whether to run quality control
            
        Returns:
            Dictionary with script and quality report
        """
        logger.info("podcast_generation_started",
                   content_id=content_data.get('id'),
                   podcast_type=podcast_type.value)
        
        try:
            # Use default preferences if none provided
            if user_preferences is None:
                user_preferences = UserProfile(user_id="default")
            
            # Step 1: Construct narrative
            narrative = await self.narrative_engine.construct_narrative(
                content_data=content_data,
                user_preferences=user_preferences,
                podcast_type=podcast_type.value
            )
            
            # Step 2: Assemble script
            script = await self.script_assembler.assemble_podcast_script(
                narrative=narrative,
                content_data=content_data,
                podcast_type=podcast_type.value,
                user_preferences=user_preferences
            )
            
            # Step 3: Quality control (if enabled)
            quality_report = None
            if quality_check:
                quality_report = await self.quality_controller.comprehensive_quality_check(
                    script=script,
                    source_content=content_data
                )
                
                # Log quality issues
                if not quality_report.passed:
                    logger.warning("quality_check_failed",
                                 content_id=content_data.get('id'),
                                 issues=quality_report.get_all_issues())
            
            logger.info("podcast_generation_complete",
                       content_id=content_data.get('id'),
                       quality_passed=quality_report.passed if quality_report else None,
                       script_length=len(script.content))
            
            return {
                'success': True,
                'script': script,
                'narrative': narrative,
                'quality_report': quality_report,
                'metadata': {
                    'content_id': content_data.get('id'),
                    'podcast_type': podcast_type.value,
                    'duration_seconds': script.estimated_duration_seconds,
                    'quality_score': quality_report.overall_score if quality_report else None
                }
            }
            
        except Exception as e:
            logger.error("podcast_generation_failed",
                        content_id=content_data.get('id'),
                        error=str(e))
            return {
                'success': False,
                'error': str(e),
                'content_id': content_data.get('id')
            }
    
    async def generate_base_podcast(
        self,
        content_data: Dict[str, Any],
        user_preferences: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Generate base podcast (essential information, balanced depth)"""
        return await self.generate_podcast(
            content_data=content_data,
            podcast_type=PodcastType.BASE,
            user_preferences=user_preferences
        )
    
    async def generate_standout_podcast(
        self,
        content_data: Dict[str, Any],
        user_preferences: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Generate standout podcast (remarkable discoveries, mystery focus)"""
        return await self.generate_podcast(
            content_data=content_data,
            podcast_type=PodcastType.STANDOUT,
            user_preferences=user_preferences
        )
    
    async def generate_topic_podcast(
        self,
        content_data: Dict[str, Any],
        user_preferences: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Generate topic-specific podcast (deep dive, expert-level)"""
        return await self.generate_podcast(
            content_data=content_data,
            podcast_type=PodcastType.TOPIC,
            user_preferences=user_preferences
        )
    
    async def generate_personalized_podcast(
        self,
        content_data: Dict[str, Any],
        user_preferences: UserProfile
    ) -> Dict[str, Any]:
        """Generate personalized podcast (user preference-driven)"""
        return await self.generate_podcast(
            content_data=content_data,
            podcast_type=PodcastType.PERSONALIZED,
            user_preferences=user_preferences
        )
    
    async def batch_generate_podcasts(
        self,
        content_items: List[Dict[str, Any]],
        podcast_type: PodcastType,
        user_preferences: Optional[UserProfile] = None,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple podcasts concurrently
        
        Args:
            content_items: List of content items
            podcast_type: Type of podcast to generate
            user_preferences: User preferences
            max_concurrent: Maximum concurrent generations
            
        Returns:
            List of generation results
        """
        logger.info("batch_generation_started",
                   num_items=len(content_items),
                   podcast_type=podcast_type.value)
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_limit(content_data):
            async with semaphore:
                return await self.generate_podcast(
                    content_data=content_data,
                    podcast_type=podcast_type,
                    user_preferences=user_preferences
                )
        
        # Generate all podcasts concurrently
        results = await asyncio.gather(
            *[generate_with_limit(item) for item in content_items],
            return_exceptions=True
        )
        
        # Count successes and failures
        successes = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failures = len(results) - successes
        
        logger.info("batch_generation_complete",
                   total=len(results),
                   successes=successes,
                   failures=failures)
        
        return results


# Convenience function for easy access
async def generate_podcast_script(
    content_data: Dict[str, Any],
    podcast_type: str = "base",
    user_preferences: Optional[Dict[str, Any]] = None,
    quality_check: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to generate podcast script
    
    Args:
        content_data: Source content
        podcast_type: Type of podcast ("base", "standout", "topic", "personalized")
        user_preferences: User preferences dict
        quality_check: Whether to run quality control
        
    Returns:
        Generation result with script and quality report
    """
    generator = PodcastGenerator()
    
    # Convert string to enum
    podcast_type_enum = PodcastType(f"{podcast_type}_podcast")
    
    # Convert dict to UserProfile if provided
    user_profile = None
    if user_preferences:
        user_profile = UserProfile(
            user_id=user_preferences.get('user_id', 'default'),
            surprise_tolerance=user_preferences.get('surprise_tolerance', 2),
            preferred_length=user_preferences.get('preferred_length', 'medium'),
            preferred_style=user_preferences.get('preferred_style', 'balanced'),
            preferred_pace=user_preferences.get('preferred_pace', 'moderate'),
            interests=user_preferences.get('interests', [])
        )
    
    return await generator.generate_podcast(
        content_data=content_data,
        podcast_type=podcast_type_enum,
        user_preferences=user_profile,
        quality_check=quality_check
    )
