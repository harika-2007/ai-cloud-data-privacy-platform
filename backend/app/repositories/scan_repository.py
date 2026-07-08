"""Scan result repository extending BaseRepository with scan-specific queries.

Provides data access methods for scan results and findings aggregation,
following the repository pattern for clean separation of database logic.
"""

from typing import Any, Optional

from sqlalchemy import func, select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import ScanResult
from app.repositories.base import BaseRepository


class ScanResultRepository(BaseRepository[ScanResult]):
    """Repository for ScanResult CRUD and aggregation operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(ScanResult, db)

    async def get_by_file_id(
        self,
        file_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ScanResult], int]:
        """Get all scan results for a specific file with pagination."""
        query = (
            select(ScanResult)
            .where(ScanResult.file_id == file_id)
            .order_by(ScanResult.severity.desc(), ScanResult.count.desc())
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_findings_summary(self, file_id: str) -> list[dict[str, Any]]:
        """Aggregate findings by data_type for a specific file.

        Returns a list of dicts with data_type, total_count, max_severity.
        """
        query = (
            select(
                ScanResult.data_type,
                func.sum(ScanResult.count).label("total_count"),
                func.max(ScanResult.severity).label("max_severity"),
            )
            .where(ScanResult.file_id == file_id)
            .group_by(ScanResult.data_type)
            .order_by(func.sum(ScanResult.count).desc())
        )
        result = await self.db.execute(query)
        rows = result.all()
        return [
            {
                "data_type": row.data_type,
                "total_count": int(row.total_count),
                "max_severity": row.max_severity,
            }
            for row in rows
        ]

    async def get_all_findings_summary(self) -> list[dict[str, Any]]:
        """Aggregate findings across all files by data_type.

        Returns a list of dicts with data_type, total_count, file_count, max_severity.
        """
        query = (
            select(
                ScanResult.data_type,
                func.sum(ScanResult.count).label("total_count"),
                func.count(func.distinct(ScanResult.file_id)).label("file_count"),
                func.max(ScanResult.severity).label("max_severity"),
            )
            .group_by(ScanResult.data_type)
            .order_by(func.sum(ScanResult.count).desc())
        )
        result = await self.db.execute(query)
        rows = result.all()
        return [
            {
                "data_type": row.data_type,
                "total_count": int(row.total_count),
                "file_count": int(row.file_count),
                "max_severity": row.max_severity,
            }
            for row in rows
        ]

    async def get_high_severity_findings(
        self,
        min_count: int = 1,
        severities: Optional[list[str]] = None,
    ) -> list[ScanResult]:
        """Get findings with high severity that meet a minimum count threshold.

        Defaults to CRITICAL and HIGH severity levels if no specific severities given.
        """
        if severities is None:
            severities = ["CRITICAL", "HIGH"]

        query = (
            select(ScanResult)
            .where(
                ScanResult.severity.in_(severities),
                ScanResult.count >= min_count,
            )
            .order_by(ScanResult.count.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_by_file_id(self, file_id: str) -> int:
        """Delete all scan results for a file. Returns number of deleted rows."""
        stmt = sa_delete(ScanResult).where(ScanResult.file_id == file_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount
