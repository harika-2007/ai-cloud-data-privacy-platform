"""AI Compliance Service.

Integrates with Ollama (Llama 3 / Qwen) to generate privacy compliance
recommendations, risk summaries, and executive reports based on scan findings.
"""

import json
import logging
from typing import Any, Optional

import httpx

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered compliance analysis via Ollama."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.enabled = settings.AI_ENABLED
        self.timeout = settings.OLLAMA_TIMEOUT

    async def generate_recommendations(
        self, file_id: str, scan_results: list[dict], risk_assessment: Optional[dict] = None
    ) -> dict:
        """Generate AI compliance recommendations from scan findings.

        When AI is disabled, returns intelligent fallback recommendations
        derived from the actual detected PII types.
        """
        if not self.enabled:
            return self._default_recommendations(scan_results)

        prompt = self._build_recommendation_prompt(scan_results, risk_assessment)
        response = await self._call_ollama(prompt)
        result = self._parse_recommendations(response, scan_results)
        # If parsing failed (e.g. model returned garbage), fall back
        if not result.get("recommended_actions"):
            return self._default_recommendations(scan_results)
        return result

    async def generate_summary(
        self, file_id: str, scan_results: list[dict], risk_assessment: Optional[dict] = None
    ) -> dict:
        """Generate a concise AI summary of findings."""
        if not self.enabled:
            return self._default_summary()

        prompt = self._build_summary_prompt(scan_results, risk_assessment)
        response = await self._call_ollama(prompt)
        return self._parse_summary(response, scan_results)

    async def get_compliance_recommendations(
        self, file_id: str = "", scan_results: list[dict] | None = None, risk_assessment: dict | None = None
    ) -> dict:
        """Get compliance recommendations, either from scan results or defaults.

        This method is called by the report service. When scan_results are
        not provided, returns a placeholder dict with a 'recommendations' key.

        Args:
            file_id: UUID of the file (for logging).
            scan_results: Optional list of finding dicts.
            risk_assessment: Optional risk assessment dict.

        Returns:
            A dict with at minimum a 'recommendations' key.
        """
        if scan_results:
            result = await self.generate_recommendations(
                file_id=file_id,
                scan_results=scan_results,
                risk_assessment=risk_assessment,
            )
        else:
            result = self._default_recommendations()
        return {"recommendations": result.get("executive_summary", "")}

    async def generate_executive_report(
        self, scan_results: list[dict], risk_assessment: Optional[dict] = None
    ) -> str:
        """Generate a comprehensive executive report."""
        if not self.enabled:
            return "AI integration is disabled. Enable AI in settings to generate executive reports."

        prompt = self._build_executive_prompt(scan_results, risk_assessment)
        response = await self._call_ollama(prompt)
        return response.get("response", "")

    def _build_recommendation_prompt(
        self, scan_results: list[dict], risk_assessment: Optional[dict] = None
    ) -> str:
        findings_text = "\n".join(
            f"- {r['data_type']}: {r['count']} occurrences (Severity: {r['severity']})"
            for r in scan_results
        )
        risk_text = ""
        if risk_assessment:
            risk_text = (
                f"\nRisk Score: {risk_assessment.get('overall_score', 'N/A')}\n"
                f"Risk Level: {risk_assessment.get('risk_level', 'N/A')}\n"
            )

        return f"""You are a Data Privacy Compliance Expert. Analyze these findings and provide recommendations.

SCAN FINDINGS:
{findings_text}
{risk_text}

Provide a structured response with:
1. Risk Summary (2-3 sentences)
2. Compliance Impact (specific regulations affected)
3. Recommended Actions (3-5 specific steps)
4. Executive Summary (1 paragraph)

Format your response as JSON with these exact keys:
- risk_summary: string
- compliance_impact: string
- recommended_actions: list of strings
- executive_summary: string
- detailed_recommendations: list of {{category, finding, severity, recommendation, priority}}"""

    def _build_summary_prompt(
        self, scan_results: list[dict], risk_assessment: Optional[dict] = None
    ) -> str:
        findings_text = "\n".join(
            f"- {r['data_type']}: {r['count']} occurrences"
            for r in scan_results
        )
        return f"""As a privacy compliance expert, summarize these data scan findings:

FINDINGS:
{findings_text}
Risk Score: {risk_assessment.get('overall_score', 'N/A') if risk_assessment else 'N/A'}
Risk Level: {risk_assessment.get('risk_level', 'N/A') if risk_assessment else 'N/A'}

Provide JSON response with: summary, key_findings (list), risk_level, suggested_actions (list)"""

    def _build_executive_prompt(
        self, scan_results: list[dict], risk_assessment: Optional[dict] = None
    ) -> str:
        findings_text = "\n".join(
            f"- {r['data_type']}: {r['count']} occurrences (Severity: {r['severity']})"
            for r in scan_results
        )
        risk_text = ""
        if risk_assessment:
            risk_text = (
                f"\nOverall Risk Score: {risk_assessment.get('overall_score', 'N/A')}\n"
                f"Risk Classification: {risk_assessment.get('risk_level', 'N/A')}\n"
                f"Explanation: {risk_assessment.get('explanation', 'N/A')}\n"
            )
        return f"""Generate a comprehensive executive compliance report:

{risk_text}

FINDINGS:
{findings_text}

Write a professional report covering:
- Executive Summary
- Key Risk Areas
- Compliance Posture
- Recommended Remediations
- Strategic Roadmap"""

    async def _call_ollama(self, prompt: str) -> dict:
        """Call Ollama API with the given prompt."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.3,
                        "max_tokens": 2048,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            return {"response": ""}
        except httpx.RequestError as e:
            logger.error(f"Ollama request failed: {e}")
            return {"response": ""}
        except Exception as e:
            logger.exception(f"Unexpected Ollama error: {e}")
            return {"response": ""}

    def _parse_recommendations(self, ollama_response: dict, scan_results: list[dict]) -> dict:
        """Parse Ollama response into structured recommendations."""
        try:
            text = ollama_response.get("response", "")
            # Try to extract JSON from the response
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(text[json_start:json_end])
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse AI recommendations JSON")
        return self._default_recommendations(scan_results)

    def _parse_summary(self, ollama_response: dict, scan_results: list[dict]) -> dict:
        """Parse Ollama response into structured summary."""
        try:
            text = ollama_response.get("response", "")
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(text[json_start:json_end])
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse AI summary JSON")
        return self._default_summary()

    def _default_recommendations(self, scan_results: list[dict] | None = None) -> dict:
        """Intelligent fallback recommendations based on detected PII types.

        When AI/LLM is unavailable, this method generates compliance
        recommendations derived from the actual scan findings, so the
        frontend never shows a blank state.
        """
        found_types = {r.get("data_type", "").lower() for r in (scan_results or [])}
        has_aadhaar = "aadhaar" in found_types
        has_pan = "pan" in found_types
        has_credit = "creditcard" in found_types or "credit_card" in found_types
        has_passport = "passport" in found_types
        has_email = "email" in found_types
        has_phone = "phone" in found_types
        has_address = "address" in found_types
        has_dob = "dob" in found_types
        high_risk = has_aadhaar or has_pan or has_credit or has_passport

        actions: list[dict] = []

        # --- PII-specific remediation steps ---
        if has_aadhaar:
            actions.append({
                "category": "Aadhaar",
                "finding": "Aadhaar numbers detected in file",
                "severity": "CRITICAL",
                "recommendation": "Mask Aadhaar numbers (show only last 4 digits) in stored records. "
                                   "Restrict access to authorized personnel only. Implement "
                                   "purpose-limited data collection per Aadhaar Act 2016.",
                "priority": "critical",
            })
        if has_pan:
            actions.append({
                "category": "PAN",
                "finding": "PAN card numbers detected",
                "severity": "HIGH",
                "recommendation": "Encrypt PAN fields at rest. Mask to last 4 characters. "
                                   "Ensure compliance with Income Tax Act 1961 Section 139A.",
                "priority": "high",
            })
        if has_credit:
            actions.append({
                "category": "Credit Card",
                "finding": "Credit card numbers detected (PCI-DSS scope)",
                "severity": "CRITICAL",
                "recommendation": "Never store full PAN (Primary Account Number) after authorization. "
                                   "Tokenize or truncate to last 4 digits. Maintain PCI-DSS compliance.",
                "priority": "critical",
            })
        if has_passport:
            actions.append({
                "category": "Passport",
                "finding": "Passport numbers detected",
                "severity": "HIGH",
                "recommendation": "Encrypt passport number fields at rest. Mask to last 4 characters. "
                                   "Limit access to authorized personnel only. Ensure compliance with "
                                   "identity document handling regulations.",
                "priority": "high",
            })
        if has_email:
            actions.append({
                "category": "Email",
                "finding": "Email addresses detected",
                "severity": "LOW",
                "recommendation": "Encrypt email fields at rest. Anonymize where possible. "
                                   "Ensure CAN-SPAM Act and GDPR Article 5 compliance for storage and processing.",
                "priority": "medium",
            })
        if has_phone:
            actions.append({
                "category": "Phone",
                "finding": "Phone numbers detected",
                "severity": "MEDIUM",
                "recommendation": "Mask phone numbers (show last 4 digits). Encrypt at rest. "
                                   "Limit access on a need-to-know basis.",
                "priority": "medium",
            })
        if has_address:
            actions.append({
                "category": "Address",
                "finding": "Physical addresses detected",
                "severity": "MEDIUM",
                "recommendation": "Encrypt address fields at rest. Anonymize where possible. "
                                   "Restrict access on a need-to-know basis. GDPR Article 5 "
                                   "requires data minimisation — only store addresses where "
                                   "necessary for service delivery.",
                "priority": "medium",
            })
        if has_dob:
            actions.append({
                "category": "Date of Birth",
                "finding": "Dates of birth detected",
                "severity": "MEDIUM",
                "recommendation": "Encrypt DOB fields at rest. Mask to year-only where full date "
                                   "is not required. Limit access on a need-to-know basis.",
                "priority": "medium",
            })

        # --- General compliance controls ---
        general_actions = [
            {
                "category": "Access Control",
                "finding": "Sensitive data stored without access restrictions",
                "severity": "HIGH",
                "recommendation": "Enable Role-Based Access Control (RBAC) to restrict "
                                   "file access to authorized users only.",
                "priority": "high",
            },
            {
                "category": "Encryption",
                "finding": "Detected PII should be encrypted before cloud storage",
                "severity": "HIGH",
                "recommendation": "Encrypt detected PII before persisting to cloud storage. "
                                   "Use AES-256 for data at rest and TLS 1.3 for data in transit.",
                "priority": "high",
            },
            {
                "category": "Audit Logging",
                "finding": "Compliance requires audit trail for PII access",
                "severity": "MEDIUM",
                "recommendation": "Enable audit logging for all access to files containing PII. "
                                   "Log who accessed what and when for compliance reporting.",
                "priority": "medium",
            },
            {
                "category": "Public Access",
                "finding": "Risk of unintended public data exposure",
                "severity": "HIGH",
                "recommendation": "Restrict public access to storage buckets. Apply "
                                   "least-privilege IAM policies and block public ACLs.",
                "priority": "high",
            },
            {
                "category": "Compliance",
                "finding": "GDPR Article 32 requires security of processing",
                "severity": "MEDIUM",
                "recommendation": "Apply GDPR Article 32 controls: pseudonymisation, "
                                   "encryption, confidentiality, availability, and "
                                   "regular testing of security measures.",
                "priority": "medium",
            },
        ]
        actions.extend(general_actions)

        # Build summary text
        if high_risk:
            risk_summary = (
                f"File contains sensitive PII including "
                f"{'Aadhaar ' if has_aadhaar else ''}"
                f"{'PAN ' if has_pan else ''}"
                f"{'Passport ' if has_passport else ''}"
                f"{'and credit card numbers ' if has_credit else ''}"
                f"which require immediate remediation. "
                f"Apply encryption, masking, and strict access controls."
            )
            compliance_impact = (
                "Aadhaar Act 2016, IT Act 2000, and PCI-DSS regulations apply. "
                "Non-compliance may result in penalties and legal liability."
            )
        elif has_email or has_phone or has_address or has_dob:
            risk_summary = (
                "File contains personal information including "
                f"{'email addresses ' if has_email else ''}"
                f"{'phone numbers ' if has_phone else ''}"
                f"{'addresses ' if has_address else ''}"
                f"{'dates of birth ' if has_dob else ''}. "
                "While lower risk than financial identifiers, GDPR and data "
                "protection laws require justified processing and consent tracking."
            )
            compliance_impact = (
                "GDPR Articles 5-7 (lawful processing) and CAN-SPAM Act apply. "
                "Maintain processing records and provide data subject access."
            )
        else:
            risk_summary = (
                "No high-severity PII detected in this file. Existing security "
                "controls should be reviewed periodically to maintain compliance."
            )
            compliance_impact = (
                "Standard data protection obligations apply. Regular compliance "
                "audits are recommended."
            )

        return {
            "risk_summary": risk_summary,
            "compliance_impact": compliance_impact,
            "recommended_actions": [a["recommendation"] for a in actions if a["priority"] in ("critical", "high")],
            "executive_summary": (
                f"Risk level: {'HIGH' if high_risk else 'MEDIUM' if (has_email or has_phone or has_address or has_dob) else 'LOW'}. "
                f"This analysis provides {(len(actions))} specific remediation steps tailored to the "
                f"detected data types. AI-powered deep analysis is available when Ollama LLM is enabled."
            ),
            "detailed_recommendations": actions,
        }

    async def chat(self, message: str, conversation_history: list[dict] | None = None) -> dict:
        """Handle a general AI chat query from the AI Assistant."""
        if not self.enabled:
            return self._default_chat_response()

        history_text = ""
        if conversation_history:
            history_text = "\n".join(
                f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')}"
                for m in conversation_history[-10:]  # last 10 messages for context
            )

        prompt = f"""You are a Data Privacy Compliance Expert AI assistant for the SecureCloud platform.
You help users understand compliance requirements, data protection regulations, and security best practices.

{history_text}

User: {message}

Provide a helpful, concise response about data privacy compliance.
If the question is off-topic (not about privacy, security, compliance, or data protection),
politely redirect to privacy compliance topics.
Keep responses under 200 words and practical.

Response:"""

        response = await self._call_ollama(prompt)
        text = response.get("response", "").strip()
        if not text:
            return self._default_chat_response()
        return {"response": text}

    def _default_chat_response(self) -> dict:
        """Default response when AI assistant is unavailable."""
        return {
            "response": (
                "**AI Assistant is temporarily unavailable.**\n\n"
                "I can't connect to the AI model right now. This could be because:\n"
                "- Ollama is not running on the server\n"
                "- The AI service is disabled in settings\n"
                "- The model is still loading\n\n"
                "Please try again later or contact your system administrator."
            )
        }

    def _default_summary(self) -> dict:
        """Default summary when AI is unavailable."""
        return {
            "summary": "AI-powered summary unavailable. AI service is disabled or unreachable.",
            "key_findings": [],
            "risk_level": "Unknown",
            "suggested_actions": ["Enable AI service for automated analysis"],
        }
