"""
Performance Optimization Service
Caching, batch processing, and query optimization for Phase 3 components
"""
from typing import Dict, List, Any, Optional
import json
import hashlib
from datetime import datetime, timedelta
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import asyncio

from app.core.cache import get_redis_client
from app.models.preferences import UserTopicPreference, UserLearningState

logger = structlog.get_logger()


class PerformanceOptimizer:
    """
    Performance Optimization for Phase 3
    
    Features:
    - Redis caching for recommendations
    - Batch preference updates
    - Query result caching
    - Recommendation pre-computation
    - Cache invalidation strategies
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = get_redis_client()
        
        # Cache TTLs (seconds)
        self.cache_ttls = {
            "recommendations": 3600,  # 1 hour
            "user_profile": 1800,  # 30 minutes
            "model_predictions": 600,  # 10 minutes
            "topic_preferences": 900,  # 15 minutes
            "learning_state": 300  # 5 minutes
        }
        
        # Batch processing limits
        self.batch_size = 100
        self.max_concurrent_tasks = 10
    
    async def get_cached_recommendations(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached recommendations if available
        
        Args:
            user_id: User ID
            context: Request context
            
        Returns:
            Cached recommendations or None
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                "recommendations",
                user_id,
                context
            )
            
            # Try to get from cache
            cached_data = await self.redis.get_cache(cache_key)
            
            if cached_data:
                logger.info("cache_hit",
                           cache_type="recommendations",
                           user_id=user_id)
                return cached_data
            
            logger.info("cache_miss",
                       cache_type="recommendations",
                       user_id=user_id)
            return None
            
        except Exception as e:
            logger.error("cache_retrieval_failed",
                        user_id=user_id,
                        error=str(e))
            return None
    
    async def cache_recommendations(
        self,
        user_id: str,
        context: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache recommendations
        
        Args:
            user_id: User ID
            context: Request context
            recommendations: Recommendations to cache
            
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key(
                "recommendations",
                user_id,
                context
            )
            
            # Store in cache
            await self.redis.set_cache(
                cache_key,
                recommendations,
                self.cache_ttls["recommendations"]
            )
            
            logger.info("recommendations_cached",
                       user_id=user_id,
                       ttl=self.cache_ttls["recommendations"])
            
            return True
            
        except Exception as e:
            logger.error("cache_storage_failed",
                        user_id=user_id,
                        error=str(e))
            return False
    
    async def invalidate_user_cache(
        self,
        user_id: str,
        cache_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Invalidate user caches
        
        Args:
            user_id: User ID
            cache_types: Specific cache types to invalidate (or all if None)
            
        Returns:
            Invalidation results
        """
        try:
            if cache_types is None:
                cache_types = list(self.cache_ttls.keys())
            
            invalidated = []
            
            for cache_type in cache_types:
                # Clear all keys for this user and cache type
                pattern = f"{cache_type}:{user_id}:*"
                deleted_count = await self.redis.clear_cache_pattern(pattern)
                
                if deleted_count > 0:
                    invalidated.append(cache_type)
            
            logger.info("cache_invalidated",
                       user_id=user_id,
                       types=invalidated)
            
            return {
                "success": True,
                "invalidated": invalidated,
                "count": len(invalidated)
            }
            
        except Exception as e:
            logger.error("cache_invalidation_failed",
                        user_id=user_id,
                        error=str(e))
            return {"success": False, "error": str(e)}
    
    async def batch_update_preferences(
        self,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch update user preferences
        
        Args:
            updates: List of preference updates
            
        Returns:
            Batch update results
        """
        try:
            logger.info("batch_update_started", n_updates=len(updates))
            
            # Group updates by user
            user_updates = {}
            for update in updates:
                user_id = update["user_id"]
                if user_id not in user_updates:
                    user_updates[user_id] = []
                user_updates[user_id].append(update)
            
            # Process in batches
            results = []
            user_ids = list(user_updates.keys())
            
            for i in range(0, len(user_ids), self.batch_size):
                batch = user_ids[i:i + self.batch_size]
                
                # Process batch concurrently
                tasks = [
                    self._process_user_updates(user_id, user_updates[user_id])
                    for user_id in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend(batch_results)
            
            # Count successes
            successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            
            logger.info("batch_update_complete",
                       total=len(updates),
                       successes=successes)
            
            return {
                "success": True,
                "total": len(updates),
                "successes": successes,
                "failures": len(results) - successes
            }
            
        except Exception as e:
            logger.error("batch_update_failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _process_user_updates(
        self,
        user_id: str,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process updates for a single user"""
        try:
            from app.services.preferences import get_preference_model
            
            preference_model = get_preference_model(self.db)
            
            for update in updates:
                update_type = update.get("type")
                
                if update_type == "topic":
                    await preference_model.update_topic_preferences(
                        user_id,
                        update["signals"],
                        learning_rate=update.get("learning_rate", 0.1)
                    )
                elif update_type == "depth":
                    await preference_model.update_depth_preference(
                        user_id,
                        update["depth_level"],
                        satisfaction_score=update["satisfaction"]
                    )
                elif update_type == "surprise":
                    await preference_model.update_surprise_preference(
                        user_id,
                        update["surprise_level"],
                        reward=update["reward"]
                    )
            
            # Invalidate cache
            await self.invalidate_user_cache(user_id, ["user_profile", "topic_preferences"])
            
            return {"success": True, "user_id": user_id}
            
        except Exception as e:
            logger.error("user_update_failed", user_id=user_id, error=str(e))
            return {"success": False, "user_id": user_id, "error": str(e)}
    
    async def precompute_recommendations(
        self,
        user_ids: List[str],
        candidate_items: List[str]
    ) -> Dict[str, Any]:
        """
        Precompute recommendations for users
        
        Args:
            user_ids: List of user IDs
            candidate_items: Candidate items
            
        Returns:
            Precomputation results
        """
        try:
            logger.info("precompute_started",
                       n_users=len(user_ids),
                       n_candidates=len(candidate_items))
            
            from app.services.recommendation import get_hybrid_engine
            
            hybrid_engine = get_hybrid_engine(self.db)
            
            # Process in batches with concurrency limit
            results = []
            
            for i in range(0, len(user_ids), self.batch_size):
                batch = user_ids[i:i + self.batch_size]
                
                # Limit concurrent tasks
                semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
                
                async def process_with_limit(user_id):
                    async with semaphore:
                        return await self._precompute_user_recommendations(
                            user_id,
                            candidate_items,
                            hybrid_engine
                        )
                
                tasks = [process_with_limit(user_id) for user_id in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend(batch_results)
            
            successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            
            logger.info("precompute_complete",
                       total=len(user_ids),
                       successes=successes)
            
            return {
                "success": True,
                "total": len(user_ids),
                "successes": successes,
                "failures": len(results) - successes
            }
            
        except Exception as e:
            logger.error("precompute_failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _precompute_user_recommendations(
        self,
        user_id: str,
        candidate_items: List[str],
        hybrid_engine
    ) -> Dict[str, Any]:
        """Precompute recommendations for a single user"""
        try:
            # Get recommendations
            result = await hybrid_engine.get_recommendations(
                user_id,
                candidate_items,
                n_recommendations=20
            )
            
            if result["success"]:
                # Cache recommendations
                context = {"precomputed": True}
                await self.cache_recommendations(
                    user_id,
                    context,
                    result["recommendations"]
                )
            
            return {"success": True, "user_id": user_id}
            
        except Exception as e:
            logger.error("user_precompute_failed", user_id=user_id, error=str(e))
            return {"success": False, "user_id": user_id, "error": str(e)}
    
    async def get_cached_user_profile(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        try:
            cache_key = f"user_profile:{user_id}"
            cached_data = await self.redis.get_cache(cache_key)
            
            if cached_data:
                return cached_data
            return None
            
        except Exception as e:
            logger.error("profile_cache_retrieval_failed",
                        user_id=user_id,
                        error=str(e))
            return None
    
    async def cache_user_profile(
        self,
        user_id: str,
        profile: Dict[str, Any]
    ) -> bool:
        """Cache user profile"""
        try:
            cache_key = f"user_profile:{user_id}"
            await self.redis.set_cache(
                cache_key,
                profile,
                self.cache_ttls["user_profile"]
            )
            return True
            
        except Exception as e:
            logger.error("profile_cache_storage_failed",
                        user_id=user_id,
                        error=str(e))
            return False
    
    def _generate_cache_key(
        self,
        cache_type: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate cache key
        
        Args:
            cache_type: Type of cache
            user_id: User ID
            context: Context data
            
        Returns:
            Cache key
        """
        # Create context hash
        context_str = json.dumps(context, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        
        return f"{cache_type}:{user_id}:{context_hash}"
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        try:
            # Get key counts by type (simplified - no info stats for now)
            key_counts = {}
            total_keys = 0
            
            for cache_type in self.cache_ttls.keys():
                # Estimate based on pattern matching
                key_counts[cache_type] = 0  # Would need scan_iter to count
            
            return {
                "total_keys": total_keys,
                "keys_by_type": key_counts,
                "note": "Stats simplified - Redis info not available in async client"
            }
            
        except Exception as e:
            logger.error("cache_stats_failed", error=str(e))
            return {"error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return hits / total
    
    async def optimize_query_performance(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Optimize query performance for user
        
        Args:
            user_id: User ID
            
        Returns:
            Optimization results
        """
        try:
            # Analyze query patterns
            # Preload frequently accessed data
            
            # Get topic preferences (most common query)
            result = await self.db.execute(
                select(UserTopicPreference).where(
                    UserTopicPreference.user_id == user_id
                ).order_by(UserTopicPreference.preference_weight.desc()).limit(20)
            )
            top_prefs = result.scalars().all()
            
            # Cache top preferences
            if top_prefs:
                profile = {
                    "top_topics": [
                        {
                            "category": p.topic_category,
                            "subcategory": p.subcategory,
                            "weight": float(p.preference_weight)
                        }
                        for p in top_prefs
                    ]
                }
                await self.cache_user_profile(user_id, profile)
            
            return {
                "success": True,
                "optimizations_applied": ["cached_top_preferences"],
                "cached_items": len(top_prefs)
            }
            
        except Exception as e:
            logger.error("query_optimization_failed",
                        user_id=user_id,
                        error=str(e))
            return {"success": False, "error": str(e)}


def get_performance_optimizer(db: AsyncSession) -> PerformanceOptimizer:
    """Get performance optimizer instance"""
    return PerformanceOptimizer(db)
