from fastapi import APIRouter
from services.filter_service import filter_service

router = APIRouter(prefix="/api/filter-health", tags=["Filter Health"])

@router.get("", summary="Get predictive filter health information")
async def get_filter_health():
    """
    Returns condition percentages for multi-stage purifier filters,
    operating hours, and maintenance schedule.
    Clearly indicates simulated telemetry model for hackathon demonstration.
    """
    data = await filter_service.get_filter_health()
    return {
        "status": "success",
        "data": data
    }

@router.post("/reset", summary="Simulate purifier filter replacement")
async def reset_filter_health():
    """Reset filter conditions to 100% after simulating physical filter service."""
    refreshed = await filter_service.reset_filters()
    return {
        "status": "success",
        "message": "Purifier filter lifecycle reset to 100% optimal condition.",
        "data": refreshed
    }

