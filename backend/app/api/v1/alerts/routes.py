"""REST API routes for alert management.

Provides endpoints to list alerts, retrieve statistics, and mark
alerts as read. All endpoints require authentication.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.alert import AlertListResponse, AlertResponse, AlertStatsResponse
from app.schemas.auth import TokenPayload
from app.schemas.common import MessageResponse
from app.services.alerting.alert_service import AlertService
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _get_alert_service(db: AsyncSession = Depends(get_db)) -> AlertService:
    """Dependency that provides an AlertService instance."""
    return AlertService(db)


# ---------------------------------------------------------------------------
# GET / - list alerts for the current user
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List alerts",
    description="Returns paginated alerts for the authenticated user.",
)
async def list_alerts(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(_get_alert_service),
) -> AlertListResponse:
    """Get a paginated list of alerts for the authenticated user.

    Results are ordered newest-first. The response includes a total
    count and the number of unread alerts.
    """
    result = await service.get_alerts(
        user_id=current_user.sub,
        page=page,
        page_size=page_size,
    )
    return AlertListResponse(
        total=result["total"],
        unread_count=result["unread_count"],
        alerts=[AlertResponse.model_validate(a) for a in result["alerts"]],
    )


# ---------------------------------------------------------------------------
# GET /stats - alert statistics
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=AlertStatsResponse,
    summary="Alert statistics",
    description="Returns aggregated alert statistics across all users.",
)
async def get_alert_stats(
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(_get_alert_service),
) -> AlertStatsResponse:
    """Get aggregate alert statistics.

    Returns total and unread counts, severity breakdowns, and
    per-type alert counts.
    """
    stats = await service.get_alert_stats()
    return AlertStatsResponse(
        total_alerts=stats.get("total_alerts", 0),
        unread_alerts=stats.get("unread_alerts", 0),
        critical_alerts=stats.get("critical_alerts", 0),
        high_alerts=stats.get("high_alerts", 0),
        medium_alerts=stats.get("medium_alerts", 0),
        low_alerts=stats.get("low_alerts", 0),
        alerts_by_type=stats.get("alerts_by_type", {}),
    )


# ---------------------------------------------------------------------------
# PUT /{id}/read - mark a single alert as read
# ---------------------------------------------------------------------------


@router.put(
    "/{id}/read",
    response_model=AlertResponse,
    summary="Mark alert as read",
    description="Marks a single alert as read by its ID.",
)
async def mark_alert_read(
    id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(_get_alert_service),
) -> AlertResponse:
    """Mark a specific alert as read by its ID.

    Args:
        id: The UUID of the alert to mark as read.

    Returns:
        The updated Alert record.

    Raises:
        NotFoundException: If the alert ID does not exist.
    """
    alert = await service.mark_as_read(id)
    if not alert:
        raise NotFoundException("Alert", id)
    return AlertResponse.model_validate(alert)


# ---------------------------------------------------------------------------
# PUT /read-all - mark all alerts as read for the current user
# ---------------------------------------------------------------------------


@router.put(
    "/read-all",
    response_model=MessageResponse,
    summary="Mark all alerts as read",
    description="Marks all unread alerts for the authenticated user as read.",
)
async def mark_all_alerts_read(
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(_get_alert_service),
) -> MessageResponse:
    """Mark every unread alert belonging to the current user as read.

    Returns a message confirming how many alerts were updated.
    """
    updated = await service.mark_all_as_read(current_user.sub)
    return MessageResponse(
        message=f"{updated} alert(s) marked as read",
    )
