"""
Integration Tests for Database Operations
Tests for database queries and performance
"""
import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserPreference


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    """Test database connection"""
    result = await db_session.execute(select(1))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a user"""
    from app.core.security import security
    
    user = User(
        email="dbtest@example.com",
        password_hash=security.hash_password("TestPass123"),
        tier="free"
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "dbtest@example.com"
    assert user.tier == "free"


@pytest.mark.asyncio
async def test_query_user_by_email(db_session: AsyncSession, test_user: User):
    """Test querying user by email"""
    result = await db_session.execute(
        select(User).where(User.email == test_user.email)
    )
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_create_user_preferences(db_session: AsyncSession, test_user: User):
    """Test creating user preferences"""
    preferences = UserPreference(
        user_id=test_user.id,
        topic_preferences={"history": {"ancient": 0.8}},
        depth_preference=4,
        surprise_tolerance=3
    )
    
    db_session.add(preferences)
    await db_session.commit()
    await db_session.refresh(preferences)
    
    assert preferences.id is not None
    assert preferences.user_id == test_user.id
    assert preferences.depth_preference == 4


@pytest.mark.asyncio
async def test_user_preferences_relationship(db_session: AsyncSession, test_user: User):
    """Test user-preferences relationship"""
    preferences = UserPreference(
        user_id=test_user.id,
        topic_preferences={},
        depth_preference=3,
        surprise_tolerance=3
    )
    
    db_session.add(preferences)
    await db_session.commit()
    
    # Query user with preferences
    result = await db_session.execute(
        select(User).where(User.id == test_user.id)
    )
    user = result.scalar_one()
    
    # Access relationship (note: need to explicitly load in async)
    await db_session.refresh(user, ["preferences"])
    
    assert len(user.preferences) > 0
    assert user.preferences[0].user_id == user.id


@pytest.mark.asyncio
async def test_database_query_performance(db_session: AsyncSession, test_user: User):
    """Test that database queries execute in <50ms"""
    start_time = time.time()
    
    result = await db_session.execute(
        select(User).where(User.id == test_user.id)
    )
    user = result.scalar_one()
    
    duration_ms = (time.time() - start_time) * 1000
    
    assert user is not None
    assert duration_ms < 50, f"Query took {duration_ms}ms, expected <50ms"


@pytest.mark.asyncio
async def test_transaction_rollback(db_session: AsyncSession):
    """Test transaction rollback on error"""
    from app.core.security import security
    
    user = User(
        email="rollback@example.com",
        password_hash=security.hash_password("TestPass123"),
        tier="free"
    )
    
    db_session.add(user)
    await db_session.flush()
    
    # Rollback
    await db_session.rollback()
    
    # User should not exist
    result = await db_session.execute(
        select(User).where(User.email == "rollback@example.com")
    )
    found_user = result.scalar_one_or_none()
    
    assert found_user is None


@pytest.mark.asyncio
async def test_cascade_delete(db_session: AsyncSession, test_user: User):
    """Test cascade delete of user preferences"""
    # Create preferences
    preferences = UserPreference(
        user_id=test_user.id,
        topic_preferences={},
        depth_preference=3,
        surprise_tolerance=3
    )
    
    db_session.add(preferences)
    await db_session.commit()
    
    pref_id = preferences.id
    
    # Delete user
    await db_session.delete(test_user)
    await db_session.commit()
    
    # Preferences should be deleted
    result = await db_session.execute(
        select(UserPreference).where(UserPreference.id == pref_id)
    )
    found_pref = result.scalar_one_or_none()
    
    assert found_pref is None
