"""
Collaborative Filtering with SVD++
User-based and item-based collaborative filtering for recommendations
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from decimal import Decimal
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.preferences import UserBehavioralSignal

logger = structlog.get_logger()


class CollaborativeFilter:
    """
    Collaborative Filtering using SVD++ (Singular Value Decomposition++)
    
    SVD++ extends basic SVD by incorporating implicit feedback
    
    Parameters:
    - n_factors: 100 (latent factors)
    - regularization: 0.02
    - learning_rate: 0.005
    - n_epochs: 20
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # SVD++ parameters
        self.n_factors = 100
        self.regularization = 0.02
        self.learning_rate = 0.005
        self.n_epochs = 20
        
        # User and item latent factors (will be loaded/computed)
        self.user_factors = {}  # user_id -> factor vector
        self.item_factors = {}  # item_id -> factor vector
        self.user_biases = {}   # user_id -> bias
        self.item_biases = {}   # item_id -> bias
        self.global_mean = 0.5  # Global mean rating
        
        # Implicit feedback factors
        self.implicit_factors = {}  # item_id -> implicit factor vector
    
    async def train_model(
        self,
        user_item_matrix: Dict[str, Dict[str, float]],
        implicit_feedback: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Train SVD++ model on user-item interaction matrix
        
        Args:
            user_item_matrix: {user_id: {item_id: rating}}
            implicit_feedback: {user_id: [item_ids]} - items user interacted with
            
        Returns:
            Training statistics
        """
        try:
            logger.info("collaborative_filter_training_started",
                       users=len(user_item_matrix))
            
            # Initialize factors
            users = list(user_item_matrix.keys())
            items = set()
            for user_ratings in user_item_matrix.values():
                items.update(user_ratings.keys())
            items = list(items)
            
            # Initialize user factors (random)
            for user_id in users:
                self.user_factors[user_id] = np.random.normal(0, 0.1, self.n_factors)
                self.user_biases[user_id] = 0.0
            
            # Initialize item factors (random)
            for item_id in items:
                self.item_factors[item_id] = np.random.normal(0, 0.1, self.n_factors)
                self.item_biases[item_id] = 0.0
                self.implicit_factors[item_id] = np.random.normal(0, 0.1, self.n_factors)
            
            # Calculate global mean
            all_ratings = []
            for user_ratings in user_item_matrix.values():
                all_ratings.extend(user_ratings.values())
            self.global_mean = np.mean(all_ratings) if all_ratings else 0.5
            
            # Training loop (Stochastic Gradient Descent)
            training_errors = []
            
            for epoch in range(self.n_epochs):
                epoch_error = 0.0
                n_samples = 0
                
                for user_id, user_ratings in user_item_matrix.items():
                    # Get implicit feedback for this user
                    user_implicit = implicit_feedback.get(user_id, []) if implicit_feedback else []
                    
                    # Compute implicit factor sum
                    implicit_sum = np.zeros(self.n_factors)
                    if user_implicit:
                        for item_id in user_implicit:
                            if item_id in self.implicit_factors:
                                implicit_sum += self.implicit_factors[item_id]
                        implicit_sum /= np.sqrt(len(user_implicit))
                    
                    for item_id, rating in user_ratings.items():
                        # Predict rating
                        prediction = self._predict_rating(
                            user_id,
                            item_id,
                            implicit_sum
                        )
                        
                        # Calculate error
                        error = rating - prediction
                        epoch_error += error ** 2
                        n_samples += 1
                        
                        # Update factors using SGD
                        self._update_factors(
                            user_id,
                            item_id,
                            error,
                            implicit_sum,
                            user_implicit
                        )
                
                # Calculate RMSE for this epoch
                rmse = np.sqrt(epoch_error / n_samples) if n_samples > 0 else 0.0
                training_errors.append(rmse)
                
                if epoch % 5 == 0:
                    logger.info("svd_training_epoch",
                               epoch=epoch,
                               rmse=rmse)
            
            logger.info("collaborative_filter_training_complete",
                       final_rmse=training_errors[-1] if training_errors else 0.0)
            
            return {
                "success": True,
                "n_users": len(users),
                "n_items": len(items),
                "n_epochs": self.n_epochs,
                "final_rmse": training_errors[-1] if training_errors else 0.0,
                "training_errors": training_errors
            }
            
        except Exception as e:
            logger.error("collaborative_filter_training_failed", error=str(e))
            raise
    
    def _predict_rating(
        self,
        user_id: str,
        item_id: str,
        implicit_sum: np.ndarray
    ) -> float:
        """
        Predict rating for user-item pair using SVD++
        
        Args:
            user_id: User ID
            item_id: Item ID
            implicit_sum: Sum of implicit factors
            
        Returns:
            Predicted rating (0-1)
        """
        if user_id not in self.user_factors or item_id not in self.item_factors:
            return self.global_mean
        
        # SVD++ prediction: μ + b_u + b_i + (p_u + |N(u)|^(-0.5) * Σy_j) · q_i
        prediction = (
            self.global_mean +
            self.user_biases[user_id] +
            self.item_biases[item_id] +
            np.dot(self.user_factors[user_id] + implicit_sum, self.item_factors[item_id])
        )
        
        # Clip to valid range
        return np.clip(prediction, 0.0, 1.0)
    
    def _update_factors(
        self,
        user_id: str,
        item_id: str,
        error: float,
        implicit_sum: np.ndarray,
        user_implicit: List[str]
    ) -> None:
        """
        Update factors using stochastic gradient descent
        
        Args:
            user_id: User ID
            item_id: Item ID
            error: Prediction error
            implicit_sum: Sum of implicit factors
            user_implicit: List of items user interacted with
        """
        # Update biases
        self.user_biases[user_id] += self.learning_rate * (
            error - self.regularization * self.user_biases[user_id]
        )
        self.item_biases[item_id] += self.learning_rate * (
            error - self.regularization * self.item_biases[item_id]
        )
        
        # Update user factors
        user_factor_update = (
            error * self.item_factors[item_id] -
            self.regularization * self.user_factors[user_id]
        )
        self.user_factors[user_id] += self.learning_rate * user_factor_update
        
        # Update item factors
        item_factor_update = (
            error * (self.user_factors[user_id] + implicit_sum) -
            self.regularization * self.item_factors[item_id]
        )
        self.item_factors[item_id] += self.learning_rate * item_factor_update
        
        # Update implicit factors
        if user_implicit:
            implicit_factor_update = (
                error * self.item_factors[item_id] / np.sqrt(len(user_implicit)) -
                self.regularization * implicit_sum
            )
            for implicit_item_id in user_implicit:
                if implicit_item_id in self.implicit_factors:
                    self.implicit_factors[implicit_item_id] += (
                        self.learning_rate * implicit_factor_update
                    )
    
    async def get_recommendations(
        self,
        user_id: str,
        candidate_items: List[str],
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get top-N recommendations for user
        
        Args:
            user_id: User ID
            candidate_items: List of candidate item IDs
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of (item_id, score) tuples
        """
        try:
            # Get user's implicit feedback
            result = await self.db.execute(
                select(UserBehavioralSignal.podcast_id).where(
                    and_(
                        UserBehavioralSignal.user_id == user_id,
                        UserBehavioralSignal.podcast_id.isnot(None)
                    )
                ).distinct()
            )
            user_implicit = [str(row[0]) for row in result.fetchall()]
            
            # Compute implicit factor sum
            implicit_sum = np.zeros(self.n_factors)
            if user_implicit:
                for item_id in user_implicit:
                    if item_id in self.implicit_factors:
                        implicit_sum += self.implicit_factors[item_id]
                implicit_sum /= np.sqrt(len(user_implicit))
            
            # Score all candidate items
            scores = []
            for item_id in candidate_items:
                score = self._predict_rating(user_id, item_id, implicit_sum)
                scores.append((item_id, float(score)))
            
            # Sort by score and return top N
            scores.sort(key=lambda x: x[1], reverse=True)
            
            return scores[:n_recommendations]
            
        except Exception as e:
            logger.error("collaborative_recommendations_failed",
                        user_id=user_id,
                        error=str(e))
            return []
    
    async def get_similar_items(
        self,
        item_id: str,
        n_similar: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get similar items based on item factors
        
        Args:
            item_id: Item ID
            n_similar: Number of similar items to return
            
        Returns:
            List of (item_id, similarity) tuples
        """
        if item_id not in self.item_factors:
            return []
        
        item_factor = self.item_factors[item_id]
        
        # Calculate cosine similarity with all other items
        similarities = []
        for other_id, other_factor in self.item_factors.items():
            if other_id != item_id:
                # Cosine similarity
                similarity = np.dot(item_factor, other_factor) / (
                    np.linalg.norm(item_factor) * np.linalg.norm(other_factor) + 1e-10
                )
                similarities.append((other_id, float(similarity)))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:n_similar]
    
    async def get_similar_users(
        self,
        user_id: str,
        n_similar: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get similar users based on user factors
        
        Args:
            user_id: User ID
            n_similar: Number of similar users to return
            
        Returns:
            List of (user_id, similarity) tuples
        """
        if user_id not in self.user_factors:
            return []
        
        user_factor = self.user_factors[user_id]
        
        # Calculate cosine similarity with all other users
        similarities = []
        for other_id, other_factor in self.user_factors.items():
            if other_id != user_id:
                # Cosine similarity
                similarity = np.dot(user_factor, other_factor) / (
                    np.linalg.norm(user_factor) * np.linalg.norm(other_factor) + 1e-10
                )
                similarities.append((other_id, float(similarity)))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:n_similar]
    
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get model statistics
        
        Returns:
            Model statistics
        """
        return {
            "n_users": len(self.user_factors),
            "n_items": len(self.item_factors),
            "n_factors": self.n_factors,
            "global_mean": float(self.global_mean),
            "regularization": self.regularization,
            "learning_rate": self.learning_rate,
            "trained": len(self.user_factors) > 0
        }


def get_collaborative_filter(db: AsyncSession) -> CollaborativeFilter:
    """Get collaborative filter instance"""
    return CollaborativeFilter(db)
