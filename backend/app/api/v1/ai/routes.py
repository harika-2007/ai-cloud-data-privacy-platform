"""AI Compliance recommendation API routes."""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.scan_repository import ScanResultRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.ai import AIRecommendationResponse, AISummaryResponse, AIChatRequest, AIChatResponse
from app.schemas.auth import TokenPayload
from app.services.ai.ai_service import AIService
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/recommend/{file_id}", response_model=AIRecommendationResponse)
async def get_ai_recommendations(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    scan_repo = ScanResultRepository(db)
    risk_repo = RiskAssessmentRepository(db)
    ai_service = AIService()

    # Fetch results
    scan_results, _ = await scan_repo.get_by_file_id(file_id, 0, 1000)
    if not scan_results:
        raise NotFoundException("Scan results", file_id)

    results_list = [
        {"data_type": r.data_type, "count": r.count, "severity": r.severity}
        for r in scan_results
    ]

    risk = await risk_repo.get_latest_by_file_id(file_id)
    risk_dict = {
        "overall_score": risk.overall_score,
        "risk_level": risk.risk_level,
        "explanation": risk.explanation,
    } if risk else None

    recommendations = await ai_service.generate_recommendations(file_id, results_list, risk_dict)
    return recommendations


@router.post("/summary/{file_id}", response_model=AISummaryResponse)
async def get_ai_summary(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    scan_repo = ScanResultRepository(db)
    risk_repo = RiskAssessmentRepository(db)
    ai_service = AIService()

    scan_results, _ = await scan_repo.get_by_file_id(file_id, 0, 1000)
    results_list = [
        {"data_type": r.data_type, "count": r.count, "severity": r.severity}
        for r in scan_results
    ]

    risk = await risk_repo.get_latest_by_file_id(file_id)
    risk_dict = {
        "overall_score": risk.overall_score,
        "risk_level": risk.risk_level,
    } if risk else None

    summary = await ai_service.generate_summary(file_id, results_list, risk_dict)
    return summary


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Send a message to the AI Compliance Assistant."""
    ai_service = AIService()
    result = await ai_service.chat(request.message, request.conversation_history)
    return result


@router.post("/executive-report")
async def get_executive_report(
    file_ids: list[str],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.services.ai.ai_service import AIService
    scan_repo = ScanResultRepository(db)
    risk_repo = RiskAssessmentRepository(db)
    ai_service = AIService()

    all_results = []
    all_risks = []

    for file_id in file_ids:
        results, _ = await scan_repo.get_by_file_id(file_id, 0, 1000)
        all_results.extend([
            {"data_type": r.data_type, "count": r.count, "severity": r.severity}
            for r in results
        ])
        risk = await risk_repo.get_latest_by_file_id(file_id)
        if risk:
            all_risks.append({
                "score": risk.overall_score,
                "level": risk.risk_level,
            })

    risk_summary = {
        "overall_score": sum(r["score"] for r in all_risks) / len(all_risks) if all_risks else 0,
        "risk_level": "HIGH" if any(r["level"] == "HIGH" for r in all_risks) else "MEDIUM",
    } if all_risks else None

    report = await ai_service.generate_executive_report(all_results, risk_summary)
    return {"report": report}
