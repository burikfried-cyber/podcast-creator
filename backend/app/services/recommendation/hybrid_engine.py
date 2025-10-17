"""
Hybrid Recommendation Engine
Combines collaborative, content-based, knowledge-based, and demographic filtering
"""
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.recommendation.collaborative_filtering import get_collaborative_filter
from app.services.recommendation.content_based_filtering import get_content_filter
from app.services.recommendation.knowledge_based_filtering import get_knowledge_filter
from app.services.recommendation.demographic_filtering import get_demographic_filter

logger = structlog.get_logger()


class HybridRecommendationEngine:
    """
    Hybrid Recommendation Engine
    
    Combines 4 filtering strategies with weighted scoring:
    - Collaborative Filtering (SVD++): 40% weight
    - Content-Based Filtering (TF-IDF): 30% weight
    - Knowledge-Based Filtering (Rules): 20% weight
    - Demographic Filtering (K-means): 10% weight
    
    Features:
    - Weighted hybrid approach
    - Fallback strategies
    - Diversity promotion
    - Real-time adaptation
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize all filters
        self.collaborative = get_collaborative_filter(db)
        self.content_based = get_content_filter(db)
        self.knowledge_based = get_knowledge_filter(db)
        self.demographic = get_demographic_filter(db)
        
        # Hybrid weights
        self.weights = {
            "collaborative": 0.4,
            "content_based": 0.3,
            "knowledge_based": 0.2,
            "demographic": 0.1
        }
        
        # Diversity parameters
        self.diversity_factor = 0.15  # 15% diversity boost
        self.min_diversity_score = 0.3
    
    async def get_recommendations(
        self,
        user_id: str,
        candidate_items: List[str],
        candidate_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
        n_recommendations: int = 10,
        diversity: bool = True
    ) -> Dict[str, Any]:
        """
        Get hybrid recommendations for user
        
        Args:
            user_id: User ID
            candidate_items: List of candidate item IDs
            candidate_metadata: Optional metadata for candidates
            n_recommendations: Number of recommendations
            diversity: Whether to promote diversity
            
        Returns:
            Recommendations with scores and explanations
        """
        try:
            logger.info("hybrid_recommendations_started",
                       user_id=user_id,
                       n_candidates=len(candidate_items))
            
            # Get recommendations from each filter
            collab_recs = await self.collaborative.get_recommendations(
                user_id,
                candidate_items,
                n_recommendations * 2  # Get more for diversity
            )
            
            content_recs = await self.content_based.get_recommendations(
                user_id,
                candidate_items,
                n_recommendations * 2
            )
            
            # Knowledge-based needs metadata
            if candidate_metadata:
                knowledge_items = [
                    {**candidate_metadata.get(item_id, {}), "id": item_id}
                    for item_id in candidate_items
                ]
                knowledge_recs = await self.knowledge_based.get_recommendations(
                    user_id,
                    knowledge_items,
                    n_recommendations * 2
                )
            else:
                knowledge_recs = []
            
            demographic_recs = await self.demographic.get_recommendations(
                user_id,
                candidate_items,
                n_recommendations * 2
            )
            
            # Combine scores with weighted hybrid
            hybrid_scores = self._combine_scores(
                collab_recs,
                content_recs,
                knowledge_recs,
                demographic_recs
            )
            
            # Apply diversity if requested
            if diversity:
                hybrid_scores = self._apply_diversity(
                    hybrid_scores,
                    candidate_metadata
                )
            
            # Sort and get top N
            sorted_recs = sorted(
                hybrid_scores.items(),
                key=lambda x: x[1]["score"],
                reverse=True
            )[:n_recommendations]
            
            # Format results
            recommendations = []
            for item_id, score_info in sorted_recs:
                recommendations.append({
                    "item_id": item_id,
                    "score": score_info["score"],
                    "component_scores": score_info["components"],
                    "explanation": self._generate_explanation(score_info)
                })
            
            logger.info("hybrid_recommendations_complete",
                       user_id=user_id,
                       n_recommendations=len(recommendations))
            
            return {
                "success": True,
                "user_id": user_id,
                "recommendations": recommendations,
                "n_candidates": len(candidate_items),
                "filters_used": self._get_active_filters(
                    collab_recs,
                    content_recs,
                    knowledge_recs,
                    demographic_recs
                )
            }
            
        except Exception as e:
            logger.error("hybrid_recommendations_failed",
                        user_id=user_id,
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }
    
    def _combine_scores(
        self,
        collab_recs: List[Tuple[str, float]],
        content_recs: List[Tuple[str, float]],
        knowledge_recs: List[Tuple[str, float]],
        demographic_recs: List[Tuple[str, float]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Combine scores from all filters using weighted hybrid
        
        Args:
            collab_recs: Collaborative filtering recommendations
            content_recs: Content-based recommendations
            knowledge_recs: Knowledge-based recommendations
            demographic_recs: Demographic recommendations
            
        Returns:
            Combined scores with component breakdown
        """
        combined = defaultdict(lambda: {
            "score": 0.0,
            "components": {
                "collaborative": 0.0,
                "content_based": 0.0,
                "knowledge_based": 0.0,
                "demographic": 0.0
            }
        })
        
        # Add collaborative scores
        for item_id, score in collab_recs:
            combined[item_id]["components"]["collaborative"] = score
            combined[item_id]["score"] += score * self.weights["collaborative"]
        
        # Add content-based scores
        for item_id, score in content_recs:
            combined[item_id]["components"]["content_based"] = score
            combined[item_id]["score"] += score * self.weights["content_based"]
        
        # Add knowledge-based scores
        for item_id, score in knowledge_recs:
            combined[item_id]["components"]["knowledge_based"] = score
            combined[item_id]["score"] += score * self.weights["knowledge_based"]
        
        # Add demographic scores
        for item_id, score in demographic_recs:
            combined[item_id]["components"]["demographic"] = score
            combined[item_id]["score"] += score * self.weights["demographic"]
        
        return dict(combined)
    
    def _apply_diversity(
        self,
        scores: Dict[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Apply diversity promotion to recommendations
        
        Args:
            scores: Current scores
            metadata: Item metadata
            
        Returns:
            Adjusted scores with diversity
        """
        if not metadata:
            return scores
        
        # Track topics/categories seen
        seen_topics = set()
        adjusted_scores = {}
        
        for item_id, score_info in scores.items():
            item_meta = metadata.get(item_id, {})
            item_topics = item_meta.get("topics", [])
            
            if isinstance(item_topics, str):
                item_topics = [item_topics]
            
            # Calculate diversity score
            diversity_score = 0.0
            for topic in item_topics:
                if topic not in seen_topics:
                    diversity_score += 1.0
                    seen_topics.add(topic)
            
            # Normalize diversity score
            if item_topics:
                diversity_score = diversity_score / len(item_topics)
            else:
                diversity_score = self.min_diversity_score
            
            # Apply diversity boost
            base_score = score_info["score"]
            boosted_score = base_score * (1 + diversity_score * self.diversity_factor)
            
            adjusted_scores[item_id] = {
                **score_info,
                "score": boosted_score,
                "diversity_score": diversity_score
            }
        
        return adjusted_scores
    
    def _generate_explanation(self, score_info: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation for recommendation
        
        Args:
            score_info: Score information
            
        Returns:
            Explanation string
        """
        components = score_info["components"]
        
        # Find dominant component
        dominant = max(components.items(), key=lambda x: x[1])
        dominant_name, dominant_score = dominant
        
        explanations = {
            "collaborative": "Users with similar tastes enjoyed this",
            "content_based": "Matches your content preferences",
            "knowledge_based": "Fits your preferred depth and topics",
            "demographic": "Popular with users like you"
        }
        
        explanation = explanations.get(dominant_name, "Recommended for you")
        
        # Add secondary reasons
        secondary = [
            name for name, score in components.items()
            if score > 0.3 and name != dominant_name
        ]
        
        if secondary:
            explanation += f" (also: {', '.join(secondary)})"
        
        return explanation
    
    def _get_active_filters(
        self,
        collab_recs: List,
        content_recs: List,
        knowledge_recs: List,
        demographic_recs: List
    ) -> List[str]:
        """Get list of filters that returned results"""
        active = []
        
        if collab_recs:
            active.append("collaborative")
        if content_recs:
            active.append("content_based")
        if knowledge_recs:
            active.append("knowledge_based")
        if demographic_recs:
            active.append("demographic")
        
        return active
    
    def update_weights(
        self,
        new_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Update hybrid weights (for A/B testing or optimization)
        
        Args:
            new_weights: New weight values
            
        Returns:
            Update status
        """
        # Validate weights sum to 1.0
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            return {
                "success": False,
                "error": f"Weights must sum to 1.0 (got {total})"
            }
        
        # Update weights
        for key, value in new_weights.items():
            if key in self.weights:
                self.weights[key] = value
        
        logger.info("hybrid_weights_updated", weights=self.weights)
        
        return {
            "success": True,
            "weights": self.weights
        }
    
    async def train_all_models(
        self,
        training_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Train all recommendation models
        
        Args:
            training_data: Training data for all models
            
        Returns:
            Training results
        """
        results = {}
        
        try:
            # Train collaborative filter
            if "user_item_matrix" in training_data:
                collab_result = await self.collaborative.train_model(
                    training_data["user_item_matrix"],
                    training_data.get("implicit_feedback")
                )
                results["collaborative"] = collab_result
            
            # Train content-based filter
            if "documents" in training_data:
                vocab_result = self.content_based.build_vocabulary(
                    training_data["documents"]
                )
                vector_result = self.content_based.vectorize_documents(
                    training_data["documents"]
                )
                results["content_based"] = {
                    "vocabulary": vocab_result,
                    "vectorization": vector_result
                }
            
            # Train demographic filter
            if "user_demographics" in training_data:
                demo_result = await self.demographic.train_clusters(
                    training_data["user_demographics"]
                )
                results["demographic"] = demo_result
            
            logger.info("all_models_trained", results=results)
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error("model_training_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all models
        
        Returns:
            Model statistics
        """
        return {
            "weights": self.weights,
            "diversity_factor": self.diversity_factor,
            "models": {
                "collaborative": self.collaborative.get_model_stats(),
                "content_based": self.content_based.get_model_stats(),
                "knowledge_based": self.knowledge_based.get_model_stats(),
                "demographic": self.demographic.get_model_stats()
            }
        }


def get_hybrid_engine(db: AsyncSession) -> HybridRecommendationEngine:
    """Get hybrid recommendation engine instance"""
    return HybridRecommendationEngine(db)
