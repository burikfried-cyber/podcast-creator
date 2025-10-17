"""
Multi-Armed Contextual Bandits
Context-aware content selection with online learning
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from decimal import Decimal
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.preferences import UserContextualPreference, UserLearningState

logger = structlog.get_logger()


class ContextualBanditSelector:
    """
    Multi-Armed Contextual Bandit for content selection
    
    Context dimensions:
    - time_of_day (morning, afternoon, evening, night)
    - day_of_week (weekday, weekend)
    - device_type (mobile, desktop, tablet)
    - location_context (home, work, commute, other)
    - mood_indicators (relaxed, focused, energetic, tired)
    
    Arms: Different content types and sources
    Strategy: Upper Confidence Bound (UCB) with contextual information
    """
    
    # Context types
    CONTEXT_TYPES = {
        "time_of_day": ["morning", "afternoon", "evening", "night"],
        "day_of_week": ["weekday", "weekend"],
        "device_type": ["mobile", "desktop", "tablet"],
        "location_context": ["home", "work", "commute", "other"],
        "mood": ["relaxed", "focused", "energetic", "tired"]
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.exploration_constant = 2.0  # UCB exploration parameter
        self.learning_rate = 0.1
    
    async def initialize_bandits(self, user_id: str) -> Dict[str, Any]:
        """
        Initialize contextual bandits for a new user
        
        Args:
            user_id: User ID
            
        Returns:
            Initialization status
        """
        try:
            # Initialize bandit data in learning state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                learning_state = UserLearningState(user_id=user_id)
                self.db.add(learning_state)
            
            # Initialize bandit arms data
            bandit_data = {
                "arms": {},  # arm_id -> {pulls, rewards, ucb}
                "total_pulls": 0,
                "context_history": [],
                "model_version": "1.0"
            }
            
            learning_state.bandit_arms_data = bandit_data
            learning_state.updated_at = datetime.utcnow()
            
            # Initialize contextual preferences for common contexts
            for context_type, values in self.CONTEXT_TYPES.items():
                for value in values:
                    # Check if exists
                    existing = await self.db.execute(
                        select(UserContextualPreference).where(
                            and_(
                                UserContextualPreference.user_id == user_id,
                                UserContextualPreference.context_type == context_type,
                                UserContextualPreference.context_value == value
                            )
                        )
                    )
                    if not existing.scalar_one_or_none():
                        context_pref = UserContextualPreference(
                            user_id=user_id,
                            context_type=context_type,
                            context_value=value,
                            topic_adjustments={},
                            depth_adjustment=0,
                            surprise_adjustment=0,
                            arm_pulls=0,
                            total_reward=Decimal("0.0")
                        )
                        self.db.add(context_pref)
            
            await self.db.commit()
            
            logger.info("bandits_initialized", user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "contexts_initialized": sum(len(v) for v in self.CONTEXT_TYPES.values())
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("bandit_initialization_failed", user_id=user_id, error=str(e))
            raise
    
    async def select_arm(
        self,
        user_id: str,
        context: Dict[str, str],
        available_arms: List[str]
    ) -> Dict[str, Any]:
        """
        Select best arm (content) given context using UCB
        
        Args:
            user_id: User ID
            context: Current context (time_of_day, device, etc.)
            available_arms: List of available content IDs
            
        Returns:
            Selected arm and selection info
        """
        try:
            # Get bandit state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state or not learning_state.bandit_arms_data:
                # Initialize if doesn't exist
                await self.initialize_bandits(user_id)
                result = await self.db.execute(
                    select(UserLearningState).where(
                        UserLearningState.user_id == user_id
                    )
                )
                learning_state = result.scalar_one()
            
            bandit_data = learning_state.bandit_arms_data
            arms_info = bandit_data["arms"]
            total_pulls = bandit_data["total_pulls"]
            
            # Calculate UCB scores for each arm
            ucb_scores = {}
            for arm_id in available_arms:
                if arm_id not in arms_info:
                    # New arm: give high exploration bonus
                    ucb_scores[arm_id] = float('inf')
                else:
                    arm_data = arms_info[arm_id]
                    pulls = arm_data["pulls"]
                    rewards = arm_data["rewards"]
                    
                    if pulls == 0:
                        ucb_scores[arm_id] = float('inf')
                    else:
                        # UCB formula: mean_reward + exploration_bonus
                        mean_reward = rewards / pulls
                        exploration_bonus = self.exploration_constant * np.sqrt(
                            np.log(total_pulls + 1) / pulls
                        )
                        ucb_scores[arm_id] = mean_reward + exploration_bonus
            
            # Apply contextual adjustments
            contextual_scores = await self._apply_contextual_adjustments(
                user_id,
                context,
                ucb_scores
            )
            
            # Select arm with highest score
            selected_arm = max(contextual_scores.items(), key=lambda x: x[1])[0]
            
            logger.info("arm_selected",
                       user_id=user_id,
                       arm=selected_arm,
                       score=contextual_scores[selected_arm])
            
            return {
                "success": True,
                "selected_arm": selected_arm,
                "ucb_score": contextual_scores[selected_arm],
                "context": context,
                "exploration_rate": self._calculate_exploration_rate(total_pulls)
            }
            
        except Exception as e:
            logger.error("arm_selection_failed", user_id=user_id, error=str(e))
            raise
    
    async def update_arm_reward(
        self,
        user_id: str,
        arm_id: str,
        reward: float,
        context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update arm with observed reward (online learning)
        
        Args:
            user_id: User ID
            arm_id: Selected arm ID
            reward: Observed reward (0-1)
            context: Context when arm was selected
            
        Returns:
            Update status
        """
        try:
            # Get bandit state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                return {"success": False, "error": "Bandit not initialized"}
            
            bandit_data = learning_state.bandit_arms_data
            arms_info = bandit_data["arms"]
            
            # Update arm data
            if arm_id not in arms_info:
                arms_info[arm_id] = {
                    "pulls": 0,
                    "rewards": 0.0,
                    "ucb": 0.0
                }
            
            arms_info[arm_id]["pulls"] += 1
            arms_info[arm_id]["rewards"] += reward
            bandit_data["total_pulls"] += 1
            
            # Calculate new UCB
            pulls = arms_info[arm_id]["pulls"]
            total_rewards = arms_info[arm_id]["rewards"]
            mean_reward = total_rewards / pulls
            exploration_bonus = self.exploration_constant * np.sqrt(
                np.log(bandit_data["total_pulls"]) / pulls
            )
            arms_info[arm_id]["ucb"] = mean_reward + exploration_bonus
            
            # Add to context history
            bandit_data["context_history"].append({
                "arm_id": arm_id,
                "reward": reward,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            })
            bandit_data["context_history"] = bandit_data["context_history"][-100:]
            
            # Update contextual preferences
            await self._update_contextual_preferences(user_id, context, reward)
            
            # Calculate regret (difference from optimal)
            regret = self._calculate_regret(arms_info, bandit_data["total_pulls"])
            learning_state.bandit_regret = Decimal(str(round(regret, 4)))
            
            learning_state.bandit_arms_data = bandit_data
            learning_state.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info("arm_reward_updated",
                       user_id=user_id,
                       arm=arm_id,
                       reward=reward,
                       mean_reward=mean_reward)
            
            return {
                "success": True,
                "arm_id": arm_id,
                "pulls": pulls,
                "mean_reward": mean_reward,
                "ucb_score": arms_info[arm_id]["ucb"],
                "regret": regret
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("arm_update_failed", user_id=user_id, error=str(e))
            raise
    
    async def _apply_contextual_adjustments(
        self,
        user_id: str,
        context: Dict[str, str],
        base_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply contextual adjustments to base UCB scores
        
        Args:
            user_id: User ID
            context: Current context
            base_scores: Base UCB scores
            
        Returns:
            Adjusted scores
        """
        adjusted_scores = base_scores.copy()
        
        # Get contextual preferences
        for context_type, context_value in context.items():
            result = await self.db.execute(
                select(UserContextualPreference).where(
                    and_(
                        UserContextualPreference.user_id == user_id,
                        UserContextualPreference.context_type == context_type,
                        UserContextualPreference.context_value == context_value
                    )
                )
            )
            context_pref = result.scalar_one_or_none()
            
            if context_pref and context_pref.arm_pulls > 0:
                # Apply learned contextual adjustment
                mean_reward = float(context_pref.total_reward) / context_pref.arm_pulls
                adjustment_factor = 1.0 + (mean_reward - 0.5) * 0.2  # ±10% adjustment
                
                for arm_id in adjusted_scores:
                    adjusted_scores[arm_id] *= adjustment_factor
        
        return adjusted_scores
    
    async def _update_contextual_preferences(
        self,
        user_id: str,
        context: Dict[str, str],
        reward: float
    ) -> None:
        """
        Update contextual preferences based on reward
        
        Args:
            user_id: User ID
            context: Context information
            reward: Observed reward
        """
        for context_type, context_value in context.items():
            result = await self.db.execute(
                select(UserContextualPreference).where(
                    and_(
                        UserContextualPreference.user_id == user_id,
                        UserContextualPreference.context_type == context_type,
                        UserContextualPreference.context_value == context_value
                    )
                )
            )
            context_pref = result.scalar_one_or_none()
            
            if context_pref:
                context_pref.arm_pulls += 1
                context_pref.total_reward = float(context_pref.total_reward) + reward
                
                # Update UCB score
                mean_reward = float(context_pref.total_reward) / context_pref.arm_pulls
                context_pref.ucb_score = Decimal(str(round(mean_reward, 4)))
                context_pref.updated_at = datetime.utcnow()
    
    def _calculate_regret(self, arms_info: Dict, total_pulls: int) -> float:
        """
        Calculate cumulative regret
        
        Args:
            arms_info: Arms information
            total_pulls: Total number of pulls
            
        Returns:
            Cumulative regret
        """
        if not arms_info or total_pulls == 0:
            return 0.0
        
        # Find best arm (highest mean reward)
        best_mean_reward = 0.0
        for arm_data in arms_info.values():
            if arm_data["pulls"] > 0:
                mean_reward = arm_data["rewards"] / arm_data["pulls"]
                best_mean_reward = max(best_mean_reward, mean_reward)
        
        # Calculate regret: difference between optimal and actual
        actual_mean_reward = sum(
            arm_data["rewards"] for arm_data in arms_info.values()
        ) / total_pulls if total_pulls > 0 else 0.0
        
        regret = (best_mean_reward - actual_mean_reward) * total_pulls
        
        return max(0.0, regret)
    
    def _calculate_exploration_rate(self, total_pulls: int) -> float:
        """
        Calculate current exploration rate (decays over time)
        
        Args:
            total_pulls: Total number of pulls
            
        Returns:
            Exploration rate
        """
        # Decay exploration rate: starts at 0.4, decays to 0.1
        initial_rate = 0.4
        min_rate = 0.1
        decay_factor = 0.05
        
        rate = initial_rate * np.exp(-decay_factor * total_pulls / 100)
        return max(min_rate, rate)
    
    async def get_bandit_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get bandit statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Bandit statistics
        """
        try:
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state or not learning_state.bandit_arms_data:
                return {
                    "initialized": False,
                    "total_pulls": 0,
                    "arms_count": 0
                }
            
            bandit_data = learning_state.bandit_arms_data
            arms_info = bandit_data["arms"]
            
            # Calculate statistics
            best_arm = None
            best_reward = 0.0
            for arm_id, arm_data in arms_info.items():
                if arm_data["pulls"] > 0:
                    mean_reward = arm_data["rewards"] / arm_data["pulls"]
                    if mean_reward > best_reward:
                        best_reward = mean_reward
                        best_arm = arm_id
            
            return {
                "initialized": True,
                "total_pulls": bandit_data["total_pulls"],
                "arms_count": len(arms_info),
                "best_arm": best_arm,
                "best_arm_reward": best_reward,
                "regret": float(learning_state.bandit_regret) if learning_state.bandit_regret else 0.0,
                "exploration_rate": self._calculate_exploration_rate(bandit_data["total_pulls"]),
                "context_history_length": len(bandit_data.get("context_history", []))
            }
            
        except Exception as e:
            logger.error("get_bandit_stats_failed", user_id=user_id, error=str(e))
            raise


def get_bandit_selector(db: AsyncSession) -> ContextualBanditSelector:
    """Get contextual bandit selector instance"""
    return ContextualBanditSelector(db)
