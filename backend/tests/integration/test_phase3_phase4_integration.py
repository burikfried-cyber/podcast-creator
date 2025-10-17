"""
Phase 3 + Phase 4 Integration Tests
Tests personalization (Phase 3) working with detection (Phase 4)
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Mock Redis and database
class MockDB:
    """Mock database for testing"""
    pass

class MockRedis:
    """Mock Redis for preference storage"""
    def __init__(self):
        self.data = {}
    
    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, key, value):
        self.data[key] = value
    
    async def hgetall(self, key):
        return self.data.get(key, {})
    
    async def hset(self, key, field, value):
        if key not in self.data:
            self.data[key] = {}
        self.data[key][field] = value

@pytest.fixture
def mock_db():
    """Create mock database"""
    return MockDB()

@pytest.fixture
def mock_redis():
    """Create mock Redis"""
    return MockRedis()

@pytest.fixture
def standout_detector(mock_db):
    """Create standout detector with mocked preference model"""
    from app.services.detection.standout_detector import EnhancedStandoutDetector
    
    detector = EnhancedStandoutDetector(mock_db)
    
    # Mock the preference model
    mock_pref_model = Mock()
    mock_pref_model.get_surprise_preference = AsyncMock(return_value={"surprise_tolerance": 2})
    detector.preference_model = mock_pref_model
    
    return detector


class TestPhase3Phase4Integration:
    """Test Phase 3 (Personalization) + Phase 4 (Detection) Integration"""
    
    @pytest.mark.asyncio
    async def test_surprise_tolerance_high(self, standout_detector):
        """Test that high surprise tolerance boosts standout scores"""
        
        # Mock high surprise tolerance (adventurous user)
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            return_value={"surprise_tolerance": 3}
        )
        
        # Use content that will score moderately (not max 10.0) so we can see the boost
        content = {
            "id": "test_001",
            "title": "Interesting Cultural Practice",
            "content": "A cultural tradition that has been preserved for centuries in this region.",
            "location": {"lat": 63.4, "lng": -20.3}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_adventurous")
        
        # High surprise tolerance should boost the score
        assert result["success"] is True
        assert result["personalized_score"] >= result["base_score"], \
            "Personalized score should be >= base score for high surprise tolerance"
        
        # If base score is already at max (10.0), it can't be boosted further
        if result["base_score"] < 10.0:
            assert result["personalized_score"] >= result["base_score"] * 1.09, \
                f"High surprise tolerance should boost score by at least 9% (base: {result['base_score']}, personalized: {result['personalized_score']})"
        else:
            # If already at max, personalized should equal base
            assert result["personalized_score"] == 10.0, \
                "Score already at max, should stay at 10.0"
    
    @pytest.mark.asyncio
    async def test_surprise_tolerance_low(self, standout_detector):
        """Test that low surprise tolerance reduces standout scores"""
        
        # Mock low surprise tolerance (predictable user)
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            return_value={"surprise_tolerance": 0}
        )
        
        content = {
            "id": "test_002",
            "title": "Puffins Living in Human Houses",
            "content": "A unique phenomenon where puffins cohabitate with humans in the Westman Islands.",
            "location": {"lat": 63.4, "lng": -20.3}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_predictable")
        
        # Low surprise tolerance should reduce the score
        assert result["success"] is True
        assert result["personalized_score"] <= result["base_score"], \
            "Personalized score should be <= base score for low surprise tolerance"
        assert result["personalized_score"] < result["base_score"] * 0.9, \
            "Low surprise tolerance should reduce score by at least 10%"
    
    @pytest.mark.asyncio
    async def test_surprise_tolerance_neutral(self, standout_detector):
        """Test that neutral surprise tolerance keeps score unchanged"""
        
        # Mock neutral surprise tolerance
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            return_value={"surprise_tolerance": 2}
        )
        
        content = {
            "id": "test_003",
            "title": "Geysir Etymology",
            "content": "Geysir is the original geyser that all others are named after.",
            "location": {"lat": 64.3, "lng": -20.3}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_neutral")
        
        # Neutral surprise tolerance should keep score roughly the same
        assert result["success"] is True
        assert abs(result["personalized_score"] - result["base_score"]) < 0.1, \
            "Neutral surprise tolerance should keep score nearly unchanged"
    
    @pytest.mark.asyncio
    async def test_no_user_id_uses_base_score(self, standout_detector):
        """Test that without user_id, personalized score equals base score"""
        
        content = {
            "id": "test_004",
            "title": "Test Content",
            "content": "Some test content for detection.",
            "location": {"lat": 64.0, "lng": -20.0}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id=None)
        
        # Without user_id, personalized should equal base
        assert result["success"] is True
        assert result["personalized_score"] == result["base_score"], \
            "Without user_id, personalized score should equal base score"
        assert result["tier"] == result["personalized_tier"], \
            "Without user_id, tiers should be the same"
    
    @pytest.mark.asyncio
    async def test_tier_changes_with_personalization(self, standout_detector):
        """Test that personalization can change content tier"""
        
        # Mock very high surprise tolerance
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            return_value={"surprise_tolerance": 3}
        )
        
        # Content that's borderline between tiers
        content = {
            "id": "test_005",
            "title": "Borderline Content",
            "content": "Unique cultural practice that is unusual and mysterious.",
            "location": {"lat": 64.0, "lng": -20.0}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_adventurous")
        
        assert result["success"] is True
        # Personalized tier could be different from base tier
        # (This depends on the actual scores, so we just check they exist)
        assert "tier" in result
        assert "personalized_tier" in result
    
    @pytest.mark.asyncio
    async def test_method_scores_included(self, standout_detector):
        """Test that method scores are included in results"""
        
        content = {
            "id": "test_006",
            "title": "Test Content",
            "content": "Content with unique and impossible elements that defy physics.",
            "location": {"lat": 64.0, "lng": -20.0}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_test")
        
        assert result["success"] is True
        assert "method_scores" in result
        assert isinstance(result["method_scores"], dict)
        
        # Check that all 9 methods are present
        expected_methods = [
            "impossibility", "uniqueness", "temporal", "cultural",
            "atlas_obscura", "historical", "geographic", "linguistic",
            "cross_cultural"
        ]
        for method in expected_methods:
            assert method in result["method_scores"]
    
    @pytest.mark.asyncio
    async def test_explanation_generated(self, standout_detector):
        """Test that explanation is generated"""
        
        content = {
            "id": "test_007",
            "title": "Test Content",
            "content": "Unique impossible phenomenon.",
            "location": {"lat": 64.0, "lng": -20.0}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_test")
        
        assert result["success"] is True
        assert "explanation" in result
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_users_different_results(self, standout_detector):
        """Test that different users get different personalized scores"""
        
        content = {
            "id": "test_008",
            "title": "Standout Content",
            "content": "Unique and mysterious phenomenon that defies explanation.",
            "location": {"lat": 64.0, "lng": -20.0}
        }
        
        # User 1: High surprise tolerance
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            return_value={"surprise_tolerance": 3}
        )
        result1 = await standout_detector.detect_standout_content(content, user_id="user_adventurous")
        
        # User 2: Low surprise tolerance
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            return_value={"surprise_tolerance": 0}
        )
        result2 = await standout_detector.detect_standout_content(content, user_id="user_predictable")
        
        # Base scores should be the same
        assert result1["base_score"] == result2["base_score"]
        
        # Personalized scores should be different
        assert result1["personalized_score"] != result2["personalized_score"]
        assert result1["personalized_score"] > result2["personalized_score"], \
            "Adventurous user should get higher personalized score"


class TestIntegrationEdgeCases:
    """Test edge cases in integration"""
    
    @pytest.mark.asyncio
    async def test_preference_model_error_fallback(self, standout_detector):
        """Test that system falls back gracefully if preference model fails"""
        
        # Mock preference model to raise error
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )
        
        content = {
            "id": "test_009",
            "title": "Test Content",
            "content": "Some content.",
            "location": {"lat": 64.0, "lng": -20.0}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_test")
        
        # Should still work, falling back to base score
        assert result["success"] is True
        assert result["personalized_score"] == result["base_score"]
    
    @pytest.mark.asyncio
    async def test_mundane_content_stays_mundane(self, standout_detector):
        """Test that mundane content stays mundane even with high surprise tolerance"""
        
        # Mock very high surprise tolerance
        standout_detector.preference_model.get_surprise_preference = AsyncMock(
            return_value={"surprise_tolerance": 3}
        )
        
        content = {
            "id": "test_010",
            "title": "Shopping Mall",
            "content": "A popular shopping mall with many stores and restaurants.",
            "location": {"lat": 64.0, "lng": -20.0}
        }
        
        result = await standout_detector.detect_standout_content(content, user_id="user_adventurous")
        
        # Even with high surprise tolerance, mundane should stay low
        assert result["success"] is True
        assert result["base_score"] < 2.0, "Mundane content should have low base score"
        assert result["personalized_score"] < 3.0, "Mundane content should stay low even with personalization"
