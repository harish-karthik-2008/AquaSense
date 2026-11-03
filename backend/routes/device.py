from fastapi import APIRouter
from services.sensor_service import sensor_service
from database.connection import DatabaseManager

router = APIRouter(prefix="/api/device", tags=["Device"])

@router.get("/status", summary="Get ESP32 device connectivity status")
async def get_device_status():
    """
    Returns real-time connection status of the ESP32 microcontroller,
    last heartbeat received timestamp, and simulation configuration.
    """
    dev_status = await sensor_service.get_device_status()
    db_status = await DatabaseManager.get_status()
    dev_status["database"] = db_status
    return {
        "status": "success",
        "data": dev_status
    }

