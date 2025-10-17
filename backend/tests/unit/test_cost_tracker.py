"""
Unit Tests for Cost Tracker
Tests for budget management and cost tracking
"""
import pytest

# Mark all tests in this file as unit tests (no external dependencies)
pytestmark = pytest.mark.unit
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.cost_tracking.cost_tracker import (
    CostTracker,
    CostEntry,
    CostSummary,
    BudgetAlert
)


@pytest.fixture
def tracker():
    """Create cost tracker instance"""
    return CostTracker()


def test_set_user_budget(tracker):
    """Test setting user budget"""
    tracker.set_user_budget("user123", Decimal("10.00"))
    
    assert tracker._user_budgets["user123"] == Decimal("10.00")


def test_track_cost(tracker):
    """Test cost tracking"""
    tracker.set_user_budget("user123", Decimal("10.00"))
    
    result = tracker.track_cost(
        api_name="TestAPI",
        cost=Decimal("0.50"),
        user_id="user123",
        success=True
    )
    
    assert result is True  # Within budget
    assert tracker.get_user_cost("user123") == Decimal("0.50")


def test_budget_enforcement(tracker):
    """Test budget enforcement"""
    tracker.set_user_budget("user123", Decimal("1.00"))
    
    # Use up most of budget
    tracker.track_cost("API1", Decimal("0.96"), user_id="user123")
    
    # This should trigger critical alert
    result = tracker.track_cost("API2", Decimal("0.05"), user_id="user123")
    
    assert result is False  # Budget exceeded
    assert len(tracker._alerts) > 0


def test_check_budget(tracker):
    """Test budget checking"""
    tracker.set_user_budget("user123", Decimal("10.00"))
    tracker.track_cost("API1", Decimal("5.00"), user_id="user123")
    
    # Should have budget
    assert tracker.check_budget("user123", Decimal("4.00")) is True
    
    # Should not have budget
    assert tracker.check_budget("user123", Decimal("6.00")) is False


def test_get_remaining_budget(tracker):
    """Test remaining budget calculation"""
    tracker.set_user_budget("user123", Decimal("10.00"))
    tracker.track_cost("API1", Decimal("3.00"), user_id="user123")
    
    remaining = tracker.get_user_remaining_budget("user123")
    
    assert remaining == Decimal("7.00")


def test_cost_summary(tracker):
    """Test cost summary generation"""
    tracker.track_cost("API1", Decimal("1.00"), success=True)
    tracker.track_cost("API2", Decimal("2.00"), success=True)
    tracker.track_cost("API1", Decimal("1.50"), success=False)
    
    summary = tracker.get_cost_summary()
    
    assert summary.total_cost == Decimal("4.50")
    assert summary.request_count == 3
    assert summary.success_count == 2
    assert summary.failure_count == 1
    assert summary.api_breakdown["API1"] == Decimal("2.50")
    assert summary.api_breakdown["API2"] == Decimal("2.00")


def test_cost_summary_with_filters(tracker):
    """Test cost summary with time filters"""
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    tracker.track_cost("API1", Decimal("1.00"), user_id="user1")
    
    # Summary from yesterday should include the cost
    summary = tracker.get_cost_summary(start_time=yesterday)
    assert summary.total_cost == Decimal("1.00")
    
    # Summary from tomorrow should be empty
    tomorrow = now + timedelta(days=1)
    summary_future = tracker.get_cost_summary(start_time=tomorrow)
    assert summary_future.total_cost == Decimal("0.00")


def test_get_cost_by_api(tracker):
    """Test getting cost by specific API"""
    tracker.track_cost("API1", Decimal("1.00"))
    tracker.track_cost("API1", Decimal("2.00"))
    tracker.track_cost("API2", Decimal("3.00"))
    
    api1_cost = tracker.get_cost_by_api("API1")
    
    assert api1_cost == Decimal("3.00")


def test_optimization_recommendations(tracker):
    """Test cost optimization recommendations"""
    tracker.set_user_budget("user123", Decimal("10.00"))
    
    # Create high-cost API usage
    for _ in range(50):
        tracker.track_cost("ExpensiveAPI", Decimal("0.10"), user_id="user123")
    
    for _ in range(10):
        tracker.track_cost("CheapAPI", Decimal("0.01"), user_id="user123")
    
    recommendations = tracker.get_optimization_recommendations("user123")
    
    assert len(recommendations) > 0
    # Should recommend about ExpensiveAPI
    assert any("ExpensiveAPI" in str(rec) for rec in recommendations)


def test_budget_alerts(tracker):
    """Test budget alert generation"""
    tracker.set_user_budget("user123", Decimal("10.00"))
    
    # Use 85% of budget (should trigger warning)
    tracker.track_cost("API1", Decimal("8.50"), user_id="user123")
    
    alerts = tracker.get_alerts(level="warning")
    assert len(alerts) > 0
    
    # Use more (should trigger critical)
    tracker.track_cost("API2", Decimal("1.00"), user_id="user123")
    
    critical_alerts = tracker.get_alerts(level="critical")
    assert len(critical_alerts) > 0


def test_reset_user_costs(tracker):
    """Test resetting user costs"""
    tracker.track_cost("API1", Decimal("5.00"), user_id="user123")
    
    assert tracker.get_user_cost("user123") == Decimal("5.00")
    
    tracker.reset_user_costs("user123")
    
    assert tracker.get_user_cost("user123") == Decimal("0.00")


def test_tracker_stats(tracker):
    """Test overall tracker statistics"""
    tracker.track_cost("API1", Decimal("1.00"), success=True)
    tracker.track_cost("API2", Decimal("2.00"), success=True)
    tracker.track_cost("API3", Decimal("1.50"), success=False)
    
    stats = tracker.get_stats()
    
    assert stats["total_cost"] == 4.50
    assert stats["total_requests"] == 3
    assert stats["success_rate"] == pytest.approx(0.666, 0.01)
    assert "API1" in stats["api_breakdown"]


def test_cost_entry_creation():
    """Test cost entry dataclass"""
    entry = CostEntry(
        api_name="TestAPI",
        cost=Decimal("0.50"),
        timestamp=datetime.utcnow(),
        user_id="user123",
        success=True
    )
    
    assert entry.api_name == "TestAPI"
    assert entry.cost == Decimal("0.50")
    assert entry.user_id == "user123"
    assert entry.success is True


def test_budget_alert_creation():
    """Test budget alert dataclass"""
    alert = BudgetAlert(
        level="warning",
        message="Budget warning",
        current_cost=Decimal("8.00"),
        budget_limit=Decimal("10.00"),
        percentage_used=0.8,
        timestamp=datetime.utcnow()
    )
    
    assert alert.level == "warning"
    assert alert.percentage_used == 0.8
    assert alert.current_cost == Decimal("8.00")
