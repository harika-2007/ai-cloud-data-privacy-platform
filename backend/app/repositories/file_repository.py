"""File repository implementing data access for file management.

Extends BaseRepository with file-specific queries including
pagination by user, type filtering, scan status updates, and statistics.
"""

from typing import Optional

from sqlalchemy import func, select

from app.models.file import File
from app.repositories.base import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository for File model operations.

    Provides specialized queries beyond the generic CRUD from BaseRepository.
    """

    def __init__(self, db):
        """Initialize with the File model and an async database session."""
        super().__init__(File, db)

    async def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[File], int]:
        """Get paginated files for a specific user, ordered by upload date.

        Args:
            user_id: The user's UUID string.
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of File records, total count).
        """
        base_query = select(File).where(File.user_id == user_id)

        # Count total matching records
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply ordering and pagination
        paginated_query = (
            base_query
            .order_by(File.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(paginated_query)
        items = list(result.scalars().all())
        return items, total

    async def get_by_type(self, file_type: str) -> list[File]:
        """Get all files matching a specific file type (e.g. 'pdf', 'csv').

        Args:
            file_type: The file extension without a leading dot (e.g. 'pdf').

        Returns:
            A list of matching File records.
        """
        result = await self.db.execute(
            select(File).where(File.file_type == file_type)
        )
        return list(result.scalars().all())

    async def update_scan_status(self, file_id: str, status: str) -> File:
        """Update the scan status of a file record.

        Args:
            file_id: The file's UUID string.
            status: The new scan status value (e.g. 'pending', 'scanning',
                    'completed', 'failed').

        Returns:
            The updated File record.
        """
        return await self.update(file_id, scan_status=status)

    async def get_file_stats(self, user_id: str) -> dict:
        """Get file statistics for a user: count by type and total size.

        Args:
            user_id: The user's UUID string.

        Returns:
            A dictionary with:
                - count_by_type: mapping of file_type to count
                - total_size: sum of file sizes in bytes
        """
        # Count by file type
        type_query = (
            select(File.file_type, func.count().label("count"))
            .where(File.user_id == user_id)
            .group_by(File.file_type)
        )
        type_result = await self.db.execute(type_query)
        count_by_type: dict[str, int] = {}
        for row in type_result:
            count_by_type[row.file_type] = row.count

        # Sum total file size
        size_query = select(
            func.coalesce(func.sum(File.file_size), 0)
        ).where(File.user_id == user_id)
        size_result = await self.db.execute(size_query)
        total_size: int = size_result.scalar() or 0

        return {
            "count_by_type": count_by_type,
            "total_size": total_size,
        }
