"""File management API routes.

Provides endpoints for uploading, listing, retrieving, downloading,
and deleting uploaded files. All endpoints require authentication.

Upload automatically triggers PII scanning and risk assessment so that
scan results are available immediately after a successful upload.
"""

import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.scan_repository import ScanResultRepository
from app.schemas.auth import TokenPayload
from app.schemas.common import MessageResponse
from app.schemas.file import FileListResponse, FileResponse, FileUploadResponse
from app.services.detection.detection_engine import DetectionEngine
from app.services.detection.scan_service import ScanService
from app.services.file.file_service import FileService
from app.services.reporting.report_service import ReportService
from app.services.risk.risk_service import RiskService
from app.utils.exceptions import NotFoundException, ForbiddenException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


def _get_file_service(db: AsyncSession = Depends(get_db)) -> FileService:
    """Dependency that provides a FileService instance."""
    return FileService(db)


def _get_scan_service(db: AsyncSession = Depends(get_db)) -> ScanService:
    """Dependency that provides a ScanService instance."""
    scan_repo = ScanResultRepository(db)
    detection_engine = DetectionEngine()
    risk_service = RiskService(db)
    return ScanService(
        scan_repository=scan_repo,
        detection_engine=detection_engine,
        risk_service=risk_service,
    )


async def _verify_file_ownership(
    file_id: str,
    current_user: TokenPayload,
    service: FileService,
) -> object:
    """Retrieve a file and verify the current user owns it (or is admin).

    Returns the File model instance on success, or raises an exception.
    """
    file_record = await service.get_file(file_id)
    if file_record.user_id != current_user.sub and current_user.role != "admin":
        raise ForbiddenException(detail="You do not have access to this file")
    return file_record


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: TokenPayload = Depends(get_current_user),
    service: FileService = Depends(_get_file_service),
    scan_service: ScanService = Depends(_get_scan_service),
) -> FileUploadResponse:
    """Upload a file for the authenticated user.

    Validates the file type and size against configured limits,
    persists it to disk, creates a metadata record, then
    **automatically runs PII detection and risk assessment**
    so results are available immediately.

    Returns the newly created file metadata (with scan_status).
    """
    # 1. Validate and persist the file
    file_record = await service.upload_file(
        user_id=current_user.sub,
        file=file,
    )

    # 2. Auto-scan: run PII detection + risk assessment
    try:
        await scan_service.start_scan(
            file_id=file_record.id,
            file_path=file_record.storage_path,
            file_type=file_record.file_type,
        )
        file_record.scan_status = "completed"
        logger.info(
            "Auto-scan completed for file_id=%s name=%s",
            file_record.id,
            file_record.original_name,
        )

        # 3. Auto-generate compliance report after successful scan
        try:
            report_service = ReportService(service.repository.db)
            await report_service.generate_report(
                user_id=current_user.sub,
                file_id=file_record.id,
                title=f"Compliance Report - {file_record.original_name}",
                report_type="compliance",
                include_ai=True,
            )
            logger.info(
                "Auto-report generated for file_id=%s name=%s",
                file_record.id,
                file_record.original_name,
            )
        except Exception as exc:
            logger.warning(
                "Auto-report generation failed for file_id=%s name=%s: %s",
                file_record.id,
                file_record.original_name,
                exc,
            )
    except Exception as exc:
        file_record.scan_status = "failed"
        logger.warning(
            "Auto-scan failed for file_id=%s name=%s: %s",
            file_record.id,
            file_record.original_name,
            exc,
        )

    await service.repository.db.flush()
    return FileUploadResponse(
        id=file_record.id,
        original_name=file_record.original_name,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        scan_status=file_record.scan_status,
        uploaded_at=file_record.uploaded_at,
    )


@router.get("", response_model=FileListResponse)
async def list_user_files(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenPayload = Depends(get_current_user),
    service: FileService = Depends(_get_file_service),
) -> FileListResponse:
    """List files belonging to the authenticated user with pagination."""
    files, total = await service.get_user_files(
        user_id=current_user.sub,
        page=page,
        page_size=page_size,
    )
    return FileListResponse(
        total=total,
        page=page,
        page_size=page_size,
        files=[FileResponse.model_validate(f) for f in files],
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_details(
    file_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: FileService = Depends(_get_file_service),
) -> FileResponse:
    """Get detailed information about a specific file.

    The authenticated user must own the file or be an admin.
    """
    file_record = await _verify_file_ownership(file_id, current_user, service)
    return FileResponse.model_validate(file_record)


@router.delete("/{file_id}", response_model=MessageResponse)
async def delete_file(
    file_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: FileService = Depends(_get_file_service),
) -> MessageResponse:
    """Delete a file. The authenticated user must own the file or be an admin.

    Removes the file from both disk storage and the database.
    """
    await _verify_file_ownership(file_id, current_user, service)
    await service.delete_file(file_id)
    return MessageResponse(message=f"File '{file_id}' deleted successfully")


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: FileService = Depends(_get_file_service),
):
    """Download a file's content.

    The authenticated user must own the file or be an admin.
    Returns the file as an attachment response.
    """
    file_record = await _verify_file_ownership(file_id, current_user, service)

    if not os.path.exists(file_record.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on storage",
        )

    return FastAPIFileResponse(
        path=file_record.storage_path,
        filename=file_record.original_name,
        media_type="application/octet-stream",
    )
