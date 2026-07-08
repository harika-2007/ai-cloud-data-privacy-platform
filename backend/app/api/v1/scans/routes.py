"""REST API routes for scan and risk assessment operations.

Provides endpoints to initiate scans, retrieve results, and access
risk assessments for uploaded files.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.file import File
from app.repositories.base import BaseRepository
from app.repositories.scan_repository import ScanResultRepository
from app.schemas.auth import TokenPayload
from app.schemas.common import MessageResponse
from app.schemas.scan import RiskAssessmentResponse, ScanResultResponse, ScanStartResponse
from app.services.detection.detection_engine import DetectionEngine
from app.services.detection.scan_service import ScanService
from app.services.risk.risk_service import RiskService
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/scans",
    tags=["Scans"],
)


def get_scan_service(db: AsyncSession = Depends(get_db)) -> ScanService:
    """Dependency factory for ScanService."""
    scan_repo = ScanResultRepository(db)
    detection_engine = DetectionEngine()
    risk_service = RiskService(db)
    return ScanService(
        scan_repository=scan_repo,
        detection_engine=detection_engine,
        risk_service=risk_service,
    )


# ---------------------------------------------------------------------------
# POST /start/{file_id} - initiate a scan on a file
# ---------------------------------------------------------------------------


@router.post(
    "/start/{file_id}",
    response_model=ScanStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a PII scan on a file",
    description="Runs the detection engine on the specified file and persists findings.",
)
async def start_scan(
    file_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Start a PII scan on the file identified by *file_id*.

    The file must exist and belong to the current user (or the user
    must be an admin). Scan findings are persisted as ScanResult records
    and a risk assessment is triggered automatically.
    """
    # Verify file exists and belongs to the user
    file_repo = BaseRepository(File, db)
    file_record = await file_repo.get(file_id)
    if not file_record:
        raise NotFoundException("File", file_id)

    # Authorization: user can scan their own files; admins can scan any
    if file_record.user_id != current_user.sub and current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to scan this file",
        )

    # Run the scan
    await scan_service.start_scan(
        file_id=file_id,
        file_path=file_record.storage_path,
        file_type=file_record.file_type,
    )

    return ScanStartResponse(
        file_id=file_id,
        status="completed",
        message=f"Scan completed for file: {file_record.original_name}",
    )


# ---------------------------------------------------------------------------
# GET /file/{file_id} - get all scan results for a file
# ---------------------------------------------------------------------------


@router.get(
    "/file/{file_id}",
    response_model=dict[str, Any],
    summary="Get scan results for a file",
    description="Returns all PII findings detected in the specified file.",
)
async def get_file_scan_results(
    file_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Retrieve all PII findings from a scan for the given file."""
    # Verify file exists
    file_repo = BaseRepository(File, db)
    file_record = await file_repo.get(file_id)
    if not file_record:
        raise NotFoundException("File", file_id)

    results, total = await scan_service.get_scan_results(
        file_id=file_id, skip=skip, limit=limit
    )

    return {
        "file_id": file_id,
        "total_findings": total,
        "results": [ScanResultResponse.model_validate(r) for r in results],
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# GET /{id} - get a single scan result by its ID
# ---------------------------------------------------------------------------


@router.get(
    "/{id}",
    response_model=ScanResultResponse,
    summary="Get a single scan result",
    description="Returns details for one specific scan finding by its ID.",
)
async def get_scan_result(
    id: str,
    current_user: TokenPayload = Depends(get_current_user),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Get a single scan result by its primary key."""
    result = await scan_service.get_scan_result(id)
    if not result:
        raise NotFoundException("ScanResult", id)
    return result


# ---------------------------------------------------------------------------
# GET / - list all scans (admin only)
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=dict[str, Any],
    summary="List all scan results",
    description="Admin-only endpoint returning all scan results across files.",
)
async def list_all_scans(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=200, description="Max records to return"),
    current_user: TokenPayload = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all scan results across all files. Requires admin role."""
    scan_repo = ScanResultRepository(db)
    items, total = await scan_repo.get_all(skip=skip, limit=limit)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [ScanResultResponse.model_validate(r) for r in items],
    }


# ---------------------------------------------------------------------------
# GET /risk/file/{file_id} - get risk assessment for a file
# ---------------------------------------------------------------------------


@router.get(
    "/risk/file/{file_id}",
    response_model=RiskAssessmentResponse,
    summary="Get risk assessment for a file",
    description="Returns the latest privacy risk assessment for the given file.",
)
async def get_file_risk_assessment(
    file_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Retrieve the latest risk assessment for the specified file."""
    # Verify file exists
    file_repo = BaseRepository(File, db)
    file_record = await file_repo.get(file_id)
    if not file_record:
        raise NotFoundException("File", file_id)

    assessment = await scan_service.get_risk_assessment(file_id)
    if not assessment:
        raise NotFoundException("RiskAssessment", f"file_id={file_id}")

    return assessment


# ---------------------------------------------------------------------------
# GET /risk/summary - get overall risk summary
# ---------------------------------------------------------------------------


@router.get(
    "/risk/summary",
    response_model=dict[str, Any],
    summary="Get overall risk summary",
    description="Returns aggregated risk statistics across all scanned files.",
)
async def get_risk_summary(
    current_user: TokenPayload = Depends(get_current_user),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Get aggregated risk statistics across all files."""
    summary = await scan_service.get_risk_summary()
    if not summary:
        return {"total_files_assessed": 0, "breakdown": []}

    total = sum(item["count"] for item in summary)
    return {
        "total_files_assessed": total,
        "breakdown": summary,
    }
