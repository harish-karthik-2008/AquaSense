"""
AquaSense AI - Analytics Route
Provides historical water-quality analytics, aggregates, trends, and summaries.
"""

from fastapi import APIRouter, Query
from typing import Optional
from services.sensor_service import sensor_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("", summary="Get historical water quality analytics and trends")
@router.get("/summary", summary="Get historical water quality analytics and trends (alias)")
async def get_analytics_summary(
    timeframe: Optional[str] = Query("24h", description="Timeframe filter: 1h, 24h, 7d, 30d, all"),
    start_date: Optional[str] = Query(None, description="Start date ISO string (e.g. 2026-11-01)"),
    end_date: Optional[str] = Query(None, description="End date ISO string (e.g. 2026-11-03)")
):
    """
    Returns statistical metrics (min, max, avg for TDS, pH, Turbidity),
    total readings count, status counts (Normal, Warning, Critical) & percentages,
    daily/weekly trends, frequently occurring anomalies, most abnormal parameter,
    and plain-English water quality summary.
    """
    summary = await sensor_service.get_analytics_summary(
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date
    )
    return {
        "status": "success",
        "data": summary
    }

