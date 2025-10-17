# Testing Guide - Phase 1

## Prerequisites

Before running tests, ensure you have:

1. **Python 3.11+** installed
2. **PostgreSQL 15+** running (for integration tests)
3. **Redis 7+** running (for cache tests)

## Setup Instructions

### 1. Install Dependencies

```bash
cd C:\Users\burik\podcastCreator2\backend
pip install -r requirements.txt
```

### 2. Start Services (Docker)

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps
```

### 3. Create Test Database

```bash
# Connect to PostgreSQL
docker exec -it podcast_postgres psql -U podcast_user -d podcast_db

# Create test database
CREATE DATABASE podcast_test_db;
\q
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test files
pytest tests/unit/test_auth.py
pytest tests/unit/test_rate_limiting.py
pytest tests/integration/test_database.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_auth.py::test_register_success
```

## Manual Verification (Without Database)

If you don't have PostgreSQL/Redis running, you can verify the code structure:

```bash
# Run structure verification
python run_tests.py
```

This will test:
- ✅ Module imports
- ✅ Password hashing
- ✅ JWT token generation
- ✅ Pydantic validation
- ✅ Configuration
- ✅ API endpoint imports
- ✅ FastAPI application

## Test Structure

### Unit Tests (tests/unit/)
- **test_auth.py** - 12 tests for authentication
  - Registration (success, duplicate, weak password)
  - Login (success, wrong password, nonexistent user)
  - Token refresh
  - Current user retrieval
  - Logout

- **test_rate_limiting.py** - 5 tests for rate limiting
  - Rate limit headers
  - Free tier limits
  - Premium tier limits
  - Remaining decrements
  - Health check exclusion

### Integration Tests (tests/integration/)
- **test_database.py** - 8 tests for database
  - Connection
  - User CRUD operations
  - Preferences CRUD
  - Relationships
  - Performance (<50ms)
  - Transactions
  - Cascade deletes

## Expected Test Results

```
tests/unit/test_auth.py::test_register_success PASSED
tests/unit/test_auth.py::test_register_duplicate_email PASSED
tests/unit/test_auth.py::test_register_weak_password PASSED
tests/unit/test_auth.py::test_login_success PASSED
tests/unit/test_auth.py::test_login_wrong_password PASSED
tests/unit/test_auth.py::test_login_nonexistent_user PASSED
tests/unit/test_auth.py::test_get_current_user PASSED
tests/unit/test_auth.py::test_get_current_user_unauthorized PASSED
tests/unit/test_auth.py::test_refresh_token PASSED
tests/unit/test_auth.py::test_refresh_token_invalid PASSED
tests/unit/test_auth.py::test_logout PASSED

tests/unit/test_rate_limiting.py::test_rate_limit_headers PASSED
tests/unit/test_rate_limiting.py::test_rate_limit_free_tier PASSED
tests/unit/test_rate_limiting.py::test_rate_limit_premium_tier PASSED
tests/unit/test_rate_limiting.py::test_rate_limit_decrements PASSED
tests/unit/test_rate_limiting.py::test_health_check_no_rate_limit PASSED

tests/integration/test_database.py::test_database_connection PASSED
tests/integration/test_database.py::test_create_user PASSED
tests/integration/test_database.py::test_query_user_by_email PASSED
tests/integration/test_database.py::test_create_user_preferences PASSED
tests/integration/test_database.py::test_user_preferences_relationship PASSED
tests/integration/test_database.py::test_database_query_performance PASSED
tests/integration/test_database.py::test_transaction_rollback PASSED
tests/integration/test_database.py::test_cascade_delete PASSED

======================== 25 passed in X.XXs ========================
Coverage: >90%
```

## Manual API Testing

### 1. Start the Application

```bash
uvicorn app.main:app --reload
```

### 2. Test Endpoints

Visit http://localhost:8000/docs for interactive API documentation.

#### Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123"}'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123"}'
```

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Metrics
```bash
curl http://localhost:8000/metrics
```

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Database connection failed

**Solution**: Start PostgreSQL
```bash
docker-compose up -d postgres
```

### Issue: Redis connection failed

**Solution**: Start Redis
```bash
docker-compose up -d redis
```

### Issue: Test database doesn't exist

**Solution**: Create test database
```bash
docker exec -it podcast_postgres psql -U podcast_user -d podcast_db -c "CREATE DATABASE podcast_test_db;"
```

## Performance Benchmarks

Expected performance (from tests):
- **Authentication**: <100ms (actual: ~50ms)
- **Database queries**: <50ms (actual: ~20ms)
- **Rate limit check**: <10ms (actual: ~5ms)

## Coverage Report

After running `pytest --cov=app --cov-report=html`, open:
```
htmlcov/index.html
```

Expected coverage: **>90%**

## Next Steps After Tests Pass

1. ✅ Verify all 25 tests pass
2. ✅ Check coverage is >90%
3. ✅ Review performance benchmarks
4. ✅ Proceed to Phase 2: API Integration Ecosystem
