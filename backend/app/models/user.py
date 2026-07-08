"""User model for authentication and RBAC.

Supports both LOCAL (email/password) and GOOGLE (OAuth 2.0) providers.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """User accounts with role-based access control.

    Supports multiple authentication providers:
    - LOCAL: email/password auth
    - GOOGLE: Google Sign-In OAuth 2.0
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Authentication
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Nullable for Google-only users
    provider: Mapped[str] = mapped_column(
        String(20), default="LOCAL", nullable=False
    )  # "LOCAL" | "GOOGLE"
    google_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    profile_picture: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Avatar URL (alias for profile_picture in Google OAuth context)
    avatar_url: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )

    # Authorization
    role: Mapped[str] = mapped_column(
        String(50), default="user", index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    files = relationship("File", back_populates="user", lazy="selectin")
    alerts = relationship("Alert", back_populates="user", lazy="selectin")
    reports = relationship("Report", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.provider}/{self.role})>"
