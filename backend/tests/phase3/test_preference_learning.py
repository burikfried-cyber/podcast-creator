"""
Phase 3 Testing: Preference Learning Accuracy Tests
Target: >85% accuracy after 5 interactions
"""
import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.preferences import get_preference_model
from app.models.preferences import UserTopicPreference, UserDepthPreference


@pytest.mark.asyncio
@pytest.mark.phase3
class TestPreferenceLearning:
    """Test preference learning accuracy"""
    
    @pytest_asyncio.fixture
    async def preference_model(self, db_session: AsyncSession):
        """Get preference model instance"""
        return get_preference_model(db_session)
    
    @pytest_asyncio.fixture
    async def test_user_id(self):
        """Test user ID"""
        return "test_user_preference_learning"
    
    async def test_topic_preference_convergence(
        self,
        preference_model,
        test_user_id
    ):
        """
        Test topic preference convergence after 5 interactions
        Target: >85% accuracy
        """
        # Simulate 5 interactions with consistent topic
        target_topic = "technology.artificial_intelligence"
        interactions = [
            {"technology.artificial_intelligence": 0.9},
            {"technology.artificial_intelligence": 0.85},
            {"technology.artificial_intelligence": 0.95},
            {"technology.artificial_intelligence": 0.88},
            {"technology.artificial_intelligence": 0.92}
        ]
        
        # Apply interactions
        for signals in interactions:
            await preference_model.update_topic_preferences(
                test_user_id,
                signals,
                learning_rate=0.1
            )
        
        # Get final preference
        prefs = await preference_model.get_topic_preferences(test_user_id)
        
        # Check if preference weight is high (>0.85)
        ai_pref = next(
            (p for p in prefs if p["subcategory"] == "artificial_intelligence"),
            None
        )
        
        assert ai_pref is not None, "AI preference should exist"
        assert ai_pref["preference_weight"] > 0.85, \
            f"Preference weight should be >0.85, got {ai_pref['preference_weight']}"
        assert ai_pref["confidence_score"] > 0.7, \
            "Confidence should be high after 5 interactions"
    
    async def test_depth_preference_bayesian_optimization(
        self,
        preference_model,
        test_user_id
    ):
        """
        Test depth preference optimization with Bayesian approach
        Target: Converge to preferred depth
        """
        # Simulate interactions at different depths
        # User prefers depth level 3 (detailed)
        interactions = [
            (3, 0.9),  # Detailed - high satisfaction
            (2, 0.6),  # Moderate - medium satisfaction
            (3, 0.95), # Detailed - high satisfaction
            (4, 0.5),  # Deep - too much
            (3, 0.88)  # Detailed - high satisfaction
        ]
        
        for depth, satisfaction in interactions:
            await preference_model.update_depth_preference(
                test_user_id,
                depth,
                satisfaction_score=satisfaction
            )
        
        # Get final preference
        depth_pref = await preference_model.get_depth_preference(test_user_id)
        
        # Should converge to depth 3
        assert depth_pref["preferred_depth"] == 3, \
            f"Should prefer depth 3, got {depth_pref['preferred_depth']}"
        assert depth_pref["confidence_score"] > 0.7, \
            "Confidence should be high"
    
    async def test_surprise_preference_q_learning(
        self,
        preference_model,
        test_user_id
    ):
        """
        Test surprise preference learning with Q-learning
        Target: Learn optimal surprise tolerance
        """
        # Simulate interactions with different surprise levels
        # User prefers balanced surprise (level 2)
        interactions = [
            (2, 0.85),  # Balanced - good reward
            (1, 0.6),   # Familiar - okay
            (2, 0.9),   # Balanced - good reward
            (3, 0.5),   # Adventurous - too much
            (2, 0.88)   # Balanced - good reward
        ]
        
        for surprise_level, reward in interactions:
            await preference_model.update_surprise_preference(
                test_user_id,
                surprise_level,
                reward=reward
            )
        
        # Get final preference
        surprise_pref = await preference_model.get_surprise_preference(test_user_id)
        
        # Should converge to level 2
        assert surprise_pref["surprise_tolerance"] == 2, \
            f"Should prefer surprise level 2, got {surprise_pref['surprise_tolerance']}"
        assert surprise_pref["confidence_score"] > 0.7, \
            "Confidence should be high"
    
    async def test_multi_topic_learning(
        self,
        preference_model,
        test_user_id
    ):
        """
        Test learning multiple topic preferences simultaneously
        """
        # Simulate diverse interactions
        interactions = [
            {"technology.artificial_intelligence": 0.9, "science.physics": 0.7},
            {"technology.artificial_intelligence": 0.85, "history.ancient": 0.6},
            {"science.physics": 0.8, "technology.programming": 0.75},
            {"technology.artificial_intelligence": 0.95, "science.physics": 0.85},
            {"technology.programming": 0.8, "science.physics": 0.9}
        ]
        
        for signals in interactions:
            await preference_model.update_topic_preferences(
                test_user_id,
                signals,
                learning_rate=0.1
            )
        
        # Get all preferences
        prefs = await preference_model.get_topic_preferences(test_user_id)
        
        # Check that multiple topics have been learned
        assert len(prefs) >= 4, "Should learn multiple topics"
        
        # Check top preferences
        top_prefs = sorted(prefs, key=lambda x: x["preference_weight"], reverse=True)[:3]
        
        # AI should be top (appeared 3 times with high scores)
        assert "artificial_intelligence" in top_prefs[0]["subcategory"], \
            "AI should be top preference"
        
        # Physics should be in top 3 (appeared 4 times)
        physics_in_top = any("physics" in p["subcategory"] for p in top_prefs)
        assert physics_in_top, "Physics should be in top 3"
    
    async def test_preference_confidence_growth(
        self,
        preference_model,
        test_user_id
    ):
        """
        Test that confidence grows with more interactions
        """
        topic = "business.entrepreneurship"
        
        # Track confidence over interactions
        confidences = []
        
        for i in range(10):
            await preference_model.update_topic_preferences(
                test_user_id,
                {topic: 0.8},
                learning_rate=0.1
            )
            
            prefs = await preference_model.get_topic_preferences(test_user_id)
            pref = next(
                (p for p in prefs if p["subcategory"] == "entrepreneurship"),
                None
            )
            
            if pref:
                confidences.append(pref["confidence_score"])
        
        # Confidence should generally increase
        assert len(confidences) >= 5, "Should have multiple confidence measurements"
        assert confidences[-1] > confidences[0], \
            "Confidence should increase over time"
        assert confidences[-1] > 0.8, \
            "Final confidence should be high"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestPreferencePersistence:
    """Test preference persistence and retrieval"""
    
    @pytest_asyncio.fixture
    async def preference_model(self, db_session: AsyncSession):
        """Get preference model instance"""
        return get_preference_model(db_session)
    
    async def test_preference_persistence(
        self,
        preference_model,
        db_session: AsyncSession
    ):
        """Test that preferences are persisted correctly"""
        user_id = "test_user_persistence"
        
        # Set preferences
        await preference_model.update_topic_preferences(
            user_id,
            {"technology.blockchain": 0.9},
            learning_rate=0.1
        )
        
        await preference_model.update_depth_preference(
            user_id,
            4,
            satisfaction_score=0.85
        )
        
        # Commit and clear session
        await db_session.commit()
        
        # Retrieve preferences (should come from database)
        topic_prefs = await preference_model.get_topic_preferences(user_id)
        depth_pref = await preference_model.get_depth_preference(user_id)
        
        # Verify persistence
        assert len(topic_prefs) > 0, "Topic preferences should be persisted"
        assert depth_pref is not None, "Depth preference should be persisted"
        
        blockchain_pref = next(
            (p for p in topic_prefs if p["subcategory"] == "blockchain"),
            None
        )
        assert blockchain_pref is not None, "Blockchain preference should exist"
        assert blockchain_pref["preference_weight"] > 0.5, \
            "Preference weight should be persisted"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestLearningRateAdaptation:
    """Test adaptive learning rate"""
    
    @pytest_asyncio.fixture
    async def preference_model(self, db_session: AsyncSession):
        """Get preference model instance"""
        return get_preference_model(db_session)
    
    async def test_high_learning_rate_fast_adaptation(
        self,
        preference_model
    ):
        """Test that high learning rate adapts quickly"""
        user_id = "test_user_fast_adapt"
        
        # Single interaction with high learning rate
        await preference_model.update_topic_preferences(
            user_id,
            {"arts.music": 0.9},
            learning_rate=0.5  # High learning rate
        )
        
        prefs = await preference_model.get_topic_preferences(user_id)
        music_pref = next(
            (p for p in prefs if p["subcategory"] == "music"),
            None
        )
        
        # Should adapt quickly
        assert music_pref is not None
        assert music_pref["preference_weight"] > 0.7, \
            "High learning rate should cause fast adaptation"
    
    async def test_low_learning_rate_slow_adaptation(
        self,
        preference_model
    ):
        """Test that low learning rate adapts slowly"""
        user_id = "test_user_slow_adapt"
        
        # Single interaction with low learning rate
        await preference_model.update_topic_preferences(
            user_id,
            {"arts.painting": 0.9},
            learning_rate=0.01  # Low learning rate
        )
        
        prefs = await preference_model.get_topic_preferences(user_id)
        painting_pref = next(
            (p for p in prefs if p["subcategory"] == "painting"),
            None
        )
        
        # Should adapt slowly
        assert painting_pref is not None
        assert painting_pref["preference_weight"] < 0.6, \
            "Low learning rate should cause slow adaptation"
