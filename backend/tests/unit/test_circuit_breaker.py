"""
Unit Tests for Circuit Breaker
Tests for circuit breaker pattern implementation
"""
import pytest

# Mark all tests in this file as unit tests (no external dependencies)
pytestmark = pytest.mark.unit
import asyncio
from app.services.api_clients.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerManager
)


@pytest.fixture
def breaker():
    """Create circuit breaker instance"""
    return CircuitBreaker(
        name="test_breaker",
        failure_threshold=3,
        recovery_timeout=1,  # 1 second for testing
        success_threshold=2
    )


@pytest.mark.asyncio
async def test_circuit_breaker_initial_state(breaker):
    """Test circuit breaker starts in CLOSED state"""
    assert breaker.state == CircuitState.CLOSED
    assert breaker.is_closed is True
    assert breaker.is_open is False


@pytest.mark.asyncio
async def test_circuit_breaker_success(breaker):
    """Test successful calls keep circuit closed"""
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_failures(breaker):
    """Test circuit opens after threshold failures"""
    async def failing_func():
        raise Exception("Test failure")
    
    # Fail 3 times (threshold)
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(failing_func)
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN
    assert breaker.is_open is True


@pytest.mark.asyncio
async def test_circuit_breaker_rejects_when_open(breaker):
    """Test circuit rejects calls when open"""
    async def failing_func():
        raise Exception("Test failure")
    
    # Open the circuit
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(failing_func)
    
    # Next call should be rejected
    with pytest.raises(CircuitBreakerError):
        await breaker.call(failing_func)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_transition(breaker):
    """Test circuit transitions to half-open after timeout"""
    async def failing_func():
        raise Exception("Test failure")
    
    # Open the circuit
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for recovery timeout
    await asyncio.sleep(1.1)
    
    # Next call should transition to half-open
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    
    # Should be in half-open or closed (if success threshold met)
    assert breaker.state in [CircuitState.HALF_OPEN, CircuitState.CLOSED]


@pytest.mark.asyncio
async def test_circuit_breaker_closes_after_successes(breaker):
    """Test circuit closes after success threshold in half-open"""
    async def failing_func():
        raise Exception("Test failure")
    
    # Open the circuit
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(failing_func)
    
    # Wait for recovery
    await asyncio.sleep(1.1)
    
    # Succeed twice (success threshold)
    async def success_func():
        return "success"
    
    await breaker.call(success_func)
    await breaker.call(success_func)
    
    # Should be closed
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_reopens_on_failure_in_half_open(breaker):
    """Test circuit reopens if call fails in half-open state"""
    async def failing_func():
        raise Exception("Test failure")
    
    # Open the circuit
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(failing_func)
    
    # Wait for recovery
    await asyncio.sleep(1.1)
    
    # Fail in half-open state
    with pytest.raises(Exception):
        await breaker.call(failing_func)
    
    # Should be open again
    assert breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_reset(breaker):
    """Test manual circuit breaker reset"""
    async def failing_func():
        raise Exception("Test failure")
    
    # Open the circuit
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Reset
    await breaker.reset()
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker._failure_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_stats(breaker):
    """Test circuit breaker statistics"""
    async def failing_func():
        raise Exception("Test failure")
    
    # Fail once
    with pytest.raises(Exception):
        await breaker.call(failing_func)
    
    stats = breaker.get_stats()
    
    assert stats["name"] == "test_breaker"
    assert stats["state"] == CircuitState.CLOSED.value
    assert stats["failure_count"] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_manager():
    """Test circuit breaker manager"""
    manager = CircuitBreakerManager()
    
    # Get breaker (should create new one)
    breaker1 = await manager.get_breaker("api1")
    
    assert breaker1.name == "api1"
    
    # Get same breaker again
    breaker2 = await manager.get_breaker("api1")
    
    assert breaker1 is breaker2


@pytest.mark.asyncio
async def test_circuit_breaker_manager_reset_all():
    """Test resetting all circuit breakers"""
    manager = CircuitBreakerManager()
    
    breaker1 = await manager.get_breaker("api1")
    breaker2 = await manager.get_breaker("api2")
    
    # Open both circuits
    async def failing_func():
        raise Exception("Test failure")
    
    for _ in range(5):
        try:
            await breaker1.call(failing_func)
        except:
            pass
        try:
            await breaker2.call(failing_func)
        except:
            pass
    
    # Reset all
    await manager.reset_all()
    
    assert breaker1.state == CircuitState.CLOSED
    assert breaker2.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_manager_stats():
    """Test getting stats for all breakers"""
    manager = CircuitBreakerManager()
    
    await manager.get_breaker("api1")
    await manager.get_breaker("api2")
    
    stats = manager.get_all_stats()
    
    assert len(stats) == 2
    assert any(s["name"] == "api1" for s in stats)
    assert any(s["name"] == "api2" for s in stats)
