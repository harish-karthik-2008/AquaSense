from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from models.sensor import SensorReadingInput
from services.sensor_service import sensor_service

router = APIRouter(prefix="/api/sensor-data", tags=["Sensor Data"])

@router.post("", summary="Receive simulated sensor readings from ESP32")
async def receive_sensor_data(data: SensorReadingInput):
    """
    Endpoint for ESP32 (Wokwi simulator) to post live sensor readings:
    - TDS (ppm)
    - pH (0-14 scale)
    - Turbidity (simulated scale)
    """
    try:
        saved_record = await sensor_service.process_reading(data)
        return {
            "status": "success",
            "message": "Sensor reading recorded and broadcast successfully.",
            "data": saved_record
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process sensor data: {str(e)}")

@router.get("/latest", summary="Get most recent water quality reading")
async def get_latest():
    """Retrieve the latest registered sensor reading from database."""
    reading = await sensor_service.get_latest_reading()
    if not reading:
        return {
            "status": "empty",
            "message": "No sensor readings available yet. Connect ESP32 simulator to begin streaming.",
            "data": None
        }
    return {
        "status": "success",
        "data": reading
    }

@router.get("/history", summary="Get historical water quality readings")
async def get_history(
    limit: int = Query(50, ge=5, le=500, description="Max number of readings to return"),
    timeframe: Optional[str] = Query("all", description="Timeframe filter: 1h, 24h, 7d, all")
):
    """Retrieve chronological history of readings for analytics charts and tables."""
    readings = await sensor_service.get_history(limit=limit, timeframe=timeframe)
    return {
        "status": "success",
        "count": len(readings),
        "data": readings
    }

@router.get("/analytics", summary="Get water quality analytics and trends")
async def get_analytics(
    timeframe: Optional[str] = Query("24h", description="Timeframe: 1h, 24h, 7d, 30d, all"),
    start_date: Optional[str] = Query(None, description="Start date ISO string"),
    end_date: Optional[str] = Query(None, description="End date ISO string")
):
    """Returns minimum, maximum, average values, counts, trends, anomalies, and summary text."""
    summary = await sensor_service.get_analytics_summary(
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date
    )
    return {
        "status": "success",
        "data": summary
    }
