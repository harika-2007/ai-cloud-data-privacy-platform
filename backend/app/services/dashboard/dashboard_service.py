"""Dashboard service for aggregating compliance metrics and analytics.

Provides business logic for the compliance dashboard, aggregating data
across all repositories to produce summary statistics, risk trends,
distribution breakdowns, and compliance scores.
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.file import File as FileModel
from app.models.scan import RiskAssessment, ScanResult
from app.repositories.alert_repository import AlertRepository
from app.repositories.file_repository import FileRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.repositories.scan_repository import ScanResultRepository

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for aggregating compliance dashboard metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_repo = FileRepository(db)
        self.scan_repo = ScanResultRepository(db)
        self.risk_repo = RiskAssessmentRepository(db)
        self.alert_repo = AlertRepository(db)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get comprehensive dashboard summary statistics.

        Returns:
            A dictionary with:
                - total_files: number of uploaded files.
                - scanned_files: number of files with completed scans.
                - total_findings: sum of all PII occurrences.
                - high_risk_files: count of files at HIGH risk level.
                - medium_risk_files: count at MEDIUM risk level.
                - low_risk_files: count at LOW risk level.
                - compliance_score: overall compliance percentage.
                - active_alerts: total unread alerts.
        """
        # Total files
        total_result = await self.db.execute(
            select(func.count()).select_from(FileModel)
        )
        total_files = total_result.scalar() or 0

        # Scanned files
        scanned_result = await self.db.execute(
            select(func.count())
            .select_from(FileModel)
            .where(FileModel.scan_status == "completed")
        )
        scanned_files = scanned_result.scalar() or 0

        # Total findings across all files
        findings_result = await self.db.execute(
            select(func.coalesce(func.sum(ScanResult.count), 0))
        )
        total_findings = findings_result.scalar() or 0

        # Risk level counts (using the latest assessment per file)
        risk_summary = await self.risk_repo.get_all_summary()
        high_risk = risk_summary.get("high_count", 0)
        medium_risk = risk_summary.get("medium_count", 0)
        low_risk = risk_summary.get("low_count", 0)

        # Compliance score: 100 minus average risk score, floored at 0
        avg_score = risk_summary.get("avg_score", 0)
        capped_score = min(avg_score, 100.0)
        compliance_score = max(0.0, 100.0 - capped_score)

        # Active (unread) alerts across all users
        unread_result = await self.db.execute(
            select(func.count())
            .select_from(Alert)
            .where(Alert.is_read.is_(False))
        )
        active_alerts = unread_result.scalar() or 0

        return {
            "total_files": total_files,
            "scanned_files": scanned_files,
            "total_findings": total_findings,
            "high_risk_files": high_risk,
            "medium_risk_files": medium_risk,
            "low_risk_files": low_risk,
            "risk_score": round(min(avg_score, 100.0), 1),
            "compliance_score": round(compliance_score, 1),
            "active_alerts": active_alerts,
        }

    async def get_risk_trends(self, days: int = 30) -> list[dict[str, Any]]:
        """Get daily average risk scores for the dashboard chart.

        Args:
            days: Number of days to look back (default 30).

        Returns:
            A list of dictionaries with ``date`` and ``score`` keys,
            ordered chronologically.
        """
        return await self.risk_repo.get_risk_trends(days=days)

    async def get_risk_distribution(self) -> list[dict[str, Any]]:
        """Get risk distribution across data types and severities.

        Returns:
            A list of dicts with data_type, total_count, file_count, max_severity.
        """
        return await self.scan_repo.get_all_findings_summary()

    async def get_compliance_score(self) -> dict[str, Any]:
        """Calculate overall and per-category compliance scores.

        Score is computed as:
            ``max(0, 100 - avg_risk_score)`` for the overall score.
            Category penalties scale with finding count and severity.

        Returns:
            A dictionary with overall_score, category_scores, and risk_level.
        """
        risk_summary = await self.risk_repo.get_all_summary()
        findings_summary = await self.scan_repo.get_all_findings_summary()

        avg_score = risk_summary.get("avg_score", 0)
        capped_avg = min(avg_score, 100.0)
        overall_compliance = max(0.0, 100.0 - capped_avg)

        # Per-category scores based on severity penalties
        category_scores: dict[str, float] = {}
        for item in findings_summary:
            data_type = item.get("data_type", "unknown")
            count = item.get("total_count", 0)
            severity = item.get("max_severity", "LOW")

            if severity == "CRITICAL":
                penalty = min(count * 5, 50)
            elif severity == "HIGH":
                penalty = min(count * 3, 30)
            elif severity == "MEDIUM":
                penalty = min(count * 2, 20)
            else:
                penalty = min(count * 1, 10)

            category_scores[data_type] = round(max(0.0, 100.0 - penalty), 1)

        # Overall risk level
        if capped_avg < 31:
            risk_level = "LOW"
        elif capped_avg < 71:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "overall_score": round(overall_compliance, 1),
            "category_scores": category_scores,
            "risk_level": risk_level,
        }

    async def get_findings_by_type(self) -> dict[str, int]:
        """Get total PII occurrences grouped by data type.

        Returns:
            A dictionary mapping data_type names to total counts.
        """
        distribution = await self.scan_repo.get_all_findings_summary()
        return {
            item.get("data_type", "unknown"): item.get("total_count", 0)
            for item in distribution
        }
