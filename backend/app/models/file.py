"""File model for uploaded file metadata."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class File(Base):
    """Uploaded file metadata and status tracking."""

    __tablename__ = "files"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_path: Mapped[str] = mapped_column(String(500))
    gcs_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scan_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="files", lazy="selectin")
    scan_results = relationship("ScanResult", back_populates="file", lazy="selectin", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="file", lazy="selectin", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="file", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<File {self.original_name} ({self.file_type})>"
