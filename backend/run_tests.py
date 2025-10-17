"""
Simple test runner to verify Phase 1 implementation
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("PHASE 1 INFRASTRUCTURE TEST")
print("=" * 70)

# Test 1: Import core modules
print("\n[TEST 1] Importing core modules...")
try:
    from app.core.config import settings
    print(f"✅ Config loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
except Exception as e:
    print(f"❌ Config import failed: {e}")
    sys.exit(1)

try:
    from app.core.security import security
    print("✅ Security module loaded")
except Exception as e:
    print(f"❌ Security import failed: {e}")
    sys.exit(1)

try:
    from app.core.cache import cache
    print("✅ Cache module loaded")
except Exception as e:
    print(f"❌ Cache import failed: {e}")
    sys.exit(1)

# Test 2: Import models
print("\n[TEST 2] Importing database models...")
try:
    from app.models.user import User, UserPreference, UserBehavior, ContentMetadata
    print("✅ All models imported successfully")
except Exception as e:
    print(f"❌ Model import failed: {e}")
    sys.exit(1)

# Test 3: Import schemas
print("\n[TEST 3] Importing Pydantic schemas...")
try:
    from app.models.schemas import (
        UserCreate, UserLogin, Token, UserPreferenceCreate,
        UserPreferenceResponse, HealthCheck
    )
    print("✅ All schemas imported successfully")
except Exception as e:
    print(f"❌ Schema import failed: {e}")
    sys.exit(1)

# Test 4: Test password hashing
print("\n[TEST 4] Testing password hashing...")
try:
    password = "TestPassword123"
    hashed = security.hash_password(password)
    verified = security.verify_password(password, hashed)
    if verified:
        print(f"✅ Password hashing works correctly")
    else:
        print(f"❌ Password verification failed")
        sys.exit(1)
except Exception as e:
    print(f"❌ Password hashing failed: {e}")
    sys.exit(1)

# Test 5: Test JWT tokens
print("\n[TEST 5] Testing JWT token generation...")
try:
    token_data = {"sub": "test-user-id", "email": "test@example.com", "tier": "free"}
    access_token = security.create_access_token(token_data)
    decoded = security.decode_token(access_token)
    if decoded and decoded.get("sub") == "test-user-id":
        print(f"✅ JWT token generation and decoding works")
    else:
        print(f"❌ JWT token decoding failed")
        sys.exit(1)
except Exception as e:
    print(f"❌ JWT token test failed: {e}")
    sys.exit(1)

# Test 6: Test Pydantic validation
print("\n[TEST 6] Testing Pydantic validation...")
try:
    # Valid user creation
    user_data = UserCreate(email="test@example.com", password="ValidPass123")
    print(f"✅ Valid user data accepted")
    
    # Invalid password (should raise error)
    try:
        invalid_user = UserCreate(email="test@example.com", password="weak")
        print(f"❌ Invalid password was accepted (should have been rejected)")
        sys.exit(1)
    except Exception:
        print(f"✅ Invalid password correctly rejected")
        
except Exception as e:
    print(f"❌ Pydantic validation test failed: {e}")
    sys.exit(1)

# Test 7: Test configuration
print("\n[TEST 7] Testing configuration...")
try:
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) >= 32
    assert settings.RATE_LIMIT_FREE_TIER == 100
    assert settings.RATE_LIMIT_PREMIUM_TIER == 1000
    print(f"✅ Configuration validated")
    print(f"   - Free tier limit: {settings.RATE_LIMIT_FREE_TIER} req/hour")
    print(f"   - Premium tier limit: {settings.RATE_LIMIT_PREMIUM_TIER} req/hour")
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    sys.exit(1)

# Test 8: Import API endpoints
print("\n[TEST 8] Importing API endpoints...")
try:
    from app.api.v1.endpoints import auth, health, preferences
    print("✅ All API endpoints imported successfully")
except Exception as e:
    print(f"❌ API endpoint import failed: {e}")
    sys.exit(1)

# Test 9: Import main application
print("\n[TEST 9] Importing FastAPI application...")
try:
    from app.main import app
    print(f"✅ FastAPI application loaded")
    print(f"   - Title: {app.title}")
    print(f"   - Version: {app.version}")
except Exception as e:
    print(f"❌ FastAPI application import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - Phase 1 Infrastructure is Ready!")
print("=" * 70)
print("\nNext steps:")
print("1. Start PostgreSQL and Redis (docker-compose up -d postgres redis)")
print("2. Run database migrations (alembic upgrade head)")
print("3. Start the application (uvicorn app.main:app --reload)")
print("4. Run full test suite (pytest)")
print("=" * 70)
