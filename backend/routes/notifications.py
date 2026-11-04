"""
AquaSense AI - Notifications and Events Router
Provides REST endpoints for retrieving notification history, unread badge metrics,
marking notifications as read or acknowledged, and cleaning up historical events.
"""

from fastapi import APIRouter, Query, HTTPException, Path, Body
from typing import Optional, Dict, Any
from services.notification_service import notification_service
from models.notification import (
    NotificationListResponse,
    NotificationSummaryResponse,
    MarkReadRequest,
    AcknowledgeNotificationRequest
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", summary="Get notifications list with filtering", response_model=NotificationListResponse)
async def get_notifications(
    status: Optional[str] = Query(None, description="Filter by status: unread, read, active, acknowledged"),
    severity: Optional[str] = Query(None, description="Filter by severity: Critical, Warning, Informational"),
    category: Optional[str] = Query(None, description="Filter by category: Water Quality, AI Anomaly, Filter Maintenance, System"),
    parameter: Optional[str] = Query(None, description="Filter by parameter: TDS, pH, Turbidity, Filter Health"),
    limit: int = Query(50, ge=1, le=200, description="Max notifications to return")
):
    """
    Retrieve historical and active notification events.
    Supports filtering by status, severity, category, and monitored parameter.
    """
    return await notification_service.get_notifications(
        status=status,
        severity=severity,
        category=category,
        parameter=parameter,
        limit=limit
    )

@router.get("/summary", summary="Get notification count summary for badges", response_model=NotificationSummaryResponse)
async def get_notifications_summary():
    """Returns total, unread, acknowledged, and priority counts for badge counters and headers."""
    return await notification_service.get_summary()

@router.get("/{notification_id}", summary="Get a specific notification by ID")
async def get_notification_by_id(notification_id: str = Path(..., description="Unique notification ID")):
    """Fetch details of a single notification event."""
    col = await notification_service.get_notifications_collection()
    doc = await col.find_one({"_id": notification_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
    return {
        "status": "success",
        "data": doc
    }

@router.post("/{notification_id}/read", summary="Mark a specific notification as read")
async def mark_notification_as_read(
    notification_id: str = Path(...),
    req: Optional[MarkReadRequest] = Body(None)
):
    """Marks a notification as read and updates unread badge counter."""
    read_by = req.read_by if req and req.read_by else "User"
    success = await notification_service.mark_as_read(notification_id=notification_id, read_by=read_by)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {
        "status": "success",
        "message": f"Notification {notification_id} marked as read.",
        "id": notification_id
    }

@router.post("/mark-all-read", summary="Batch mark all unread notifications as read")
async def mark_all_notifications_as_read():
    """Sets is_read to true for all currently unread notifications."""
    count = await notification_service.mark_all_as_read()
    return {
        "status": "success",
        "message": f"Marked {count} notifications as read.",
        "read_count": count
    }

@router.post("/{notification_id}/acknowledge", summary="Acknowledge a specific notification")
async def acknowledge_notification(
    notification_id: str = Path(...),
    req: Optional[AcknowledgeNotificationRequest] = Body(None)
):
    """
    Acknowledge a notification event to dismiss it from active state.
    Also synchronizes status to any linked alert.
    """
    ack_by = req.acknowledged_by if req and req.acknowledged_by else "User"
    success = await notification_service.acknowledge_notification(
        notification_id=notification_id,
        acknowledged_by=ack_by
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {
        "status": "success",
        "message": f"Notification {notification_id} acknowledged successfully.",
        "id": notification_id
    }

@router.post("/acknowledge-all", summary="Batch acknowledge all active notifications")
async def acknowledge_all_notifications(req: Optional[AcknowledgeNotificationRequest] = Body(None)):
    """Acknowledge all unacknowledged notifications in the system."""
    ack_by = req.acknowledged_by if req and req.acknowledged_by else "User"
    count = await notification_service.acknowledge_all(acknowledged_by=ack_by)
    return {
        "status": "success",
        "message": f"Acknowledged {count} notifications.",
        "acknowledged_count": count
    }

@router.delete("/clear", summary="Clear all acknowledged historical notifications")
async def clear_acknowledged_notifications():
    """Clean up acknowledged historical notifications from the database."""
    deleted_count = await notification_service.clear_acknowledged()
    return {
        "status": "success",
        "message": f"Cleared {deleted_count} acknowledged notifications.",
        "deleted_count": deleted_count
    }

