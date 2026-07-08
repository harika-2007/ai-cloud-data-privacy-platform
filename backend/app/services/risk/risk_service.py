"""Risk scoring service for calculating privacy risk from scan findings.

Computes weighted risk scores based on detected PII types, categorizes
into risk levels (LOW / MEDIUM / HIGH), and persists assessments.
"""

import logging
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import RiskAssessment, ScanResult
from app.repositories.base import BaseRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Risk weights for each PII data type
# ---------------------------------------------------------------------------

RISK_WEIGHTS: dict[str, float] = {
    "CreditCard": 35.0,
    "Aadhaar": 25.0,
    "PAN": 20.0,
    "Passport": 30.0,
    "Phone": 5.0,
    "Email": 5.0,
    "Address": 10.0,
    "DOB": 5.0,
}

# Default weight for unknown data types
DEFAULT_WEIGHT: float = 20.0

# Risk level thresholds
RISK_LEVEL_LOW_MAX: float = 30.0
RISK_LEVEL_MEDIUM_MAX: float = 70.0


def _calculate_risk_level(score: float) -> str:
    """Map a numerical risk score to a risk level string.

    Args:
        score: The calculated risk score (non-negative float).

    Returns:
        "LOW" for scores 0-30, "MEDIUM" for 31-70, "HIGH" for 71+.
    """
    if score <= RISK_LEVEL_LOW_MAX:
        return "LOW"
    elif score <= RISK_LEVEL_MEDIUM_MAX:
        return "MEDIUM"
    else:
        return "HIGH"


class RiskService:
    """Service for calculating and managing privacy risk assessments."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = RiskAssessmentRepository(db)

    def _calculate_risk(
        self,
        scan_results: list[ScanResult],
    ) -> tuple[float, str, dict[str, Any], str]:
        """Compute risk score, level, breakdown, and explanation from scan results.

        Args:
            scan_results: List of ScanResult records (findings) for a file.

        Returns:
            Tuple of (overall_score, risk_level, breakdown_dict, explanation_text).
        """
        breakdown: dict[str, Any] = {}
        total_score = 0.0

        for scan in scan_results:
            if scan.data_type is None:
                continue
            weight = RISK_WEIGHTS.get(scan.data_type, DEFAULT_WEIGHT)
            contribution = scan.count * weight
            total_score += contribution
            breakdown[scan.data_type] = {
                "count": scan.count,
                "weight": weight,
                "contribution": contribution,
                "severity": scan.severity,
            }

        # Cap score at 100 for a percentage-based interpretation
        total_score = min(total_score, 100.0)

        risk_level = _calculate_risk_level(total_score)

        # Build human-readable explanation
        parts: list[str] = []
        for data_type, info in sorted(
            breakdown.items(), key=lambda x: x[1]["contribution"], reverse=True
        ):
            parts.append(
                f"{data_type}: {info['count']} occurrence(s) "
                f"at weight {info['weight']} = {info['contribution']:.0f} points"
            )
        explanation = (
            f"Risk Score: {total_score:.1f} ({risk_level}).\n"
            + "\n".join(parts)
        )

        return total_score, risk_level, breakdown, explanation

    async def assess_file(self, file_id: str) -> RiskAssessment:
        """Run risk assessment for a file based on its scan results.

        Retrieves existing ScanResult records for the file, calculates
        the risk score, and persists a RiskAssessment record.

        Args:
            file_id: UUID of the file to assess.

        Returns:
            The newly created RiskAssessment record.
        """
        # Fetch scan results for this file
        scan_repo = BaseRepository(ScanResult, self.db)
        query = select(ScanResult).where(ScanResult.file_id == file_id)
        result = await self.db.execute(query)
        scan_results = list(result.scalars().all())

        if not scan_results:
            raise NotFoundException("ScanResult", f"file_id={file_id}")

        # Calculate risk
        overall_score, risk_level, breakdown, explanation = self._calculate_risk(
            scan_results
        )

        # Persist assessment
        assessment = await self.repository.create(
            file_id=file_id,
            overall_score=overall_score,
            risk_level=risk_level,
            breakdown=breakdown,
            explanation=explanation,
        )

        logger.info(
            "Risk assessment created for file_id=%s: score=%.1f level=%s",
            file_id,
            overall_score,
            risk_level,
        )

        return assessment

    async def get_risk_assessment(self, file_id: str) -> Optional[RiskAssessment]:
        """Retrieve the latest risk assessment for a file."""
        return await self.repository.get_latest_by_file_id(file_id)

    async def get_risk_summary(self) -> list[dict[str, Any]]:
        """Get aggregated risk statistics across all files."""
        return await self.repository.get_summary()
