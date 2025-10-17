"""
Unit Tests for API Orchestrator
Tests for intelligent API selection and coordination
"""
import pytest

# Mark all tests in this file as unit tests (no external dependencies)
pytestmark = pytest.mark.unit
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from app.services.orchestration.api_orchestrator import (
    APIOrchestrator,
    ContentType,
    UserTier,
    BUDGET_CONFIGS
)
from app.services.api_clients.base import (
    BaseAPIClient,
    APIConfig,
    APITier,
    APICategory,
    APIResponse
)


@pytest.fixture
def orchestrator():
    """Create orchestrator instance"""
    return APIOrchestrator()


@pytest.fixture
def mock_api_client():
    """Create mock API client"""
    config = APIConfig(
        name="MockAPI",
        base_url="https://api.mock.com",
        tier=APITier.FREE,
        category=APICategory.TOURISM,
        rate_limit=100,
        rate_period=3600,
        cost_per_request=0.0
    )
    
    client = Mock(spec=BaseAPIClient)
    client.config = config
    client.search = AsyncMock(return_value=APIResponse(
        success=True,
        data={"items": [{"title": "Test Item"}], "total_results": 1},
        cost=0.0,
        response_time=0.1,
        source="MockAPI"
    ))
    
    return client


@pytest.mark.asyncio
async def test_register_api(orchestrator, mock_api_client):
    """Test API client registration"""
    orchestrator.register_api("mock_api", mock_api_client)
    
    assert "mock_api" in orchestrator.api_registry
    assert orchestrator.get_api("mock_api") == mock_api_client


@pytest.mark.asyncio
async def test_budget_configs():
    """Test budget configurations for different tiers"""
    free_config = BUDGET_CONFIGS[UserTier.FREE]
    premium_config = BUDGET_CONFIGS[UserTier.PREMIUM]
    enterprise_config = BUDGET_CONFIGS[UserTier.ENTERPRISE]
    
    assert free_config.max_cost_per_request == Decimal("0.10")
    assert free_config.preferred_free_ratio == 0.9
    
    assert premium_config.max_cost_per_request == Decimal("0.50")
    assert premium_config.preferred_free_ratio == 0.7
    
    assert enterprise_config.max_cost_per_request == Decimal("1.50")
    assert enterprise_config.preferred_free_ratio == 0.5


@pytest.mark.asyncio
async def test_api_strategy_selection_base(orchestrator, mock_api_client):
    """Test API strategy selection for BASE content"""
    orchestrator.register_api("mock_api", mock_api_client)
    
    budget_config = BUDGET_CONFIGS[UserTier.FREE]
    strategy = orchestrator._select_api_strategy(
        content_type=ContentType.BASE,
        budget_config=budget_config
    )
    
    assert strategy.parallel_execution is True
    assert strategy.min_sources == 2
    assert strategy.timeout == 5.0


@pytest.mark.asyncio
async def test_api_strategy_selection_standout(orchestrator, mock_api_client):
    """Test API strategy selection for STANDOUT content"""
    orchestrator.register_api("mock_api", mock_api_client)
    
    budget_config = BUDGET_CONFIGS[UserTier.PREMIUM]
    strategy = orchestrator._select_api_strategy(
        content_type=ContentType.STANDOUT,
        budget_config=budget_config
    )
    
    assert strategy.parallel_execution is True
    assert strategy.min_sources == 3
    assert strategy.max_sources == 7


@pytest.mark.asyncio
async def test_result_aggregation(orchestrator):
    """Test result aggregation and deduplication"""
    results = [
        APIResponse(
            success=True,
            data={"items": [{"title": "Item 1"}, {"title": "Item 2"}]},
            cost=0.01,
            response_time=0.1,
            source="API1"
        ),
        APIResponse(
            success=True,
            data={"items": [{"title": "Item 1"}, {"title": "Item 3"}]},  # Duplicate
            cost=0.02,
            response_time=0.2,
            source="API2"
        )
    ]
    
    aggregated = orchestrator._aggregate_results(results)
    
    assert aggregated["total_count"] == 3  # Deduplicated
    assert len(aggregated["sources"]) == 2


@pytest.mark.asyncio
async def test_orchestrator_stats(orchestrator, mock_api_client):
    """Test orchestrator statistics"""
    orchestrator.register_api("mock_api", mock_api_client)
    orchestrator._total_cost = Decimal("1.50")
    orchestrator._request_count = 100
    
    stats = orchestrator.get_stats()
    
    assert stats["total_cost"] == 1.50
    assert stats["total_requests"] == 100
    assert stats["avg_cost_per_request"] == 0.015
    assert stats["registered_apis"] == 1


@pytest.mark.asyncio
async def test_content_types():
    """Test content type enum"""
    assert ContentType.BASE.value == "base"
    assert ContentType.STANDOUT.value == "standout"
    assert ContentType.TOPIC_SPECIFIC.value == "topic_specific"
    assert ContentType.ENRICHMENT.value == "enrichment"


@pytest.mark.asyncio
async def test_user_tiers():
    """Test user tier enum"""
    assert UserTier.FREE.value == "free"
    assert UserTier.PREMIUM.value == "premium"
    assert UserTier.ENTERPRISE.value == "enterprise"
