"""
Cost Tracker
Real-time API cost monitoring and budget enforcement
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import structlog

logger = structlog.get_logger()


@dataclass
class CostEntry:
    """Single cost entry"""
    api_name: str
    cost: Decimal
    timestamp: datetime
    user_id: Optional[str] = None
    request_type: Optional[str] = None
    success: bool = True


@dataclass
class BudgetAlert:
    """Budget alert"""
    level: str  # warning, critical
    message: str
    current_cost: Decimal
    budget_limit: Decimal
    percentage_used: float
    timestamp: datetime


@dataclass
class CostSummary:
    """Cost summary for a period"""
    total_cost: Decimal
    api_breakdown: Dict[str, Decimal] = field(default_factory=dict)
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_cost_per_request: Decimal = Decimal("0.0")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class CostTracker:
    """
    Tracks API costs and enforces budgets
    
    Features:
    - Real-time cost tracking
    - Budget enforcement per user/tier
    - Cost analytics and reporting
    - Budget alerts
    - Cost optimization recommendations
    """
    
    def __init__(self):
        self._cost_entries: List[CostEntry] = []
        self._user_budgets: Dict[str, Decimal] = {}
        self._user_costs: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.0"))
        self._alerts: List[BudgetAlert] = []
        
        # Alert thresholds
        self.warning_threshold = 0.8  # 80% of budget
        self.critical_threshold = 0.95  # 95% of budget
    
    def set_user_budget(self, user_id: str, budget: Decimal):
        """
        Set budget for a user
        
        Args:
            user_id: User identifier
            budget: Budget amount
        """
        self._user_budgets[user_id] = budget
        logger.info(f"Set budget for user {user_id}: ${budget}")
    
    def track_cost(
        self,
        api_name: str,
        cost: Decimal,
        user_id: Optional[str] = None,
        request_type: Optional[str] = None,
        success: bool = True
    ) -> bool:
        """
        Track API cost
        
        Args:
            api_name: API name
            cost: Cost amount
            user_id: Optional user ID
            request_type: Optional request type
            success: Whether request was successful
            
        Returns:
            True if within budget, False if budget exceeded
        """
        # Create cost entry
        entry = CostEntry(
            api_name=api_name,
            cost=cost,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            request_type=request_type,
            success=success
        )
        
        self._cost_entries.append(entry)
        
        # Update user cost if user_id provided
        if user_id:
            self._user_costs[user_id] += cost
            
            # Check budget
            if user_id in self._user_budgets:
                budget = self._user_budgets[user_id]
                current_cost = self._user_costs[user_id]
                percentage_used = float(current_cost / budget) if budget > 0 else 0.0
                
                # Check for alerts
                if percentage_used >= self.critical_threshold:
                    self._create_alert(
                        level="critical",
                        message=f"User {user_id} has used {percentage_used:.1%} of budget",
                        current_cost=current_cost,
                        budget_limit=budget,
                        percentage_used=percentage_used
                    )
                    return False
                    
                elif percentage_used >= self.warning_threshold:
                    self._create_alert(
                        level="warning",
                        message=f"User {user_id} has used {percentage_used:.1%} of budget",
                        current_cost=current_cost,
                        budget_limit=budget,
                        percentage_used=percentage_used
                    )
        
        logger.debug(
            "Cost tracked",
            api=api_name,
            cost=float(cost),
            user_id=user_id,
            success=success
        )
        
        return True
    
    def check_budget(self, user_id: str, estimated_cost: Decimal) -> bool:
        """
        Check if user has budget for estimated cost
        
        Args:
            user_id: User identifier
            estimated_cost: Estimated cost
            
        Returns:
            True if within budget, False otherwise
        """
        if user_id not in self._user_budgets:
            # No budget set, allow
            return True
        
        budget = self._user_budgets[user_id]
        current_cost = self._user_costs[user_id]
        
        return (current_cost + estimated_cost) <= budget
    
    def get_user_cost(self, user_id: str) -> Decimal:
        """Get current cost for user"""
        return self._user_costs[user_id]
    
    def get_user_remaining_budget(self, user_id: str) -> Optional[Decimal]:
        """Get remaining budget for user"""
        if user_id not in self._user_budgets:
            return None
        
        budget = self._user_budgets[user_id]
        current_cost = self._user_costs[user_id]
        
        return max(budget - current_cost, Decimal("0.0"))
    
    def get_cost_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        api_name: Optional[str] = None
    ) -> CostSummary:
        """
        Get cost summary for a period
        
        Args:
            start_time: Start of period (default: all time)
            end_time: End of period (default: now)
            user_id: Filter by user
            api_name: Filter by API
            
        Returns:
            CostSummary
        """
        # Filter entries
        filtered_entries = self._cost_entries
        
        if start_time:
            filtered_entries = [e for e in filtered_entries if e.timestamp >= start_time]
        
        if end_time:
            filtered_entries = [e for e in filtered_entries if e.timestamp <= end_time]
        
        if user_id:
            filtered_entries = [e for e in filtered_entries if e.user_id == user_id]
        
        if api_name:
            filtered_entries = [e for e in filtered_entries if e.api_name == api_name]
        
        # Calculate summary
        total_cost = sum(e.cost for e in filtered_entries)
        request_count = len(filtered_entries)
        success_count = sum(1 for e in filtered_entries if e.success)
        failure_count = request_count - success_count
        
        # API breakdown
        api_breakdown = defaultdict(lambda: Decimal("0.0"))
        for entry in filtered_entries:
            api_breakdown[entry.api_name] += entry.cost
        
        # Average cost
        avg_cost = total_cost / request_count if request_count > 0 else Decimal("0.0")
        
        return CostSummary(
            total_cost=total_cost,
            api_breakdown=dict(api_breakdown),
            request_count=request_count,
            success_count=success_count,
            failure_count=failure_count,
            avg_cost_per_request=avg_cost,
            period_start=start_time,
            period_end=end_time
        )
    
    def get_cost_by_api(self, api_name: str) -> Decimal:
        """Get total cost for specific API"""
        return sum(
            e.cost for e in self._cost_entries
            if e.api_name == api_name
        )
    
    def get_optimization_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations
        
        Args:
            user_id: User identifier
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Get user's API usage
        user_entries = [e for e in self._cost_entries if e.user_id == user_id]
        
        if not user_entries:
            return recommendations
        
        # Calculate API costs
        api_costs = defaultdict(lambda: Decimal("0.0"))
        api_counts = defaultdict(int)
        
        for entry in user_entries:
            api_costs[entry.api_name] += entry.cost
            api_counts[entry.api_name] += 1
        
        # Find expensive APIs
        total_cost = sum(api_costs.values())
        
        for api_name, cost in api_costs.items():
            percentage = float(cost / total_cost) if total_cost > 0 else 0.0
            
            if percentage > 0.3:  # API accounts for >30% of costs
                recommendations.append({
                    "type": "high_cost_api",
                    "api": api_name,
                    "cost": float(cost),
                    "percentage": percentage,
                    "message": f"{api_name} accounts for {percentage:.1%} of your costs. Consider using free alternatives.",
                    "priority": "high" if percentage > 0.5 else "medium"
                })
        
        # Check for repeated queries (caching opportunity)
        # This is simplified - in production, you'd analyze actual query patterns
        if len(user_entries) > 100:
            recommendations.append({
                "type": "caching_opportunity",
                "message": "Enable aggressive caching to reduce API calls",
                "estimated_savings": float(total_cost * Decimal("0.2")),  # Estimate 20% savings
                "priority": "medium"
            })
        
        # Check budget usage
        if user_id in self._user_budgets:
            budget = self._user_budgets[user_id]
            current_cost = self._user_costs[user_id]
            percentage_used = float(current_cost / budget) if budget > 0 else 0.0
            
            if percentage_used > 0.7:
                recommendations.append({
                    "type": "budget_warning",
                    "message": f"You've used {percentage_used:.1%} of your budget",
                    "current_cost": float(current_cost),
                    "budget": float(budget),
                    "priority": "high" if percentage_used > 0.9 else "medium"
                })
        
        return recommendations
    
    def _create_alert(
        self,
        level: str,
        message: str,
        current_cost: Decimal,
        budget_limit: Decimal,
        percentage_used: float
    ):
        """Create budget alert"""
        alert = BudgetAlert(
            level=level,
            message=message,
            current_cost=current_cost,
            budget_limit=budget_limit,
            percentage_used=percentage_used,
            timestamp=datetime.utcnow()
        )
        
        self._alerts.append(alert)
        
        logger.warning(
            f"Budget alert: {level}",
            message=message,
            current_cost=float(current_cost),
            budget=float(budget_limit),
            percentage=percentage_used
        )
    
    def get_alerts(
        self,
        level: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[BudgetAlert]:
        """
        Get budget alerts
        
        Args:
            level: Filter by level (warning, critical)
            since: Get alerts since this time
            
        Returns:
            List of alerts
        """
        alerts = self._alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        
        return alerts
    
    def reset_user_costs(self, user_id: str):
        """Reset costs for a user (e.g., monthly reset)"""
        self._user_costs[user_id] = Decimal("0.0")
        logger.info(f"Reset costs for user {user_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall cost tracking statistics"""
        summary = self.get_cost_summary()
        
        return {
            "total_cost": float(summary.total_cost),
            "total_requests": summary.request_count,
            "success_rate": summary.success_count / summary.request_count if summary.request_count > 0 else 0,
            "avg_cost_per_request": float(summary.avg_cost_per_request),
            "api_breakdown": {k: float(v) for k, v in summary.api_breakdown.items()},
            "active_users": len(self._user_costs),
            "users_with_budgets": len(self._user_budgets),
            "total_alerts": len(self._alerts),
            "critical_alerts": len([a for a in self._alerts if a.level == "critical"])
        }


# Global cost tracker instance
cost_tracker = CostTracker()
