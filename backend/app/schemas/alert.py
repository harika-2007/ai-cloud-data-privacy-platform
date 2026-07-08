"""Pydantic schemas for alerting module."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertResponse(BaseModel):
    """Alert response schema."""
    id: str
    file_id: Optional[str] = None
    user_id: Optional[str] = None
    alert_type: str
    severity: str
    message: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    """Paginated alert list response."""
    total: int
    unread_count: int
    alerts: list[AlertResponse]


class AlertStatsResponse(BaseModel):
    """Alert statistics response."""
    total_alerts: int
    unread_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    alerts_by_type: dict[str, int]
