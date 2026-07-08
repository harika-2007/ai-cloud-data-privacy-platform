"""Google Cloud DLP Integration Service.

Scans files for sensitive data using Google Cloud Data Loss Prevention API.
Supports multiple infoTypes including Aadhaar, PAN, Email, Phone, Credit Card.
"""

import logging
from typing import Any, Optional

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class DLPService:
    """Service for Google Cloud DLP API integration."""

    INFO_TYPES = [
        "US_SOCIAL_SECURITY_NUMBER",
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "CREDIT_CARD_NUMBER",
        "INDIA_AADHAAR",
        "INDIA_PAN",
        "PERSON_NAME",
        "US_BANK_NUMBER",
        "US_DRIVERS_LICENSE_NUMBER",
        "DATE_OF_BIRTH",
    ]

    def __init__(self):
        self.project = settings.GOOGLE_CLOUD_PROJECT
        self.enabled = settings.DLP_ENABLED and bool(self.project)
        self._client = None

    @property
    def client(self):
        """Lazy-init DLP client."""
        if self._client is None and self.enabled:
            try:
                from google.cloud import dlp_v2
                self._client = dlp_v2.DlpServiceClient()
            except Exception as e:
                logger.error(f"Failed to initialize DLP client: {e}")
                self.enabled = False
        return self._client

    async def inspect_content(self, text: str, content_type: str = "text/plain") -> list[dict]:
        """Inspect text content using Cloud DLP API."""
        if not self.enabled or not text.strip():
            return []

        try:
            parent = f"projects/{self.project}/locations/global"
            inspect_config = {
                "info_types": [{"name": it} for it in self.INFO_TYPES],
                "min_likelihood": "POSSIBLE",
                "include_quote": True,
            }
            item = {"value": text, "type": content_type}

            response = self.client.inspect_content(
                request={
                    "parent": parent,
                    "inspect_config": inspect_config,
                    "item": item,
                }
            )

            return self._map_findings(response.result)
        except Exception as e:
            logger.error(f"DLP inspection failed: {e}")
            return []

    async def inspect_file(self, file_path: str, file_type: str) -> list[dict]:
        """Read a file and inspect its content using Cloud DLP."""
        try:
            text = self._read_file_content(file_path, file_type)
            if not text:
                return []
            return await self.inspect_content(text)
        except Exception as e:
            logger.error(f"DLP file inspection failed: {e}")
            return []

    def _read_file_content(self, file_path: str, file_type: str) -> str:
        """Read file content based on type."""
        try:
            if file_type == "txt":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            elif file_type == "csv":
                import pandas as pd
                df = pd.read_csv(file_path)
                return df.to_string()
            elif file_type == "xlsx":
                import pandas as pd
                df = pd.read_excel(file_path)
                return df.to_string()
            elif file_type == "pdf":
                text = []
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        text.append(page.extract_text() or "")
                except Exception:
                    import subprocess
                    result = subprocess.run(
                        ["pdftotext", file_path, "-"],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        text.append(result.stdout)
                return "\n".join(text)
            return ""
        except Exception as e:
            logger.error(f"Failed to read file for DLP: {e}")
            return ""

    def _map_findings(self, result: Any) -> list[dict]:
        """Map DLP findings to internal format."""
        findings = {}
        for finding in result.findings:
            info_type = finding.info_type.name
            if info_type not in findings:
                findings[info_type] = {
                    "data_type": info_type,
                    "count": 0,
                    "severity": self._map_likelihood(finding.likelihood),
                    "sample_values": [],
                }
            findings[info_type]["count"] += 1
            if hasattr(finding, "quote") and finding.quote and len(findings[info_type]["sample_values"]) < 5:
                findings[info_type]["sample_values"].append(finding.quote)

        return list(findings.values())

    def _map_likelihood(self, likelihood) -> str:
        """Map DLP likelihood to severity string."""
        likelihood_str = str(likelihood)
        if "VERY_LIKELY" in likelihood_str:
            return "CRITICAL"
        elif "LIKELY" in likelihood_str:
            return "HIGH"
        elif "POSSIBLE" in likelihood_str:
            return "MEDIUM"
        return "LOW"
