"""
AquaSense AI - Filter Health Router
Provides endpoints for predictive filter health evaluation, historical wear analysis,
maintenance recommendations, configurable thresholds, and service history logs.
"""

from fastapi import APIRouter, Query, Body
from typing import Optional, Dict, Any
from services.filter_service import filter_service
from services.sensor_service import sensor_service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/filter-health", tags=["Filter Health"])

class ResetFilterRequest(BaseModel):
    technician: Optional[str] = "Simulated Service / User"
    notes: Optional[str] = "Simulated cartridge replacement completed."

class FilterThresholdsInput(BaseModel):
    filter_warning_threshold: Optional[float] = Field(None, ge=5.0, le=90.0)
    filter_critical_threshold: Optional[float] = Field(None, ge=1.0, le=50.0)
    filter_max_operating_hours: Optional[float] = Field(None, ge=100.0, le=10000.0)

@router.get("", summary="Get predictive filter health information")
async def get_filter_health():
    """
    Returns estimated filter health percentage, filter condition,
    usage duration, last maintenance date, maintenance recommendation,
    and reason for recommendation.
    """
    data = await filter_service.get_filter_health()
    return {
        "status": "success",
        "data": data
    }

@router.post("/reset", summary="Simulate purifier filter replacement")
async def reset_filter_health(req: Optional[ResetFilterRequest] = Body(None)):
    """Reset filter conditions to 100% after simulating physical filter service."""
    tech = req.technician if req and req.technician else "Simulated Service / User"
    notes = req.notes if req and req.notes else "Simulated cartridge replacement completed."
    refreshed = await filter_service.reset_filters(technician=tech, notes=notes)
    return {
        "status": "success",
        "message": "Purifier filter lifecycle reset to 100% optimal condition.",
        "data": refreshed
    }

@router.get("/history", summary="Get filter usage history snapshots")
async def get_filter_usage_history(limit: int = Query(50, ge=1, le=200)):
    """Returns chronological snapshots of filter usage, runtime, and condition."""
    history = await filter_service.get_usage_history(limit=limit)
    return {
        "status": "success",
        "count": len(history),
        "data": history
    }

@router.get("/maintenance-log", summary="Get filter maintenance service logs")
async def get_filter_maintenance_logs(limit: int = Query(20, ge=1, le=100)):
    """Returns records of historical cartridge replacements, resets, and inspections."""
    logs = await filter_service.get_maintenance_logs(limit=limit)
    return {
        "status": "success",
        "count": len(logs),
        "data": logs
    }

@router.get("/thresholds", summary="Get filter maintenance warning thresholds")
async def get_filter_thresholds():
    """Returns current configurable maintenance warning thresholds."""
    settings = await sensor_service.get_settings()
    return {
        "status": "success",
        "data": {
            "filter_warning_threshold": settings.get("filter_warning_threshold", 30.0),
            "filter_critical_threshold": settings.get("filter_critical_threshold", 15.0),
            "filter_max_operating_hours": settings.get("filter_max_operating_hours", 2000.0)
        }
    }

@router.post("/thresholds", summary="Update filter maintenance warning thresholds")
async def update_filter_thresholds(input_data: FilterThresholdsInput):
    """Update configurable maintenance thresholds for filter health."""
    updates = {k: v for k, v in input_data.model_dump().items() if v is not None}
    updated = await sensor_service.update_settings(updates)
    return {
        "status": "success",
        "message": "Filter maintenance thresholds updated successfully.",
        "data": {
            "filter_warning_threshold": updated.get("filter_warning_threshold", 30.0),
            "filter_critical_threshold": updated.get("filter_critical_threshold", 15.0),
            "filter_max_operating_hours": updated.get("filter_max_operating_hours", 2000.0)
        }
    }
