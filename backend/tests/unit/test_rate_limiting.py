"""
Unit Tests for Rate Limiting
Tests for tier-based rate limiting
"""
import pytest
from httpx import AsyncClient

# Check if Phase 1 is available
try:
    from app.core.cache import cache
    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False
    cache = None

# Mark as integration tests (require database/Redis)
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not PHASE1_AVAILABLE,
        reason="Phase 1 dependencies not available (database/Redis required)"
    )
]


@pytest.mark.asyncio
async def test_rate_limit_headers(client: AsyncClient, auth_headers: dict):
    """Test that rate limit headers are present"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_free_tier(client: AsyncClient, test_user):
    """Test rate limiting for free tier"""
    # Clear any existing rate limits
    await cache.reset_rate_limit(str(test_user.id))
    
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "TestPassword123"
        }
    )
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make requests up to limit
    for i in range(5):
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining >= 0


@pytest.mark.asyncio
async def test_rate_limit_premium_tier(client: AsyncClient, premium_user):
    """Test rate limiting for premium tier"""
    # Clear any existing rate limits
    await cache.reset_rate_limit(str(premium_user.id))
    
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": premium_user.email,
            "password": "PremiumPass123"
        }
    )
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make requests
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    
    # Premium should have higher limit
    limit = int(response.headers["X-RateLimit-Limit"])
    assert limit == 1000  # Premium tier limit


@pytest.mark.asyncio
async def test_rate_limit_decrements(client: AsyncClient, auth_headers: dict, test_user):
    """Test that rate limit remaining decrements"""
    # Clear any existing rate limits
    await cache.reset_rate_limit(str(test_user.id))
    
    # First request
    response1 = await client.get("/api/v1/auth/me", headers=auth_headers)
    remaining1 = int(response1.headers["X-RateLimit-Remaining"])
    
    # Second request
    response2 = await client.get("/api/v1/auth/me", headers=auth_headers)
    remaining2 = int(response2.headers["X-RateLimit-Remaining"])
    
    # Remaining should decrease
    assert remaining2 < remaining1


@pytest.mark.asyncio
async def test_health_check_no_rate_limit(client: AsyncClient):
    """Test that health check is not rate limited"""
    # Make many requests
    for _ in range(10):
        response = await client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers
