"""Pydantic schemas for dashboard module."""

from typing import Any, Optional
from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard summary statistics."""
    total_files: int
    scanned_files: int
    total_findings: int
    high_risk_files: int
    medium_risk_files: int
    low_risk_files: int
    risk_score: float = 0.0
    compliance_score: float
    active_alerts: int


class RiskTrend(BaseModel):
    """Risk trend data point."""
    date: str
    score: float


class RiskDistribution(BaseModel):
    """Risk distribution breakdown."""
    data_type: str
    count: int
    severity: str


class ComplianceScore(BaseModel):
    """Compliance score breakdown."""
    overall_score: float
    category_scores: dict[str, float]
    risk_level: str


class DashboardResponse(BaseModel):
    """Complete dashboard data response."""
    stats: DashboardStats
    risk_trends: list[RiskTrend]
    risk_distribution: list[RiskDistribution]
    compliance: ComplianceScore
    recent_alerts: list[dict[str, Any]]
    findings_by_type: dict[str, int]
