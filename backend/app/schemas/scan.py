"""Pydantic schemas for scan results module."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class ScanResultResponse(BaseModel):
    """Individual scan finding response."""
    id: str
    file_id: str
    data_type: str
    count: int
    severity: str
    sample_values: Optional[list[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskAssessmentResponse(BaseModel):
    """Risk assessment result response."""
    id: str
    file_id: str
    overall_score: float
    risk_level: str
    breakdown: Optional[dict[str, Any]] = None
    explanation: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanStartResponse(BaseModel):
    """Response when a scan is initiated."""
    file_id: str
    status: str
    message: str
