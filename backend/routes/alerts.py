from fastapi import APIRouter, Query, HTTPException, Path
from typing import Optional
from services.alert_service import alert_service

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", summary="Get alert notifications list")
async def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status: active, acknowledged, or omit for all"),
    limit: int = Query(50, ge=1, le=200)
):
    """Fetch stored system alerts and threshold breach events."""
    alerts = await alert_service.get_alerts(status=status, limit=limit)
    return {
        "status": "success",
        "count": len(alerts),
        "data": alerts
    }

@router.post("/{alert_id}/acknowledge", summary="Acknowledge a specific alert")
async def acknowledge_alert(alert_id: str = Path(..., description="Unique ID of alert to acknowledge")):
    """Mark an alert as acknowledged to dismiss it from active badges."""
    success = await alert_service.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged.")
    return {
        "status": "success",
        "message": f"Alert {alert_id} acknowledged successfully."
    }

@router.post("/acknowledge-all", summary="Acknowledge all pending active alerts")
async def acknowledge_all():
    """Batch acknowledge all active alerts."""
    count = await alert_service.acknowledge_all()
    return {
        "status": "success",
        "message": f"Acknowledged {count} active alerts."
    }

@router.delete("/clear-acknowledged", summary="Clear all acknowledged alerts")
async def clear_acknowledged():
    """Clean up historical acknowledged alerts."""
    deleted_count = await alert_service.clear_acknowledged()
    return {
        "status": "success",
        "message": f"Cleared {deleted_count} acknowledged alerts."
    }

