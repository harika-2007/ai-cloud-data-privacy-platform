"""Health check API routes.

Provides an endpoint for monitoring the application's operational status,
including database connectivity and external service availability.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Application health check",
    description="Returns the current health status of the application and its dependencies.",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Perform a comprehensive health check of the application.

    Verifies database connectivity and reports the status of all
    configured external services (AI/Ollama, DLP, GCS).

    Args:
        db: The async database session used to verify database connectivity.

    Returns:
        A dictionary containing the overall health status, application version,
        and individual status for each dependency.
    """
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

    # Database health check
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        health_status["status"] = "degraded"

    health_status["database"] = db_status

    # External service status indicators
    health_status["ai"] = _check_service_status(
        "AI",
        settings.AI_ENABLED,
        {"model": settings.OLLAMA_MODEL, "base_url": settings.OLLAMA_BASE_URL},
    )

    health_status["dlp"] = _check_service_status(
        "DLP",
        settings.DLP_ENABLED,
        {"project": settings.GOOGLE_CLOUD_PROJECT},
    )

    health_status["gcs"] = _check_service_status(
        "GCS",
        bool(settings.GCS_BUCKET_NAME),
        {"bucket": settings.GCS_BUCKET_NAME},
    )

    # Overall status
    if health_status["database"] != "healthy":
        health_status["status"] = "degraded"

    logger.info("Health check result: %s", health_status["status"])

    return health_status


def _check_service_status(
    service_name: str,
    enabled: bool,
    details: dict,
) -> dict:
    """Build a status dictionary for an external service.

    Args:
        service_name: The human-readable name of the service.
        enabled: Whether the service is configured/enabled.
        details: Additional details about the service configuration.

    Returns:
        A dictionary with the service status and configuration details.
    """
    return {
        "status": "configured" if enabled else "disabled",
        "enabled": enabled,
        **details,
    }
