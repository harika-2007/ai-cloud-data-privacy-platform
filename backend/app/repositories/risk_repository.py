"""Risk Assessment Repository for database operations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import RiskAssessment
from app.repositories.base import BaseRepository


class RiskAssessmentRepository(BaseRepository[RiskAssessment]):
    """Repository for risk assessment CRUD and analytics."""

    def __init__(self, db: AsyncSession):
        super().__init__(RiskAssessment, db)

    async def get_latest_by_file_id(self, file_id: str):
        result = await self.db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.file_id == file_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all_summary(self) -> dict:
        result = await self.db.execute(
            select(
                func.avg(RiskAssessment.overall_score).label("avg_score"),
                func.count().label("total"),
            ).select_from(RiskAssessment)
        )
        row = result.one()

        # Count risk levels
        high = await self.db.execute(
            select(func.count()).select_from(RiskAssessment).where(RiskAssessment.risk_level == "HIGH")
        )
        medium = await self.db.execute(
            select(func.count()).select_from(RiskAssessment).where(RiskAssessment.risk_level == "MEDIUM")
        )
        low = await self.db.execute(
            select(func.count()).select_from(RiskAssessment).where(RiskAssessment.risk_level == "LOW")
        )

        return {
            "avg_score": round(row.avg_score or 0, 2),
            "total": row.total or 0,
            "high_count": high.scalar() or 0,
            "medium_count": medium.scalar() or 0,
            "low_count": low.scalar() or 0,
        }

    async def get_risk_trends(self, days: int = 30) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(RiskAssessment.created_at, RiskAssessment.overall_score)
            .where(RiskAssessment.created_at >= cutoff)
            .order_by(RiskAssessment.created_at)
        )
        trends = {}
        for row in result:
            date_key = row.created_at.strftime("%Y-%m-%d") if row.created_at else ""
            if date_key not in trends:
                trends[date_key] = []
            trends[date_key].append(row.overall_score)

        return [
            {"date": date, "score": round(sum(scores) / len(scores), 1)}
            for date, scores in sorted(trends.items())
        ]

    async def get_high_risk_files(self, min_score: float = 71.0) -> list[RiskAssessment]:
        result = await self.db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.overall_score >= min_score)
            .order_by(RiskAssessment.overall_score.desc())
        )
        return list(result.scalars().all())

    async def get_summary(self) -> list[dict]:
        """Aggregate risk statistics across all files, grouped by risk level.

        Returns:
            A list of dicts with risk_level, count, average_score.
        """
        query = (
            select(
                RiskAssessment.risk_level,
                func.count(RiskAssessment.id).label("count"),
                func.avg(RiskAssessment.overall_score).label("avg_score"),
            )
            .group_by(RiskAssessment.risk_level)
        )
        result = await self.db.execute(query)
        rows = result.all()
        return [
            {
                "risk_level": row.risk_level,
                "count": int(row.count),
                "average_score": round(float(row.avg_score), 2) if row.avg_score else 0.0,
            }
            for row in rows
        ]
