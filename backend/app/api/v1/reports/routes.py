"""REST API routes for report generation and management.

Provides endpoints to generate compliance reports, list reports,
retrieve report details, and download PDF documents.
All endpoints require authentication.
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import TokenPayload
from app.schemas.common import MessageResponse
from app.schemas.report import (
    ReportGenerateRequest,
    ReportListResponse,
    ReportResponse,
)
from app.services.reporting.report_service import ReportService
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


def _get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    """Dependency that provides a ReportService instance."""
    return ReportService(db)


# ---------------------------------------------------------------------------
# POST /generate - generate a new report
# ---------------------------------------------------------------------------


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a report",
    description="Generates a compliance/audit report with PDF for a file.",
)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
) -> ReportResponse:
    """Generate a comprehensive compliance report.

    The report includes scan findings, risk assessment, and optionally
    AI-powered compliance recommendations. A PDF document is created
    and the report record is persisted.

    Args:
        request: The report generation parameters (file_id, title,
            report_type, include_ai_summary).

    Returns:
        The newly created Report record.
    """
    report = await service.generate_report(
        user_id=current_user.sub,
        file_id=request.file_id,
        title=request.title,
        report_type=request.report_type,
        include_ai=request.include_ai_summary,
    )
    return ReportResponse.model_validate(report)


# ---------------------------------------------------------------------------
# GET / - list reports for the current user
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List reports",
    description="Returns paginated reports for the authenticated user.",
)
async def list_reports(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenPayload = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
) -> ReportListResponse:
    """Get a paginated list of reports for the authenticated user."""
    skip = (page - 1) * page_size
    reports, total = await service.get_reports(
        user_id=current_user.sub,
        skip=skip,
        limit=page_size,
    )
    return ReportListResponse(
        total=total,
        reports=[ReportResponse.model_validate(r) for r in reports],
    )


# ---------------------------------------------------------------------------
# GET /{id} - get report details
# ---------------------------------------------------------------------------


@router.get(
    "/{id}",
    response_model=ReportResponse,
    summary="Get report details",
    description="Returns detailed information about a specific report.",
)
async def get_report(
    id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
) -> ReportResponse:
    """Get a single report by its ID.

    Args:
        id: The UUID of the report.

    Returns:
        The Report record.

    Raises:
        NotFoundException: If the report ID does not exist.
    """
    report = await service.get_report(id)
    if not report:
        raise NotFoundException("Report", id)
    return ReportResponse.model_validate(report)


# ---------------------------------------------------------------------------
# GET /{id}/download - download the PDF for a report
# ---------------------------------------------------------------------------


@router.get(
    "/{id}/download",
    summary="Download report PDF",
    description="Downloads the PDF document for a generated report.",
)
async def download_report(
    id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
):
    """Download the PDF file associated with a report.

    Args:
        id: The UUID of the report.

    Returns:
        A FileResponse streaming the PDF.

    Raises:
        NotFoundException: If the report or its PDF file does not exist.
    """
    report = await service.get_report(id)
    if not report:
        raise NotFoundException("Report", id)

    if not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found for this report",
        )

    safe_filename = report.title.replace(" ", "_").replace("/", "_") + ".pdf"
    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=safe_filename,
    )
