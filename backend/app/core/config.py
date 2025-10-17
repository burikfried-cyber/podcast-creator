"""
Application Configuration
Centralized settings management with Pydantic
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Location-Based Podcast Generator"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://podcast_user:podcast_pass@localhost:5432/podcast_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB_CACHE: int = 0
    REDIS_DB_SESSIONS: int = 1
    REDIS_DB_RATE_LIMIT: int = 2
    REDIS_TTL_DEFAULT: int = 1800  # 30 minutes
    
    # Rate Limiting
    RATE_LIMIT_FREE_TIER: int = 100
    RATE_LIMIT_PREMIUM_TIER: int = 1000
    RATE_LIMIT_WINDOW_HOURS: int = 1
    
    # Security
    BCRYPT_COST_FACTOR: int = 12
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # API Keys for Content Generation
    PERPLEXITY_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is sufficiently long"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic"""
        # Handle both asyncpg and aiosqlite
        url = self.DATABASE_URL.replace("+asyncpg", "")
        url = url.replace("+aiosqlite", "")
        return url
    
    @property
    def access_token_expire_seconds(self) -> int:
        """Get access token expiration in seconds"""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    @property
    def refresh_token_expire_seconds(self) -> int:
        """Get refresh token expiration in seconds"""
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    @property
    def rate_limit_window_seconds(self) -> int:
        """Get rate limit window in seconds"""
        return self.RATE_LIMIT_WINDOW_HOURS * 60 * 60


# Global settings instance
settings = Settings()
