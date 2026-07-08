"""Alert Repository for database operations."""

from typing import Any, Optional

from sqlalchemy import case, select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Repository for alert CRUD and specialized queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(Alert, db)

    async def get_unread_count(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Alert).where(
                and_(Alert.user_id == user_id, Alert.is_read == False)
            )
        )
        return result.scalar() or 0

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Alert], int]:
        query = select(Alert).where(Alert.user_id == user_id).order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        count_result = await self.db.execute(
            select(func.count()).select_from(Alert).where(Alert.user_id == user_id)
        )
        total = count_result.scalar() or 0
        return items, total

    async def get_alerts_stats(self) -> dict:
        total_r = await self.db.execute(select(func.count()).select_from(Alert))
        total = total_r.scalar() or 0
        unread_r = await self.db.execute(
            select(func.count()).select_from(Alert).where(Alert.is_read == False)
        )
        unread = unread_r.scalar() or 0
        severity_counts = {}
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            cnt_r = await self.db.execute(
                select(func.count()).select_from(Alert).where(Alert.severity == sev)
            )
            severity_counts[f"{sev.lower()}_alerts"] = cnt_r.scalar() or 0
        type_result = await self.db.execute(
            select(Alert.alert_type, func.count().label("c")).group_by(Alert.alert_type)
        )
        type_counts = {row.alert_type: row.c for row in type_result}
        return {"total_alerts": total, "unread_alerts": unread, **severity_counts, "alerts_by_type": type_counts}

    async def mark_as_read(self, alert_id: str) -> Optional[Alert]:
        return await self.update(alert_id, is_read=True)

    async def mark_all_as_read(self, user_id: str) -> int:
        result = await self.db.execute(
            update(Alert).where(and_(Alert.user_id == user_id, Alert.is_read == False)).values(is_read=True)
        )
        await self.db.flush()
        return result.rowcount

    async def get_recent_alerts(self, limit: int = 10) -> list[Alert]:
        result = await self.db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(limit))
        return list(result.scalars().all())
