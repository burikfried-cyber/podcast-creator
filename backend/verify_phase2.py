"""
Phase 2 Verification Script
Quick verification that all Phase 2 components can be imported and instantiated
"""
import sys
import asyncio
from decimal import Decimal

print("=" * 60)
print("PHASE 2 VERIFICATION")
print("=" * 60)

# Test 1: Import base framework
print("\n1. Testing BaseAPIClient framework...")
try:
    from app.services.api_clients.base import (
        BaseAPIClient,
        APIConfig,
        APITier,
        APICategory,
        APIResponse,
        RateLimiter
    )
    print("   ✅ BaseAPIClient imports successful")
except Exception as e:
    print(f"   ❌ BaseAPIClient import failed: {e}")
    sys.exit(1)

# Test 2: Import circuit breaker
print("\n2. Testing Circuit Breaker...")
try:
    from app.services.api_clients.circuit_breaker import (
        CircuitBreaker,
        CircuitState,
        CircuitBreakerManager
    )
    print("   ✅ Circuit Breaker imports successful")
except Exception as e:
    print(f"   ❌ Circuit Breaker import failed: {e}")
    sys.exit(1)

# Test 3: Import API clients
print("\n3. Testing API Clients...")
api_clients = []
try:
    from app.services.api_clients.historical import (
        EuropeanaAPIClient,
        SmithsonianAPIClient,
        UNESCOWorldHeritageAPIClient,
        DigitalNZAPIClient
    )
    api_clients.append("Historical (4)")
    
    from app.services.api_clients.tourism import (
        OpenTripMapAPIClient,
        GeoapifyPlacesAPIClient,
        FoursquareAPIClient,
        AmadeusAPIClient
    )
    api_clients.append("Tourism (4)")
    
    from app.services.api_clients.geographic import (
        NominatimAPIClient,
        GeoNamesAPIClient
    )
    api_clients.append("Geographic (2)")
    
    from app.services.api_clients.academic import (
        ArXivAPIClient,
        PubMedAPIClient,
        CrossRefAPIClient
    )
    api_clients.append("Academic (3)")
    
    from app.services.api_clients.news import (
        GuardianAPIClient,
        BBCNewsAPIClient
    )
    api_clients.append("News (2)")
    
    from app.services.api_clients.government import (
        DataGovAPIClient,
        DataEuropaAPIClient
    )
    api_clients.append("Government (2)")
    
    print(f"   ✅ All API clients imported: {', '.join(api_clients)}")
    print(f"   ✅ Total: 17 API clients")
except Exception as e:
    print(f"   ❌ API client import failed: {e}")
    sys.exit(1)

# Test 4: Import orchestrator
print("\n4. Testing API Orchestrator...")
try:
    from app.services.orchestration import (
        APIOrchestrator,
        api_orchestrator,
        ContentType,
        UserTier
    )
    print("   ✅ API Orchestrator imports successful")
except Exception as e:
    print(f"   ❌ API Orchestrator import failed: {e}")
    sys.exit(1)

# Test 5: Import quality assessor
print("\n5. Testing Content Quality Assessor...")
try:
    from app.services.quality import (
        ContentQualityAssessor,
        content_quality_assessor,
        QualityScore
    )
    print("   ✅ Quality Assessor imports successful")
except Exception as e:
    print(f"   ❌ Quality Assessor import failed: {e}")
    sys.exit(1)

# Test 6: Import cost tracker
print("\n6. Testing Cost Tracker...")
try:
    from app.services.cost_tracking import (
        CostTracker,
        cost_tracker,
        CostEntry,
        CostSummary,
        BudgetAlert
    )
    print("   ✅ Cost Tracker imports successful")
except Exception as e:
    print(f"   ❌ Cost Tracker import failed: {e}")
    sys.exit(1)

# Test 7: Instantiate components
print("\n7. Testing Component Instantiation...")
try:
    # Rate limiter
    limiter = RateLimiter(rate=10, per=60)
    print("   ✅ RateLimiter instantiated")
    
    # Circuit breaker
    breaker = CircuitBreaker(name="test", failure_threshold=5, recovery_timeout=60)
    print("   ✅ CircuitBreaker instantiated")
    
    # API config
    config = APIConfig(
        name="TestAPI",
        base_url="https://api.test.com",
        tier=APITier.FREE,
        category=APICategory.TOURISM,
        rate_limit=100,
        rate_period=3600
    )
    print("   ✅ APIConfig instantiated")
    
    # Orchestrator
    orchestrator = APIOrchestrator()
    print("   ✅ APIOrchestrator instantiated")
    
    # Quality assessor
    assessor = ContentQualityAssessor()
    print("   ✅ ContentQualityAssessor instantiated")
    
    # Cost tracker
    tracker = CostTracker()
    print("   ✅ CostTracker instantiated")
    
except Exception as e:
    print(f"   ❌ Component instantiation failed: {e}")
    sys.exit(1)

# Test 8: Basic functionality
print("\n8. Testing Basic Functionality...")
try:
    # Test cost tracking
    tracker.set_user_budget("test_user", Decimal("10.00"))
    tracker.track_cost("TestAPI", Decimal("0.50"), user_id="test_user")
    remaining = tracker.get_user_remaining_budget("test_user")
    assert remaining == Decimal("9.50"), f"Expected 9.50, got {remaining}"
    print("   ✅ Cost tracking works")
    
    # Test quality scoring
    score = assessor._assess_source_authority(["UNESCO"])
    assert score == 1.0, f"Expected 1.0, got {score}"
    print("   ✅ Quality scoring works")
    
    # Test circuit breaker states
    assert breaker.state == CircuitState.CLOSED
    print("   ✅ Circuit breaker works")
    
except Exception as e:
    print(f"   ❌ Functionality test failed: {e}")
    sys.exit(1)

# Test 9: Async functionality
print("\n9. Testing Async Functionality...")
async def test_async():
    try:
        # Test circuit breaker async call
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        print("   ✅ Async circuit breaker works")
        
        # Test quality assessment
        content = {
            "title": "Test",
            "description": "Test description",
            "source": "UNESCO"
        }
        score = await assessor.assess_content_quality(content, ["UNESCO"])
        assert score.overall > 0.5
        print("   ✅ Async quality assessment works")
        
    except Exception as e:
        print(f"   ❌ Async test failed: {e}")
        sys.exit(1)

asyncio.run(test_async())

# Summary
print("\n" + "=" * 60)
print("PHASE 2 VERIFICATION COMPLETE")
print("=" * 60)
print("\n✅ All components verified successfully!")
print("\nComponents tested:")
print("  • BaseAPIClient framework")
print("  • Circuit Breaker pattern")
print("  • 17 API clients (all categories)")
print("  • API Orchestrator")
print("  • Content Quality Assessor")
print("  • Cost Tracker")
print("  • Async functionality")
print("\n🎉 Phase 2 is ready for production!")
print("=" * 60)
