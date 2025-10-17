"""
Health Check Endpoint
System health monitoring
"""
from datetime import datetime
from fastapi import APIRouter
from sqlalchemy import text
from app.db.base import engine
from app.core.cache import cache
from app.core.config import settings
from app.models.schemas import HealthCheck
import structlog

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """
    Check health of all system components
    
    Returns:
        Health status of database, Redis, and application
    """
    # Check database
    db_status = "healthy"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check Redis
    redis_health = await cache.health_check()
    redis_status = "healthy" if all(redis_health.values()) else "unhealthy"
    
    return HealthCheck(
        status="healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.utcnow()
    )
