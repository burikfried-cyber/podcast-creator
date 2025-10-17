"""
Demographic Filtering with K-means Clustering
User clustering based on demographics for cold start and group recommendations
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import defaultdict
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.preferences import UserColdStartData

logger = structlog.get_logger()


class DemographicFilter:
    """
    Demographic Filtering using K-means clustering
    
    Features:
    - User clustering by demographics
    - Cluster-based recommendations
    - Cold start support
    - Statistical modeling
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Clustering parameters
        self.n_clusters = 10
        self.max_iterations = 100
        self.convergence_threshold = 0.001
        
        # Cluster data
        self.cluster_centroids = {}  # cluster_id -> centroid vector
        self.cluster_profiles = {}   # cluster_id -> preference profile
        self.user_clusters = {}      # user_id -> cluster_id
        
        # Feature encoding
        self.feature_encoders = self._initialize_encoders()
    
    def _initialize_encoders(self) -> Dict[str, Dict]:
        """Initialize feature encoders for demographics"""
        return {
            "age_range": {
                "18-24": 0,
                "25-34": 1,
                "35-44": 2,
                "45-54": 3,
                "55-64": 4,
                "65+": 5
            },
            "education_level": {
                "high_school": 0,
                "some_college": 1,
                "bachelors": 2,
                "masters": 3,
                "doctorate": 4
            },
            "occupation_category": {
                "student": 0,
                "technology": 1,
                "business": 2,
                "healthcare": 3,
                "education": 4,
                "creative": 5,
                "service": 6,
                "other": 7
            }
        }
    
    async def train_clusters(
        self,
        user_demographics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Train K-means clustering on user demographics
        
        Args:
            user_demographics: {user_id: {age_range, education, occupation, location}}
            
        Returns:
            Training statistics
        """
        try:
            logger.info("demographic_clustering_started",
                       n_users=len(user_demographics))
            
            # Encode user features
            user_vectors = {}
            for user_id, demographics in user_demographics.items():
                vector = self._encode_demographics(demographics)
                if vector is not None:
                    user_vectors[user_id] = vector
            
            if len(user_vectors) < self.n_clusters:
                logger.warning("insufficient_users_for_clustering",
                             n_users=len(user_vectors),
                             n_clusters=self.n_clusters)
                return {"success": False, "error": "Insufficient users"}
            
            # Initialize centroids (K-means++)
            centroids = self._initialize_centroids_kmeans_pp(
                list(user_vectors.values())
            )
            
            # K-means iterations
            for iteration in range(self.max_iterations):
                # Assign users to clusters
                clusters = defaultdict(list)
                for user_id, vector in user_vectors.items():
                    cluster_id = self._assign_to_cluster(vector, centroids)
                    clusters[cluster_id].append((user_id, vector))
                    self.user_clusters[user_id] = cluster_id
                
                # Update centroids
                new_centroids = {}
                max_shift = 0.0
                
                for cluster_id, members in clusters.items():
                    if members:
                        vectors = [v for _, v in members]
                        new_centroid = np.mean(vectors, axis=0)
                        
                        # Calculate shift
                        if cluster_id in centroids:
                            shift = np.linalg.norm(new_centroid - centroids[cluster_id])
                            max_shift = max(max_shift, shift)
                        
                        new_centroids[cluster_id] = new_centroid
                
                centroids = new_centroids
                
                # Check convergence
                if max_shift < self.convergence_threshold:
                    logger.info("clustering_converged",
                               iteration=iteration,
                               max_shift=max_shift)
                    break
            
            self.cluster_centroids = centroids
            
            # Build cluster profiles
            await self._build_cluster_profiles(clusters)
            
            logger.info("demographic_clustering_complete",
                       n_clusters=len(centroids),
                       iterations=iteration + 1)
            
            return {
                "success": True,
                "n_clusters": len(centroids),
                "n_users": len(user_vectors),
                "iterations": iteration + 1,
                "converged": max_shift < self.convergence_threshold
            }
            
        except Exception as e:
            logger.error("demographic_clustering_failed", error=str(e))
            raise
    
    def _encode_demographics(
        self,
        demographics: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """
        Encode demographics into feature vector
        
        Args:
            demographics: Demographic information
            
        Returns:
            Feature vector or None if insufficient data
        """
        features = []
        
        # Age range (one-hot encoded)
        age_range = demographics.get("age_range", "25-34")
        age_encoded = np.zeros(len(self.feature_encoders["age_range"]))
        if age_range in self.feature_encoders["age_range"]:
            age_encoded[self.feature_encoders["age_range"][age_range]] = 1.0
        features.extend(age_encoded)
        
        # Education level (one-hot encoded)
        education = demographics.get("education_level", "bachelors")
        edu_encoded = np.zeros(len(self.feature_encoders["education_level"]))
        if education in self.feature_encoders["education_level"]:
            edu_encoded[self.feature_encoders["education_level"][education]] = 1.0
        features.extend(edu_encoded)
        
        # Occupation category (one-hot encoded)
        occupation = demographics.get("occupation", "other")
        # Map occupation to category
        occ_category = self._categorize_occupation(occupation)
        occ_encoded = np.zeros(len(self.feature_encoders["occupation_category"]))
        if occ_category in self.feature_encoders["occupation_category"]:
            occ_encoded[self.feature_encoders["occupation_category"][occ_category]] = 1.0
        features.extend(occ_encoded)
        
        # Location features (simplified - could use lat/long)
        # For now, just add a placeholder
        features.append(0.5)
        
        return np.array(features)
    
    def _categorize_occupation(self, occupation: str) -> str:
        """Categorize occupation into broad category"""
        occupation = occupation.lower()
        
        if any(word in occupation for word in ["student", "intern"]):
            return "student"
        elif any(word in occupation for word in ["engineer", "developer", "programmer", "tech"]):
            return "technology"
        elif any(word in occupation for word in ["manager", "executive", "business", "finance"]):
            return "business"
        elif any(word in occupation for word in ["doctor", "nurse", "healthcare", "medical"]):
            return "healthcare"
        elif any(word in occupation for word in ["teacher", "professor", "educator"]):
            return "education"
        elif any(word in occupation for word in ["artist", "designer", "writer", "creative"]):
            return "creative"
        elif any(word in occupation for word in ["service", "retail", "hospitality"]):
            return "service"
        else:
            return "other"
    
    def _initialize_centroids_kmeans_pp(
        self,
        vectors: List[np.ndarray]
    ) -> Dict[int, np.ndarray]:
        """
        Initialize centroids using K-means++ algorithm
        
        Args:
            vectors: List of feature vectors
            
        Returns:
            Initial centroids
        """
        centroids = {}
        
        # Choose first centroid randomly
        first_idx = np.random.randint(0, len(vectors))
        centroids[0] = vectors[first_idx]
        
        # Choose remaining centroids
        for k in range(1, self.n_clusters):
            # Calculate distances to nearest centroid
            distances = []
            for vector in vectors:
                min_dist = float('inf')
                for centroid in centroids.values():
                    dist = np.linalg.norm(vector - centroid)
                    min_dist = min(min_dist, dist)
                distances.append(min_dist ** 2)
            
            # Choose next centroid with probability proportional to distance
            distances = np.array(distances)
            probabilities = distances / distances.sum()
            next_idx = np.random.choice(len(vectors), p=probabilities)
            centroids[k] = vectors[next_idx]
        
        return centroids
    
    def _assign_to_cluster(
        self,
        vector: np.ndarray,
        centroids: Dict[int, np.ndarray]
    ) -> int:
        """
        Assign vector to nearest cluster
        
        Args:
            vector: Feature vector
            centroids: Cluster centroids
            
        Returns:
            Cluster ID
        """
        min_dist = float('inf')
        assigned_cluster = 0
        
        for cluster_id, centroid in centroids.items():
            dist = np.linalg.norm(vector - centroid)
            if dist < min_dist:
                min_dist = dist
                assigned_cluster = cluster_id
        
        return assigned_cluster
    
    async def _build_cluster_profiles(
        self,
        clusters: Dict[int, List[Tuple[str, np.ndarray]]]
    ) -> None:
        """
        Build preference profiles for each cluster
        
        Args:
            clusters: Cluster assignments
        """
        for cluster_id, members in clusters.items():
            user_ids = [user_id for user_id, _ in members]
            
            # Aggregate preferences from cluster members
            # This would query user preferences and aggregate
            # For now, create a placeholder profile
            self.cluster_profiles[cluster_id] = {
                "n_members": len(members),
                "user_ids": user_ids[:10],  # Sample
                "avg_demographics": self._calculate_avg_demographics(members)
            }
    
    def _calculate_avg_demographics(
        self,
        members: List[Tuple[str, np.ndarray]]
    ) -> Dict[str, Any]:
        """Calculate average demographics for cluster"""
        if not members:
            return {}
        
        vectors = [v for _, v in members]
        avg_vector = np.mean(vectors, axis=0)
        
        return {
            "avg_vector": avg_vector.tolist(),
            "n_members": len(members)
        }
    
    async def get_recommendations(
        self,
        user_id: str,
        candidate_items: List[str],
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get demographic-based recommendations
        
        Args:
            user_id: User ID
            candidate_items: Candidate item IDs
            n_recommendations: Number of recommendations
            
        Returns:
            List of (item_id, score) tuples
        """
        try:
            # Get user's cluster
            cluster_id = self.user_clusters.get(user_id)
            
            if cluster_id is None:
                # Assign user to cluster based on demographics
                cluster_id = await self._assign_user_to_cluster(user_id)
            
            if cluster_id is None:
                return []
            
            # Get cluster profile
            cluster_profile = self.cluster_profiles.get(cluster_id, {})
            
            # Score items based on cluster preferences
            # This is simplified - in production, use cluster's aggregate preferences
            scores = []
            base_score = 0.7  # Base score for cluster members
            
            for item_id in candidate_items:
                # Add some variance
                score = base_score + np.random.normal(0, 0.1)
                score = max(0.0, min(1.0, score))
                scores.append((item_id, float(score)))
            
            # Sort by score
            scores.sort(key=lambda x: x[1], reverse=True)
            
            return scores[:n_recommendations]
            
        except Exception as e:
            logger.error("demographic_recommendations_failed",
                        user_id=user_id,
                        error=str(e))
            return []
    
    async def _assign_user_to_cluster(self, user_id: str) -> Optional[int]:
        """
        Assign user to cluster based on demographics
        
        Args:
            user_id: User ID
            
        Returns:
            Cluster ID or None
        """
        # Get user demographics
        result = await self.db.execute(
            select(UserColdStartData).where(
                UserColdStartData.user_id == user_id
            )
        )
        cold_start = result.scalar_one_or_none()
        
        if not cold_start:
            return None
        
        # Encode demographics
        demographics = {
            "age_range": cold_start.age_range,
            "education_level": cold_start.education_level,
            "occupation": cold_start.occupation
        }
        
        vector = self._encode_demographics(demographics)
        if vector is None:
            return None
        
        # Assign to nearest cluster
        cluster_id = self._assign_to_cluster(vector, self.cluster_centroids)
        self.user_clusters[user_id] = cluster_id
        
        return cluster_id
    
    def get_cluster_info(self, cluster_id: int) -> Dict[str, Any]:
        """
        Get information about a cluster
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Cluster information
        """
        if cluster_id not in self.cluster_profiles:
            return {}
        
        profile = self.cluster_profiles[cluster_id]
        centroid = self.cluster_centroids.get(cluster_id)
        
        return {
            "cluster_id": cluster_id,
            "n_members": profile.get("n_members", 0),
            "centroid": centroid.tolist() if centroid is not None else None,
            "sample_users": profile.get("user_ids", [])
        }
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            "n_clusters": len(self.cluster_centroids),
            "n_users_clustered": len(self.user_clusters),
            "cluster_sizes": {
                cluster_id: profile.get("n_members", 0)
                for cluster_id, profile in self.cluster_profiles.items()
            },
            "trained": len(self.cluster_centroids) > 0
        }


def get_demographic_filter(db: AsyncSession) -> DemographicFilter:
    """Get demographic filter instance"""
    return DemographicFilter(db)
