"""
Unit Tests for API Clients
Tests for BaseAPIClient and specific API implementations
"""
import pytest

# Mark all tests in this file as unit tests (no external dependencies)
pytestmark = pytest.mark.unit
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse,
    RateLimiter
)
from app.services.api_clients.historical.europeana import EuropeanaAPIClient
from app.services.api_clients.tourism.opentripmap import OpenTripMapAPIClient
from app.services.api_clients.geographic.nominatim import NominatimAPIClient


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter token bucket algorithm"""
    limiter = RateLimiter(rate=2, per=1)  # 2 requests per second
    
    # Should allow 2 requests immediately
    await limiter.acquire()
    await limiter.acquire()
    
    # Third request should be delayed
    import time
    start = time.time()
    await limiter.acquire()
    duration = time.time() - start
    
    assert duration >= 0.4  # Should wait at least 0.4 seconds


@pytest.mark.asyncio
async def test_api_config_creation():
    """Test API configuration"""
    config = APIConfig(
        name="TestAPI",
        base_url="https://api.test.com",
        tier=APITier.FREE,
        category=APICategory.TOURISM,
        rate_limit=100,
        rate_period=3600,
        cost_per_request=0.0
    )
    
    assert config.name == "TestAPI"
    assert config.tier == APITier.FREE
    assert config.category == APICategory.TOURISM
    assert config.cost_per_request == 0.0


@pytest.mark.asyncio
async def test_api_response_creation():
    """Test API response object"""
    response = APIResponse(
        success=True,
        data={"test": "data"},
        status_code=200,
        cost=0.01,
        response_time=0.5,
        source="TestAPI"
    )
    
    assert response.success is True
    assert response.data == {"test": "data"}
    assert response.status_code == 200
    assert response.cost == 0.01
    assert response.source == "TestAPI"


@pytest.mark.asyncio
async def test_europeana_transform_response():
    """Test Europeana response transformation"""
    client = EuropeanaAPIClient(api_key="test_key")
    
    raw_data = {
        "totalResults": 2,
        "items": [
            {
                "id": "/123/abc",
                "title": ["Test Artifact"],
                "dcDescription": ["A test description"],
                "dcCreator": ["Test Creator"],
                "year": ["2020"],
                "type": "IMAGE",
                "country": ["France"],
                "edmPreview": ["http://example.com/thumb.jpg"]
            }
        ]
    }
    
    transformed = client.transform_response(raw_data)
    
    assert transformed["total_results"] == 2
    assert len(transformed["items"]) == 1
    assert transformed["items"][0]["title"] == "Test Artifact"
    assert transformed["items"][0]["creator"] == "Test Creator"
    assert transformed["source"] == "Europeana"


@pytest.mark.asyncio
async def test_opentripmap_transform_response():
    """Test OpenTripMap response transformation"""
    client = OpenTripMapAPIClient(api_key="test_key")
    
    raw_data = [
        {
            "xid": "test123",
            "name": "Test POI",
            "kinds": "historic_architecture,tourist_attraction",
            "point": {"lat": 48.8566, "lon": 2.3522}
        }
    ]
    
    transformed = client.transform_response(raw_data)
    
    assert transformed["total_results"] == 1
    assert transformed["items"][0]["title"] == "Test POI"
    assert transformed["items"][0]["latitude"] == 48.8566
    assert "historic_architecture" in transformed["items"][0]["kinds"]


@pytest.mark.asyncio
async def test_nominatim_transform_response():
    """Test Nominatim response transformation"""
    client = NominatimAPIClient()
    
    raw_data = [
        {
            "place_id": "12345",
            "display_name": "Paris, France",
            "type": "city",
            "lat": "48.8566",
            "lon": "2.3522",
            "address": {
                "city": "Paris",
                "country": "France"
            }
        }
    ]
    
    transformed = client.transform_response(raw_data)
    
    assert transformed["total_results"] == 1
    assert transformed["items"][0]["title"] == "Paris, France"
    assert transformed["items"][0]["latitude"] == 48.8566


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test cache key generation"""
    config = APIConfig(
        name="TestAPI",
        base_url="https://api.test.com",
        tier=APITier.FREE,
        category=APICategory.TOURISM,
        rate_limit=100,
        rate_period=3600
    )
    
    client = BaseAPIClient(config)
    
    # Same params should generate same key
    key1 = client._generate_cache_key("/search", {"q": "test", "limit": 10})
    key2 = client._generate_cache_key("/search", {"q": "test", "limit": 10})
    
    assert key1 == key2
    
    # Different params should generate different key
    key3 = client._generate_cache_key("/search", {"q": "different", "limit": 10})
    
    assert key1 != key3


@pytest.mark.asyncio
async def test_api_stats():
    """Test API client statistics"""
    config = APIConfig(
        name="TestAPI",
        base_url="https://api.test.com",
        tier=APITier.FREEMIUM,
        category=APICategory.TOURISM,
        rate_limit=100,
        rate_period=3600,
        cost_per_request=0.01
    )
    
    client = BaseAPIClient(config)
    client._request_count = 100
    client._error_count = 5
    client._total_cost = 1.0
    
    stats = client.get_stats()
    
    assert stats["name"] == "TestAPI"
    assert stats["tier"] == "freemium"
    assert stats["requests"] == 100
    assert stats["errors"] == 5
    assert stats["error_rate"] == 0.05
    assert stats["total_cost"] == 1.0


@pytest.mark.asyncio
async def test_api_tiers():
    """Test API tier classification"""
    assert APITier.FREE.value == "free"
    assert APITier.FREEMIUM.value == "freemium"
    assert APITier.PREMIUM.value == "premium"


@pytest.mark.asyncio
async def test_api_categories():
    """Test API category classification"""
    assert APICategory.HISTORICAL.value == "historical"
    assert APICategory.TOURISM.value == "tourism"
    assert APICategory.ACADEMIC.value == "academic"
    assert APICategory.NEWS.value == "news"
    assert APICategory.GOVERNMENT.value == "government"
