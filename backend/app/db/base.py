"""
Database Base Configuration
SQLAlchemy async setup - supports both SQLite (dev) and PostgreSQL (production)
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Create async engine
# Use different settings for SQLite vs PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite configuration with WAL mode for concurrent access (DEV ONLY)
    logger.warning("using_sqlite_database", 
                   message="SQLite is for development only. Use PostgreSQL for production!")
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # 30 second timeout instead of default 5
        },
        poolclass=NullPool,
    )
    
    # Enable WAL mode for better concurrency
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
    
    logger.info("database_engine_created", type="SQLite", mode="WAL")
    
elif settings.DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration (PRODUCTION)
    logger.info("using_postgresql_database", message="Production-ready database!")
    
    import ssl
    
    # Create SSL context for Supabase
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,  # Reduced for better stability
        max_overflow=10,  # Reduced overflow
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "ssl": ssl_context,  # SSL context for Supabase
            "timeout": 60,  # Increased timeout
            "command_timeout": 60,  # Increased command timeout
            "server_settings": {
                "application_name": "podcast_creator",
                "jit": "off"  # Disable JIT for better performance on small queries
            }
        }
    )
    
    logger.info("database_engine_created", 
                type="PostgreSQL", 
                pool_size=10, 
                max_overflow=20)
else:
    raise ValueError(f"Unsupported database URL: {settings.DATABASE_URL}")

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
    from app.models import user, preferences  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
