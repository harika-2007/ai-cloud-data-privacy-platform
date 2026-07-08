"""Pydantic schemas for file management module."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """Response after successful file upload."""
    id: str
    original_name: str
    file_type: str
    file_size: int
    scan_status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class FileResponse(BaseModel):
    """Full file information response."""
    id: str
    user_id: str
    original_name: str
    stored_name: str
    file_type: str
    file_size: int
    storage_path: str
    gcs_path: Optional[str] = None
    scan_status: str
    uploaded_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    """Paginated file list response."""
    total: int
    page: int
    page_size: int
    files: list[FileResponse]
