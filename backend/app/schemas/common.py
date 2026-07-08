"""Common/shared Pydantic schemas."""

from typing import Any, Optional
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Standard message response."""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
    errors: Optional[dict[str, list[str]]] = None


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = 1
    page_size: int = 20


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    ai_service: str
    dlp_service: str
    storage_service: str
