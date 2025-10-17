"""
LSTM Neural Network for Pattern Recognition
Predicts engagement, completion, preference strength, and churn risk
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from decimal import Decimal
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.preferences import UserLearningState

logger = structlog.get_logger()


class LSTMPatternRecognizer:
    """
    LSTM-based pattern recognition for user behavior
    
    Architecture: Input(128) -> LSTM(64x2) -> Dense(32) -> Output(4)
    
    Inputs:
    - historical_engagement_sequence
    - content_feature_vectors
    - contextual_embeddings
    - temporal_encodings
    
    Outputs:
    - engagement_probability
    - completion_likelihood
    - preference_strength_estimate
    - churn_risk_score
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Model dimensions
        self.input_dim = 128
        self.lstm_hidden_dim = 64
        self.lstm_layers = 2
        self.dense_dim = 32
        self.output_dim = 4
        
        # Sequence length for LSTM
        self.sequence_length = 10
        
        # Initialize weights (simplified - in production use PyTorch/TensorFlow)
        self.learning_rate = 0.001
        
    async def initialize_lstm(self, user_id: str) -> Dict[str, Any]:
        """
        Initialize LSTM model state for a new user
        
        Args:
            user_id: User ID
            
        Returns:
            Initialization status
        """
        try:
            # Get or create learning state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                learning_state = UserLearningState(user_id=user_id)
                self.db.add(learning_state)
            
            # Initialize LSTM state
            lstm_state = {
                "hidden_state": np.zeros(self.lstm_hidden_dim).tolist(),
                "cell_state": np.zeros(self.lstm_hidden_dim).tolist(),
                "sequence_history": [],
                "predictions_history": [],
                "model_version": "1.0",
                "training_iterations": 0
            }
            
            learning_state.lstm_model_state = lstm_state
            learning_state.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info("lstm_initialized", user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "model_version": "1.0"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("lstm_initialization_failed", user_id=user_id, error=str(e))
            raise
    
    async def predict_patterns(
        self,
        user_id: str,
        engagement_sequence: List[float],
        content_features: Dict[str, float],
        context: Dict[str, Any],
        temporal_info: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Predict user behavior patterns using LSTM
        
        Args:
            user_id: User ID
            engagement_sequence: Recent engagement scores (0-1)
            content_features: Content feature vector
            context: Contextual information
            temporal_info: Temporal encodings
            
        Returns:
            Predictions for engagement, completion, preference, churn
        """
        try:
            # Get current LSTM state
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state or not learning_state.lstm_model_state:
                # Initialize if doesn't exist
                await self.initialize_lstm(user_id)
                result = await self.db.execute(
                    select(UserLearningState).where(
                        UserLearningState.user_id == user_id
                    )
                )
                learning_state = result.scalar_one()
            
            lstm_state = learning_state.lstm_model_state
            
            # Prepare input vector
            input_vector = self._prepare_input(
                engagement_sequence,
                content_features,
                context,
                temporal_info
            )
            
            # Get hidden and cell states
            hidden_state = np.array(lstm_state["hidden_state"])
            cell_state = np.array(lstm_state["cell_state"])
            
            # LSTM forward pass (simplified)
            new_hidden, new_cell, output = self._lstm_forward(
                input_vector,
                hidden_state,
                cell_state
            )
            
            # Predictions
            predictions = {
                "engagement_probability": float(output[0]),
                "completion_likelihood": float(output[1]),
                "preference_strength": float(output[2]),
                "churn_risk": float(output[3])
            }
            
            # Update LSTM state
            lstm_state["hidden_state"] = new_hidden.tolist()
            lstm_state["cell_state"] = new_cell.tolist()
            
            # Add to sequence history (keep last 100)
            lstm_state["sequence_history"].append({
                "input": input_vector.tolist(),
                "output": output.tolist(),
                "timestamp": datetime.utcnow().isoformat()
            })
            lstm_state["sequence_history"] = lstm_state["sequence_history"][-100:]
            
            # Add to predictions history
            lstm_state["predictions_history"].append({
                "predictions": predictions,
                "timestamp": datetime.utcnow().isoformat()
            })
            lstm_state["predictions_history"] = lstm_state["predictions_history"][-100:]
            
            learning_state.lstm_model_state = lstm_state
            learning_state.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info("lstm_prediction_made",
                       user_id=user_id,
                       engagement=predictions["engagement_probability"],
                       churn_risk=predictions["churn_risk"])
            
            return {
                "success": True,
                "predictions": predictions,
                "confidence": self._calculate_confidence(lstm_state),
                "sequence_length": len(lstm_state["sequence_history"])
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("lstm_prediction_failed", user_id=user_id, error=str(e))
            raise
    
    async def update_lstm(
        self,
        user_id: str,
        actual_outcomes: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Update LSTM model with actual outcomes (online learning)
        
        Args:
            user_id: User ID
            actual_outcomes: Actual observed outcomes
            
        Returns:
            Update status
        """
        try:
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state or not learning_state.lstm_model_state:
                return {"success": False, "error": "LSTM not initialized"}
            
            lstm_state = learning_state.lstm_model_state
            
            # Get last prediction
            if not lstm_state["predictions_history"]:
                return {"success": False, "error": "No predictions to update"}
            
            last_prediction = lstm_state["predictions_history"][-1]["predictions"]
            
            # Calculate loss (MSE)
            loss = 0.0
            for key in actual_outcomes:
                if key in last_prediction:
                    error = actual_outcomes[key] - last_prediction[key]
                    loss += error ** 2
            
            loss = loss / len(actual_outcomes)
            
            # Online learning: simplified gradient descent
            # In production, use proper backpropagation through time (BPTT)
            lstm_state["training_iterations"] += 1
            
            # Calculate accuracy
            accuracy = 1.0 - min(1.0, loss)
            learning_state.lstm_accuracy = Decimal(str(round(accuracy, 2)))
            
            learning_state.lstm_model_state = lstm_state
            learning_state.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info("lstm_updated",
                       user_id=user_id,
                       loss=loss,
                       accuracy=accuracy)
            
            return {
                "success": True,
                "loss": loss,
                "accuracy": accuracy,
                "training_iterations": lstm_state["training_iterations"]
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("lstm_update_failed", user_id=user_id, error=str(e))
            raise
    
    def _prepare_input(
        self,
        engagement_sequence: List[float],
        content_features: Dict[str, float],
        context: Dict[str, Any],
        temporal_info: Dict[str, float]
    ) -> np.ndarray:
        """
        Prepare input vector for LSTM
        
        Args:
            engagement_sequence: Recent engagement scores
            content_features: Content features
            context: Context information
            temporal_info: Temporal features
            
        Returns:
            Input vector of size input_dim (128)
        """
        input_vector = np.zeros(self.input_dim)
        
        # Engagement sequence (first 20 dims)
        seq_len = min(len(engagement_sequence), 20)
        input_vector[:seq_len] = engagement_sequence[-seq_len:]
        
        # Content features (next 40 dims)
        content_values = list(content_features.values())[:40]
        input_vector[20:20+len(content_values)] = content_values
        
        # Context embeddings (next 40 dims)
        context_idx = 60
        if "time_of_day" in context:
            # Encode time of day (0-23 hours -> 0-1)
            time_encoding = self._encode_time(context["time_of_day"])
            input_vector[context_idx:context_idx+4] = time_encoding
            context_idx += 4
        
        if "device" in context:
            # One-hot encode device
            device_encoding = self._encode_device(context["device"])
            input_vector[context_idx:context_idx+3] = device_encoding
            context_idx += 3
        
        # Temporal features (remaining dims)
        temporal_values = list(temporal_info.values())
        temp_len = min(len(temporal_values), self.input_dim - context_idx)
        input_vector[context_idx:context_idx+temp_len] = temporal_values[:temp_len]
        
        return input_vector
    
    def _lstm_forward(
        self,
        input_vector: np.ndarray,
        hidden_state: np.ndarray,
        cell_state: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Simplified LSTM forward pass
        
        In production, use PyTorch or TensorFlow for proper LSTM implementation
        
        Args:
            input_vector: Input vector
            hidden_state: Previous hidden state
            cell_state: Previous cell state
            
        Returns:
            New hidden state, new cell state, output
        """
        # Simplified LSTM (not a real LSTM, just a placeholder)
        # In production, use proper LSTM with gates (forget, input, output)
        
        # Project input to hidden dimension
        input_proj = input_vector[:self.lstm_hidden_dim]
        if len(input_proj) < self.lstm_hidden_dim:
            input_proj = np.pad(input_proj, (0, self.lstm_hidden_dim - len(input_proj)))
        
        # Simplified gates (normally would have forget, input, output gates)
        forget_gate = self._sigmoid(input_proj + hidden_state)
        input_gate = self._sigmoid(input_proj - hidden_state)
        output_gate = self._sigmoid(input_proj * 0.5)
        
        # Update cell state
        new_cell = forget_gate * cell_state + input_gate * np.tanh(input_proj)
        
        # Update hidden state
        new_hidden = output_gate * np.tanh(new_cell)
        
        # Output layer (4 outputs)
        output = np.zeros(self.output_dim)
        output[0] = self._sigmoid(np.mean(new_hidden[:16]))  # engagement_probability
        output[1] = self._sigmoid(np.mean(new_hidden[16:32]))  # completion_likelihood
        output[2] = self._sigmoid(np.mean(new_hidden[32:48]))  # preference_strength
        output[3] = self._sigmoid(np.mean(new_hidden[48:64]))  # churn_risk
        
        return new_hidden, new_cell, output
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function"""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))
    
    def _encode_time(self, time_of_day: str) -> np.ndarray:
        """Encode time of day as cyclical features"""
        time_map = {
            "morning": 0.25,
            "afternoon": 0.5,
            "evening": 0.75,
            "night": 1.0
        }
        t = time_map.get(time_of_day, 0.5)
        # Cyclical encoding: sin and cos
        return np.array([
            np.sin(2 * np.pi * t),
            np.cos(2 * np.pi * t),
            t,
            1.0 - t
        ])
    
    def _encode_device(self, device: str) -> np.ndarray:
        """One-hot encode device type"""
        device_map = {"mobile": 0, "desktop": 1, "tablet": 2}
        idx = device_map.get(device, 0)
        encoding = np.zeros(3)
        encoding[idx] = 1.0
        return encoding
    
    def _calculate_confidence(self, lstm_state: Dict) -> float:
        """Calculate prediction confidence based on history"""
        if len(lstm_state["predictions_history"]) < 5:
            return 0.5
        
        # Confidence based on consistency of recent predictions
        recent_predictions = lstm_state["predictions_history"][-10:]
        engagement_preds = [p["predictions"]["engagement_probability"] for p in recent_predictions]
        
        # Lower variance = higher confidence
        variance = np.var(engagement_preds)
        confidence = 1.0 - min(1.0, variance * 2)
        
        return float(confidence)
    
    async def get_lstm_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get current LSTM state for user
        
        Args:
            user_id: User ID
            
        Returns:
            Current LSTM state
        """
        try:
            result = await self.db.execute(
                select(UserLearningState).where(
                    UserLearningState.user_id == user_id
                )
            )
            learning_state = result.scalar_one_or_none()
            
            if not learning_state or not learning_state.lstm_model_state:
                return {
                    "initialized": False,
                    "model_version": None,
                    "training_iterations": 0
                }
            
            lstm_state = learning_state.lstm_model_state
            
            return {
                "initialized": True,
                "model_version": lstm_state.get("model_version"),
                "training_iterations": lstm_state.get("training_iterations", 0),
                "sequence_length": len(lstm_state.get("sequence_history", [])),
                "accuracy": float(learning_state.lstm_accuracy) if learning_state.lstm_accuracy else None,
                "last_prediction": lstm_state["predictions_history"][-1] if lstm_state.get("predictions_history") else None
            }
            
        except Exception as e:
            logger.error("get_lstm_state_failed", user_id=user_id, error=str(e))
            raise


def get_lstm_recognizer(db: AsyncSession) -> LSTMPatternRecognizer:
    """Get LSTM pattern recognizer instance"""
    return LSTMPatternRecognizer(db)
