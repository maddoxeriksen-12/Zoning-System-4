"""
Application configuration settings
"""

from typing import List, Optional
from pydantic import BaseModel, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application Settings
    DEBUG: bool = True
    SECRET_KEY: str = "zoning-project-secret-key-change-in-production"
    CSRF_SECRET_KEY: str = "zoning-csrf-secret-key-change-in-production"

    # Database Configuration (Local PostgreSQL)
    DATABASE_URL: str = "postgresql://zoning_user:zoning_password@postgres:5432/zoning_db"

    # AI Service Configuration (Grok)
    GROK_API_KEY: Optional[str] = None
    GROK_BASE_URL: str = "https://api.x.ai/v1"
    GROK_MODEL: str = "grok-4-fast-reasoning"
    GROK_MAX_TOKENS: int = 8000
    GROK_TEMPERATURE: float = 0.1

    # API Configuration
    API_V1_STR: str = "/api"
    ALLOWED_HOSTS: List[str] = ["*"]

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3002",
        "http://localhost:5001",  # Document uploader
    ]
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_HEADERS: List[str] = ["*"]

    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = [
        ".pdf", ".doc", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".tiff"
    ]

    # Rate Limiting
    GROK_RATE_LIMIT_REQUESTS: int = 5
    GROK_RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    GROK_RATE_LIMIT_BURST: int = 1

    # Redis Configuration
    REDIS_URL: str = "redis://redis:6379"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Processing Configuration
    AI_PROCESSING_TIMEOUT: int = 300  # 5 minutes
    MAX_TEXT_LENGTH: int = 1000000  # 1MB text limit

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()