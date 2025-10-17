"""
Content-Based Filtering with TF-IDF
Recommends items based on content similarity using TF-IDF and topic embeddings
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import Counter, defaultdict
import math
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.preferences import UserTopicPreference, UserBehavioralSignal

logger = structlog.get_logger()


class ContentBasedFilter:
    """
    Content-Based Filtering using TF-IDF and Cosine Similarity
    
    Features:
    - TF-IDF vectorization of content
    - Topic embeddings
    - Cosine similarity for matching
    - User profile building from history
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # TF-IDF data structures
        self.document_vectors = {}  # item_id -> TF-IDF vector
        self.vocabulary = set()
        self.idf_scores = {}  # term -> IDF score
        self.document_count = 0
        
        # Topic embeddings (simplified - in production use Word2Vec/BERT)
        self.topic_embeddings = {}  # topic -> embedding vector
        self.embedding_dim = 50
        
        # User profiles
        self.user_profiles = {}  # user_id -> profile vector
    
    def build_vocabulary(
        self,
        documents: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build vocabulary and calculate IDF scores
        
        Args:
            documents: {item_id: {title, description, topics, keywords}}
            
        Returns:
            Vocabulary statistics
        """
        try:
            logger.info("building_vocabulary", n_documents=len(documents))
            
            # Extract all terms
            term_document_frequency = Counter()
            
            for item_id, content in documents.items():
                # Tokenize content
                terms = self._tokenize_content(content)
                unique_terms = set(terms)
                
                # Update vocabulary
                self.vocabulary.update(unique_terms)
                
                # Count document frequency for each term
                for term in unique_terms:
                    term_document_frequency[term] += 1
            
            self.document_count = len(documents)
            
            # Calculate IDF scores
            for term, doc_freq in term_document_frequency.items():
                # IDF = log(N / df)
                self.idf_scores[term] = math.log(self.document_count / doc_freq)
            
            logger.info("vocabulary_built",
                       vocabulary_size=len(self.vocabulary),
                       document_count=self.document_count)
            
            return {
                "success": True,
                "vocabulary_size": len(self.vocabulary),
                "document_count": self.document_count,
                "avg_idf": np.mean(list(self.idf_scores.values())) if self.idf_scores else 0.0
            }
            
        except Exception as e:
            logger.error("vocabulary_building_failed", error=str(e))
            raise
    
    def vectorize_documents(
        self,
        documents: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create TF-IDF vectors for all documents
        
        Args:
            documents: {item_id: {title, description, topics, keywords}}
            
        Returns:
            Vectorization statistics
        """
        try:
            logger.info("vectorizing_documents", n_documents=len(documents))
            
            for item_id, content in documents.items():
                # Tokenize
                terms = self._tokenize_content(content)
                
                # Calculate term frequencies
                term_freq = Counter(terms)
                total_terms = len(terms)
                
                # Create TF-IDF vector
                vector = {}
                for term, count in term_freq.items():
                    if term in self.idf_scores:
                        # TF = count / total_terms
                        tf = count / total_terms
                        # TF-IDF = TF * IDF
                        vector[term] = tf * self.idf_scores[term]
                
                # Normalize vector (L2 normalization)
                norm = math.sqrt(sum(v ** 2 for v in vector.values()))
                if norm > 0:
                    vector = {term: score / norm for term, score in vector.items()}
                
                self.document_vectors[item_id] = vector
            
            logger.info("documents_vectorized",
                       n_vectors=len(self.document_vectors))
            
            return {
                "success": True,
                "n_vectors": len(self.document_vectors),
                "avg_vector_size": np.mean([len(v) for v in self.document_vectors.values()]) if self.document_vectors else 0
            }
            
        except Exception as e:
            logger.error("vectorization_failed", error=str(e))
            raise
    
    def _tokenize_content(self, content: Dict[str, Any]) -> List[str]:
        """
        Tokenize content into terms
        
        Args:
            content: Content dictionary
            
        Returns:
            List of terms
        """
        terms = []
        
        # Extract from title (higher weight)
        if "title" in content:
            title_terms = self._simple_tokenize(content["title"])
            terms.extend(title_terms * 3)  # Title terms weighted 3x
        
        # Extract from description
        if "description" in content:
            desc_terms = self._simple_tokenize(content["description"])
            terms.extend(desc_terms)
        
        # Extract from topics
        if "topics" in content:
            if isinstance(content["topics"], list):
                terms.extend(content["topics"])
            elif isinstance(content["topics"], str):
                terms.extend(content["topics"].split(","))
        
        # Extract from keywords
        if "keywords" in content:
            if isinstance(content["keywords"], list):
                terms.extend(content["keywords"] * 2)  # Keywords weighted 2x
            elif isinstance(content["keywords"], str):
                terms.extend(content["keywords"].split(",") * 2)
        
        return terms
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization (split by whitespace and lowercase)
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Remove punctuation and lowercase
        text = text.lower()
        for char in ".,!?;:()[]{}\"'":
            text = text.replace(char, " ")
        
        # Split and filter
        tokens = [t.strip() for t in text.split() if len(t.strip()) > 2]
        
        # Remove common stop words
        stop_words = {
            "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "up", "about", "into", "through",
            "during", "before", "after", "above", "below", "between", "under"
        }
        tokens = [t for t in tokens if t not in stop_words]
        
        return tokens
    
    async def build_user_profile(
        self,
        user_id: str,
        user_history: List[str]
    ) -> Dict[str, Any]:
        """
        Build user profile from interaction history
        
        Args:
            user_id: User ID
            user_history: List of item IDs user interacted with
            
        Returns:
            Profile building status
        """
        try:
            # Get user's topic preferences
            result = await self.db.execute(
                select(UserTopicPreference).where(
                    UserTopicPreference.user_id == user_id
                ).order_by(UserTopicPreference.preference_weight.desc())
            )
            topic_prefs = result.scalars().all()
            
            # Aggregate vectors from user history
            profile_vector = defaultdict(float)
            
            for item_id in user_history:
                if item_id in self.document_vectors:
                    item_vector = self.document_vectors[item_id]
                    for term, score in item_vector.items():
                        profile_vector[term] += score
            
            # Incorporate topic preferences
            for topic_pref in topic_prefs:
                topic_key = f"{topic_pref.topic_category}.{topic_pref.subcategory}"
                weight = float(topic_pref.preference_weight)
                profile_vector[topic_key] += weight
            
            # Normalize profile vector
            if profile_vector:
                norm = math.sqrt(sum(v ** 2 for v in profile_vector.values()))
                if norm > 0:
                    profile_vector = {
                        term: score / norm
                        for term, score in profile_vector.items()
                    }
            
            self.user_profiles[user_id] = dict(profile_vector)
            
            logger.info("user_profile_built",
                       user_id=user_id,
                       profile_size=len(profile_vector))
            
            return {
                "success": True,
                "user_id": user_id,
                "profile_size": len(profile_vector),
                "history_items": len(user_history),
                "topic_preferences": len(topic_prefs)
            }
            
        except Exception as e:
            logger.error("user_profile_building_failed",
                        user_id=user_id,
                        error=str(e))
            raise
    
    def calculate_similarity(
        self,
        vector1: Dict[str, float],
        vector2: Dict[str, float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vector1: First vector
            vector2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        # Get common terms
        common_terms = set(vector1.keys()) & set(vector2.keys())
        
        if not common_terms:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(vector1[term] * vector2[term] for term in common_terms)
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vector1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vector2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = dot_product / (mag1 * mag2)
        
        return max(0.0, min(1.0, similarity))  # Clip to [0, 1]
    
    async def get_recommendations(
        self,
        user_id: str,
        candidate_items: List[str],
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get content-based recommendations for user
        
        Args:
            user_id: User ID
            candidate_items: List of candidate item IDs
            n_recommendations: Number of recommendations
            
        Returns:
            List of (item_id, score) tuples
        """
        try:
            # Get or build user profile
            if user_id not in self.user_profiles:
                # Build from behavioral signals
                result = await self.db.execute(
                    select(UserBehavioralSignal.podcast_id).where(
                        and_(
                            UserBehavioralSignal.user_id == user_id,
                            UserBehavioralSignal.podcast_id.isnot(None)
                        )
                    ).distinct().limit(50)
                )
                user_history = [str(row[0]) for row in result.fetchall()]
                await self.build_user_profile(user_id, user_history)
            
            user_profile = self.user_profiles.get(user_id, {})
            
            if not user_profile:
                return []
            
            # Calculate similarity for each candidate
            scores = []
            for item_id in candidate_items:
                if item_id in self.document_vectors:
                    item_vector = self.document_vectors[item_id]
                    similarity = self.calculate_similarity(user_profile, item_vector)
                    scores.append((item_id, float(similarity)))
            
            # Sort by similarity
            scores.sort(key=lambda x: x[1], reverse=True)
            
            return scores[:n_recommendations]
            
        except Exception as e:
            logger.error("content_recommendations_failed",
                        user_id=user_id,
                        error=str(e))
            return []
    
    def get_similar_items(
        self,
        item_id: str,
        candidate_items: List[str],
        n_similar: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get similar items based on content
        
        Args:
            item_id: Item ID
            candidate_items: Candidate items to compare
            n_similar: Number of similar items
            
        Returns:
            List of (item_id, similarity) tuples
        """
        if item_id not in self.document_vectors:
            return []
        
        item_vector = self.document_vectors[item_id]
        
        # Calculate similarity with candidates
        similarities = []
        for candidate_id in candidate_items:
            if candidate_id != item_id and candidate_id in self.document_vectors:
                candidate_vector = self.document_vectors[candidate_id]
                similarity = self.calculate_similarity(item_vector, candidate_vector)
                similarities.append((candidate_id, float(similarity)))
        
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
            "vocabulary_size": len(self.vocabulary),
            "document_count": self.document_count,
            "n_vectors": len(self.document_vectors),
            "n_user_profiles": len(self.user_profiles),
            "avg_vector_size": np.mean([len(v) for v in self.document_vectors.values()]) if self.document_vectors else 0,
            "trained": len(self.document_vectors) > 0
        }


def get_content_filter(db: AsyncSession) -> ContentBasedFilter:
    """Get content-based filter instance"""
    return ContentBasedFilter(db)
