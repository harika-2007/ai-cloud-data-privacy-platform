"""REST API routes for the compliance dashboard.

Provides endpoints for dashboard statistics, risk trends,
risk distribution, and compliance scores. All endpoints require
authentication.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import TokenPayload
from app.schemas.dashboard import (
    ComplianceScore,
    DashboardResponse,
    DashboardStats,
    RiskDistribution,
    RiskTrend,
)
from app.services.alerting.alert_service import AlertService
from app.services.dashboard.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    """Dependency that provides a DashboardService instance."""
    return DashboardService(db)


# ---------------------------------------------------------------------------
# GET /stats - main dashboard statistics
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Dashboard statistics",
    description="Returns summary metrics for the compliance dashboard.",
)
async def get_dashboard_stats(
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(_get_dashboard_service),
) -> DashboardStats:
    """Get comprehensive dashboard summary statistics.

    Returns total files, scanned files, total findings, risk-level
    breakdowns, compliance score, and active alert count.
    """
    stats = await service.get_dashboard_stats()
    return DashboardStats(
        total_files=stats["total_files"],
        scanned_files=stats["scanned_files"],
        total_findings=stats["total_findings"],
        high_risk_files=stats["high_risk_files"],
        medium_risk_files=stats["medium_risk_files"],
        low_risk_files=stats["low_risk_files"],
        risk_score=stats["risk_score"],
        compliance_score=stats["compliance_score"],
        active_alerts=stats["active_alerts"],
    )


# ---------------------------------------------------------------------------
# GET /trends - risk score trends over time
# ---------------------------------------------------------------------------


@router.get(
    "/trends",
    response_model=list[RiskTrend],
    summary="Risk trends",
    description="Returns daily average risk scores for the chart.",
)
async def get_risk_trends(
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(_get_dashboard_service),
) -> list[RiskTrend]:
    """Get daily average risk scores for the specified look-back period."""
    trends = await service.get_risk_trends(days=days)
    return [RiskTrend(**t) for t in trends]


# ---------------------------------------------------------------------------
# GET /distribution - risk distribution across data types
# ---------------------------------------------------------------------------


@router.get(
    "/distribution",
    response_model=list[RiskDistribution],
    summary="Risk distribution",
    description="Returns findings grouped by data type and severity.",
)
async def get_risk_distribution(
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(_get_dashboard_service),
) -> list[RiskDistribution]:
    """Get risk distribution across all data types and severities."""
    distribution = await service.get_risk_distribution()
    return [
        RiskDistribution(
            data_type=item.get("data_type", "unknown"),
            count=item.get("total_count", 0),
            severity=item.get("max_severity", "LOW"),
        )
        for item in distribution
    ]


# ---------------------------------------------------------------------------
# GET /compliance - compliance score breakdown
# ---------------------------------------------------------------------------


@router.get(
    "/compliance",
    response_model=ComplianceScore,
    summary="Compliance score",
    description="Returns overall and per-category compliance scores.",
)
async def get_compliance_score(
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(_get_dashboard_service),
) -> ComplianceScore:
    """Get the compliance score breakdown.

    Returns overall compliance percentage, per-category scores,
    and the associated risk level.
    """
    score_data = await service.get_compliance_score()
    return ComplianceScore(
        overall_score=score_data["overall_score"],
        category_scores=score_data["category_scores"],
        risk_level=score_data["risk_level"],
    )


# ---------------------------------------------------------------------------
# GET /full - complete dashboard data (aggregated response)
# ---------------------------------------------------------------------------


@router.get(
    "/full",
    response_model=DashboardResponse,
    summary="Full dashboard data",
    description="Returns all dashboard data in a single aggregated response.",
)
async def get_full_dashboard(
    days: int = Query(30, ge=1, le=365, description="Look-back window in days for trends"),
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(_get_dashboard_service),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Get complete dashboard data in one call.

    Aggregates statistics, risk trends, distribution, compliance scores,
    recent alerts, and findings by type into a single response.
    """
    alert_service = AlertService(db)
    stats_data = await service.get_dashboard_stats()
    trends_data = await service.get_risk_trends(days=days)
    distribution_data = await service.get_risk_distribution()
    compliance_data = await service.get_compliance_score()
    findings_data = await service.get_findings_by_type()
    alerts = await alert_service.get_recent_alerts(limit=10)

    return DashboardResponse(
        stats=DashboardStats(
            total_files=stats_data["total_files"],
            scanned_files=stats_data["scanned_files"],
            total_findings=stats_data["total_findings"],
            high_risk_files=stats_data["high_risk_files"],
            medium_risk_files=stats_data["medium_risk_files"],
            low_risk_files=stats_data["low_risk_files"],
            risk_score=stats_data["risk_score"],
            compliance_score=stats_data["compliance_score"],
            active_alerts=stats_data["active_alerts"],
        ),
        risk_trends=[RiskTrend(**t) for t in trends_data],
        risk_distribution=[
            RiskDistribution(
                data_type=item.get("data_type", "unknown"),
                count=item.get("total_count", 0),
                severity=item.get("max_severity", "LOW"),
            )
            for item in distribution_data
        ],
        compliance=ComplianceScore(
            overall_score=compliance_data["overall_score"],
            category_scores=compliance_data["category_scores"],
            risk_level=compliance_data["risk_level"],
        ),
        recent_alerts=[
            {
                "id": a.id,
                "file_id": a.file_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "is_read": a.is_read,
                "created_at": str(a.created_at) if a.created_at else None,
            }
            for a in alerts
        ],
        findings_by_type=findings_data,
    )
