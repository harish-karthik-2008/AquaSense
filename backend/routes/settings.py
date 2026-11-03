from fastapi import APIRouter
from models.settings import ThresholdSettings
from services.sensor_service import sensor_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("", summary="Get current threshold configurations")
async def get_settings():
    """Retrieve warning and critical threshold values for TDS, pH, and Turbidity."""
    settings = await sensor_service.get_settings()
    if "_id" in settings:
        del settings["_id"]
    return {
        "status": "success",
        "data": settings
    }

@router.post("", summary="Update threshold configurations")
async def update_settings(settings: ThresholdSettings):
    """Update system thresholds and AI sensitivity settings."""
    updated = await sensor_service.update_settings(settings.model_dump())
    if "_id" in updated:
        del updated["_id"]
    return {
        "status": "success",
        "message": "Threshold configurations updated successfully.",
        "data": updated
    }

