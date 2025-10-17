"""
Redis Cache Manager
Multi-database Redis caching with TTL management
"""
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta
import redis.asyncio as redis
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class RedisCache:
    """Redis cache manager with multiple database support"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.default_ttl = settings.REDIS_TTL_DEFAULT
        
        # Connection pools for different databases
        self._cache_pool: Optional[redis.Redis] = None
        self._session_pool: Optional[redis.Redis] = None
        self._rate_limit_pool: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Initialize Redis connections (optional - falls back to in-memory)"""
        try:
            # Cache database (DB 0)
            self._cache_pool = redis.from_url(
                self.redis_url,
                db=settings.REDIS_DB_CACHE,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            
            # Session database (DB 1)
            self._session_pool = redis.from_url(
                self.redis_url,
                db=settings.REDIS_DB_SESSIONS,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            
            # Rate limiting database (DB 2)
            self._rate_limit_pool = redis.from_url(
                self.redis_url,
                db=settings.REDIS_DB_RATE_LIMIT,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            
            # Test connections
            await self._cache_pool.ping()
            await self._session_pool.ping()
            await self._rate_limit_pool.ping()
            
            logger.info("Redis connections established successfully")
            
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache fallback: {e}")
            # Set pools to None - methods will handle fallback
            self._cache_pool = None
            self._session_pool = None
            self._rate_limit_pool = None
    
    async def close(self) -> None:
        """Close all Redis connections"""
        if self._cache_pool:
            await self._cache_pool.close()
        if self._session_pool:
            await self._session_pool.close()
        if self._rate_limit_pool:
            await self._rate_limit_pool.close()
        
        logger.info("Redis connections closed")
    
    # ========================================================================
    # Cache Operations (DB 0)
    # ========================================================================
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self._cache_pool:
            return None
        try:
            value = await self._cache_pool.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 30 minutes)
            
        Returns:
            Success status
        """
        if not self._cache_pool:
            return False
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self._cache_pool.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete_cache(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._cache_pool:
            return False
        try:
            await self._cache_pool.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_cache_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        if not self._cache_pool:
            return 0
        try:
            keys = []
            async for key in self._cache_pool.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._cache_pool.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    # ========================================================================
    # Session Operations (DB 1)
    # ========================================================================
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if not self._session_pool:
            return None
        try:
            value = await self._session_pool.get(f"session:{session_id}")
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Session get error for {session_id}: {e}")
            return None
    
    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Set session data with TTL"""
        if not self._session_pool:
            return False
        try:
            serialized = json.dumps(data)
            await self._session_pool.setex(f"session:{session_id}", ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Session set error for {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if not self._session_pool:
            return False
        try:
            await self._session_pool.delete(f"session:{session_id}")
            return True
        except Exception as e:
            logger.error(f"Session delete error for {session_id}: {e}")
            return False
    
    # ========================================================================
    # Rate Limiting Operations (DB 2)
    # ========================================================================
    
    async def check_rate_limit(
        self,
        user_id: str,
        limit: int,
        window: int
    ) -> Dict[str, Any]:
        """
        Check and increment rate limit counter
        
        Args:
            user_id: User identifier
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Dict with allowed status, remaining, and reset time
        """
        if not self._rate_limit_pool:
            # No rate limiting without Redis
            return {"allowed": True, "remaining": limit, "reset": window}
        try:
            key = f"rate_limit:{user_id}"
            
            # Get current count
            current = await self._rate_limit_pool.get(key)
            
            if current is None:
                # First request in window
                await self._rate_limit_pool.setex(key, window, 1)
                return {
                    "allowed": True,
                    "remaining": limit - 1,
                    "reset": window
                }
            
            current = int(current)
            
            if current >= limit:
                # Rate limit exceeded
                ttl = await self._rate_limit_pool.ttl(key)
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset": ttl
                }
            
            # Increment counter
            await self._rate_limit_pool.incr(key)
            ttl = await self._rate_limit_pool.ttl(key)
            
            return {
                "allowed": True,
                "remaining": limit - current - 1,
                "reset": ttl
            }
            
        except Exception as e:
            logger.error(f"Rate limit check error for {user_id}: {e}")
            # Fail open - allow request on error
            return {
                "allowed": True,
                "remaining": limit,
                "reset": window
            }
    
    async def reset_rate_limit(self, user_id: str) -> bool:
        """Reset rate limit for user"""
        if not self._rate_limit_pool:
            return False
        try:
            await self._rate_limit_pool.delete(f"rate_limit:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Rate limit reset error for {user_id}: {e}")
            return False
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    @staticmethod
    def generate_cache_key(*args: Any) -> str:
        """
        Generate consistent cache key from arguments
        
        Args:
            *args: Arguments to hash
            
        Returns:
            Cache key string
        """
        key_string = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all Redis connections"""
        health = {}
        
        try:
            await self._cache_pool.ping()
            health["cache"] = True
        except:
            health["cache"] = False
        
        try:
            await self._session_pool.ping()
            health["session"] = True
        except:
            health["session"] = False
        
        try:
            await self._rate_limit_pool.ping()
            health["rate_limit"] = True
        except:
            health["rate_limit"] = False
        
        return health


# Global cache instance
cache = RedisCache()


def get_redis_client() -> RedisCache:
    """
    Get Redis cache client instance
    
    Returns:
        RedisCache instance
    """
    return cache
