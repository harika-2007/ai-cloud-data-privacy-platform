"""Scan service orchestrating PII detection, result persistence, and risk assessment.

Coordinates between the DetectionEngine, ScanResultRepository, and RiskService
to run scans on uploaded files and persist structured findings.
"""

import logging
from typing import Any, Optional

from app.models.scan import ScanResult, RiskAssessment
from app.repositories.scan_repository import ScanResultRepository
from app.services.detection.detection_engine import DetectionEngine
from app.services.risk.risk_service import RiskService
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class ScanService:
    """Service layer for initiating scans and retrieving scan results."""

    def __init__(
        self,
        scan_repository: ScanResultRepository,
        detection_engine: Optional[DetectionEngine] = None,
        risk_service: Optional[RiskService] = None,
    ):
        self.repository = scan_repository
        self.detection_engine = detection_engine or DetectionEngine()
        self.risk_service = risk_service

    async def start_scan(self, file_id: str, file_path: str, file_type: str) -> list[ScanResult]:
        """Run PII detection on a file and persist the results.

        Also triggers risk assessment for the file if a risk_service is configured.

        Args:
            file_id: UUID of the File record being scanned.
            file_path: Filesystem path to the uploaded file.
            file_type: File extension (csv, xlsx, pdf, txt).

        Returns:
            A list of newly created ScanResult records.
        """
        logger.info("Starting scan for file_id=%s (type=%s)", file_id, file_type)

        # Run detection engine
        findings = self.detection_engine.detect_file(file_path, file_type)
        logger.info(
            "Detection complete for file_id=%s: %d finding types",
            file_id,
            len(findings),
        )

        # Persist each finding as a ScanResult record
        scan_results: list[ScanResult] = []
        for finding in findings:
            scan_result = await self.repository.create(
                file_id=file_id,
                data_type=finding["data_type"],
                count=finding["count"],
                severity=finding["severity"],
                sample_values=finding.get("sample_values"),
            )
            scan_results.append(scan_result)

        # Trigger risk assessment if service is available
        if self.risk_service is not None:
            try:
                await self.risk_service.assess_file(file_id)
                logger.info("Risk assessment completed for file_id=%s", file_id)
            except Exception as e:
                logger.warning(
                    "Risk assessment failed for file_id=%s: %s", file_id, e
                )

        return scan_results

    async def get_scan_results(
        self,
        file_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ScanResult], int]:
        """Retrieve all scan results for a file with pagination."""
        return await self.repository.get_by_file_id(
            file_id=file_id,
            skip=skip,
            limit=limit,
        )

    async def get_scan_summary(self, file_id: str) -> list[dict[str, Any]]:
        """Get findings aggregated by data_type for a file."""
        return await self.repository.get_findings_summary(file_id)

    async def get_scan_result(self, scan_id: str) -> Optional[ScanResult]:
        """Get a single scan result by its ID."""
        return await self.repository.get(scan_id)

    async def run_risk_assessment(self, file_id: str) -> Optional[RiskAssessment]:
        """Explicitly trigger risk assessment for a scanned file.

        Args:
            file_id: UUID of the File whose risk should be assessed.

        Returns:
            The newly created RiskAssessment, or None if no risk_service configured.
        """
        if self.risk_service is None:
            logger.warning("No risk_service configured; skipping risk assessment")
            return None

        return await self.risk_service.assess_file(file_id)

    async def get_risk_assessment(self, file_id: str) -> Optional[RiskAssessment]:
        """Retrieve the latest risk assessment for a file."""
        if self.risk_service is None:
            return None
        return await self.risk_service.get_risk_assessment(file_id)

    async def get_risk_summary(self) -> list[dict[str, Any]]:
        """Get aggregated risk summary across all files."""
        if self.risk_service is None:
            return []
        return await self.risk_service.get_risk_summary()
