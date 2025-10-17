"""
Authentication Endpoints
User registration, login, token refresh
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.user import User
from app.models.schemas import (
    UserCreate,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse
)
from app.core.security import security
from app.middleware.auth import get_current_active_user
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user data
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = security.hash_password(user_data.password)
    
    # Create user
    new_user = User(
        email=user_data.email,
        password_hash=password_hash,
        tier="free",
        is_active=True,
        is_verified=False
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info("User registered", user_id=str(new_user.id), email=new_user.email)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    User login with email and password
    
    Args:
        credentials: Login credentials
        db: Database session
        
    Returns:
        JWT token pair
        
    Raises:
        HTTPException: If credentials invalid
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not security.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create token pair
    tokens = security.create_token_pair(
        user_id=str(user.id),
        email=user.email,
        tier=user.tier
    )
    
    logger.info("User logged in", user_id=str(user.id), email=user.email)
    
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh
) -> Token:
    """
    Refresh access token using refresh token
    
    Args:
        token_data: Refresh token
        
    Returns:
        New JWT token pair
        
    Raises:
        HTTPException: If refresh token invalid
    """
    # Refresh tokens
    new_tokens = security.refresh_access_token(token_data.refresh_token)
    
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    logger.info("Token refreshed")
    
    return new_tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current user information
    
    Args:
        current_user: Authenticated user
        
    Returns:
        User data
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Logout user (client should discard tokens)
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    logger.info("User logged out", user_id=str(current_user.id))
    
    return {"message": "Successfully logged out"}
