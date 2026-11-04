"""
AquaSense AI - Intelligent Water Quality Recommendations Router
Provides REST endpoints to retrieve active recommendations, historical logs,
trigger on-demand evaluations, and dismiss active advisories.
"""

from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, Dict, Any, List
from services.recommendation_service import recommendation_service
from models.recommendation import (
    RecommendationSummaryResponse,
    DismissRecommendationRequest
)

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

@router.get("", summary="Get current intelligent water quality recommendations", response_model=RecommendationSummaryResponse)
async def get_recommendations(
    priority: Optional[str] = Query(None, description="Filter by priority: Critical, Warning, or Informational"),
    category: Optional[str] = Query(None, description="Filter by category"),
    include_dismissed: bool = Query(False, description="Whether to include dismissed recommendations")
):
    """
    Returns active prioritized water quality recommendations synthesized from
    instantaneous sensor readings, historical analytics, ML anomalies, and filter health.
    """
    return await recommendation_service.get_active_recommendations(
        priority=priority,
        category=category,
        include_dismissed=include_dismissed
    )

@router.get("/history", summary="Get recommendation history log")
async def get_recommendation_history(
    limit: int = Query(50, ge=1, le=200, description="Max number of historical records to return")
):
    """Returns chronological audit log of all generated recommendations."""
    history = await recommendation_service.get_recommendation_history(limit=limit)
    return {
        "status": "success",
        "count": len(history),
        "data": history
    }

@router.post("/evaluate", summary="Force on-demand recommendation evaluation")
async def evaluate_recommendations():
    """Forces an immediate multi-factor evaluation across all sensor and filter telemetry."""
    recs = await recommendation_service.evaluate_and_generate_recommendations(trigger_broadcast=True)
    summary = recommendation_service._build_summary_response(recs)
    return {
        "status": "success",
        "message": f"Evaluated {len(recs)} active recommendation(s).",
        "data": summary
    }

@router.post("/{rec_id}/dismiss", summary="Dismiss or acknowledge an active recommendation")
async def dismiss_recommendation(
    rec_id: str,
    req: Optional[DismissRecommendationRequest] = Body(None)
):
    """Acknowledge or dismiss an active recommendation so it no longer appears in the active list."""
    dismissed_by = req.dismissed_by if req and req.dismissed_by else "User"
    success = await recommendation_service.dismiss_recommendation(rec_id=rec_id, dismissed_by=dismissed_by)
    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found or already dismissed.")
    return {
        "status": "success",
        "message": "Recommendation dismissed successfully.",
        "id": rec_id
    }

