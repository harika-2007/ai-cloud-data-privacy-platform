"""Report Repository for database operations."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for report CRUD and specialized queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(Report, db)

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Report], int]:
        query = select(Report).where(Report.user_id == user_id).order_by(Report.generated_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        count_r = await self.db.execute(select(func.count()).select_from(Report).where(Report.user_id == user_id))
        total = count_r.scalar() or 0
        return items, total

    async def get_by_type(self, report_type: str) -> list[Report]:
        result = await self.db.execute(select(Report).where(Report.report_type == report_type))
        return list(result.scalars().all())
