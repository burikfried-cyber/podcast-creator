"""
Real-time Adaptation Pipeline
Online learning and preference drift detection for dynamic user modeling
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from collections import deque
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.preferences import (
    UserLearningState,
    UserBehavioralSignal,
    UserTopicPreference
)
from app.services.preferences import get_preference_model
from app.services.learning import get_hmm_tracker, get_lstm_recognizer, get_bandit_selector

logger = structlog.get_logger()


class RealTimeAdapter:
    """
    Real-time Adaptation Pipeline
    
    Features:
    - Online gradient descent for preference updates
    - Exponential moving average with adaptive learning rate
    - Contextual adjustment with attention mechanism
    - Preference drift detection using ADWIN algorithm
    - Concept drift handling
    - Adaptive exploration rate
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.preference_model = get_preference_model(db)
        self.hmm_tracker = get_hmm_tracker(db)
        self.lstm_recognizer = get_lstm_recognizer(db)
        self.bandit_selector = get_bandit_selector(db)
        
        # Adaptation parameters
        self.base_learning_rate = 0.1
        self.min_learning_rate = 0.01
        self.max_learning_rate = 0.3
        self.momentum = 0.9
        
        # Drift detection parameters (ADWIN)
        self.drift_threshold = 0.002
        self.window_size = 100
        self.min_window_size = 30
        
        # Attention mechanism parameters
        self.attention_decay = 0.95
        self.recency_weight = 0.3
        
    async def process_interaction(
        self,
        user_id: str,
        interaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user interaction in real-time
        
        Args:
            user_id: User ID
            interaction: Interaction data (type, content_id, engagement, context)
            
        Returns:
            Processing results with adaptations
        """
        try:
            logger.info("processing_interaction",
                       user_id=user_id,
                       interaction_type=interaction.get("type"))
            
            # Extract interaction features
            engagement_score = interaction.get("engagement_score", 0.5)
            content_id = interaction.get("content_id")
            context = interaction.get("context", {})
            interaction_type = interaction.get("type", "view")
            
            # Update behavioral learning models
            learning_updates = await self._update_learning_models(
                user_id,
                interaction
            )
            
            # Detect preference drift
            drift_detected = await self._detect_drift(
                user_id,
                engagement_score
            )
            
            # Calculate adaptive learning rate
            learning_rate = await self._calculate_adaptive_learning_rate(
                user_id,
                drift_detected
            )
            
            # Update preferences with online gradient descent
            preference_updates = await self._update_preferences_online(
                user_id,
                interaction,
                learning_rate
            )
            
            # Apply contextual attention
            attention_weights = await self._apply_contextual_attention(
                user_id,
                context
            )
            
            # Adjust exploration rate
            exploration_update = await self._adjust_exploration_rate(
                user_id,
                engagement_score
            )
            
            logger.info("interaction_processed",
                       user_id=user_id,
                       drift_detected=drift_detected,
                       learning_rate=learning_rate)
            
            return {
                "success": True,
                "user_id": user_id,
                "learning_updates": learning_updates,
                "preference_updates": preference_updates,
                "drift_detected": drift_detected,
                "learning_rate": learning_rate,
                "attention_weights": attention_weights,
                "exploration_update": exploration_update
            }
            
        except Exception as e:
            logger.error("interaction_processing_failed",
                        user_id=user_id,
                        error=str(e))
            raise
    
    async def _update_learning_models(
        self,
        user_id: str,
        interaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update HMM, LSTM, and Bandit models
        
        Args:
            user_id: User ID
            interaction: Interaction data
            
        Returns:
            Update results
        """
        updates = {}
        
        # Update HMM with observation
        if "playback_behavior" in interaction:
            hmm_result = await self.hmm_tracker.update_hmm(
                user_id,
                interaction["playback_behavior"]
            )
            updates["hmm"] = hmm_result
        
        # Update LSTM with actual outcomes
        if "actual_engagement" in interaction:
            lstm_result = await self.lstm_recognizer.update_lstm(
                user_id,
                {"engagement_probability": interaction["actual_engagement"]}
            )
            updates["lstm"] = lstm_result
        
        # Update Bandit with reward
        if "content_id" in interaction and "engagement_score" in interaction:
            bandit_result = await self.bandit_selector.update_arm_reward(
                user_id,
                interaction["content_id"],
                interaction["engagement_score"],
                interaction.get("context", {})
            )
            updates["bandit"] = bandit_result
        
        return updates
    
    async def _detect_drift(
        self,
        user_id: str,
        current_engagement: float
    ) -> bool:
        """
        Detect preference drift using ADWIN algorithm
        
        Args:
            user_id: User ID
            current_engagement: Current engagement score
            
        Returns:
            True if drift detected
        """
        try:
            # Get learning state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                return False
            
            # Get drift detection state
            drift_state = learning_state.drift_detection_state or {
                "window": [],
                "mean": 0.5,
                "variance": 0.1,
                "drift_count": 0
            }
            
            # Add current engagement to window
            window = drift_state["window"]
            window.append(current_engagement)
            
            # Maintain window size
            if len(window) > self.window_size:
                window.pop(0)
            
            # Need minimum window size
            if len(window) < self.min_window_size:
                drift_state["window"] = window
                learning_state.drift_detection_state = drift_state
                await self.db.commit()
                return False
            
            # ADWIN: Split window and compare distributions
            drift_detected = False
            
            if len(window) >= self.min_window_size * 2:
                # Split window in half
                mid = len(window) // 2
                window1 = window[:mid]
                window2 = window[mid:]
                
                # Calculate means
                mean1 = np.mean(window1)
                mean2 = np.mean(window2)
                
                # Calculate difference
                diff = abs(mean1 - mean2)
                
                # Detect drift if difference exceeds threshold
                if diff > self.drift_threshold:
                    drift_detected = True
                    drift_state["drift_count"] += 1
                    
                    # Reset window on drift
                    drift_state["window"] = window[-self.min_window_size:]
                    drift_state["mean"] = mean2
                    
                    logger.warning("preference_drift_detected",
                                 user_id=user_id,
                                 diff=diff,
                                 drift_count=drift_state["drift_count"])
                else:
                    drift_state["mean"] = np.mean(window)
                    drift_state["window"] = window
            
            # Update state
            learning_state.drift_detection_state = drift_state
            await self.db.commit()
            
            return drift_detected
            
        except Exception as e:
            logger.error("drift_detection_failed", user_id=user_id, error=str(e))
            return False
    
    async def _calculate_adaptive_learning_rate(
        self,
        user_id: str,
        drift_detected: bool
    ) -> float:
        """
        Calculate adaptive learning rate
        
        Args:
            user_id: User ID
            drift_detected: Whether drift was detected
            
        Returns:
            Adaptive learning rate
        """
        try:
            # Get learning state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                return self.base_learning_rate
            
            # Get adaptation state
            adaptation_state = learning_state.adaptation_state or {
                "learning_rate": self.base_learning_rate,
                "gradient_history": [],
                "update_count": 0
            }
            
            # Increase learning rate on drift
            if drift_detected:
                learning_rate = min(
                    self.max_learning_rate,
                    adaptation_state["learning_rate"] * 1.5
                )
            else:
                # Decay learning rate over time
                update_count = adaptation_state["update_count"]
                decay_factor = 1.0 / (1.0 + 0.001 * update_count)
                learning_rate = max(
                    self.min_learning_rate,
                    self.base_learning_rate * decay_factor
                )
            
            # Update state
            adaptation_state["learning_rate"] = learning_rate
            adaptation_state["update_count"] += 1
            learning_state.adaptation_state = adaptation_state
            
            await self.db.commit()
            
            return learning_rate
            
        except Exception as e:
            logger.error("learning_rate_calculation_failed",
                        user_id=user_id,
                        error=str(e))
            return self.base_learning_rate
    
    async def _update_preferences_online(
        self,
        user_id: str,
        interaction: Dict[str, Any],
        learning_rate: float
    ) -> Dict[str, Any]:
        """
        Update preferences using online gradient descent
        
        Args:
            user_id: User ID
            interaction: Interaction data
            learning_rate: Adaptive learning rate
            
        Returns:
            Update results
        """
        updates = {}
        
        # Extract signals
        engagement = interaction.get("engagement_score", 0.5)
        content_topics = interaction.get("topics", [])
        content_depth = interaction.get("depth_level", 2)
        content_novelty = interaction.get("novelty_score", 0.5)
        
        # Update topic preferences
        if content_topics:
            topic_signals = {topic: engagement for topic in content_topics}
            topic_result = await self.preference_model.update_topic_preferences(
                user_id,
                topic_signals,
                learning_rate=learning_rate
            )
            updates["topics"] = topic_result
        
        # Update depth preference
        depth_result = await self.preference_model.update_depth_preference(
            user_id,
            content_depth,
            satisfaction_score=engagement
        )
        updates["depth"] = depth_result
        
        # Update surprise preference
        surprise_result = await self.preference_model.update_surprise_preference(
            user_id,
            int(content_novelty * 5),  # Convert to 0-5 scale
            reward=engagement
        )
        updates["surprise"] = surprise_result
        
        return updates
    
    async def _apply_contextual_attention(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Apply attention mechanism to weight recent contexts
        
        Args:
            user_id: User ID
            context: Current context
            
        Returns:
            Attention weights for different contexts
        """
        try:
            # Get recent behavioral signals
            result = await self.db.execute(
                select(UserBehavioralSignal).where(
                    UserBehavioralSignal.user_id == user_id
                ).order_by(UserBehavioralSignal.created_at.desc()).limit(50)
            )
            recent_signals = result.scalars().all()
            
            if not recent_signals:
                return {"current": 1.0}
            
            # Calculate attention weights based on recency and similarity
            attention_weights = {}
            current_time = datetime.utcnow()
            
            for signal in recent_signals:
                # Time decay
                time_diff = (current_time - signal.created_at).total_seconds()
                time_weight = np.exp(-time_diff / 3600)  # Decay over hours
                
                # Context similarity
                signal_context = signal.context or {}
                similarity = self._calculate_context_similarity(
                    context,
                    signal_context
                )
                
                # Combined attention weight
                attention = time_weight * similarity
                
                # Aggregate by context type
                context_key = signal_context.get("time_of_day", "unknown")
                if context_key not in attention_weights:
                    attention_weights[context_key] = 0.0
                attention_weights[context_key] += attention
            
            # Normalize weights
            total = sum(attention_weights.values())
            if total > 0:
                attention_weights = {
                    k: v / total for k, v in attention_weights.items()
                }
            
            # Add current context with recency boost
            current_context_key = context.get("time_of_day", "current")
            attention_weights[current_context_key] = attention_weights.get(
                current_context_key, 0.0
            ) + self.recency_weight
            
            # Re-normalize
            total = sum(attention_weights.values())
            if total > 0:
                attention_weights = {
                    k: v / total for k, v in attention_weights.items()
                }
            
            return attention_weights
            
        except Exception as e:
            logger.error("attention_calculation_failed",
                        user_id=user_id,
                        error=str(e))
            return {"current": 1.0}
    
    def _calculate_context_similarity(
        self,
        context1: Dict[str, Any],
        context2: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity between two contexts
        
        Args:
            context1: First context
            context2: Second context
            
        Returns:
            Similarity score (0-1)
        """
        similarity = 0.0
        n_features = 0
        
        # Compare time of day
        if "time_of_day" in context1 and "time_of_day" in context2:
            similarity += 1.0 if context1["time_of_day"] == context2["time_of_day"] else 0.0
            n_features += 1
        
        # Compare device
        if "device" in context1 and "device" in context2:
            similarity += 1.0 if context1["device"] == context2["device"] else 0.0
            n_features += 1
        
        # Compare location
        if "location" in context1 and "location" in context2:
            similarity += 1.0 if context1["location"] == context2["location"] else 0.0
            n_features += 1
        
        return similarity / n_features if n_features > 0 else 0.5
    
    async def _adjust_exploration_rate(
        self,
        user_id: str,
        engagement_score: float
    ) -> Dict[str, Any]:
        """
        Adjust exploration rate based on engagement
        
        Args:
            user_id: User ID
            engagement_score: Current engagement score
            
        Returns:
            Exploration rate update
        """
        try:
            # Get learning state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                return {}
            
            # Get current exploration rate from bandit state
            bandit_data = learning_state.bandit_arms_data or {}
            current_epsilon = bandit_data.get("exploration_rate", 0.2)
            
            # Adjust based on engagement
            if engagement_score > 0.7:
                # High engagement: reduce exploration (exploit more)
                new_epsilon = max(0.05, current_epsilon * 0.95)
            elif engagement_score < 0.3:
                # Low engagement: increase exploration
                new_epsilon = min(0.4, current_epsilon * 1.1)
            else:
                # Moderate engagement: gradual decay
                new_epsilon = max(0.1, current_epsilon * 0.98)
            
            # Update bandit state
            bandit_data["exploration_rate"] = new_epsilon
            learning_state.bandit_arms_data = bandit_data
            
            await self.db.commit()
            
            return {
                "old_epsilon": current_epsilon,
                "new_epsilon": new_epsilon,
                "adjustment": "decrease" if new_epsilon < current_epsilon else "increase"
            }
            
        except Exception as e:
            logger.error("exploration_adjustment_failed",
                        user_id=user_id,
                        error=str(e))
            return {}
    
    async def get_adaptation_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get adaptation statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Adaptation statistics
        """
        try:
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                return {"initialized": False}
            
            drift_state = learning_state.drift_detection_state or {}
            adaptation_state = learning_state.adaptation_state or {}
            
            return {
                "initialized": True,
                "drift_detection": {
                    "window_size": len(drift_state.get("window", [])),
                    "current_mean": drift_state.get("mean", 0.5),
                    "drift_count": drift_state.get("drift_count", 0)
                },
                "adaptation": {
                    "learning_rate": adaptation_state.get("learning_rate", self.base_learning_rate),
                    "update_count": adaptation_state.get("update_count", 0)
                },
                "exploration": {
                    "epsilon": learning_state.bandit_arms_data.get("exploration_rate", 0.2) if learning_state.bandit_arms_data else 0.2
                }
            }
            
        except Exception as e:
            logger.error("get_adaptation_stats_failed",
                        user_id=user_id,
                        error=str(e))
            return {"error": str(e)}


def get_real_time_adapter(db: AsyncSession) -> RealTimeAdapter:
    """Get real-time adapter instance"""
    return RealTimeAdapter(db)
