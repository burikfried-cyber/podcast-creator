"""
API Orchestrator
Intelligent API selection and coordination based on content type, user tier, and budget
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from decimal import Decimal
from app.services.api_clients.base import (
    BaseAPIClient,
    APIResponse,
    APITier,
    APICategory
)
from app.services.api_clients.circuit_breaker import circuit_breaker_manager, CircuitBreakerError
import structlog

logger = structlog.get_logger()


class ContentType(Enum):
    """Content type for gathering strategy"""
    BASE = "base"  # Essential location information
    STANDOUT = "standout"  # Unique/unusual discoveries
    TOPIC_SPECIFIC = "topic_specific"  # User preference-driven
    ENRICHMENT = "enrichment"  # Additional context


class UserTier(Enum):
    """User subscription tier"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class BudgetConfig:
    """Budget configuration per user tier"""
    tier: UserTier
    max_cost_per_request: Decimal
    preferred_free_ratio: float  # Ratio of free vs paid APIs
    quality_threshold: float  # Minimum quality score


# Budget configurations
BUDGET_CONFIGS = {
    UserTier.FREE: BudgetConfig(
        tier=UserTier.FREE,
        max_cost_per_request=Decimal("0.10"),
        preferred_free_ratio=0.9,  # 90% free APIs
        quality_threshold=0.6
    ),
    UserTier.PREMIUM: BudgetConfig(
        tier=UserTier.PREMIUM,
        max_cost_per_request=Decimal("0.50"),
        preferred_free_ratio=0.7,  # 70% free APIs
        quality_threshold=0.75
    ),
    UserTier.ENTERPRISE: BudgetConfig(
        tier=UserTier.ENTERPRISE,
        max_cost_per_request=Decimal("1.50"),
        preferred_free_ratio=0.5,  # 50% free APIs
        quality_threshold=0.85
    )
}


@dataclass
class APIStrategy:
    """Strategy for API selection"""
    primary_apis: List[BaseAPIClient]
    fallback_apis: List[BaseAPIClient]
    parallel_execution: bool
    min_sources: int
    max_sources: int
    timeout: float


class APIOrchestrator:
    """
    Orchestrates API calls with intelligent selection
    
    Features:
    - Content type-based API selection
    - Budget-aware API prioritization
    - Parallel execution for performance
    - Circuit breaker integration
    - Fallback mechanisms
    - Cost tracking
    """
    
    def __init__(self):
        self.api_registry: Dict[str, BaseAPIClient] = {}
        self._total_cost = Decimal("0.0")
        self._request_count = 0
    
    def register_api(self, name: str, client: BaseAPIClient):
        """
        Register API client
        
        Args:
            name: API name
            client: API client instance
        """
        self.api_registry[name] = client
        logger.info(f"Registered API client: {name}")
    
    def get_api(self, name: str) -> Optional[BaseAPIClient]:
        """Get registered API client by name"""
        return self.api_registry.get(name)
    
    async def orchestrate_content_gathering(
        self,
        query: str,
        content_type: ContentType,
        user_tier: UserTier,
        location: Optional[Dict[str, float]] = None,
        categories: Optional[List[APICategory]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Orchestrate content gathering from multiple APIs
        
        Args:
            query: Search query
            content_type: Type of content to gather
            user_tier: User subscription tier
            location: Optional location dict with lat/lon
            categories: Filter by API categories
            **kwargs: Additional parameters
            
        Returns:
            Aggregated results from multiple APIs
        """
        # Get budget config
        budget_config = BUDGET_CONFIGS[user_tier]
        
        # Select API strategy
        strategy = self._select_api_strategy(
            content_type=content_type,
            budget_config=budget_config,
            categories=categories
        )
        
        logger.info(
            "Orchestrating content gathering",
            content_type=content_type.value,
            user_tier=user_tier.value,
            primary_apis=len(strategy.primary_apis),
            fallback_apis=len(strategy.fallback_apis)
        )
        
        # Execute API calls
        results = await self._execute_strategy(
            strategy=strategy,
            query=query,
            location=location,
            budget_config=budget_config,
            **kwargs
        )
        
        # Aggregate and deduplicate results
        aggregated = self._aggregate_results(results)
        
        # Track costs
        total_cost = sum(r.cost for r in results if r.success)
        self._total_cost += Decimal(str(total_cost))
        self._request_count += len(results)
        
        return {
            "query": query,
            "content_type": content_type.value,
            "user_tier": user_tier.value,
            "total_results": aggregated["total_count"],
            "items": aggregated["items"],
            "sources": aggregated["sources"],
            "cost": float(total_cost),
            "api_calls": len(results),
            "successful_calls": sum(1 for r in results if r.success),
            "cached_calls": sum(1 for r in results if r.cached)
        }
    
    def _select_api_strategy(
        self,
        content_type: ContentType,
        budget_config: BudgetConfig,
        categories: Optional[List[APICategory]] = None
    ) -> APIStrategy:
        """
        Select optimal API strategy based on content type and budget
        
        Args:
            content_type: Type of content
            budget_config: Budget configuration
            categories: Filter by categories
            
        Returns:
            APIStrategy with selected APIs
        """
        # Filter APIs by category if specified
        available_apis = list(self.api_registry.values())
        
        if categories:
            available_apis = [
                api for api in available_apis
                if api.config.category in categories
            ]
        
        # Sort APIs by cost and tier
        free_apis = [api for api in available_apis if api.config.tier == APITier.FREE]
        freemium_apis = [api for api in available_apis if api.config.tier == APITier.FREEMIUM]
        premium_apis = [api for api in available_apis if api.config.tier == APITier.PREMIUM]
        
        # Strategy based on content type
        if content_type == ContentType.BASE:
            # Base content: prioritize authoritative free sources
            primary = free_apis[:3]
            fallback = freemium_apis[:2]
            parallel = True
            min_sources = 2
            max_sources = 5
            timeout = 5.0
            
        elif content_type == ContentType.STANDOUT:
            # Standout: wide scanning with premium validation
            free_ratio = budget_config.preferred_free_ratio
            num_free = int(5 * free_ratio)
            num_premium = 5 - num_free
            
            primary = free_apis[:num_free] + premium_apis[:num_premium]
            fallback = freemium_apis[:2]
            parallel = True
            min_sources = 3
            max_sources = 7
            timeout = 8.0
            
        elif content_type == ContentType.TOPIC_SPECIFIC:
            # Topic-specific: focused gathering with depth
            primary = free_apis[:2] + freemium_apis[:2]
            fallback = premium_apis[:1]
            parallel = True
            min_sources = 2
            max_sources = 4
            timeout = 6.0
            
        else:  # ENRICHMENT
            # Enrichment: opportunistic gathering
            primary = free_apis[:2]
            fallback = []
            parallel = True
            min_sources = 1
            max_sources = 3
            timeout = 4.0
        
        return APIStrategy(
            primary_apis=primary,
            fallback_apis=fallback,
            parallel_execution=parallel,
            min_sources=min_sources,
            max_sources=max_sources,
            timeout=timeout
        )
    
    async def _execute_strategy(
        self,
        strategy: APIStrategy,
        query: str,
        location: Optional[Dict[str, float]],
        budget_config: BudgetConfig,
        **kwargs
    ) -> List[APIResponse]:
        """
        Execute API strategy with circuit breaker protection
        
        Args:
            strategy: API strategy
            query: Search query
            location: Optional location
            budget_config: Budget configuration
            **kwargs: Additional parameters
            
        Returns:
            List of API responses
        """
        results = []
        
        # Execute primary APIs
        if strategy.parallel_execution:
            # Parallel execution
            tasks = [
                self._call_api_with_circuit_breaker(api, query, location, **kwargs)
                for api in strategy.primary_apis
            ]
            
            try:
                primary_results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=strategy.timeout
                )
                results.extend([r for r in primary_results if isinstance(r, APIResponse)])
            except asyncio.TimeoutError:
                logger.warning(f"Primary API calls timed out after {strategy.timeout}s")
        else:
            # Sequential execution
            for api in strategy.primary_apis:
                result = await self._call_api_with_circuit_breaker(api, query, location, **kwargs)
                results.append(result)
                
                # Check if we have enough successful results
                successful = sum(1 for r in results if r.success)
                if successful >= strategy.min_sources:
                    break
        
        # Check if we need fallback APIs
        successful_count = sum(1 for r in results if r.success)
        
        if successful_count < strategy.min_sources and strategy.fallback_apis:
            logger.info(f"Using fallback APIs (successful: {successful_count}/{strategy.min_sources})")
            
            for api in strategy.fallback_apis:
                result = await self._call_api_with_circuit_breaker(api, query, location, **kwargs)
                results.append(result)
                
                successful_count = sum(1 for r in results if r.success)
                if successful_count >= strategy.min_sources:
                    break
        
        return results
    
    async def _call_api_with_circuit_breaker(
        self,
        api: BaseAPIClient,
        query: str,
        location: Optional[Dict[str, float]],
        **kwargs
    ) -> APIResponse:
        """
        Call API with circuit breaker protection
        
        Args:
            api: API client
            query: Search query
            location: Optional location
            **kwargs: Additional parameters
            
        Returns:
            APIResponse
        """
        # Get circuit breaker for this API
        breaker = await circuit_breaker_manager.get_breaker(
            name=api.config.name,
            failure_threshold=5,
            recovery_timeout=60
        )
        
        try:
            # Call API through circuit breaker
            result = await breaker.call(api.search, query, **kwargs)
            return result
            
        except CircuitBreakerError as e:
            logger.warning(f"Circuit breaker open for {api.config.name}: {e}")
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                source=api.config.name
            )
            
        except Exception as e:
            logger.error(f"API call failed for {api.config.name}: {e}")
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                source=api.config.name
            )
    
    def _aggregate_results(self, results: List[APIResponse]) -> Dict[str, Any]:
        """
        Aggregate and deduplicate results from multiple APIs
        
        Args:
            results: List of API responses
            
        Returns:
            Aggregated results
        """
        all_items = []
        sources = []
        
        for response in results:
            if response.success and response.data:
                items = response.data.get("items", [])
                all_items.extend(items)
                sources.append({
                    "name": response.source,
                    "count": len(items),
                    "cached": response.cached,
                    "cost": response.cost,
                    "response_time": response.response_time
                })
        
        # Deduplicate by title (simple approach)
        seen_titles = set()
        unique_items = []
        
        for item in all_items:
            title = item.get("title", "").lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_items.append(item)
        
        return {
            "total_count": len(unique_items),
            "items": unique_items,
            "sources": sources
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        api_stats = [
            api.get_stats()
            for api in self.api_registry.values()
        ]
        
        circuit_breaker_stats = circuit_breaker_manager.get_all_stats()
        
        return {
            "total_cost": float(self._total_cost),
            "total_requests": self._request_count,
            "avg_cost_per_request": float(self._total_cost / self._request_count) if self._request_count > 0 else 0,
            "registered_apis": len(self.api_registry),
            "api_stats": api_stats,
            "circuit_breakers": circuit_breaker_stats
        }


# Global orchestrator instance
api_orchestrator = APIOrchestrator()
