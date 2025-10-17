"""
Pytest Configuration and Fixtures
Shared test setup and utilities
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Try to import Phase 1 components, but don't fail if not set up
try:
    from app.main import app
    from app.db.base import Base, get_db
    from app.core.config import settings
    from app.core.cache import cache
    from app.models.user import User
    from app.core.security import security
    PHASE1_AVAILABLE = True
except ImportError:
    app = None
    Base = None
    get_db = None
    settings = None
    cache = None
    User = None
    security = None
    PHASE1_AVAILABLE = False

# Test database URL (only if Phase 1 is available)
if PHASE1_AVAILABLE:
    TEST_DATABASE_URL = "postgresql+asyncpg://podcast_user:podcast_pass@localhost:5432/podcast_test_db"
    
    # Create test engine
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create test session factory
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
else:
    test_engine = None
    TestSessionLocal = None


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session
    
    Yields:
        Test database session
    """
    if not PHASE1_AVAILABLE:
        pytest.skip("Phase 1 not available")
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client
    
    Args:
        db_session: Test database session
        
    Yields:
        Test HTTP client
    """
    # Override database dependency
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """
    Create test user
    
    Args:
        db_session: Test database session
        
    Returns:
        Test user
    """
    user = User(
        email="test@example.com",
        password_hash=security.hash_password("TestPassword123"),
        tier="free",
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
async def premium_user(db_session: AsyncSession) -> User:
    """
    Create premium test user
    
    Args:
        db_session: Test database session
        
    Returns:
        Premium test user
    """
    user = User(
        email="premium@example.com",
        password_hash=security.hash_password("PremiumPass123"),
        tier="premium",
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """
    Create authentication headers for test user
    
    Args:
        test_user: Test user
        
    Returns:
        Headers with JWT token
    """
    tokens = security.create_token_pair(
        user_id=str(test_user.id),
        email=test_user.email,
        tier=test_user.tier
    )
    
    return {
        "Authorization": f"Bearer {tokens['access_token']}"
    }


@pytest.fixture(scope="function")
def premium_auth_headers(premium_user: User) -> dict:
    """
    Create authentication headers for premium user
    
    Args:
        premium_user: Premium test user
        
    Returns:
        Headers with JWT token
    """
    tokens = security.create_token_pair(
        user_id=str(premium_user.id),
        email=premium_user.email,
        tier=premium_user.tier
    )
    
    return {
        "Authorization": f"Bearer {tokens['access_token']}"
    }


@pytest.fixture(scope="session", autouse=True)
async def setup_redis():
    """Setup Redis for tests"""
    if not PHASE1_AVAILABLE or cache is None:
        yield
        return
    
    await cache.connect()
    yield
    await cache.close()
