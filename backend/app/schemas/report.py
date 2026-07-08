"""Pydantic schemas for reporting module."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class ReportResponse(BaseModel):
    """Report response schema."""
    id: str
    user_id: str
    file_id: Optional[str] = None
    title: str
    report_type: str
    ai_summary: Optional[str] = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""
    file_id: Optional[str] = None
    title: str
    report_type: str = "compliance"
    include_ai_summary: bool = True


class ReportListResponse(BaseModel):
    """Paginated report list response."""
    total: int
    reports: list[ReportResponse]
