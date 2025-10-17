"""
Phase 3 Testing: Behavioral Pattern Recognition Tests
Target: >90% state prediction accuracy
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.learning import (
    get_hmm_tracker,
    get_lstm_recognizer,
    get_bandit_selector
)


@pytest.mark.asyncio
@pytest.mark.phase3
class TestHMMEngagement:
    """Test HMM engagement tracking"""
    
    @pytest_asyncio.fixture
    async def hmm_tracker(self, db_session: AsyncSession):
        """Get HMM tracker"""
        return get_hmm_tracker(db_session)
    
    @pytest_asyncio.fixture
    async def test_user_id(self):
        """Test user ID"""
        return "test_user_hmm"
    
    async def test_hmm_initialization(
        self,
        hmm_tracker,
        test_user_id
    ):
        """Test HMM initialization"""
        result = await hmm_tracker.initialize_hmm(test_user_id)
        
        assert result["success"], "HMM initialization should succeed"
        assert result["n_states"] == 4, "Should have 4 states"
        assert result["n_observations"] == 5, "Should have 5 observations"
    
    async def test_state_inference(
        self,
        hmm_tracker,
        test_user_id
    ):
        """Test state inference from observations"""
        # Initialize
        await hmm_tracker.initialize_hmm(test_user_id)
        
        # Provide observations indicating engagement
        observations = [
            {"playback_speed": 1.0, "pauses": 0, "skips": 0, "replays": 1, "completion": 0.9},
            {"playback_speed": 1.0, "pauses": 1, "skips": 0, "replays": 0, "completion": 0.85},
            {"playback_speed": 1.0, "pauses": 0, "skips": 0, "replays": 2, "completion": 0.95}
        ]
        
        for obs in observations:
            result = await hmm_tracker.update_hmm(test_user_id, obs)
            assert result["success"], "Update should succeed"
        
        # Get current state
        state = await hmm_tracker.get_current_state(test_user_id)
        
        assert state is not None, "Should have current state"
        # With high completion and replays, should likely be "engaged"
        assert state["state"] in ["engaged", "distracted"], \
            f"State should be engaged or distracted, got {state['state']}"
    
    async def test_state_transition(
        self,
        hmm_tracker,
        test_user_id
    ):
        """Test state transitions"""
        await hmm_tracker.initialize_hmm(test_user_id)
        
        # Start with engaged behavior
        engaged_obs = {"playback_speed": 1.0, "pauses": 0, "skips": 0, "replays": 1, "completion": 0.9}
        await hmm_tracker.update_hmm(test_user_id, engaged_obs)
        
        state1 = await hmm_tracker.get_current_state(test_user_id)
        
        # Switch to bored behavior
        bored_obs = {"playback_speed": 1.5, "pauses": 3, "skips": 2, "replays": 0, "completion": 0.3}
        await hmm_tracker.update_hmm(test_user_id, bored_obs)
        await hmm_tracker.update_hmm(test_user_id, bored_obs)
        
        state2 = await hmm_tracker.get_current_state(test_user_id)
        
        # States should be different
        assert state1["state"] != state2["state"] or state1["probability"] != state2["probability"], \
            "State should change with different observations"
    
    async def test_hmm_accuracy_tracking(
        self,
        hmm_tracker,
        test_user_id
    ):
        """Test HMM accuracy tracking"""
        await hmm_tracker.initialize_hmm(test_user_id)
        
        # Provide observations and actual states
        observation = {"playback_speed": 1.0, "pauses": 0, "skips": 0, "replays": 1, "completion": 0.9}
        await hmm_tracker.update_hmm(test_user_id, observation)
        
        # Get HMM state
        hmm_state = await hmm_tracker.get_hmm_state(test_user_id)
        
        assert "accuracy" in hmm_state or hmm_state["accuracy"] is None, \
            "Should track accuracy"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestLSTMPatterns:
    """Test LSTM pattern recognition"""
    
    @pytest_asyncio.fixture
    async def lstm_recognizer(self, db_session: AsyncSession):
        """Get LSTM recognizer"""
        return get_lstm_recognizer(db_session)
    
    @pytest_asyncio.fixture
    async def test_user_id(self):
        """Test user ID"""
        return "test_user_lstm"
    
    async def test_lstm_initialization(
        self,
        lstm_recognizer,
        test_user_id
    ):
        """Test LSTM initialization"""
        result = await lstm_recognizer.initialize_lstm(test_user_id)
        
        assert result["success"], "LSTM initialization should succeed"
        assert result["model_version"] == "1.0", "Should have model version"
    
    async def test_pattern_prediction(
        self,
        lstm_recognizer,
        test_user_id
    ):
        """Test LSTM pattern prediction"""
        await lstm_recognizer.initialize_lstm(test_user_id)
        
        # Provide engagement sequence
        engagement_sequence = [0.8, 0.85, 0.9, 0.88, 0.92]
        content_features = {
            "duration": 45.0,
            "complexity": 0.7,
            "novelty": 0.5
        }
        context = {
            "time_of_day": "evening",
            "device": "mobile"
        }
        temporal_info = {
            "hour": 20.0,
            "day_of_week": 3.0
        }
        
        result = await lstm_recognizer.predict_patterns(
            test_user_id,
            engagement_sequence,
            content_features,
            context,
            temporal_info
        )
        
        assert result["success"], "Prediction should succeed"
        assert "predictions" in result, "Should have predictions"
        
        predictions = result["predictions"]
        assert "engagement_probability" in predictions
        assert "completion_likelihood" in predictions
        assert "preference_strength" in predictions
        assert "churn_risk" in predictions
        
        # All predictions should be in [0, 1]
        for key, value in predictions.items():
            assert 0 <= value <= 1, f"{key} should be in [0, 1], got {value}"
    
    async def test_lstm_online_learning(
        self,
        lstm_recognizer,
        test_user_id
    ):
        """Test LSTM online learning"""
        await lstm_recognizer.initialize_lstm(test_user_id)
        
        # Make prediction
        engagement_sequence = [0.7, 0.75, 0.8]
        result = await lstm_recognizer.predict_patterns(
            test_user_id,
            engagement_sequence,
            {"duration": 30.0},
            {"time_of_day": "morning"},
            {"hour": 9.0}
        )
        
        # Update with actual outcomes
        actual_outcomes = {
            "engagement_probability": 0.85,
            "completion_likelihood": 0.9
        }
        
        update_result = await lstm_recognizer.update_lstm(
            test_user_id,
            actual_outcomes
        )
        
        assert update_result["success"], "Update should succeed"
        assert "loss" in update_result, "Should calculate loss"
        assert "accuracy" in update_result, "Should calculate accuracy"
    
    async def test_lstm_sequence_history(
        self,
        lstm_recognizer,
        test_user_id
    ):
        """Test LSTM sequence history tracking"""
        await lstm_recognizer.initialize_lstm(test_user_id)
        
        # Make multiple predictions
        for i in range(5):
            await lstm_recognizer.predict_patterns(
                test_user_id,
                [0.7 + i * 0.05],
                {"duration": 30.0},
                {"time_of_day": "morning"},
                {"hour": 9.0}
            )
        
        # Get LSTM state
        state = await lstm_recognizer.get_lstm_state(test_user_id)
        
        assert state["initialized"], "Should be initialized"
        assert state["sequence_length"] == 5, "Should track 5 sequences"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestContextualBandits:
    """Test contextual bandits"""
    
    @pytest_asyncio.fixture
    async def bandit_selector(self, db_session: AsyncSession):
        """Get bandit selector"""
        return get_bandit_selector(db_session)
    
    @pytest_asyncio.fixture
    async def test_user_id(self):
        """Test user ID"""
        return "test_user_bandits"
    
    async def test_bandit_initialization(
        self,
        bandit_selector,
        test_user_id
    ):
        """Test bandit initialization"""
        result = await bandit_selector.initialize_bandits(test_user_id)
        
        assert result["success"], "Bandit initialization should succeed"
        assert result["contexts_initialized"] > 0, "Should initialize contexts"
    
    async def test_arm_selection(
        self,
        bandit_selector,
        test_user_id
    ):
        """Test UCB arm selection"""
        await bandit_selector.initialize_bandits(test_user_id)
        
        # Select arm
        context = {
            "time_of_day": "evening",
            "device_type": "mobile"
        }
        available_arms = ["arm1", "arm2", "arm3"]
        
        result = await bandit_selector.select_arm(
            test_user_id,
            context,
            available_arms
        )
        
        assert result["success"], "Arm selection should succeed"
        assert result["selected_arm"] in available_arms, \
            "Selected arm should be from available arms"
        assert "ucb_score" in result, "Should have UCB score"
    
    async def test_reward_update(
        self,
        bandit_selector,
        test_user_id
    ):
        """Test reward update for arms"""
        await bandit_selector.initialize_bandits(test_user_id)
        
        context = {"time_of_day": "morning"}
        
        # Select and update multiple times
        for i in range(5):
            # Select arm
            result = await bandit_selector.select_arm(
                test_user_id,
                context,
                ["arm1", "arm2"]
            )
            
            selected_arm = result["selected_arm"]
            
            # Update with reward
            reward = 0.8 if selected_arm == "arm1" else 0.3
            update_result = await bandit_selector.update_arm_reward(
                test_user_id,
                selected_arm,
                reward,
                context
            )
            
            assert update_result["success"], "Reward update should succeed"
        
        # Get stats
        stats = await bandit_selector.get_bandit_stats(test_user_id)
        
        assert stats["initialized"], "Should be initialized"
        assert stats["total_pulls"] == 5, "Should have 5 pulls"
        # arm1 should be best (higher reward)
        assert stats["best_arm"] == "arm1", "arm1 should be best"
    
    async def test_exploration_exploitation_tradeoff(
        self,
        bandit_selector,
        test_user_id
    ):
        """Test exploration vs exploitation"""
        await bandit_selector.initialize_bandits(test_user_id)
        
        context = {"time_of_day": "afternoon"}
        arms = ["arm1", "arm2", "arm3"]
        
        # Make arm1 clearly better
        for _ in range(10):
            await bandit_selector.update_arm_reward(
                test_user_id,
                "arm1",
                0.9,
                context
            )
        
        # Select multiple times
        selections = []
        for _ in range(20):
            result = await bandit_selector.select_arm(
                test_user_id,
                context,
                arms
            )
            selections.append(result["selected_arm"])
        
        # Should mostly select arm1 (exploitation) but sometimes explore
        arm1_count = selections.count("arm1")
        
        # Should exploit mostly (>60%) but not always (exploration)
        assert arm1_count >= 12, "Should mostly exploit best arm"
        assert arm1_count < 20, "Should still explore sometimes"
    
    async def test_regret_calculation(
        self,
        bandit_selector,
        test_user_id
    ):
        """Test regret calculation"""
        await bandit_selector.initialize_bandits(test_user_id)
        
        context = {"time_of_day": "evening"}
        
        # Update arms with different rewards
        await bandit_selector.update_arm_reward(test_user_id, "arm1", 0.9, context)
        await bandit_selector.update_arm_reward(test_user_id, "arm2", 0.5, context)
        await bandit_selector.update_arm_reward(test_user_id, "arm2", 0.4, context)
        
        # Get stats
        stats = await bandit_selector.get_bandit_stats(test_user_id)
        
        assert "regret" in stats, "Should calculate regret"
        assert stats["regret"] >= 0, "Regret should be non-negative"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestBehavioralIntegration:
    """Test integration of behavioral learning models"""
    
    async def test_all_models_initialized(
        self,
        db_session: AsyncSession
    ):
        """Test that all models can be initialized for a user"""
        user_id = "test_user_integration"
        
        hmm = get_hmm_tracker(db_session)
        lstm = get_lstm_recognizer(db_session)
        bandits = get_bandit_selector(db_session)
        
        # Initialize all
        hmm_result = await hmm.initialize_hmm(user_id)
        lstm_result = await lstm.initialize_lstm(user_id)
        bandit_result = await bandits.initialize_bandits(user_id)
        
        assert hmm_result["success"], "HMM should initialize"
        assert lstm_result["success"], "LSTM should initialize"
        assert bandit_result["success"], "Bandits should initialize"
    
    async def test_models_work_together(
        self,
        db_session: AsyncSession
    ):
        """Test that models can work together"""
        user_id = "test_user_together"
        
        hmm = get_hmm_tracker(db_session)
        lstm = get_lstm_recognizer(db_session)
        bandits = get_bandit_selector(db_session)
        
        # Initialize
        await hmm.initialize_hmm(user_id)
        await lstm.initialize_lstm(user_id)
        await bandits.initialize_bandits(user_id)
        
        # Simulate interaction
        # 1. HMM tracks engagement state
        observation = {"playback_speed": 1.0, "pauses": 0, "skips": 0, "replays": 1, "completion": 0.9}
        await hmm.update_hmm(user_id, observation)
        
        # 2. LSTM predicts patterns
        lstm_result = await lstm.predict_patterns(
            user_id,
            [0.8, 0.85, 0.9],
            {"duration": 45.0},
            {"time_of_day": "evening"},
            {"hour": 20.0}
        )
        
        # 3. Bandits select content
        bandit_result = await bandits.select_arm(
            user_id,
            {"time_of_day": "evening"},
            ["content1", "content2"]
        )
        
        # All should succeed
        assert lstm_result["success"], "LSTM should work"
        assert bandit_result["success"], "Bandits should work"
