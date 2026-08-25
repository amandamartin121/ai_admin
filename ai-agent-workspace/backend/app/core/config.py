"""
Configuration settings for the application.
Loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./dev.db"

    # JWT Settings
    jwt_secret: str = "dev-secret-key-change-in-production-min-32-chars"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o-mini"

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "tauri://localhost", "http://localhost:1420"]

    # File Storage
    file_storage_path: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB

    # Environment
    environment: str = "development"

    # Super Admin (for seed)
    super_admin_email: str = "admin@example.com"
    super_admin_password: str = "ChangeMe123!"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# Global settings instance
settings = Settings()
