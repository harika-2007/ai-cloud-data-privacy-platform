"""Report service for generating compliance and audit reports.

Provides business logic for creating PDF reports with cover pages,
findings tables, risk assessments, AI compliance recommendations,
and pagination. Uses ReportLab for PDF generation.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.models.report import Report
from app.models.scan import RiskAssessment
from app.repositories.report_repository import ReportRepository
from app.repositories.scan_repository import ScanResultRepository
from app.services.ai.ai_service import AIService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ReportService:
    """Service for generating compliance, audit, and summary reports."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ReportRepository(db)
        self.scan_repository = ScanResultRepository(db)
        self.output_dir = settings.REPORT_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_report(
        self,
        user_id: str,
        file_id: Optional[str],
        title: str,
        report_type: str,
        include_ai: bool = True,
    ) -> Report:
        """Generate a complete compliance report with PDF document.

        Fetches scan results and the latest risk assessment for the specified
        file, optionally enriches with AI compliance recommendations, generates
        a PDF via ReportLab, and persists the report record.

        Args:
            user_id: UUID of the requesting user.
            file_id: UUID of the file to report on (may be None for summary reports).
            title: Report title.
            report_type: Category (compliance, audit, summary).
            include_ai: Whether to include AI-generated compliance analysis.

        Returns:
            The newly created Report model (includes ``pdf_path``).
        """
        # Fetch scan results
        scan_results, _ = await self.scan_repository.get_by_file_id(
            file_id=file_id,
            skip=0,
            limit=1000,
        ) if file_id else ([], 0)

        # Fetch latest risk assessment
        risk_assessment: Optional[RiskAssessment] = None
        if file_id:
            risk_result = await self.db.execute(
                select(RiskAssessment)
                .where(RiskAssessment.file_id == file_id)
                .order_by(RiskAssessment.created_at.desc())
                .limit(1)
            )
            risk_assessment = risk_result.scalar_one_or_none()

        # Build findings list and risk dict for report_data and AI
        findings_list = [
            {"data_type": r.data_type, "count": r.count, "severity": r.severity}
            for r in scan_results
        ]
        risk_dict = {
            "overall_score": risk_assessment.overall_score,
            "risk_level": risk_assessment.risk_level,
            "explanation": risk_assessment.explanation,
            "breakdown": risk_assessment.breakdown,
        } if risk_assessment else None

        # Fetch AI summary if requested
        ai_summary: Optional[str] = None
        if include_ai and file_id and settings.AI_ENABLED:
            try:
                ai_service = AIService()
                ai_result = await ai_service.get_compliance_recommendations(
                    file_id=file_id,
                    scan_results=findings_list,
                    risk_assessment=risk_dict,
                )
                ai_summary = ai_result.get("recommendations", "") if ai_result else None
            except Exception as e:
                logger.warning("AI summary generation failed: %s", e)

        # Build report data
        report_data = {
            "title": title,
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "findings": findings_list,
            "risk_assessment": risk_dict,
        }

        # Generate PDF
        pdf_filename = (
            f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_id or 'summary'}.pdf"
        )
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        self._create_pdf(
            pdf_path=pdf_path,
            title=title,
            scan_results=report_data["findings"],
            risk_assessment=report_data["risk_assessment"],
            ai_summary=ai_summary,
        )

        # Persist report record
        report = await self.repository.create(
            user_id=user_id,
            file_id=file_id,
            title=title,
            report_type=report_type,
            report_data=report_data,
            pdf_path=pdf_path,
            ai_summary=ai_summary,
        )

        logger.info("Report generated: id=%s title='%s' pdf=%s", report.id, title, pdf_path)
        return report

    async def generate_pdf(
        self,
        report: Report,
    ) -> str:
        """Regenerate the PDF for an existing report (e.g. after data updates).

        Args:
            report: The Report model instance with ``report_data`` populated.

        Returns:
            The filesystem path to the generated PDF.
        """
        pdf_filename = f"{report.report_type}_{report.id[:8]}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        report_data = report.report_data or {}
        self._create_pdf(
            pdf_path=pdf_path,
            title=report.title,
            scan_results=report_data.get("findings", []),
            risk_assessment=report_data.get("risk_assessment"),
            ai_summary=report.ai_summary,
        )

        # Update the stored pdf_path
        updated = await self.repository.update(report.id, pdf_path=pdf_path)
        logger.info("PDF regenerated for report id=%s: %s", report.id, pdf_path)
        return updated.pdf_path or pdf_path

    # ------------------------------------------------------------------
    # PDF generation (internal)
    # ------------------------------------------------------------------

    def _create_pdf(
        self,
        pdf_path: str,
        title: str,
        scan_results: list[dict[str, Any]],
        risk_assessment: Optional[dict[str, Any]] = None,
        ai_summary: Optional[str] = None,
    ) -> None:
        """Build a PDF document using ReportLab.

        The output includes:
            - Cover page with title and generation date.
            - Executive summary.
            - Findings table (data_type, count, severity).
            - Risk assessment section with score and level.
            - AI compliance recommendations (if provided).
            - Remediation recommendations.
            - Footer with page numbers.

        Args:
            pdf_path: Destination path for the PDF file.
            title: Report title for the cover page.
            scan_results: List of finding dicts with ``data_type``, ``count``, ``severity``.
            risk_assessment: Optional dict with ``overall_score``, ``risk_level``,
                ``explanation``.
            ai_summary: Optional AI-generated compliance analysis text.
        """
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        styles = getSampleStyleSheet()

        # ---- Custom styles ----
        cover_title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontSize=26,
            spaceAfter=6,
            textColor=colors.HexColor("#1a237e"),
            alignment=TA_CENTER,
        )
        cover_subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontSize=14,
            spaceAfter=4,
            textColor=colors.HexColor("#5c6bc0"),
            alignment=TA_CENTER,
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#283593"),
        )
        sub_heading = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#3949ab"),
        )
        body_style = ParagraphStyle(
            "BodyText2",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=8,
            leading=14,
        )
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
        )
        risk_high = colors.HexColor("#e53935")
        risk_medium = colors.HexColor("#fb8c00")
        risk_low = colors.HexColor("#43a047")

        elements: list = []

        # ==================================================================
        # 1. Cover page
        # ==================================================================
        elements.append(Spacer(1, 120))
        elements.append(Paragraph("Privacy Compliance Report", cover_title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(title, cover_subtitle_style))
        elements.append(Spacer(1, 30))
        elements.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
                ParagraphStyle(
                    "CoverDate",
                    parent=body_style,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor("#888888"),
                ),
            )
        )
        elements.append(Spacer(1, 8))
        elements.append(
            Paragraph(
                f"Report Type: <b>{report_type_from_title(title)}</b>",
                ParagraphStyle(
                    "CoverType",
                    parent=body_style,
                    alignment=TA_CENTER,
                ),
            )
        )
        elements.append(PageBreak())

        # ==================================================================
        # 2. Executive Summary
        # ==================================================================
        elements.append(Paragraph("Executive Summary", section_heading))
        elements.append(Spacer(1, 6))

        total_findings = sum(r.get("count", 0) for r in scan_results)
        data_type_count = len(scan_results)

        summary_text = (
            f"This report provides a detailed privacy compliance analysis "
            f"of the scanned file. A total of <b>{total_findings}</b> PII "
            f"occurrence(s) across <b>{data_type_count}</b> data type(s) were "
            f"detected."
        )
        elements.append(Paragraph(summary_text, body_style))

        if risk_assessment:
            score = risk_assessment.get("overall_score", 0)
            level = risk_assessment.get("risk_level", "UNKNOWN")
            color = risk_high if score >= 71 else (risk_medium if score >= 31 else risk_low)
            elements.append(
                Paragraph(
                    f'Overall Risk Score: <b>{score:.1f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; '
                    f'Risk Level: <font color="{color.hexval()}"><b>{level}</b></font>',
                    body_style,
                )
            )
        elements.append(Spacer(1, 12))

        # ==================================================================
        # 3. Findings Table
        # ==================================================================
        elements.append(Paragraph("Findings Summary", section_heading))
        elements.append(Spacer(1, 6))

        if scan_results:
            table_data: list[list[str]] = [
                ["Data Type", "Occurrences", "Severity"]
            ]
            for r in scan_results:
                table_data.append([
                    r.get("data_type", "Unknown"),
                    str(r.get("count", 0)),
                    r.get("severity", "LOW"),
                ])

            col_widths = [220, 120, 120]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#283593")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                # Body
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#e8eaf6")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No findings detected.", body_style))

        elements.append(Spacer(1, 20))

        # ==================================================================
        # 4. Risk Assessment
        # ==================================================================
        elements.append(Paragraph("Risk Assessment", section_heading))
        elements.append(Spacer(1, 6))

        if risk_assessment:
            score = risk_assessment.get("overall_score", 0)
            level = risk_assessment.get("risk_level", "UNKNOWN")
            explanation = risk_assessment.get("explanation", "")

            color = risk_high if score >= 71 else (risk_medium if score >= 31 else risk_low)
            elements.append(
                Paragraph(
                    f'<font color="{color.hexval()}"><b>Score: {score:.1f} '
                    f'&mdash; {level}</b></font>',
                    body_style,
                )
            )
            if explanation:
                elements.append(Paragraph(f"<b>Analysis:</b> {explanation}", body_style))

            # Breakdown sub-section
            breakdown = risk_assessment.get("breakdown", {})
            if breakdown:
                elements.append(Paragraph("Risk Breakdown", sub_heading))
                breakdown_data: list[list[str]] = [["Data Type", "Count", "Weight", "Contribution"]]
                for data_type, info in sorted(
                    breakdown.items(),
                    key=lambda x: x[1].get("contribution", 0),
                    reverse=True,
                ):
                    breakdown_data.append([
                        data_type,
                        str(info.get("count", 0)),
                        str(info.get("weight", 0)),
                        str(info.get("contribution", 0)),
                    ])
                btable = Table(breakdown_data, colWidths=[160, 80, 80, 120], repeatRows=1)
                btable.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#eceff1")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elements.append(btable)
        else:
            elements.append(Paragraph("No risk assessment available.", body_style))

        elements.append(Spacer(1, 20))

        # ==================================================================
        # 5. AI Compliance Recommendations
        # ==================================================================
        if ai_summary:
            elements.append(Paragraph("AI Compliance Recommendations", section_heading))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(ai_summary[:3000], body_style))
            elements.append(Spacer(1, 12))
            elements.append(PageBreak())

        # ==================================================================
        # 6. Remediation Recommendations
        # ==================================================================
        elements.append(Paragraph("Recommendations", section_heading))
        elements.append(Spacer(1, 6))
        recommendations = self._generate_recommendations(scan_results, risk_assessment)
        if recommendations:
            for rec in recommendations:
                elements.append(Paragraph(f"&#8226; {rec}", body_style))
        else:
            elements.append(Paragraph(
                "No specific remediation actions required at this time. "
                "Continue regular monitoring.",
                body_style,
            ))

        # ==================================================================
        # 7. Footer
        # ==================================================================
        elements.append(Spacer(1, 40))
        elements.append(Paragraph(
            "This report was generated by the AI-Powered Cloud Data Privacy "
            "Compliance & Security Monitoring Platform.",
            footer_style,
        ))
        elements.append(Paragraph(
            f"Page <page/> of <totalpages/> &nbsp;|&nbsp; "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
            footer_style,
        ))

        # Build the PDF
        doc.build(elements)
        logger.info("PDF created: %s (%d pages estimated)", pdf_path, len(elements))

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    async def get_reports(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Report], int]:
        """Get paginated reports for a user.

        Args:
            user_id: UUID of the user.
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            A tuple of (list of Report records, total count).
        """
        return await self.repository.get_by_user_id(user_id, skip=skip, limit=limit)

    async def get_report(self, report_id: str) -> Optional[Report]:
        """Get a single report by its ID.

        Args:
            report_id: UUID of the report.

        Returns:
            The Report record, or None if not found.
        """
        return await self.repository.get(report_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_recommendations(
        scan_results: list[dict[str, Any]],
        risk_assessment: Optional[dict[str, Any]] = None,
    ) -> list[str]:
        """Generate actionable remediation recommendations based on findings.

        Args:
            scan_results: List of finding dicts.
            risk_assessment: Optional risk assessment dict.

        Returns:
            A list of recommendation strings.
        """
        recs: list[str] = []

        if risk_assessment and risk_assessment.get("overall_score", 0) >= 71:
            recs.append(
                "Immediate remediation required: High privacy risk detected. "
                "Conduct a full Privacy Impact Assessment (PIA)."
            )

        for result in scan_results:
            data_type = result.get("data_type", "")
            count = result.get("count", 0)
            if count == 0:
                continue

            if data_type == "Aadhaar":
                recs.append(
                    f"Mask or encrypt {count} Aadhaar number(s). "
                    "Implement strict access controls and audit logging."
                )
            elif data_type == "PAN":
                recs.append(
                    f"Secure {count} PAN card number(s). "
                    "Ensure encryption at rest and in transit."
                )
            elif data_type == "CreditCard":
                recs.append(
                    f"PCI DSS compliance required: {count} credit card number(s) "
                    "detected. Implement tokenization or masking."
                )
            elif data_type == "Email":
                recs.append(
                    f"{count} email address(es) found. "
                    "Review data retention and consent policies."
                )
            elif data_type == "Phone":
                recs.append(
                    f"{count} phone number(s) found. "
                    "Verify lawful basis for processing."
                )

        if not recs:
            recs.append("No specific recommendations. Continue regular monitoring.")

        return recs


def report_type_from_title(title: str) -> str:
    """Extract a human-readable type label from the title."""
    lower = title.lower()
    if "audit" in lower:
        return "Audit Report"
    elif "summary" in lower or "overview" in lower:
        return "Summary Report"
    return "Compliance Report"
