"""
Base API Client
Foundation for all external API integrations with async HTTP, rate limiting, caching, and error handling
"""
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import hashlib
import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from app.core.cache import cache
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class APITier(Enum):
    """API tier classification for cost and priority"""
    FREE = "free"
    FREEMIUM = "freemium"
    PREMIUM = "premium"


class APICategory(Enum):
    """API category for content classification"""
    HISTORICAL = "historical"
    CULTURAL = "cultural"
    TOURISM = "tourism"
    GEOGRAPHIC = "geographic"
    ACADEMIC = "academic"
    NEWS = "news"
    GOVERNMENT = "government"


class RateLimiter:
    """Token bucket rate limiter for API calls"""
    
    def __init__(self, rate: int, per: int):
        """
        Initialize rate limiter
        
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = datetime.now()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make API call"""
        async with self._lock:
            current = datetime.now()
            time_passed = (current - self.last_check).total_seconds()
            self.last_check = current
            
            # Replenish tokens
            self.allowance += time_passed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate
            
            # Check if we have tokens
            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self.allowance = 1.0
            
            self.allowance -= 1.0


class APIConfig:
    """Configuration for API client"""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        tier: APITier,
        category: APICategory,
        rate_limit: int,
        rate_period: int,
        cost_per_request: float = 0.0,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 1800,  # 30 minutes
        requires_auth: bool = False,
        auth_type: str = "api_key",
        headers: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.base_url = base_url
        self.tier = tier
        self.category = category
        self.rate_limit = rate_limit
        self.rate_period = rate_period
        self.cost_per_request = cost_per_request
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self.requires_auth = requires_auth
        self.auth_type = auth_type
        self.headers = headers or {}


class APIResponse:
    """Standardized API response"""
    
    def __init__(
        self,
        success: bool,
        data: Any,
        error: Optional[str] = None,
        status_code: Optional[int] = None,
        cached: bool = False,
        cost: float = 0.0,
        response_time: float = 0.0,
        source: str = ""
    ):
        self.success = success
        self.data = data
        self.error = error
        self.status_code = status_code
        self.cached = cached
        self.cost = cost
        self.response_time = response_time
        self.source = source
        self.timestamp = datetime.utcnow()


class BaseAPIClient(ABC):
    """
    Base class for all API clients
    Provides async HTTP, rate limiting, caching, and error handling
    """
    
    def __init__(self, config: APIConfig, api_key: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            config: API configuration
            api_key: API key for authentication
        """
        self.config = config
        self.api_key = api_key
        self.rate_limiter = RateLimiter(config.rate_limit, config.rate_period)
        self.session: Optional[ClientSession] = None
        self._request_count = 0
        self._error_count = 0
        self._total_cost = 0.0
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = ClientTimeout(total=self.config.timeout)
            connector = TCPConnector(limit=100, limit_per_host=10)
            
            self.session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self._get_default_headers()
            )
            
            logger.info(f"API client connected: {self.config.name}")
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info(
                f"API client closed: {self.config.name}",
                requests=self._request_count,
                errors=self._error_count,
                cost=self._total_cost
            )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests"""
        headers = {
            "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}",
            "Accept": "application/json",
        }
        headers.update(self.config.headers)
        
        # Add authentication if required
        if self.config.requires_auth and self.api_key:
            if self.config.auth_type == "api_key":
                headers["X-API-Key"] = self.api_key
            elif self.config.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        key_string = f"{self.config.name}:{endpoint}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[APIResponse]:
        """Get cached response if available"""
        cached_data = await cache.get_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for {self.config.name}")
            return APIResponse(
                success=True,
                data=cached_data,
                cached=True,
                source=self.config.name
            )
        return None
    
    async def _cache_response(self, cache_key: str, data: Any):
        """Cache response data"""
        await cache.set_cache(cache_key, data, ttl=self.config.cache_ttl)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            APIResponse object
        """
        if not self.session:
            await self.connect()
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Build URL
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        
        # Track metrics
        start_time = datetime.now()
        self._request_count += 1
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers
            ) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Track cost
                self._total_cost += self.config.cost_per_request
                
                # Parse response
                if response.status == 200:
                    response_data = await self._parse_response(response)
                    
                    logger.info(
                        f"API request successful: {self.config.name}",
                        endpoint=endpoint,
                        status=response.status,
                        response_time=response_time
                    )
                    
                    return APIResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status,
                        cost=self.config.cost_per_request,
                        response_time=response_time,
                        source=self.config.name
                    )
                else:
                    error_text = await response.text()
                    self._error_count += 1
                    
                    logger.warning(
                        f"API request failed: {self.config.name}",
                        endpoint=endpoint,
                        status=response.status,
                        error=error_text
                    )
                    
                    return APIResponse(
                        success=False,
                        data=None,
                        error=f"HTTP {response.status}: {error_text}",
                        status_code=response.status,
                        cost=self.config.cost_per_request,
                        response_time=response_time,
                        source=self.config.name
                    )
                    
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._error_count += 1
            
            logger.error(
                f"API request error: {self.config.name}",
                endpoint=endpoint,
                error=str(e),
                exc_info=True
            )
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time=response_time,
                source=self.config.name
            )
    
    async def _parse_response(self, response: aiohttp.ClientResponse) -> Any:
        """
        Parse API response
        Override this method for custom parsing (e.g., XML)
        
        Args:
            response: aiohttp response object
            
        Returns:
            Parsed response data
        """
        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            return await response.json()
        elif "application/xml" in content_type or "text/xml" in content_type:
            return await response.text()
        else:
            return await response.text()
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> APIResponse:
        """
        Make GET request
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            use_cache: Whether to use caching
            
        Returns:
            APIResponse object
        """
        params = params or {}
        
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(endpoint, params)
            cached = await self._get_cached_response(cache_key)
            if cached:
                return cached
        
        # Make request
        response = await self._make_request("GET", endpoint, params=params)
        
        # Cache successful response
        if response.success and use_cache:
            cache_key = self._generate_cache_key(endpoint, params)
            await self._cache_response(cache_key, response.data)
        
        return response
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """Make POST request"""
        return await self._make_request("POST", endpoint, params=params, data=data)
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> APIResponse:
        """
        Search API - must be implemented by subclasses
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            APIResponse with search results
        """
        pass
    
    @abstractmethod
    def transform_response(self, raw_data: Any) -> Dict[str, Any]:
        """
        Transform API response to standardized format
        Must be implemented by subclasses
        
        Args:
            raw_data: Raw API response data
            
        Returns:
            Standardized data dictionary
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API client statistics"""
        return {
            "name": self.config.name,
            "tier": self.config.tier.value,
            "category": self.config.category.value,
            "requests": self._request_count,
            "errors": self._error_count,
            "error_rate": self._error_count / self._request_count if self._request_count > 0 else 0,
            "total_cost": self._total_cost,
            "avg_cost_per_request": self._total_cost / self._request_count if self._request_count > 0 else 0
        }
