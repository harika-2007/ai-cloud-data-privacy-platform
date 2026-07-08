"""Application configuration management.

Uses pydantic-settings to load from environment variables with sensible defaults.
All configuration is centralized here for easy management.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Privacy Compliance Platform"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Cloud Data Privacy Compliance and Security Monitoring Platform"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production-but-really-change-it!", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Frontend URL (used for Google OAuth redirect back to the frontend)
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/privacy_platform",
        validation_alias="DATABASE_URL"
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/privacy_platform",
        validation_alias="DATABASE_SYNC_URL"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Google Cloud
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GCS_BUCKET_NAME: str = "privacy-platform-uploads"
    GCS_LOCATION: str = "us-central1"
    DLP_ENABLED: bool = False
    PUBSUB_ENABLED: bool = False
    PUBSUB_TOPIC_SCANS: str = "scan-events"
    PUBSUB_TOPIC_ALERTS: str = "alert-events"
    PUBSUB_TOPIC_REPORTS: str = "report-events"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".pdf", ".txt"]
    UPLOAD_DIR: str = "uploads"

    # Google OAuth 2.0
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # AI / Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 120
    AI_ENABLED: bool = True

    # Alerting
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@privacy-platform.com"
    ALERT_EMAIL_ENABLED: bool = False
    HIGH_RISK_THRESHOLD: float = 71.0
    EXCESSIVE_FINDINGS_THRESHOLD: int = 100

    # Report
    REPORT_OUTPUT_DIR: str = "reports"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Ensure upload and report directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_OUTPUT_DIR, exist_ok=True)
