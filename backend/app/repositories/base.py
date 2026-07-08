"""Base repository implementing common CRUD operations.

Follows the Repository pattern to abstract database access.
All module-specific repositories inherit from this base class.
"""

from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.exceptions import NotFoundException

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic base repository with common CRUD methods."""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def get(self, id: str) -> Optional[ModelType]:
        """Get a record by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_or_raise(self, id: str) -> ModelType:
        """Get a record by ID or raise NotFoundException."""
        instance = await self.get(id)
        if not instance:
            raise NotFoundException(self.model.__name__, id)
        return instance

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        order_by: Optional[str] = None,
        descending: bool = True,
        **filters,
    ) -> tuple[list[ModelType], int]:
        """Get paginated records with optional filters."""
        query = select(self.model)

        # Apply filters
        for field, value in filters.items():
            if value is not None:
                column = getattr(self.model, field, None)
                if column is not None:
                    query = query.where(column == value)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            query = query.order_by(order_column.desc() if descending else order_column.asc())
        else:
            query = query.order_by(self.model.created_at.desc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def update(self, id: str, **kwargs) -> ModelType:
        """Update a record by ID with the given fields."""
        instance = await self.get_or_raise(id)
        for key, value in kwargs.items():
            if value is not None and hasattr(instance, key):
                setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: str) -> bool:
        """Delete a record by ID. Returns True if deleted."""
        instance = await self.get(id)
        if not instance:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def count(self, **filters) -> int:
        """Count records matching given filters."""
        query = select(func.count()).select_from(self.model)
        for field, value in filters.items():
            if value is not None:
                column = getattr(self.model, field, None)
                if column is not None:
                    query = query.where(column == value)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def exists(self, **filters) -> bool:
        """Check if any record matches the given filters."""
        query = select(self.model).limit(1)
        for field, value in filters.items():
            if value is not None:
                column = getattr(self.model, field, None)
                if column is not None:
                    query = query.where(column == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
