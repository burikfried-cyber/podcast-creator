"""
User Preference Model
Multi-dimensional user profiling with exponential moving average updates
"""
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.preferences import (
    UserTopicPreference,
    UserDepthPreference,
    UserSurprisePreference,
    UserContextualPreference
)

logger = structlog.get_logger()


class UserPreferenceModel:
    """
    Multi-dimensional user preference model
    Handles topic, depth, surprise, and contextual preferences
    """
    
    # Topic categories (10 primary × 12 subcategories each = 120 total)
    TOPIC_CATEGORIES = {
        "history": ["ancient", "medieval", "modern", "military", "cultural", "political", 
                   "economic", "social", "biographical", "archaeological", "regional", "thematic"],
        "science": ["physics", "chemistry", "biology", "astronomy", "earth_science", "mathematics",
                   "computer_science", "engineering", "medicine", "psychology", "neuroscience", "ecology"],
        "technology": ["ai_ml", "software", "hardware", "internet", "mobile", "cybersecurity",
                      "blockchain", "robotics", "space_tech", "biotech", "cleantech", "emerging"],
        "arts": ["visual", "music", "literature", "theater", "film", "dance",
                "architecture", "photography", "design", "crafts", "performance", "digital"],
        "philosophy": ["ethics", "metaphysics", "epistemology", "logic", "aesthetics", "political",
                      "existentialism", "phenomenology", "pragmatism", "eastern", "modern", "applied"],
        "business": ["entrepreneurship", "finance", "marketing", "management", "economics", "strategy",
                    "innovation", "leadership", "operations", "analytics", "startups", "corporate"],
        "culture": ["anthropology", "sociology", "linguistics", "mythology", "folklore", "traditions",
                   "customs", "festivals", "cuisine", "fashion", "pop_culture", "subcultures"],
        "nature": ["wildlife", "conservation", "climate", "geography", "oceanography", "forestry",
                  "biodiversity", "ecosystems", "natural_disasters", "geology", "meteorology", "sustainability"],
        "society": ["politics", "law", "education", "healthcare", "urban_planning", "social_issues",
                   "human_rights", "inequality", "demographics", "community", "activism", "policy"],
        "personal": ["psychology", "relationships", "productivity", "wellness", "spirituality", "mindfulness",
                    "career", "finance", "hobbies", "travel", "food", "lifestyle"]
    }
    
    # Depth levels (0-5)
    DEPTH_LEVELS = {
        0: "surface",      # Quick overview, headlines
        1: "light",        # Basic explanation, accessible
        2: "moderate",     # Standard depth, some detail
        3: "detailed",     # In-depth analysis, comprehensive
        4: "deep",         # Expert-level, technical
        5: "academic"      # Research-level, scholarly
    }
    
    # Surprise levels (0-5)
    SURPRISE_LEVELS = {
        0: "predictable",  # Familiar topics, expected content
        1: "familiar",     # Known areas, slight variation
        2: "balanced",     # Mix of familiar and new
        3: "adventurous",  # New topics, different perspectives
        4: "exploratory",  # Unusual combinations, creative
        5: "radical"       # Completely unexpected, challenging
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alpha = 0.1  # Exponential moving average weight for new observations
        self.decay = 0.95  # Decay factor for old preferences
    
    async def initialize_user_preferences(
        self,
        user_id: str,
        initial_topics: Optional[Dict[str, float]] = None,
        initial_depth: int = 2,
        initial_surprise: int = 2
    ) -> Dict[str, Any]:
        """
        Initialize preferences for a new user
        
        Args:
            user_id: User ID
            initial_topics: Initial topic preferences (optional)
            initial_depth: Initial depth preference (0-5)
            initial_surprise: Initial surprise tolerance (0-5)
            
        Returns:
            Initialization status
        """
        try:
            # Initialize topic preferences
            if initial_topics:
                for category, subcategories in self.TOPIC_CATEGORIES.items():
                    for subcategory in subcategories:
                        key = f"{category}.{subcategory}"
                        weight = initial_topics.get(key, 0.5)
                        
                        topic_pref = UserTopicPreference(
                            user_id=user_id,
                            topic_category=category,
                            subcategory=subcategory,
                            preference_weight=Decimal(str(weight)),
                            confidence_score=Decimal("0.30")  # Low initial confidence
                        )
                        self.db.add(topic_pref)
            
            # Initialize depth preference
            depth_pref = UserDepthPreference(
                user_id=user_id,
                preferred_depth=initial_depth,
                confidence_score=Decimal("0.30")
            )
            self.db.add(depth_pref)
            
            # Initialize surprise preference
            surprise_pref = UserSurprisePreference(
                user_id=user_id,
                surprise_tolerance=initial_surprise,
                q_values={str(i): 0.0 for i in range(6)},  # Initialize Q-values
                confidence_score=Decimal("0.30")
            )
            self.db.add(surprise_pref)
            
            await self.db.commit()
            
            logger.info("user_preferences_initialized", user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "topics_initialized": len(initial_topics) if initial_topics else 0,
                "depth": initial_depth,
                "surprise": initial_surprise
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("preference_initialization_failed", user_id=user_id, error=str(e))
            raise
    
    async def update_topic_preferences(
        self,
        user_id: str,
        topic_signals: Dict[str, float],
        learning_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update topic preferences using exponential moving average
        
        Args:
            user_id: User ID
            topic_signals: Dict of topic -> signal strength (0-1)
            learning_rate: Optional custom learning rate
            
        Returns:
            Update statistics
        """
        alpha = learning_rate or self.alpha
        updated_count = 0
        
        try:
            for topic_key, signal in topic_signals.items():
                if "." not in topic_key:
                    continue
                
                category, subcategory = topic_key.split(".", 1)
                
                # Get existing preference
                result = await self.db.execute(
                    select(UserTopicPreference).where(
                        and_(
                            UserTopicPreference.user_id == user_id,
                            UserTopicPreference.topic_category == category,
                            UserTopicPreference.subcategory == subcategory
                        )
                    )
                )
                pref = result.scalar_one_or_none()
                
                if pref:
                    # Exponential moving average update
                    old_weight = float(pref.preference_weight)
                    new_weight = alpha * signal + (1 - alpha) * old_weight
                    
                    # Update confidence based on interaction count
                    interaction_count = pref.interaction_count + 1
                    confidence = min(0.95, 0.3 + (interaction_count * 0.05))
                    
                    pref.preference_weight = Decimal(str(round(new_weight, 3)))
                    pref.confidence_score = Decimal(str(round(confidence, 2)))
                    pref.interaction_count = interaction_count
                    pref.last_interaction = datetime.utcnow()
                    pref.updated_at = datetime.utcnow()
                    
                    updated_count += 1
                else:
                    # Create new preference
                    pref = UserTopicPreference(
                        user_id=user_id,
                        topic_category=category,
                        subcategory=subcategory,
                        preference_weight=Decimal(str(signal)),
                        confidence_score=Decimal("0.30"),
                        interaction_count=1,
                        last_interaction=datetime.utcnow()
                    )
                    self.db.add(pref)
                    updated_count += 1
            
            await self.db.commit()
            
            logger.info("topic_preferences_updated", 
                       user_id=user_id, 
                       updated_count=updated_count)
            
            return {
                "success": True,
                "updated_count": updated_count,
                "learning_rate": alpha
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("topic_update_failed", user_id=user_id, error=str(e))
            raise
    
    async def update_depth_preference(
        self,
        user_id: str,
        observed_depth: int,
        satisfaction_score: float
    ) -> Dict[str, Any]:
        """
        Update depth preference using Bayesian optimization
        
        Args:
            user_id: User ID
            observed_depth: Depth level that was consumed (0-5)
            satisfaction_score: User satisfaction (0-1)
            
        Returns:
            Update statistics
        """
        try:
            result = await self.db.execute(
                select(UserDepthPreference).where(
                    UserDepthPreference.user_id == user_id
                )
            )
            depth_pref = result.scalar_one_or_none()
            
            if not depth_pref:
                # Initialize if doesn't exist
                depth_pref = UserDepthPreference(
                    user_id=user_id,
                    preferred_depth=observed_depth
                )
                self.db.add(depth_pref)
            
            # Bayesian update: Beta distribution
            # Success if satisfaction > 0.6
            if satisfaction_score > 0.6:
                depth_pref.alpha_prior = float(depth_pref.alpha_prior) + satisfaction_score
            else:
                depth_pref.beta_prior = float(depth_pref.beta_prior) + (1 - satisfaction_score)
            
            # Update weights using Beta distribution mean
            total = float(depth_pref.alpha_prior) + float(depth_pref.beta_prior)
            success_rate = float(depth_pref.alpha_prior) / total
            
            # Adjust weights based on observed depth and satisfaction
            weights = [0.167] * 6
            weights[observed_depth] = weights[observed_depth] * (1 + satisfaction_score)
            
            # Normalize
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            
            depth_pref.surface_weight = Decimal(str(round(weights[0], 3)))
            depth_pref.light_weight = Decimal(str(round(weights[1], 3)))
            depth_pref.moderate_weight = Decimal(str(round(weights[2], 3)))
            depth_pref.detailed_weight = Decimal(str(round(weights[3], 3)))
            depth_pref.deep_weight = Decimal(str(round(weights[4], 3)))
            depth_pref.academic_weight = Decimal(str(round(weights[5], 3)))
            
            # Update preferred depth (highest weight)
            depth_pref.preferred_depth = weights.index(max(weights))
            depth_pref.confidence_score = Decimal(str(round(success_rate, 2)))
            depth_pref.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info("depth_preference_updated",
                       user_id=user_id,
                       preferred_depth=depth_pref.preferred_depth,
                       confidence=float(depth_pref.confidence_score))
            
            return {
                "success": True,
                "preferred_depth": depth_pref.preferred_depth,
                "confidence": float(depth_pref.confidence_score),
                "weights": weights
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("depth_update_failed", user_id=user_id, error=str(e))
            raise
    
    async def update_surprise_preference(
        self,
        user_id: str,
        surprise_level: int,
        reward: float
    ) -> Dict[str, Any]:
        """
        Update surprise preference using reinforcement learning (Q-learning)
        
        Args:
            user_id: User ID
            surprise_level: Surprise level experienced (0-5)
            reward: Reward signal (0-1)
            
        Returns:
            Update statistics
        """
        try:
            result = await self.db.execute(
                select(UserSurprisePreference).where(
                    UserSurprisePreference.user_id == user_id
                )
            )
            surprise_pref = result.scalar_one_or_none()
            
            if not surprise_pref:
                # Initialize if doesn't exist
                surprise_pref = UserSurprisePreference(
                    user_id=user_id,
                    surprise_tolerance=surprise_level,
                    q_values={str(i): 0.0 for i in range(6)}
                )
                self.db.add(surprise_pref)
            
            # Q-learning update
            learning_rate = float(surprise_pref.learning_rate)
            q_values = surprise_pref.q_values
            
            # Current Q-value
            current_q = q_values.get(str(surprise_level), 0.0)
            
            # Update Q-value: Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
            # Simplified: Q(s,a) = Q(s,a) + α[r - Q(s,a)]
            new_q = current_q + learning_rate * (reward - current_q)
            q_values[str(surprise_level)] = round(new_q, 4)
            
            surprise_pref.q_values = q_values
            
            # Update surprise tolerance (select action with highest Q-value)
            best_level = max(range(6), key=lambda x: q_values.get(str(x), 0.0))
            surprise_pref.surprise_tolerance = best_level
            
            # Decay exploration rate
            exploration_rate = float(surprise_pref.exploration_rate)
            new_exploration = max(0.1, exploration_rate * 0.95)  # Decay with minimum
            surprise_pref.exploration_rate = Decimal(str(round(new_exploration, 2)))
            
            # Update confidence
            max_q = max(q_values.values())
            min_q = min(q_values.values())
            confidence = (max_q - min_q) / (max_q + 0.001) if max_q > 0 else 0.5
            surprise_pref.confidence_score = Decimal(str(round(confidence, 2)))
            
            surprise_pref.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info("surprise_preference_updated",
                       user_id=user_id,
                       surprise_tolerance=best_level,
                       exploration_rate=new_exploration)
            
            return {
                "success": True,
                "surprise_tolerance": best_level,
                "exploration_rate": new_exploration,
                "q_values": q_values
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("surprise_update_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get complete user preference profile
        
        Args:
            user_id: User ID
            
        Returns:
            Complete preference profile
        """
        try:
            # Get topic preferences
            topic_result = await self.db.execute(
                select(UserTopicPreference).where(
                    UserTopicPreference.user_id == user_id
                ).order_by(UserTopicPreference.preference_weight.desc())
            )
            topics = topic_result.scalars().all()
            
            # Get depth preference
            depth_result = await self.db.execute(
                select(UserDepthPreference).where(
                    UserDepthPreference.user_id == user_id
                )
            )
            depth = depth_result.scalar_one_or_none()
            
            # Get surprise preference
            surprise_result = await self.db.execute(
                select(UserSurprisePreference).where(
                    UserSurprisePreference.user_id == user_id
                )
            )
            surprise = surprise_result.scalar_one_or_none()
            
            # Format topic preferences
            topic_prefs = {}
            for topic in topics:
                key = f"{topic.topic_category}.{topic.subcategory}"
                topic_prefs[key] = {
                    "weight": float(topic.preference_weight),
                    "confidence": float(topic.confidence_score),
                    "interactions": topic.interaction_count
                }
            
            # Get top topics
            top_topics = sorted(
                topic_prefs.items(),
                key=lambda x: x[1]["weight"],
                reverse=True
            )[:20]
            
            return {
                "user_id": user_id,
                "topics": {
                    "all": topic_prefs,
                    "top_20": dict(top_topics),
                    "count": len(topic_prefs)
                },
                "depth": {
                    "preferred_level": depth.preferred_depth if depth else 2,
                    "level_name": self.DEPTH_LEVELS.get(depth.preferred_depth if depth else 2),
                    "confidence": float(depth.confidence_score) if depth else 0.5,
                    "weights": {
                        "surface": float(depth.surface_weight) if depth else 0.167,
                        "light": float(depth.light_weight) if depth else 0.167,
                        "moderate": float(depth.moderate_weight) if depth else 0.167,
                        "detailed": float(depth.detailed_weight) if depth else 0.167,
                        "deep": float(depth.deep_weight) if depth else 0.167,
                        "academic": float(depth.academic_weight) if depth else 0.165
                    }
                } if depth else None,
                "surprise": {
                    "tolerance_level": surprise.surprise_tolerance if surprise else 2,
                    "level_name": self.SURPRISE_LEVELS.get(surprise.surprise_tolerance if surprise else 2),
                    "confidence": float(surprise.confidence_score) if surprise else 0.5,
                    "exploration_rate": float(surprise.exploration_rate) if surprise else 0.4,
                    "q_values": surprise.q_values if surprise else {}
                } if surprise else None
            }
            
        except Exception as e:
            logger.error("get_preferences_failed", user_id=user_id, error=str(e))
            raise


# Global instance (will be initialized with db session)
def get_preference_model(db: AsyncSession) -> UserPreferenceModel:
    """Get preference model instance with database session"""
    return UserPreferenceModel(db)
