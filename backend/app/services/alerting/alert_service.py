"""Alert service for creating, querying, and managing security alerts.

Provides business logic for generating alerts from scan findings,
checking risk thresholds, sending email notifications, and
computing alert statistics.
"""

import logging
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.models.alert import Alert
from app.models.file import File as FileModel
from app.models.scan import RiskAssessment, ScanResult
from app.repositories.alert_repository import AlertRepository
from app.repositories.scan_repository import ScanResultRepository

logger = logging.getLogger(__name__)


class AlertService:
    """Service layer for alert lifecycle management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_repository = AlertRepository(db)

    async def create_alert(
        self,
        file_id: str,
        user_id: str,
        alert_type: str,
        severity: str,
        message: str,
    ) -> Alert:
        """Create a new alert record and optionally send an email notification.

        Args:
            file_id: UUID of the associated file.
            user_id: UUID of the user to alert.
            alert_type: Category of alert (e.g. 'high_risk', 'excessive_findings').
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW).
            message: Human-readable alert message.

        Returns:
            The newly created Alert record.
        """
        alert = await self.alert_repository.create(
            file_id=file_id,
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )

        logger.info(
            "Alert created: type=%s severity=%s file_id=%s user_id=%s",
            alert_type,
            severity,
            file_id,
            user_id,
        )

        # Attempt email notification if enabled
        if settings.ALERT_EMAIL_ENABLED and settings.SMTP_HOST:
            try:
                await self.send_email_alert(alert)
            except Exception as e:
                logger.warning("Failed to send email alert: %s", e)

        return alert

    async def check_and_alert(self, file_id: str) -> list[Alert]:
        """Evaluate scan results and risk for a file, creating alerts as needed.

        Triggers:
            - High risk alert when risk score >= ``settings.HIGH_RISK_THRESHOLD`` (default 71.0).
            - Excessive findings alert when total findings >=
              ``settings.EXCESSIVE_FINDINGS_THRESHOLD`` (default 100).

        Args:
            file_id: UUID of the file to evaluate.

        Returns:
            A list of newly created Alert records (empty if no triggers met).
        """
        alerts: list[Alert] = []

        # Fetch file and its owner
        file_query = await self.db.execute(
            select(FileModel).where(FileModel.id == file_id)
        )
        file_record = file_query.scalar_one_or_none()
        if not file_record:
            logger.warning("check_and_alert: file not found file_id=%s", file_id)
            return alerts

        user_id = file_record.user_id

        # -- Check risk assessment (latest for this file) --
        risk_query = await self.db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.file_id == file_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(1)
        )
        risk_assessment: Optional[RiskAssessment] = risk_query.scalar_one_or_none()

        if risk_assessment and risk_assessment.overall_score >= settings.HIGH_RISK_THRESHOLD:
            alert = await self.create_alert(
                file_id=file_id,
                user_id=user_id,
                alert_type="high_risk",
                severity="HIGH",
                message=(
                    f"High privacy risk detected: File '{file_record.original_name}' "
                    f"scored {risk_assessment.overall_score:.1f} "
                    f"({risk_assessment.risk_level}). Immediate review recommended."
                ),
            )
            alerts.append(alert)

        # -- Check total number of findings --
        count_result = await self.db.execute(
            select(func.count())
            .select_from(ScanResult)
            .where(ScanResult.file_id == file_id)
        )
        total_findings = count_result.scalar() or 0

        if total_findings >= settings.EXCESSIVE_FINDINGS_THRESHOLD:
            alert = await self.create_alert(
                file_id=file_id,
                user_id=user_id,
                alert_type="excessive_findings",
                severity="MEDIUM",
                message=(
                    f"Excessive PII findings ({total_findings}) detected in file "
                    f"'{file_record.original_name}'. Review recommended."
                ),
            )
            alerts.append(alert)

        logger.info(
            "check_and_alert for file_id=%s: %d alert(s) created",
            file_id,
            len(alerts),
        )

        return alerts

    async def get_alerts(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Get paginated alerts for a user.

        Args:
            user_id: UUID of the user.
            page: Page number (1-based).
            page_size: Items per page.

        Returns:
            A dictionary with ``total``, ``unread_count``, and ``alerts`` list.
        """
        skip = (page - 1) * page_size
        alerts, total = await self.alert_repository.get_by_user_id(
            user_id=user_id,
            skip=skip,
            limit=page_size,
        )
        unread_count = await self.alert_repository.get_unread_count(user_id)

        return {
            "total": total,
            "unread_count": unread_count,
            "alerts": alerts,
        }

    async def get_unread_count(self, user_id: str) -> int:
        """Get the number of unread alerts for a user.

        Args:
            user_id: UUID of the user.

        Returns:
            Count of unread alerts.
        """
        return await self.alert_repository.get_unread_count(user_id)

    async def mark_as_read(self, alert_id: str) -> Optional[Alert]:
        """Mark a single alert as read.

        Args:
            alert_id: UUID of the alert.

        Returns:
            The updated Alert record, or None if not found.
        """
        return await self.alert_repository.mark_as_read(alert_id)

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all alerts for a user as read.

        Args:
            user_id: UUID of the user.

        Returns:
            The number of alerts updated.
        """
        return await self.alert_repository.mark_all_as_read(user_id)

    async def get_recent_alerts(self, limit: int = 10) -> list[Alert]:
        """Get the most recent alerts across all users.

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            A list of recent Alert records.
        """
        return await self.alert_repository.get_recent_alerts(limit=limit)

    async def get_alert_stats(self) -> dict[str, Any]:
        """Get aggregate alert statistics across all users.

        Returns:
            A dictionary with total_alerts, unread_alerts, by_severity, and by_type.
        """
        return await self.alert_repository.get_alerts_stats()

    async def send_email_alert(self, alert: Alert) -> bool:
        """Send an email notification for an alert via SMTP.

        Respects ``settings.ALERT_EMAIL_ENABLED`` and ``settings.SMTP_HOST``.
        In production the recipient email would be resolved from the User model;
        currently logs the prepared message.

        Args:
            alert: The Alert record to notify about.

        Returns:
            True if the email was prepared (or sent), False on failure.
        """
        if not settings.SMTP_HOST or not settings.ALERT_EMAIL_ENABLED:
            logger.debug("Email alerts not configured; skipping notification")
            return False

        try:
            import smtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg.set_content(
                f"Alert Type: {alert.alert_type}\n"
                f"Severity: {alert.severity}\n"
                f"Message: {alert.message}\n"
                f"File ID: {alert.file_id}\n"
                f"Created: {alert.created_at}\n"
            )
            msg["Subject"] = (
                f"[Privacy Platform] {alert.severity} Alert: {alert.alert_type}"
            )
            msg["From"] = settings.SMTP_FROM_EMAIL

            logger.info(
                "Email alert prepared: subject='%s' severity=%s",
                msg["Subject"],
                alert.severity,
            )

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    # server.send_message(msg)  # enable when recipients are configured

            return True

        except Exception as e:
            logger.error("Failed to send email alert: %s", e)
            return False
