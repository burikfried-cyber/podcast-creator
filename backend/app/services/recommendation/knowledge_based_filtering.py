"""
Knowledge-Based Filtering
Expert system rules with user constraints for recommendations
"""
from typing import Dict, List, Any, Optional, Tuple
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.preferences import (
    UserDepthPreference,
    UserSurprisePreference,
    UserTopicPreference
)

logger = structlog.get_logger()


class KnowledgeBasedFilter:
    """
    Knowledge-Based Filtering using expert rules
    
    Features:
    - Hard constraint filtering
    - Soft preference scoring
    - Rule-based matching
    - User requirement satisfaction
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Expert rules for content matching
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[str, Any]:
        """Initialize expert rules"""
        return {
            "depth_matching": {
                "surface": {"max_duration": 15, "complexity": "low"},
                "light": {"max_duration": 30, "complexity": "low"},
                "moderate": {"max_duration": 45, "complexity": "medium"},
                "detailed": {"max_duration": 60, "complexity": "medium"},
                "deep": {"max_duration": 90, "complexity": "high"},
                "academic": {"max_duration": 120, "complexity": "high"}
            },
            "surprise_matching": {
                "predictable": {"novelty_threshold": 0.1, "topic_deviation": 0.0},
                "familiar": {"novelty_threshold": 0.3, "topic_deviation": 0.2},
                "balanced": {"novelty_threshold": 0.5, "topic_deviation": 0.4},
                "adventurous": {"novelty_threshold": 0.7, "topic_deviation": 0.6},
                "exploratory": {"novelty_threshold": 0.85, "topic_deviation": 0.8},
                "radical": {"novelty_threshold": 1.0, "topic_deviation": 1.0}
            },
            "quality_thresholds": {
                "min_source_authority": 0.6,
                "min_content_completeness": 0.7,
                "min_overall_quality": 0.65
            }
        }
    
    async def get_recommendations(
        self,
        user_id: str,
        candidate_items: List[Dict[str, Any]],
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get knowledge-based recommendations
        
        Args:
            user_id: User ID
            candidate_items: List of candidate items with metadata
            n_recommendations: Number of recommendations
            
        Returns:
            List of (item_id, score) tuples
        """
        try:
            # Get user preferences
            depth_pref = await self._get_depth_preference(user_id)
            surprise_pref = await self._get_surprise_preference(user_id)
            topic_prefs = await self._get_topic_preferences(user_id)
            
            # Score each candidate
            scores = []
            for item in candidate_items:
                score = self._score_item(
                    item,
                    depth_pref,
                    surprise_pref,
                    topic_prefs
                )
                
                if score > 0:  # Only include items that pass constraints
                    scores.append((item["id"], float(score)))
            
            # Sort by score
            scores.sort(key=lambda x: x[1], reverse=True)
            
            logger.info("knowledge_recommendations_generated",
                       user_id=user_id,
                       candidates=len(candidate_items),
                       passed=len(scores))
            
            return scores[:n_recommendations]
            
        except Exception as e:
            logger.error("knowledge_recommendations_failed",
                        user_id=user_id,
                        error=str(e))
            return []
    
    def _score_item(
        self,
        item: Dict[str, Any],
        depth_pref: Optional[Dict],
        surprise_pref: Optional[Dict],
        topic_prefs: Dict[str, float]
    ) -> float:
        """
        Score item based on knowledge rules
        
        Args:
            item: Item metadata
            depth_pref: User depth preference
            surprise_pref: User surprise preference
            topic_prefs: User topic preferences
            
        Returns:
            Score (0-1)
        """
        score = 0.0
        
        # Hard constraints (must pass)
        if not self._check_hard_constraints(item):
            return 0.0
        
        # Depth matching (30% weight)
        depth_score = self._score_depth_match(item, depth_pref)
        score += depth_score * 0.3
        
        # Surprise matching (20% weight)
        surprise_score = self._score_surprise_match(item, surprise_pref)
        score += surprise_score * 0.2
        
        # Topic matching (40% weight)
        topic_score = self._score_topic_match(item, topic_prefs)
        score += topic_score * 0.4
        
        # Quality bonus (10% weight)
        quality_score = self._score_quality(item)
        score += quality_score * 0.1
        
        return score
    
    def _check_hard_constraints(self, item: Dict[str, Any]) -> bool:
        """
        Check if item passes hard constraints
        
        Args:
            item: Item metadata
            
        Returns:
            True if passes all constraints
        """
        # Check minimum quality
        quality_thresholds = self.rules["quality_thresholds"]
        
        if "source_authority" in item:
            if item["source_authority"] < quality_thresholds["min_source_authority"]:
                return False
        
        if "content_completeness" in item:
            if item["content_completeness"] < quality_thresholds["min_content_completeness"]:
                return False
        
        if "overall_quality" in item:
            if item["overall_quality"] < quality_thresholds["min_overall_quality"]:
                return False
        
        return True
    
    def _score_depth_match(
        self,
        item: Dict[str, Any],
        depth_pref: Optional[Dict]
    ) -> float:
        """
        Score depth matching
        
        Args:
            item: Item metadata
            depth_pref: User depth preference
            
        Returns:
            Depth match score (0-1)
        """
        if not depth_pref or "depth_level" not in item:
            return 0.5  # Neutral score
        
        preferred_depth = depth_pref.get("preferred_depth", 2)
        item_depth = item["depth_level"]
        
        # Get depth rules
        depth_levels = ["surface", "light", "moderate", "detailed", "deep", "academic"]
        preferred_level_name = depth_levels[preferred_depth]
        depth_rules = self.rules["depth_matching"][preferred_level_name]
        
        # Check duration match
        duration_score = 1.0
        if "duration" in item:
            max_duration = depth_rules["max_duration"]
            if item["duration"] > max_duration * 1.5:
                duration_score = 0.5  # Penalty for too long
            elif item["duration"] > max_duration:
                duration_score = 0.8  # Slight penalty
        
        # Check complexity match
        complexity_score = 1.0
        if "complexity" in item:
            if item["complexity"] == depth_rules["complexity"]:
                complexity_score = 1.0
            else:
                complexity_score = 0.6
        
        # Distance penalty (prefer exact match or ±1 level)
        distance = abs(item_depth - preferred_depth)
        distance_score = max(0.0, 1.0 - (distance * 0.2))
        
        return (duration_score + complexity_score + distance_score) / 3.0
    
    def _score_surprise_match(
        self,
        item: Dict[str, Any],
        surprise_pref: Optional[Dict]
    ) -> float:
        """
        Score surprise matching
        
        Args:
            item: Item metadata
            surprise_pref: User surprise preference
            
        Returns:
            Surprise match score (0-1)
        """
        if not surprise_pref or "novelty_score" not in item:
            return 0.5  # Neutral score
        
        tolerance = surprise_pref.get("surprise_tolerance", 2)
        item_novelty = item["novelty_score"]
        
        # Get surprise rules
        surprise_levels = ["predictable", "familiar", "balanced", "adventurous", "exploratory", "radical"]
        tolerance_name = surprise_levels[tolerance]
        surprise_rules = self.rules["surprise_matching"][tolerance_name]
        
        # Check if novelty is within acceptable range
        threshold = surprise_rules["novelty_threshold"]
        
        if item_novelty <= threshold:
            # Within tolerance
            score = 1.0 - abs(item_novelty - threshold * 0.7) / threshold
        else:
            # Above tolerance - penalty
            score = max(0.0, 1.0 - (item_novelty - threshold))
        
        return max(0.0, min(1.0, score))
    
    def _score_topic_match(
        self,
        item: Dict[str, Any],
        topic_prefs: Dict[str, float]
    ) -> float:
        """
        Score topic matching
        
        Args:
            item: Item metadata
            topic_prefs: User topic preferences
            
        Returns:
            Topic match score (0-1)
        """
        if not topic_prefs or "topics" not in item:
            return 0.5  # Neutral score
        
        item_topics = item["topics"]
        if isinstance(item_topics, str):
            item_topics = [item_topics]
        
        # Calculate weighted match
        total_weight = 0.0
        matched_weight = 0.0
        
        for topic in item_topics:
            # Check if topic matches any preference
            for pref_topic, weight in topic_prefs.items():
                if topic in pref_topic or pref_topic in topic:
                    matched_weight += weight
                    total_weight += 1.0
                    break
        
        if total_weight == 0:
            return 0.3  # Low score for no topic match
        
        return min(1.0, matched_weight / total_weight)
    
    def _score_quality(self, item: Dict[str, Any]) -> float:
        """
        Score overall quality
        
        Args:
            item: Item metadata
            
        Returns:
            Quality score (0-1)
        """
        quality_scores = []
        
        if "source_authority" in item:
            quality_scores.append(item["source_authority"])
        
        if "content_completeness" in item:
            quality_scores.append(item["content_completeness"])
        
        if "overall_quality" in item:
            quality_scores.append(item["overall_quality"])
        
        if "engagement_score" in item:
            quality_scores.append(item["engagement_score"])
        
        if not quality_scores:
            return 0.7  # Default quality
        
        return sum(quality_scores) / len(quality_scores)
    
    async def _get_depth_preference(self, user_id: str) -> Optional[Dict]:
        """Get user depth preference"""
        result = await self.db.execute(
            select(UserDepthPreference).where(
                UserDepthPreference.user_id == user_id
            )
        )
        depth_pref = result.scalar_one_or_none()
        
        if depth_pref:
            return {
                "preferred_depth": depth_pref.preferred_depth,
                "confidence": float(depth_pref.confidence_score)
            }
        return None
    
    async def _get_surprise_preference(self, user_id: str) -> Optional[Dict]:
        """Get user surprise preference"""
        result = await self.db.execute(
            select(UserSurprisePreference).where(
                UserSurprisePreference.user_id == user_id
            )
        )
        surprise_pref = result.scalar_one_or_none()
        
        if surprise_pref:
            return {
                "surprise_tolerance": surprise_pref.surprise_tolerance,
                "confidence": float(surprise_pref.confidence_score)
            }
        return None
    
    async def _get_topic_preferences(self, user_id: str) -> Dict[str, float]:
        """Get user topic preferences"""
        result = await self.db.execute(
            select(UserTopicPreference).where(
                UserTopicPreference.user_id == user_id
            ).order_by(UserTopicPreference.preference_weight.desc()).limit(20)
        )
        topic_prefs = result.scalars().all()
        
        prefs = {}
        for pref in topic_prefs:
            key = f"{pref.topic_category}.{pref.subcategory}"
            prefs[key] = float(pref.preference_weight)
        
        return prefs
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            "n_rules": len(self.rules),
            "depth_levels": len(self.rules["depth_matching"]),
            "surprise_levels": len(self.rules["surprise_matching"]),
            "quality_thresholds": self.rules["quality_thresholds"]
        }


def get_knowledge_filter(db: AsyncSession) -> KnowledgeBasedFilter:
    """Get knowledge-based filter instance"""
    return KnowledgeBasedFilter(db)
