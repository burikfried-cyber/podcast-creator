"""
Phase 3 Testing: Cold Start Engagement Tests
Target: >70% completion rate
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cold_start import get_cold_start_solver


@pytest.mark.asyncio
@pytest.mark.phase3
class TestColdStartOnboarding:
    """Test cold start onboarding process"""
    
    @pytest_asyncio.fixture
    async def cold_start_solver(self, db_session: AsyncSession):
        """Get cold start solver"""
        return get_cold_start_solver(db_session)
    
    @pytest_asyncio.fixture
    async def test_user_id(self):
        """Test user ID"""
        return "test_user_cold_start"
    
    async def test_onboarding_start(
        self,
        cold_start_solver,
        test_user_id
    ):
        """Test starting onboarding process"""
        result = await cold_start_solver.start_onboarding(test_user_id)
        
        assert result["success"], "Onboarding should start successfully"
        assert "current_section" in result, "Should return first section"
        assert result["progress"]["current"] == 0, "Should start at section 0"
        assert result["progress"]["total"] > 0, "Should have total sections"
    
    async def test_topic_selection(
        self,
        cold_start_solver,
        test_user_id
    ):
        """Test topic selection in questionnaire"""
        # Start onboarding
        await cold_start_solver.start_onboarding(test_user_id)
        
        # Submit topic answers
        topic_answers = {
            "topic_interests": {
                "technology": 5,
                "science": 4,
                "business": 3
            }
        }
        
        result = await cold_start_solver.submit_answers(
            test_user_id,
            "topics",
            topic_answers
        )
        
        assert result["success"], "Answer submission should succeed"
        assert not result["completed"], "Should not be completed yet"
        assert "next_section" in result, "Should have next section"
    
    async def test_complete_onboarding(
        self,
        cold_start_solver,
        test_user_id
    ):
        """Test completing full onboarding"""
        # Start onboarding
        await cold_start_solver.start_onboarding(test_user_id)
        
        # Submit all sections
        sections = [
            ("topics", {
                "topic_interests": {
                    "technology": 5,
                    "science": 4
                }
            }),
            ("depth", {
                "depth_preference": 3
            }),
            ("surprise", {
                "scenario_choices": [
                    {"surprise_level": 2},
                    {"surprise_level": 3}
                ]
            }),
            ("demographics", {
                "age_range": "25-34",
                "education_level": "bachelors",
                "occupation": "software engineer"
            })
        ]
        
        for section_id, answers in sections:
            result = await cold_start_solver.submit_answers(
                test_user_id,
                section_id,
                answers
            )
            
            if section_id == "demographics":
                # Last section
                assert result["completed"], "Should be completed"
                assert "exploration_strategy" in result, "Should have exploration strategy"
            else:
                assert not result["completed"], "Should not be completed yet"
    
    async def test_onboarding_status(
        self,
        cold_start_solver,
        test_user_id
    ):
        """Test getting onboarding status"""
        # Before starting
        status = await cold_start_solver.get_onboarding_status(test_user_id)
        assert not status["started"], "Should not be started"
        
        # After starting
        await cold_start_solver.start_onboarding(test_user_id)
        status = await cold_start_solver.get_onboarding_status(test_user_id)
        assert status["started"], "Should be started"
        assert not status["completed"], "Should not be completed"
    
    async def test_questionnaire_structure(
        self,
        cold_start_solver
    ):
        """Test questionnaire structure"""
        questionnaire = cold_start_solver.get_questionnaire()
        
        assert "sections" in questionnaire, "Should have sections"
        assert len(questionnaire["sections"]) > 0, "Should have at least one section"
        
        # Check section structure
        for section in questionnaire["sections"]:
            assert "id" in section, "Section should have ID"
            assert "title" in section, "Section should have title"
            assert "type" in section, "Section should have type"
            assert "questions" in section, "Section should have questions"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestExplorationStrategy:
    """Test exploration strategies"""
    
    @pytest_asyncio.fixture
    async def cold_start_solver(self, db_session: AsyncSession):
        """Get cold start solver"""
        return get_cold_start_solver(db_session)
    
    async def test_epsilon_greedy_exploration(
        self,
        cold_start_solver
    ):
        """Test epsilon-greedy exploration"""
        user_id = "test_user_exploration"
        
        # Complete onboarding
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(
            user_id,
            "topics",
            {"topic_interests": {"technology": 5}}
        )
        await cold_start_solver.submit_answers(
            user_id,
            "depth",
            {"depth_preference": 3}
        )
        await cold_start_solver.submit_answers(
            user_id,
            "surprise",
            {"scenario_choices": [{"surprise_level": 2}]}
        )
        await cold_start_solver.submit_answers(
            user_id,
            "demographics",
            {"age_range": "25-34"}
        )
        
        # Get exploration recommendations
        candidates = [f"item_{i}" for i in range(20)]
        recommendations = await cold_start_solver.get_exploration_recommendations(
            user_id,
            candidates,
            n_recommendations=10
        )
        
        assert len(recommendations) == 10, "Should return 10 recommendations"
        assert all(item in candidates for item in recommendations), \
            "All recommendations should be from candidates"
    
    async def test_exploration_rate_decay(
        self,
        cold_start_solver
    ):
        """Test that exploration rate decays over time"""
        user_id = "test_user_decay"
        
        # Complete onboarding
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(user_id, "topics", {"topic_interests": {"technology": 5}})
        await cold_start_solver.submit_answers(user_id, "depth", {"depth_preference": 3})
        await cold_start_solver.submit_answers(user_id, "surprise", {"scenario_choices": [{"surprise_level": 2}]})
        await cold_start_solver.submit_answers(user_id, "demographics", {"age_range": "25-34"})
        
        # Get initial status
        status1 = await cold_start_solver.get_onboarding_status(user_id)
        initial_epsilon = status1["exploration_rate"]
        
        # Make several exploration calls
        candidates = [f"item_{i}" for i in range(20)]
        for _ in range(5):
            await cold_start_solver.get_exploration_recommendations(
                user_id,
                candidates,
                n_recommendations=10
            )
        
        # Get updated status
        status2 = await cold_start_solver.get_onboarding_status(user_id)
        final_epsilon = status2["exploration_rate"]
        
        # Epsilon should decay
        assert final_epsilon < initial_epsilon, \
            f"Exploration rate should decay: {initial_epsilon} -> {final_epsilon}"
        assert final_epsilon >= 0.05, "Should not go below minimum"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestPreferenceInitialization:
    """Test preference initialization from questionnaire"""
    
    @pytest_asyncio.fixture
    async def cold_start_solver(self, db_session: AsyncSession):
        """Get cold start solver"""
        return get_cold_start_solver(db_session)
    
    @pytest_asyncio.fixture
    async def preference_model(self, db_session: AsyncSession):
        """Get preference model"""
        from app.services.preferences import get_preference_model
        return get_preference_model(db_session)
    
    async def test_topic_initialization(
        self,
        cold_start_solver,
        preference_model
    ):
        """Test that topics are initialized from questionnaire"""
        user_id = "test_user_topic_init"
        
        # Complete onboarding with specific topics
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(
            user_id,
            "topics",
            {
                "topic_interests": {
                    "technology": 5,
                    "science": 4,
                    "history": 2
                }
            }
        )
        
        # Check that preferences were initialized
        topic_prefs = await preference_model.get_topic_preferences(user_id)
        
        assert len(topic_prefs) > 0, "Should have topic preferences"
        
        # Technology should have highest weight
        tech_prefs = [p for p in topic_prefs if p["topic_category"] == "technology"]
        assert len(tech_prefs) > 0, "Should have technology preferences"
        
        # Check weights are reasonable
        max_weight = max(p["preference_weight"] for p in topic_prefs)
        assert max_weight > 0.5, "Should have strong initial preferences"
    
    async def test_depth_initialization(
        self,
        cold_start_solver,
        preference_model
    ):
        """Test that depth preference is initialized"""
        user_id = "test_user_depth_init"
        
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(user_id, "topics", {"topic_interests": {"technology": 5}})
        await cold_start_solver.submit_answers(
            user_id,
            "depth",
            {"depth_preference": 4}  # Deep level
        )
        
        # Check depth preference
        depth_pref = await preference_model.get_depth_preference(user_id)
        
        assert depth_pref is not None, "Should have depth preference"
        assert depth_pref["preferred_depth"] == 4, "Should match selected depth"
    
    async def test_surprise_initialization(
        self,
        cold_start_solver,
        preference_model
    ):
        """Test that surprise preference is initialized"""
        user_id = "test_user_surprise_init"
        
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(user_id, "topics", {"topic_interests": {"technology": 5}})
        await cold_start_solver.submit_answers(user_id, "depth", {"depth_preference": 3})
        await cold_start_solver.submit_answers(
            user_id,
            "surprise",
            {
                "scenario_choices": [
                    {"surprise_level": 3},
                    {"surprise_level": 4}
                ]
            }
        )
        
        # Check surprise preference
        surprise_pref = await preference_model.get_surprise_preference(user_id)
        
        assert surprise_pref is not None, "Should have surprise preference"
        # Should be around 3-4 (adventurous)
        assert surprise_pref["surprise_tolerance"] >= 2, "Should reflect adventurous choices"


@pytest.mark.asyncio
@pytest.mark.phase3
class TestDemographicClustering:
    """Test demographic clustering integration"""
    
    @pytest_asyncio.fixture
    async def cold_start_solver(self, db_session: AsyncSession):
        """Get cold start solver"""
        return get_cold_start_solver(db_session)
    
    async def test_cluster_assignment(
        self,
        cold_start_solver
    ):
        """Test that users are assigned to clusters"""
        user_id = "test_user_clustering"
        
        # Complete onboarding with demographics
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(user_id, "topics", {"topic_interests": {"technology": 5}})
        await cold_start_solver.submit_answers(user_id, "depth", {"depth_preference": 3})
        await cold_start_solver.submit_answers(user_id, "surprise", {"scenario_choices": [{"surprise_level": 2}]})
        await cold_start_solver.submit_answers(
            user_id,
            "demographics",
            {
                "age_range": "25-34",
                "education_level": "bachelors",
                "occupation": "software engineer"
            }
        )
        
        # Check status
        status = await cold_start_solver.get_onboarding_status(user_id)
        
        assert status["completed"], "Onboarding should be complete"
        # Cluster assignment happens if demographic filter is trained
        # For now, just verify the process completes


@pytest.mark.asyncio
@pytest.mark.phase3
class TestOnboardingCompletion:
    """Test onboarding completion metrics"""
    
    @pytest_asyncio.fixture
    async def cold_start_solver(self, db_session: AsyncSession):
        """Get cold start solver"""
        return get_cold_start_solver(db_session)
    
    async def test_completion_time(
        self,
        cold_start_solver
    ):
        """Test that onboarding can be completed quickly"""
        import time
        
        user_id = "test_user_completion_time"
        
        start_time = time.time()
        
        # Complete onboarding
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(user_id, "topics", {"topic_interests": {"technology": 5}})
        await cold_start_solver.submit_answers(user_id, "depth", {"depth_preference": 3})
        await cold_start_solver.submit_answers(user_id, "surprise", {"scenario_choices": [{"surprise_level": 2}]})
        await cold_start_solver.submit_answers(user_id, "demographics", {"age_range": "25-34"})
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (target: <2 minutes, but test should be much faster)
        assert duration < 10, f"Onboarding processing should be fast, took {duration:.2f}s"
    
    async def test_minimal_questions(
        self,
        cold_start_solver
    ):
        """Test that questionnaire is not too long"""
        questionnaire = cold_start_solver.get_questionnaire()
        
        total_questions = sum(
            len(section["questions"])
            for section in questionnaire["sections"]
        )
        
        # Should have reasonable number of questions
        assert total_questions <= 15, \
            f"Should have ≤15 questions, got {total_questions}"
    
    async def test_optional_demographics(
        self,
        cold_start_solver
    ):
        """Test that demographics are optional"""
        user_id = "test_user_optional_demo"
        
        # Complete without demographics
        await cold_start_solver.start_onboarding(user_id)
        await cold_start_solver.submit_answers(user_id, "topics", {"topic_interests": {"technology": 5}})
        await cold_start_solver.submit_answers(user_id, "depth", {"depth_preference": 3})
        await cold_start_solver.submit_answers(user_id, "surprise", {"scenario_choices": [{"surprise_level": 2}]})
        
        # Submit empty demographics
        result = await cold_start_solver.submit_answers(
            user_id,
            "demographics",
            {}
        )
        
        # Should still complete
        assert result["completed"], "Should complete without demographics"
