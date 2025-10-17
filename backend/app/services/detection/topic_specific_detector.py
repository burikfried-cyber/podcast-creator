"""
Topic-Specific Content Detector
8 specialist detectors with depth-adaptive content selection
Target: >85% user satisfaction
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.preferences import get_preference_model
from app.services.detection.topic_specialists import (
    HistoricalContentDetector,
    CulturalContentDetector,
    ArchitecturalContentDetector,
    NatureContentDetector,
    CulinaryContentDetector,
    ArtsContentDetector,
    ScientificContentDetector,
    FolkloreContentDetector
)

logger = structlog.get_logger()


class TopicSpecificDetector:
    """
    Topic-Specific Content Detection
    
    Specialists:
    1. History
    2. Culture
    3. Architecture
    4. Nature
    5. Food/Culinary
    6. Arts
    7. Science
    8. Folklore
    
    Depth Levels (0-5):
    0: Surface - Basic facts
    1: Light - Simple explanations
    2: Moderate - Detailed information
    3: Detailed - In-depth analysis
    4: Deep - Expert knowledge
    5: Academic - Scholarly depth
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.preference_model = get_preference_model(db)
        
        # Initialize specialists
        self.topic_specialists = {
            'history': HistoricalContentDetector(),
            'culture': CulturalContentDetector(),
            'architecture': ArchitecturalContentDetector(),
            'nature': NatureContentDetector(),
            'food': CulinaryContentDetector(),
            'arts': ArtsContentDetector(),
            'science': ScientificContentDetector(),
            'folklore': FolkloreContentDetector()
        }
    
    async def detect_topic_content(
        self,
        gathered_content: Dict[str, Any],
        topic: str,
        depth_level: int,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect topic-specific content with depth adaptation
        
        Args:
            gathered_content: API-gathered content
            topic: Topic category
            depth_level: Depth level (0-5)
            user_id: Optional user ID for personalization
            
        Returns:
            Topic-specific content with confidence score
        """
        try:
            logger.info("topic_detection_started",
                       topic=topic,
                       depth_level=depth_level)
            
            # Get specialist
            if topic not in self.topic_specialists:
                raise ValueError(f"Unknown topic: {topic}")
            
            specialist = self.topic_specialists[topic]
            
            # Extract topic-relevant content
            topic_content = await specialist.extract_content(
                gathered_content,
                depth_level
            )
            
            # Apply depth-appropriate filtering
            if depth_level >= 5:  # Expert/Academic
                filtered_content = await specialist.apply_expert_filter(topic_content)
            elif depth_level >= 3:  # Intermediate/Advanced
                filtered_content = await specialist.apply_intermediate_filter(topic_content)
            else:  # Surface/Basic
                filtered_content = await specialist.apply_basic_filter(topic_content)
            
            # Personalize if user provided
            if user_id:
                user_profile = await self._get_user_profile(user_id)
                personalized_content = await specialist.personalize_content(
                    filtered_content,
                    user_profile
                )
            else:
                personalized_content = filtered_content
            
            # Calculate confidence
            confidence_score = specialist.calculate_confidence(personalized_content)
            
            logger.info("topic_detection_complete",
                       topic=topic,
                       confidence=confidence_score)
            
            return {
                "success": True,
                "topic": topic,
                "depth_level": depth_level,
                "content": personalized_content,
                "confidence_score": confidence_score,
                "content_count": len(personalized_content.get("items", [])),
                "detected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("topic_detection_failed",
                        topic=topic,
                        error=str(e))
            raise
    
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile for personalization"""
        try:
            topic_prefs = await self.preference_model.get_topic_preferences(user_id)
            depth_pref = await self.preference_model.get_depth_preference(user_id)
            surprise_pref = await self.preference_model.get_surprise_preference(user_id)
            
            return {
                "topic_preferences": topic_prefs,
                "depth_preference": depth_pref,
                "surprise_preference": surprise_pref
            }
        except Exception as e:
            logger.error("user_profile_retrieval_failed",
                        user_id=user_id,
                        error=str(e))
            return {}


def get_topic_specific_detector(db: AsyncSession) -> TopicSpecificDetector:
    """Get topic-specific detector instance"""
    return TopicSpecificDetector(db)
