"""
Rate Limiting Middleware
Tier-based request rate limiting with Redis
"""
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.cache import cache
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing rate limits based on user tier"""
    
    def __init__(self, app):
        super().__init__(app)
        self.window_seconds = settings.rate_limit_window_seconds
        self.limits = {
            "free": settings.RATE_LIMIT_FREE_TIER,
            "premium": settings.RATE_LIMIT_PREMIUM_TIER,
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting
        
        Args:
            request: FastAPI request
            call_next: Next middleware/route handler
            
        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get user info from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        user_tier = getattr(request.state, "user_tier", "free")
        
        # Use IP address for unauthenticated requests
        if not user_id:
            user_id = f"ip:{request.client.host}"
            user_tier = "free"
        
        # Get rate limit for user tier
        limit = self.limits.get(user_tier, self.limits["free"])
        
        # Check rate limit
        rate_limit_result = await cache.check_rate_limit(
            user_id=user_id,
            limit=limit,
            window=self.window_seconds
        )
        
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
            "X-RateLimit-Reset": str(rate_limit_result["reset"]),
        }
        
        # Check if rate limit exceeded
        if not rate_limit_result["allowed"]:
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                tier=user_tier,
                limit=limit
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Limit: {limit} requests per hour.",
                    "retry_after": rate_limit_result["reset"]
                },
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


async def check_rate_limit_dependency(
    request: Request,
    limit: int = None,
    window: int = None
) -> bool:
    """
    Dependency for checking rate limits in specific endpoints
    
    Args:
        request: FastAPI request
        limit: Custom rate limit (optional)
        window: Custom time window in seconds (optional)
        
    Returns:
        True if within rate limit
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    user_id = getattr(request.state, "user_id", f"ip:{request.client.host}")
    user_tier = getattr(request.state, "user_tier", "free")
    
    # Use custom limit or tier-based limit
    if limit is None:
        limit = (
            settings.RATE_LIMIT_PREMIUM_TIER
            if user_tier == "premium"
            else settings.RATE_LIMIT_FREE_TIER
        )
    
    if window is None:
        window = settings.rate_limit_window_seconds
    
    # Check rate limit
    result = await cache.check_rate_limit(
        user_id=user_id,
        limit=limit,
        window=window
    )
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {limit} requests per hour.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(result["reset"]),
                "Retry-After": str(result["reset"])
            }
        )
    
    return True
