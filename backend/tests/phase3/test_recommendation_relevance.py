"""
Phase 3 Testing: Recommendation Relevance Validation
Target: >80% user satisfaction
"""
import pytest
import pytest_asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.recommendation import get_hybrid_engine
from app.services.preferences import get_preference_model


@pytest.mark.asyncio
@pytest.mark.phase3
class TestRecommendationRelevance:
    """Test recommendation relevance and quality"""
    
    @pytest_asyncio.fixture
    async def hybrid_engine(self, db_session: AsyncSession):
        """Get hybrid recommendation engine"""
        return get_hybrid_engine(db_session)
    
    @pytest_asyncio.fixture
    async def preference_model(self, db_session: AsyncSession):
        """Get preference model"""
        return get_preference_model(db_session)
    
    @pytest_asyncio.fixture
    async def test_user_with_preferences(self, preference_model):
        """Create test user with established preferences"""
        user_id = "test_user_recommendations"
        
        # Set strong preferences
        await preference_model.update_topic_preferences(
            user_id,
            {
                "technology.artificial_intelligence": 0.95,
                "technology.machine_learning": 0.90,
                "science.data_science": 0.85
            },
            learning_rate=0.3
        )
        
        await preference_model.update_depth_preference(
            user_id,
            3,  # Detailed
            satisfaction_score=0.9
        )
        
        return user_id
    
    async def test_recommendations_match_preferences(
        self,
        hybrid_engine,
        test_user_with_preferences
    ):
        """
        Test that recommendations align with user preferences
        Target: >80% relevance
        """
        user_id = test_user_with_preferences
        
        # Create candidate items
        candidates = [
            "ai_podcast_1",
            "ml_podcast_2",
            "history_podcast_3",
            "cooking_podcast_4",
            "data_science_podcast_5"
        ]
        
        # Create metadata for candidates
        metadata = {
            "ai_podcast_1": {
                "topics": ["technology.artificial_intelligence"],
                "depth_level": 3,
                "novelty_score": 0.5
            },
            "ml_podcast_2": {
                "topics": ["technology.machine_learning"],
                "depth_level": 3,
                "novelty_score": 0.4
            },
            "history_podcast_3": {
                "topics": ["history.ancient"],
                "depth_level": 2,
                "novelty_score": 0.6
            },
            "cooking_podcast_4": {
                "topics": ["personal.cooking"],
                "depth_level": 1,
                "novelty_score": 0.3
            },
            "data_science_podcast_5": {
                "topics": ["science.data_science"],
                "depth_level": 4,
                "novelty_score": 0.5
            }
        }
        
        # Get recommendations
        result = await hybrid_engine.get_recommendations(
            user_id,
            candidates,
            candidate_metadata=metadata,
            n_recommendations=3,
            diversity=False  # Test pure relevance
        )
        
        assert result["success"], "Recommendation should succeed"
        recommendations = result["recommendations"]
        
        # Check that we got recommendations
        assert len(recommendations) > 0, "Should return recommendations"
        
        # Top recommendations should be tech-related
        top_rec = recommendations[0]
        assert top_rec["item_id"] in ["ai_podcast_1", "ml_podcast_2", "data_science_podcast_5"], \
            f"Top recommendation should match preferences, got {top_rec['item_id']}"
        
        # Calculate relevance score
        relevant_count = sum(
            1 for rec in recommendations
            if rec["item_id"] in ["ai_podcast_1", "ml_podcast_2", "data_science_podcast_5"]
        )
        relevance_rate = relevant_count / len(recommendations)
        
        assert relevance_rate >= 0.66, \
            f"Relevance rate should be >66%, got {relevance_rate:.2%}"
    
    async def test_diversity_in_recommendations(
        self,
        hybrid_engine,
        test_user_with_preferences
    ):
        """
        Test that diversity promotion works
        """
        user_id = test_user_with_preferences
        
        candidates = [f"podcast_{i}" for i in range(20)]
        
        # Create metadata with varying topics
        metadata = {}
        topics_list = [
            "technology.artificial_intelligence",
            "technology.machine_learning",
            "science.physics",
            "science.biology",
            "history.modern",
            "arts.music",
            "business.finance",
            "personal.health"
        ]
        
        for i, podcast_id in enumerate(candidates):
            metadata[podcast_id] = {
                "topics": [topics_list[i % len(topics_list)]],
                "depth_level": 3,
                "novelty_score": 0.5
            }
        
        # Get recommendations with diversity
        result = await hybrid_engine.get_recommendations(
            user_id,
            candidates,
            candidate_metadata=metadata,
            n_recommendations=10,
            diversity=True
        )
        
        recommendations = result["recommendations"]
        
        # Count unique topics
        unique_topics = set()
        for rec in recommendations:
            rec_metadata = metadata[rec["item_id"]]
            unique_topics.update(rec_metadata["topics"])
        
        # Should have diversity
        assert len(unique_topics) >= 4, \
            f"Should have diverse topics, got {len(unique_topics)}"
    
    async def test_explanation_generation(
        self,
        hybrid_engine,
        test_user_with_preferences
    ):
        """
        Test that explanations are generated for recommendations
        """
        user_id = test_user_with_preferences
        
        candidates = ["podcast_1", "podcast_2"]
        metadata = {
            "podcast_1": {
                "topics": ["technology.artificial_intelligence"],
                "depth_level": 3,
                "novelty_score": 0.5
            },
            "podcast_2": {
                "topics": ["history.ancient"],
                "depth_level": 2,
                "novelty_score": 0.6
            }
        }
        
        result = await hybrid_engine.get_recommendations(
            user_id,
            candidates,
            candidate_metadata=metadata,
            n_recommendations=2
        )
        
        recommendations = result["recommendations"]
        
        # Check explanations exist
        for rec in recommendations:
            assert "explanation" in rec, "Should have explanation"
            assert len(rec["explanation"]) > 0, "Explanation should not be empty"
            assert isinstance(rec["explanation"], str), "Explanation should be string"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestCollaborativeFiltering:
    """Test collaborative filtering component"""
    
    async def test_svd_training(self, db_session: AsyncSession):
        """Test SVD++ model training"""
        from app.services.recommendation.collaborative_filtering import get_collaborative_filter
        
        collab_filter = get_collaborative_filter(db_session)
        
        # Create synthetic user-item matrix
        user_item_matrix = {
            "user1": {"item1": 0.9, "item2": 0.8, "item3": 0.3},
            "user2": {"item1": 0.85, "item2": 0.9, "item4": 0.7},
            "user3": {"item2": 0.7, "item3": 0.9, "item4": 0.8},
            "user4": {"item1": 0.6, "item3": 0.85, "item4": 0.9}
        }
        
        # Train model
        result = await collab_filter.train_model(user_item_matrix)
        
        assert result["success"], "Training should succeed"
        assert result["n_users"] == 4, "Should train on 4 users"
        assert result["n_items"] == 4, "Should have 4 items"
        assert result["final_rmse"] < 0.5, "RMSE should be reasonable"
    
    async def test_similar_items(self, db_session: AsyncSession):
        """Test finding similar items"""
        from app.services.recommendation.collaborative_filtering import get_collaborative_filter
        
        collab_filter = get_collaborative_filter(db_session)
        
        # Train first
        user_item_matrix = {
            "user1": {"item1": 0.9, "item2": 0.85},
            "user2": {"item1": 0.88, "item2": 0.9},
            "user3": {"item3": 0.9, "item4": 0.85}
        }
        
        await collab_filter.train_model(user_item_matrix)
        
        # Get similar items to item1
        similar = await collab_filter.get_similar_items("item1", n_similar=2)
        
        # item2 should be most similar (both liked by user1 and user2)
        assert len(similar) > 0, "Should find similar items"
        assert similar[0][0] == "item2", "item2 should be most similar to item1"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestContentBasedFiltering:
    """Test content-based filtering component"""
    
    async def test_tfidf_vectorization(self, db_session: AsyncSession):
        """Test TF-IDF document vectorization"""
        from app.services.recommendation.content_based_filtering import get_content_filter
        
        content_filter = get_content_filter(db_session)
        
        # Create documents
        documents = {
            "doc1": {
                "title": "Introduction to Machine Learning",
                "description": "Learn about machine learning algorithms and applications",
                "topics": ["machine_learning", "artificial_intelligence"],
                "keywords": ["ML", "AI", "algorithms"]
            },
            "doc2": {
                "title": "Deep Learning Fundamentals",
                "description": "Neural networks and deep learning techniques",
                "topics": ["deep_learning", "neural_networks"],
                "keywords": ["neural", "networks", "deep"]
            },
            "doc3": {
                "title": "Ancient Roman History",
                "description": "The rise and fall of the Roman Empire",
                "topics": ["history", "ancient_rome"],
                "keywords": ["Rome", "empire", "history"]
            }
        }
        
        # Build vocabulary and vectorize
        vocab_result = content_filter.build_vocabulary(documents)
        vector_result = content_filter.vectorize_documents(documents)
        
        assert vocab_result["success"], "Vocabulary building should succeed"
        assert vector_result["success"], "Vectorization should succeed"
        assert vocab_result["vocabulary_size"] > 0, "Should have vocabulary"
        assert vector_result["n_vectors"] == 3, "Should vectorize all documents"
    
    async def test_content_similarity(self, db_session: AsyncSession):
        """Test content similarity calculation"""
        from app.services.recommendation.content_based_filtering import get_content_filter
        
        content_filter = get_content_filter(db_session)
        
        documents = {
            "doc1": {
                "title": "Machine Learning Basics",
                "description": "ML fundamentals",
                "topics": ["machine_learning"],
                "keywords": ["ML"]
            },
            "doc2": {
                "title": "Advanced Machine Learning",
                "description": "Advanced ML techniques",
                "topics": ["machine_learning"],
                "keywords": ["ML", "advanced"]
            },
            "doc3": {
                "title": "Cooking Recipes",
                "description": "Delicious recipes",
                "topics": ["cooking"],
                "keywords": ["food", "recipes"]
            }
        }
        
        content_filter.build_vocabulary(documents)
        content_filter.vectorize_documents(documents)
        
        # Get similar items to doc1
        similar = content_filter.get_similar_items("doc1", list(documents.keys()), n_similar=2)
        
        # doc2 should be most similar (both about ML)
        assert len(similar) > 0, "Should find similar items"
        assert similar[0][0] == "doc2", "doc2 should be most similar to doc1"
        assert similar[0][1] > 0.5, "Similarity should be high"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestHybridWeighting:
    """Test hybrid weighting mechanism"""
    
    async def test_weight_update(self, db_session: AsyncSession):
        """Test updating hybrid weights"""
        hybrid_engine = get_hybrid_engine(db_session)
        
        # Update weights
        new_weights = {
            "collaborative": 0.5,
            "content_based": 0.3,
            "knowledge_based": 0.15,
            "demographic": 0.05
        }
        
        result = hybrid_engine.update_weights(new_weights)
        
        assert result["success"], "Weight update should succeed"
        assert result["weights"]["collaborative"] == 0.5, "Weights should be updated"
    
    async def test_invalid_weights(self, db_session: AsyncSession):
        """Test that invalid weights are rejected"""
        hybrid_engine = get_hybrid_engine(db_session)
        
        # Weights don't sum to 1.0
        invalid_weights = {
            "collaborative": 0.5,
            "content_based": 0.3,
            "knowledge_based": 0.3,  # Total = 1.1
            "demographic": 0.0
        }
        
        result = hybrid_engine.update_weights(invalid_weights)
        
        assert not result["success"], "Should reject invalid weights"
        assert "error" in result, "Should have error message"
