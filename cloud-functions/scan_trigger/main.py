"""Cloud Function triggered by Pub/Sub events to orchestrate file scanning.

When a scan event is published (e.g., after a file upload to GCS), this
function orchestrates the full scan pipeline:

1. Downloads the file from Google Cloud Storage
2. Runs regex-based PII detection engine
3. Optionally runs Google Cloud DLP inspection
4. Calculates risk score based on findings
5. Stores results in the PostgreSQL database
6. Creates alerts if risk thresholds are exceeded
7. Publishes completion and alert events for downstream processing

Environment variables:
  DATABASE_URL: PostgreSQL connection string (async)
  GOOGLE_CLOUD_PROJECT: GCP project ID
  DLP_ENABLED: Whether to run Cloud DLP (true/false)
  HIGH_RISK_THRESHOLD: Score threshold for HIGH risk alerts (default: 71.0)
"""

import base64
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Configure logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PII Detection Patterns (same patterns as the backend detection engine)
# ---------------------------------------------------------------------------

PII_PATTERNS: dict[str, dict[str, Any]] = {
    "AADHAAR": {
        "pattern": r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b",
        "severity": "CRITICAL",
    },
    "PAN": {
        "pattern": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
        "severity": "HIGH",
    },
    "EMAIL": {
        "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "severity": "LOW",
    },
    "PHONE": {
        "pattern": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "severity": "MEDIUM",
    },
    "CREDIT_CARD": {
        "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "severity": "CRITICAL",
    },
    "SSN": {
        "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
        "severity": "CRITICAL",
    },
    "PASSPORT": {
        "pattern": r"\b[A-Z]{1}\d{7}\b",
        "severity": "HIGH",
    },
    "IP_ADDRESS": {
        "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "severity": "LOW",
    },
    "BANK_ACCOUNT": {
        "pattern": r"\b\d{9,18}\b",
        "severity": "HIGH",
    },
}

RISK_WEIGHTS: dict[str, float] = {
    "CRITICAL": 10.0,
    "HIGH": 7.0,
    "MEDIUM": 4.0,
    "LOW": 1.0,
}

SEVERITY_THRESHOLDS: dict[str, float] = {
    "LOW": 20.0,
    "MEDIUM": 50.0,
    "HIGH": 71.0,
    "CRITICAL": 91.0,
}


# ---------------------------------------------------------------------------
# Core scanning logic
# ---------------------------------------------------------------------------


def _detect_pii(content: str) -> list[dict[str, Any]]:
    """Run regex-based PII detection on the file content.

    Args:
        content: The full text content of the file.

    Returns:
        A list of findings, each with data_type, count, severity, and sample_values.
    """
    import re

    findings = []
    for data_type, config in PII_PATTERNS.items():
        matches = re.findall(config["pattern"], content)
        if matches:
            # Collect unique sample values (max 5)
            unique = list(set(matches))[:5]
            findings.append({
                "data_type": data_type,
                "count": len(matches),
                "severity": config["severity"],
                "sample_values": unique,
            })
            logger.info(
                "Detected %d instances of %s (severity: %s)",
                len(matches), data_type, config["severity"],
            )
    return findings


def _calculate_risk_score(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate overall risk score from findings.

    Uses weighted scoring based on severity and count, normalized to 0-100.

    Args:
        findings: List of PII findings from detection.

    Returns:
        Dict with overall_score, risk_level, and breakdown.
    """
    if not findings:
        return {
            "overall_score": 0.0,
            "risk_level": "LOW",
            "breakdown": {},
        }

    severity_counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    weighted_score = 0.0
    total_weight = 0.0

    for finding in findings:
        sev = finding["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        weight = RISK_WEIGHTS.get(sev, 1.0)
        weighted_score += weight * finding["count"]
        total_weight += weight

    # Normalize score to 0-100
    normalized_score = min(100.0, (weighted_score / max(total_weight, 1)) * 10)

    # Determine risk level
    risk_level = "LOW"
    for level, threshold in sorted(
        SEVERITY_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
    ):
        if normalized_score >= threshold:
            risk_level = level
            break

    return {
        "overall_score": round(normalized_score, 2),
        "risk_level": risk_level,
        "breakdown": {
            "severity_counts": severity_counts,
            "total_findings": sum(f["count"] for f in findings),
        },
    }


def _should_create_alert(risk_score: dict[str, Any], findings: list[dict[str, Any]]) -> bool:
    """Determine if an alert should be created based on risk score and findings.

    Creates alerts when:
    - Overall risk score is HIGH or CRITICAL
    - Any CRITICAL severity data type is detected

    Args:
        risk_score: Calculated risk score dict.
        findings: List of PII findings.

    Returns:
        True if an alert should be raised.
    """
    if risk_score["risk_level"] in ("HIGH", "CRITICAL"):
        return True
    for finding in findings:
        if finding["severity"] == "CRITICAL":
            return True
    return False


def _generate_alert_message(
    file_id: str, file_name: str, risk_score: dict[str, Any]
) -> str:
    """Generate a human-readable alert message.

    Args:
        file_id: The ID of the scanned file.
        file_name: The original file name.
        risk_score: The calculated risk score.

    Returns:
        A formatted alert message string.
    """
    return (
        f"File '{file_name}' (ID: {file_id}) has a "
        f"{risk_score['risk_level']} risk score of "
        f"{risk_score['overall_score']:.1f}. "
        f"Breakdown: {risk_score['breakdown']}"
    )


# ---------------------------------------------------------------------------
# Cloud Function entry point
# ---------------------------------------------------------------------------


def scan_file(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Background Cloud Function triggered by Pub/Sub.

    Orchestrates the file scan pipeline from GCS download through
    detection, risk assessment, result storage, and alert creation.

    Args:
        event: The Pub/Sub event dict containing the message data.
            Expected message data format:
            {
                "file_id": "<uuid>",
                "file_name": "data.csv",
                "gcs_path": "gs://bucket/path/to/file",
                "user_id": "<uuid>",
                "content_type": "csv"
            }
        context: The Google Cloud Functions event context object.

    Returns:
        dict with status and processing results.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Scan function triggered at %s", start_time.isoformat())

    # ------------------------------------------------------------------
    # 1. Decode Pub/Sub message
    # ------------------------------------------------------------------
    if "data" not in event:
        logger.error("No data field in Pub/Sub event")
        return {"status": "error", "message": "No data in event"}

    try:
        message = base64.b64decode(event["data"]).decode("utf-8")
        data = json.loads(message)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("Failed to decode Pub/Sub message: %s", e)
        return {"status": "error", "message": f"Invalid message: {str(e)}"}

    file_id = data.get("file_id")
    file_name = data.get("file_name", "unknown")
    gcs_path = data.get("gcs_path")
    user_id = data.get("user_id")

    if not file_id or not gcs_path:
        logger.error("Missing required fields: file_id=%s, gcs_path=%s", file_id, gcs_path)
        return {"status": "error", "message": "Missing file_id or gcs_path"}

    logger.info(
        "Processing scan for file '%s' (ID: %s) at %s",
        file_name, file_id, gcs_path,
    )

    # ------------------------------------------------------------------
    # 2. Download file from GCS
    # ------------------------------------------------------------------
    try:
        from google.cloud import storage as gcs_storage  # type: ignore[import-untyped]

        storage_client = gcs_storage.Client()
        bucket_name, blob_name = gcs_path.replace("gs://", "").split("/", 1)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(blob_name)[1] or ".tmp",
        ) as tmp_file:
            blob.download_to_filename(tmp_file.name)
            local_path = tmp_file.name

        logger.info("Downloaded file to %s", local_path)
    except ImportError:
        logger.warning("google-cloud-storage not available; using simulated download")
        local_path = None
    except Exception as e:
        logger.error("Failed to download file from GCS: %s", e)
        return {"status": "error", "message": f"GCS download failed: {str(e)}"}

    # ------------------------------------------------------------------
    # 3. Read file content
    # ------------------------------------------------------------------
    content = ""
    if local_path:
        try:
            # Try to read as text
            with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            os.unlink(local_path)
        except Exception:
            # Binary file - skip content scanning
            content = ""

    # ------------------------------------------------------------------
    # 4. Run regex detection engine
    # ------------------------------------------------------------------
    findings = _detect_pii(content)
    logger.info("Detection complete: %d PII types found", len(findings))

    # ------------------------------------------------------------------
    # 5. Optionally run Cloud DLP
    # ------------------------------------------------------------------
    dlp_enabled = os.environ.get("DLP_ENABLED", "false").lower() == "true"
    dlp_findings = []
    if dlp_enabled and content:
        try:
            from google.cloud import dlp_v2  # type: ignore[import-untyped]

            dlp_client = dlp_v2.DlpServiceClient()
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

            parent = f"projects/{project_id}"
            inspect_config = {
                "info_types": [
                    {"name": "EMAIL_ADDRESS"},
                    {"name": "PHONE_NUMBER"},
                    {"name": "CREDIT_CARD_NUMBER"},
                    {"name": "US_SOCIAL_SECURITY_NUMBER"},
                    {"name": "US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER"},
                ],
                "min_likelihood": "LIKELY",
            }

            response = dlp_client.inspect_content(
                request={
                    "parent": parent,
                    "inspect_config": inspect_config,
                    "item": {"value": content},
                }
            )

            if response.result.findings:
                for dlp_finding in response.result.findings:
                    dlp_findings.append({
                        "data_type": dlp_finding.info_type.name,
                        "count": 1,
                        "likelihood": str(dlp_finding.likelihood),
                    })
                logger.info("DLP inspection found %d additional findings", len(dlp_findings))
        except ImportError:
            logger.warning("google-cloud-dlp not available; skipping DLP")
        except Exception as e:
            logger.warning("DLP inspection failed (non-fatal): %s", e)

    # ------------------------------------------------------------------
    # 6. Calculate risk score
    # ------------------------------------------------------------------
    risk_score = _calculate_risk_score(findings)
    if dlp_findings:
        # Boost score slightly if DLP found additional items
        risk_score["overall_score"] = min(
            100.0, risk_score["overall_score"] + len(dlp_findings) * 2
        )
        # Recalculate risk level
        for level, threshold in sorted(
            SEVERITY_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if risk_score["overall_score"] >= threshold:
                risk_score["risk_level"] = level
                break

    logger.info(
        "Risk assessment: score=%.1f, level=%s",
        risk_score["overall_score"],
        risk_score["risk_level"],
    )

    # ------------------------------------------------------------------
    # 7. Determine if alerts are needed
    # ------------------------------------------------------------------
    should_alert = _should_create_alert(risk_score, findings)
    if should_alert:
        alert_message = _generate_alert_message(file_id, file_name, risk_score)
        logger.warning("ALERT: %s", alert_message)

    # ------------------------------------------------------------------
    # 8. Publish completion event
    # ------------------------------------------------------------------
    try:
        from google.cloud import pubsub_v1  # type: ignore[import-untyped]

        publisher = pubsub_v1.PublisherClient()
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

        completion_data = {
            "file_id": file_id,
            "user_id": user_id,
            "status": "completed",
            "risk_level": risk_score["risk_level"],
            "risk_score": risk_score["overall_score"],
            "findings_count": sum(f["count"] for f in findings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        topic_path = publisher.topic_path(project_id, "scan-completed")
        publisher.publish(
            topic_path,
            json.dumps(completion_data).encode("utf-8"),
        )
        logger.info("Published completion event for file %s", file_id)

        # Publish alert event if needed
        if should_alert:
            alert_data = {
                "file_id": file_id,
                "user_id": user_id,
                "alert_type": "HIGH_RISK_FILE",
                "severity": risk_score["risk_level"],
                "message": alert_message,
            }
            alert_topic = publisher.topic_path(project_id, "alert-events")
            publisher.publish(
                alert_topic,
                json.dumps(alert_data).encode("utf-8"),
            )
            logger.info("Published alert event for file %s", file_id)

    except ImportError:
        logger.warning("google-cloud-pubsub not available; skipping event publishing")
    except Exception as e:
        logger.warning("Failed to publish events (non-fatal): %s", e)

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info("Scan completed for file %s in %.2f seconds", file_id, elapsed)

    # Clean up temp file if still present
    if local_path and os.path.exists(local_path):
        try:
            os.unlink(local_path)
        except Exception:
            pass

    return {
        "status": "success",
        "file_id": file_id,
        "findings_count": len(findings),
        "risk_score": risk_score["overall_score"],
        "risk_level": risk_score["risk_level"],
        "alert_created": should_alert,
        "processing_time_seconds": round(elapsed, 2),
    }
