"""Pydantic schemas for AI compliance module."""

from typing import Any, Optional
from pydantic import BaseModel


class AIRecommendationRequest(BaseModel):
    """Request for AI compliance recommendations."""
    file_id: str


class ComplianceRecommendation(BaseModel):
    """Single compliance recommendation."""
    category: str
    finding: str
    severity: str
    recommendation: str
    priority: str


class AIRecommendationResponse(BaseModel):
    """AI-generated compliance recommendations response."""
    risk_summary: str
    compliance_impact: str
    recommended_actions: list[str]
    executive_summary: str
    detailed_recommendations: list[ComplianceRecommendation]


class AIChatRequest(BaseModel):
    """Request for an AI chat query."""
    message: str
    conversation_history: Optional[list[dict[str, Any]]] = None


class AIChatResponse(BaseModel):
    """Response from the AI chat assistant."""
    response: str


class AISummaryResponse(BaseModel):
    """AI-generated summary response."""
    summary: str
    key_findings: list[str]
    risk_level: str
    suggested_actions: list[str]
