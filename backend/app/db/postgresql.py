"""
PostgreSQL Database Configuration
Production-ready async setup with connection pooling
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Create async engine for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections when pool is full
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "server_settings": {
            "application_name": "podcast_creator",
            "jit": "off"  # Disable JIT for better performance on small queries
        }
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for getting async database sessions
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create all tables"""
    # Import all models to ensure they're registered with SQLAlchemy
    from app.models import user, preferences, podcast  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("database_initialized", database="PostgreSQL")


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    logger.info("database_connections_closed")


async def check_db_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        bool: True if connection is successful
    """
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        logger.info("database_connection_check", status="success")
        return True
    except Exception as e:
        logger.error("database_connection_check", status="failed", error=str(e))
        return False
