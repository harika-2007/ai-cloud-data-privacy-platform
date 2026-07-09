"""Application configuration management.

Uses pydantic-settings to load from environment variables with sensible defaults.
All configuration is centralized here for easy management.
"""

import os
import re
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Privacy Compliance Platform"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "AI-Powered Cloud Data Privacy Compliance and Security Monitoring Platform"
    )
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(
        default="development",
        pattern="^(development|staging|production)$",
    )

    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production-but-really-change-it!",
        min_length=32,
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # CORS — comma-separated list of allowed origins
    # For development with ngrok, set CORS_ORIGINS=* (allow all) or
    # include your ngrok URL explicitly.
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:5173,"
        "http://localhost:5174,http://127.0.0.1:3000,"
        "http://127.0.0.1:5173,http://127.0.0.1:8000"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list.

        Supports '*' for development (allow all origins). When '*' is set,
        the middleware switches to allow all origins with credentials support,
        which requires explicit origin matching via regex. We handle this
        by returning ['*'] and letting the middleware do the right thing.
        """
        origins = []
        for origin in self.CORS_ORIGINS.split(","):
            origin = origin.strip()
            if origin:
                origins.append(origin)
        return origins

    @property
    def use_cors_wildcard(self) -> bool:
        """Check if CORS should allow all origins (development only)."""
        return "*" in self.cors_origins_list and self.ENVIRONMENT == "development"

    # Frontend URL (used for Google OAuth redirect back to the frontend)
    FRONTEND_URL: str = "http://localhost:3000"

    # Explicit ngrok URL override — set this when running behind ngrok
    # so the backend can construct correct absolute URLs (redirect URIs).
    # Example: NGROK_URL=https://your-subdomain.ngrok-free.dev
    NGROK_URL: str = ""

    # Public backend URL — used for Google OAuth redirect_uri construction.
    # When empty, derived dynamically from the incoming request.
    # Set this explicitly in production deployments.
    PUBLIC_URL: str = ""

    # Secure cookies — auto-enabled in production, override for ngrok HTTPS
    SECURE_COOKIES: bool = Field(
        default=False,
        description="Set Secure flag on cookies. Auto-enabled in production, "
        "manually set True for ngrok HTTPS.",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/privacy_platform",
        validation_alias="DATABASE_URL",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/privacy_platform",
        validation_alias="DATABASE_SYNC_URL",
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_async_url(cls, v: str) -> str:
        """Auto-convert sync postgresql:// to async postgresql+asyncpg://.

        Render provides DATABASE_URL in sync format (postgresql://...).
        This validator auto-adds the +asyncpg driver so the async engine works.
        """
        if v and isinstance(v, str) and v.startswith("postgresql://"):
            if "+asyncpg" not in v:
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("DATABASE_SYNC_URL", mode="before")
    @classmethod
    def ensure_sync_url(cls, v: str) -> str:
        """Strip +asyncpg from sync database URLs if present."""
        if v and isinstance(v, str):
            v = v.replace("+asyncpg", "", 1)
        return v

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

    # Google OAuth redirect URI.
    # When empty, the backend generates it dynamically from the incoming
    # request (Host header + X-Forwarded-Proto). Set this explicitly if
    # you need a fixed URI for production deployments.
    GOOGLE_REDIRECT_URI: str = ""

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
    LOG_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Ensure upload and report directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_OUTPUT_DIR, exist_ok=True)
