"""
FastAPI Application Entry Point
Main application setup and configuration
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import time
from app.core.config import settings
from app.core.logging import configure_logging, log_request
from app.core.file_logging import setup_file_logging, log_section
from app.core.cache import cache
from app.core.monitoring import PrometheusMiddleware, metrics_endpoint
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.router import api_router
from app.db.base import init_db, close_db
import structlog

# Configure logging
configure_logging()
log_file = setup_file_logging()
logger = structlog.get_logger()

log_section("APPLICATION STARTUP")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting application", version=settings.APP_VERSION)
    
    try:
        # Initialize database
        try:
            await init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.error("Database initialization failed", error=str(e))
            logger.warning("App will start without database connection")
        
        # Connect to Redis
        try:
            await cache.connect()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning("Redis connection failed", error=str(e))
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down application")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
        # Close Redis connections
        await cache.close()
        logger.info("Redis connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Location-Based Podcast Generator",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus monitoring middleware
app.add_middleware(PrometheusMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()
    
    # Get user ID if available
    user_id = getattr(request.state, "user_id", None)
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id
        )
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            error=str(e)
        )
        raise


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Metrics endpoint
app.add_route("/metrics", metrics_endpoint, methods=["GET"])

# Configure static file serving for audio files
AUDIO_DIR = os.getenv("AUDIO_STORAGE_PATH", "/tmp/podcast_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
logger.info("audio_directory_configured", path=AUDIO_DIR)

try:
    app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
    logger.info("audio_static_files_mounted", path="/audio")
except Exception as e:
    logger.warning("audio_static_files_mount_failed", error=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
