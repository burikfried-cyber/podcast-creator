"""
Integration Test Configuration
Overrides global conftest to avoid Redis dependency
"""
import pytest


@pytest.fixture
def setup_redis():
    """Override global Redis setup - Integration tests don't need Redis"""
    yield None


@pytest.fixture
def cache():
    """Override global cache - Integration tests don't need cache"""
    return None
