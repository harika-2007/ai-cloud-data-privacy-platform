"""User repository for authentication and user management.

Provides data access methods for the User model, extending the base
repository with user-specific queries.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address.

        Args:
            email: The email address to look up.

        Returns:
            The User instance if found, None otherwise.
        """
        result = await self.db.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get a user by their Google OAuth ID.

        Args:
            google_id: The Google account ID (sub claim from ID token).

        Returns:
            The User instance if found, None otherwise.
        """
        result = await self.db.execute(
            select(self.model).where(self.model.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def get_by_role(self, role: str) -> list[User]:
        """Get all users with a specific role.

        Args:
            role: The role to filter by (e.g., 'admin', 'user', 'analyst', 'viewer').

        Returns:
            List of User instances matching the given role.
        """
        result = await self.db.execute(
            select(self.model)
            .where(self.model.role == role)
            .order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_last_login(self, user_id: str) -> User:
        """Update the last login timestamp for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            The updated User instance.

        Raises:
            NotFoundException: If no user with the given ID exists.
        """
        return await self.update(
            user_id,
            last_login=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
