"""
Hidden Markov Model for User Engagement
Tracks engagement states based on behavioral observations
"""
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from decimal import Decimal
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.preferences import UserLearningState

logger = structlog.get_logger()


class HMMEngagementTracker:
    """
    Hidden Markov Model for tracking user engagement states
    
    States: ['engaged', 'distracted', 'bored', 'overwhelmed']
    Observations: ['playback_speed_changes', 'pause_frequency', 'skip_patterns', 
                   'replay_segments', 'completion_percentage']
    """
    
    # Engagement states
    STATES = ['engaged', 'distracted', 'bored', 'overwhelmed']
    STATE_TO_IDX = {state: idx for idx, state in enumerate(STATES)}
    
    # Observation types
    OBSERVATIONS = [
        'playback_speed_changes',
        'pause_frequency',
        'skip_patterns',
        'replay_segments',
        'completion_percentage'
    ]
    OBS_TO_IDX = {obs: idx for idx, obs in enumerate(OBSERVATIONS)}
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.n_states = len(self.STATES)
        self.n_observations = len(self.OBSERVATIONS)
        
        # Initialize default transition matrix (4x4)
        # Rows: current state, Columns: next state
        self.default_transition_matrix = np.array([
            [0.7, 0.15, 0.10, 0.05],  # engaged -> [engaged, distracted, bored, overwhelmed]
            [0.3, 0.4, 0.2, 0.1],      # distracted -> ...
            [0.2, 0.3, 0.4, 0.1],      # bored -> ...
            [0.1, 0.2, 0.3, 0.4]       # overwhelmed -> ...
        ])
        
        # Initialize default emission matrix (4x5)
        # Rows: states, Columns: observations
        self.default_emission_matrix = np.array([
            [0.1, 0.1, 0.05, 0.3, 0.9],   # engaged: low speed changes, low pauses, low skips, high replay, high completion
            [0.3, 0.4, 0.3, 0.1, 0.6],    # distracted: medium speed, high pauses, medium skips, low replay, medium completion
            [0.2, 0.3, 0.7, 0.05, 0.3],   # bored: low speed, medium pauses, high skips, very low replay, low completion
            [0.5, 0.5, 0.4, 0.2, 0.4]     # overwhelmed: high speed, high pauses, medium skips, low replay, medium completion
        ])
        
        # Initial state probabilities (uniform)
        self.default_initial_probs = np.array([0.25, 0.25, 0.25, 0.25])
    
    async def initialize_hmm(self, user_id: str) -> Dict[str, Any]:
        """
        Initialize HMM for a new user
        
        Args:
            user_id: User ID
            
        Returns:
            Initialization status
        """
        try:
            # Check if already exists
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                learning_state = UserLearningState(user_id=user_id)
                self.db.add(learning_state)
            
            # Initialize HMM state
            hmm_state = {
                "current_state": "engaged",
                "transition_matrix": self.default_transition_matrix.tolist(),
                "emission_matrix": self.default_emission_matrix.tolist(),
                "state_probabilities": self.default_initial_probs.tolist(),
                "observation_history": [],
                "state_history": [],
                "model_version": "1.0"
            }
            
            learning_state.hmm_states = hmm_state
            learning_state.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info("hmm_initialized", user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "initial_state": "engaged"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("hmm_initialization_failed", user_id=user_id, error=str(e))
            raise
    
    async def update_engagement_state(
        self,
        user_id: str,
        observations: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Update engagement state based on observations using Baum-Welch algorithm
        
        Args:
            user_id: User ID
            observations: Dict of observation_type -> value (0-1)
            
        Returns:
            Updated state and probabilities
        """
        try:
            # Get current HMM state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state or not learning_state.hmm_states:
                # Initialize if doesn't exist
                await self.initialize_hmm(user_id)
                result = await self.db.execute(
                    select(UserLearningState).where(
                        UserLearningState.user_id == user_id
                    )
                )
                learning_state = result.scalar_one()
            
            hmm_state = learning_state.hmm_states
            
            # Convert to numpy arrays
            transition_matrix = np.array(hmm_state["transition_matrix"])
            emission_matrix = np.array(hmm_state["emission_matrix"])
            state_probs = np.array(hmm_state["state_probabilities"])
            
            # Convert observations to vector
            obs_vector = self._observations_to_vector(observations)
            
            # Forward algorithm: compute state probabilities given observations
            new_state_probs = self._forward_step(
                state_probs,
                transition_matrix,
                emission_matrix,
                obs_vector
            )
            
            # Determine most likely current state
            current_state_idx = np.argmax(new_state_probs)
            current_state = self.STATES[current_state_idx]
            
            # Online learning: Update transition and emission matrices
            if len(hmm_state["observation_history"]) > 0:
                transition_matrix, emission_matrix = self._baum_welch_update(
                    transition_matrix,
                    emission_matrix,
                    hmm_state["observation_history"][-10:],  # Last 10 observations
                    obs_vector,
                    learning_rate=0.01
                )
            
            # Update HMM state
            hmm_state["current_state"] = current_state
            hmm_state["state_probabilities"] = new_state_probs.tolist()
            hmm_state["transition_matrix"] = transition_matrix.tolist()
            hmm_state["emission_matrix"] = emission_matrix.tolist()
            
            # Add to history (keep last 100)
            hmm_state["observation_history"].append(obs_vector.tolist())
            hmm_state["observation_history"] = hmm_state["observation_history"][-100:]
            
            hmm_state["state_history"].append({
                "state": current_state,
                "probabilities": new_state_probs.tolist(),
                "timestamp": datetime.utcnow().isoformat()
            })
            hmm_state["state_history"] = hmm_state["state_history"][-100:]
            
            learning_state.hmm_states = hmm_state
            learning_state.updated_at = datetime.utcnow()
            
            # Calculate accuracy (if we have enough history)
            if len(hmm_state["state_history"]) >= 10:
                accuracy = self._calculate_accuracy(hmm_state["state_history"])
                learning_state.hmm_accuracy = Decimal(str(round(accuracy, 2)))
            
            await self.db.commit()
            
            logger.info("engagement_state_updated",
                       user_id=user_id,
                       state=current_state,
                       confidence=float(new_state_probs[current_state_idx]))
            
            return {
                "success": True,
                "current_state": current_state,
                "state_probabilities": {
                    state: float(prob)
                    for state, prob in zip(self.STATES, new_state_probs)
                },
                "confidence": float(new_state_probs[current_state_idx]),
                "observations_processed": len(hmm_state["observation_history"])
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("engagement_update_failed", user_id=user_id, error=str(e))
            raise
    
    def _observations_to_vector(self, observations: Dict[str, float]) -> np.ndarray:
        """Convert observation dict to vector"""
        vector = np.zeros(self.n_observations)
        for obs_name, value in observations.items():
            if obs_name in self.OBS_TO_IDX:
                idx = self.OBS_TO_IDX[obs_name]
                vector[idx] = value
        return vector
    
    def _forward_step(
        self,
        state_probs: np.ndarray,
        transition_matrix: np.ndarray,
        emission_matrix: np.ndarray,
        observation: np.ndarray
    ) -> np.ndarray:
        """
        Forward algorithm step: compute P(state | observation)
        
        Args:
            state_probs: Current state probabilities
            transition_matrix: State transition matrix
            emission_matrix: Observation emission matrix
            observation: Current observation vector
            
        Returns:
            Updated state probabilities
        """
        # Compute emission probabilities for each state
        emission_probs = np.zeros(self.n_states)
        for state_idx in range(self.n_states):
            # Probability of observing this observation in this state
            # Using Gaussian-like similarity
            state_emissions = emission_matrix[state_idx]
            similarity = 1.0 - np.mean(np.abs(state_emissions - observation))
            emission_probs[state_idx] = max(0.01, similarity)  # Avoid zero probability
        
        # Forward step: P(state_t) = sum(P(state_t-1) * P(state_t | state_t-1)) * P(obs | state_t)
        new_probs = np.dot(state_probs, transition_matrix) * emission_probs
        
        # Normalize
        new_probs = new_probs / (np.sum(new_probs) + 1e-10)
        
        return new_probs
    
    def _baum_welch_update(
        self,
        transition_matrix: np.ndarray,
        emission_matrix: np.ndarray,
        observation_history: List[List[float]],
        new_observation: np.ndarray,
        learning_rate: float = 0.01
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Online Baum-Welch update for HMM parameters
        
        Args:
            transition_matrix: Current transition matrix
            emission_matrix: Current emission matrix
            observation_history: Recent observation history
            new_observation: New observation
            learning_rate: Learning rate for updates
            
        Returns:
            Updated transition and emission matrices
        """
        if len(observation_history) < 2:
            return transition_matrix, emission_matrix
        
        # Simple online update: adjust based on recent observations
        # This is a simplified version of Baum-Welch
        
        # Update emission matrix: move emissions toward observed values
        obs_array = np.array(observation_history)
        mean_obs = np.mean(obs_array, axis=0)
        
        for state_idx in range(self.n_states):
            # Adjust emission probabilities toward observed patterns
            emission_matrix[state_idx] = (
                (1 - learning_rate) * emission_matrix[state_idx] +
                learning_rate * mean_obs
            )
        
        # Ensure valid probabilities (0-1 range)
        emission_matrix = np.clip(emission_matrix, 0.01, 0.99)
        
        # Normalize transition matrix rows
        transition_matrix = transition_matrix / (transition_matrix.sum(axis=1, keepdims=True) + 1e-10)
        
        return transition_matrix, emission_matrix
    
    def _calculate_accuracy(self, state_history: List[Dict]) -> float:
        """
        Calculate model accuracy based on state consistency
        
        Args:
            state_history: Recent state history
            
        Returns:
            Accuracy score (0-1)
        """
        if len(state_history) < 2:
            return 0.5
        
        # Measure consistency: higher confidence in predictions = higher accuracy
        confidences = []
        for state_entry in state_history[-10:]:
            probs = state_entry["probabilities"]
            max_prob = max(probs)
            confidences.append(max_prob)
        
        # Average confidence as proxy for accuracy
        accuracy = np.mean(confidences)
        return float(accuracy)
    
    async def get_engagement_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get current engagement state for user
        
        Args:
            user_id: User ID
            
        Returns:
            Current engagement state
        """
        try:
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state or not learning_state.hmm_states:
                return {
                    "current_state": "engaged",
                    "state_probabilities": {state: 0.25 for state in self.STATES},
                    "confidence": 0.25,
                    "initialized": False
                }
            
            hmm_state = learning_state.hmm_states
            state_probs = hmm_state["state_probabilities"]
            current_state = hmm_state["current_state"]
            current_idx = self.STATE_TO_IDX[current_state]
            
            return {
                "current_state": current_state,
                "state_probabilities": {
                    state: float(prob)
                    for state, prob in zip(self.STATES, state_probs)
                },
                "confidence": float(state_probs[current_idx]),
                "observation_count": len(hmm_state.get("observation_history", [])),
                "accuracy": float(learning_state.hmm_accuracy) if learning_state.hmm_accuracy else None,
                "initialized": True
            }
            
        except Exception as e:
            logger.error("get_engagement_failed", user_id=user_id, error=str(e))
            raise


def get_hmm_tracker(db: AsyncSession) -> HMMEngagementTracker:
    """Get HMM engagement tracker instance"""
    return HMMEngagementTracker(db)
