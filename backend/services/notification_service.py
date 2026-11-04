"""
AquaSense AI - Notification and Event Management Service
Provides persistent event management, lifecycle tracking (unread, read, acknowledged),
smart deduplication, cross-system linking (alerts and recommendations), and real-time
WebSocket streaming.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from database.connection import DatabaseManager
from models.notification import (
    Notification,
    NotificationListResponse,
    NotificationSummaryResponse
)
from services.websocket_manager import ws_manager

class NotificationService:
    def __init__(self):
        # In-memory debounce cache: deduplication_key -> last_emitted_iso
        self._recent_debounce: Dict[str, str] = {}
        self.debounce_seconds = 45 # Prevent duplicate notifications within 45 seconds

    async def get_notifications_collection(self):
        db = await DatabaseManager.get_db()
        return db["notifications"]

    async def create_notification(
        self,
        title: str,
        message: str,
        severity: str, # Critical, Warning, Informational
        category: str, # Water Quality, AI Anomaly, Filter Maintenance, System
        parameter: Optional[str] = None,
        reading_value: Optional[float] = None,
        threshold_value: Optional[str] = None,
        suggested_action: Optional[str] = None,
        related_alert_id: Optional[str] = None,
        related_recommendation_id: Optional[str] = None,
        source_event: str = "alert_service"
    ) -> Optional[Notification]:
        """
        Creates, deduplicates, persists, and broadcasts a notification event.
        If an unacknowledged notification with identical fingerprint exists, updates
        occurrence count and timestamp rather than inserting duplicate clutter.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        col = await self.get_notifications_collection()

        # Deterministic deduplication fingerprint
        dedup_key = f"{category.lower()}:{str(parameter).lower()}:{severity.lower()}:{title[:30].lower()}"

        # 1. Check if unacknowledged notification with identical fingerprint exists in DB
        existing = await col.find_one({
            "deduplication_key": dedup_key,
            "is_acknowledged": False
        })

        if existing:
            # Update occurrence count and latest timestamp
            new_count = int(existing.get("occurrence_count", 1)) + 1
            await col.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "updated_at": now_iso,
                    "reading_value": reading_value,
                    "occurrence_count": new_count,
                    "message": message,
                    "related_alert_id": related_alert_id or existing.get("related_alert_id"),
                    "related_recommendation_id": related_recommendation_id or existing.get("related_recommendation_id")
                }}
            )
            existing["updated_at"] = now_iso
            existing["reading_value"] = reading_value
            existing["occurrence_count"] = new_count
            existing["message"] = message
            if "_id" in existing:
                existing["id"] = str(existing["_id"])
            return Notification(**existing)

        # 2. Check memory debounce cooldown
        last_emitted = self._recent_debounce.get(dedup_key)
        if last_emitted:
            try:
                delta = (datetime.fromisoformat(now_iso) - datetime.fromisoformat(last_emitted)).total_seconds()
                if delta < self.debounce_seconds:
                    return None
            except Exception:
                pass

        self._recent_debounce[dedup_key] = now_iso

        # 3. Create fresh notification
        notif_id = str(uuid.uuid4())
        doc = {
            "_id": notif_id,
            "id": notif_id,
            "created_at": now_iso,
            "updated_at": now_iso,
            "title": title,
            "message": message,
            "severity": severity,
            "category": category,
            "parameter": parameter,
            "reading_value": reading_value,
            "threshold_value": threshold_value,
            "suggested_action": suggested_action,
            "is_read": False,
            "read_at": None,
            "is_acknowledged": False,
            "acknowledged_at": None,
            "acknowledged_by": None,
            "occurrence_count": 1,
            "deduplication_key": dedup_key,
            "related_alert_id": related_alert_id,
            "related_recommendation_id": related_recommendation_id,
            "source_event": source_event
        }

        await col.insert_one(doc)
        notif_obj = Notification(**doc)

        # 4. Broadcast via WebSocket in real-time (Requirement 11)
        await ws_manager.broadcast("notification_created", notif_obj.model_dump())
        return notif_obj

    async def create_from_alert(self, alert_dict: Dict[str, Any]) -> Optional[Notification]:
        """
        Generates a notification corresponding to an alert triggered in the system.
        Maps alert types (Threshold, Range, Anomaly, Maintenance) into categories.
        """
        alert_type = alert_dict.get("alert_type", "Threshold")
        param = alert_dict.get("parameter", "System")
        severity = alert_dict.get("severity", "Warning")

        category = "Water Quality"
        if alert_type == "Anomaly" or param == "Profile":
            category = "AI Anomaly"
        elif alert_type == "Maintenance" or param == "Filter Health":
            category = "Filter Maintenance"

        return await self.create_notification(
            title=alert_dict.get("title", f"{param} Alert"),
            message=alert_dict.get("message", ""),
            severity=severity,
            category=category,
            parameter=param,
            reading_value=alert_dict.get("reading_value"),
            threshold_value=alert_dict.get("threshold_value"),
            suggested_action=alert_dict.get("suggested_action"),
            related_alert_id=alert_dict.get("id"),
            source_event="alert_service"
        )

    async def get_notifications(
        self,
        status: Optional[str] = None, # unread, read, active, acknowledged, or None (all)
        severity: Optional[str] = None, # Critical, Warning, Informational
        category: Optional[str] = None,
        parameter: Optional[str] = None,
        limit: int = 50
    ) -> NotificationListResponse:
        """Fetch notification events matching filters with status metrics."""
        col = await self.get_notifications_collection()
        query: Dict[str, Any] = {}

        if status == "unread":
            query["is_read"] = False
        elif status == "read":
            query["is_read"] = True
        elif status == "active":
            query["is_acknowledged"] = False
        elif status == "acknowledged":
            query["is_acknowledged"] = True

        if severity:
            query["severity"] = severity
        if category:
            query["category"] = category
        if parameter:
            query["parameter"] = parameter

        cursor = col.find(query).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)

        notifications: List[Notification] = []
        for it in items:
            if "_id" in it:
                it["id"] = str(it["_id"])
            notifications.append(Notification(**it))

        # Calculate high-level summary counts
        total = await col.count_documents({})
        unread_count = await col.count_documents({"is_read": False})
        critical_count = await col.count_documents({"severity": "Critical", "is_acknowledged": False})
        warning_count = await col.count_documents({"severity": "Warning", "is_acknowledged": False})

        return NotificationListResponse(
            status="success",
            total=total,
            unread_count=unread_count,
            critical_count=critical_count,
            warning_count=warning_count,
            data=notifications
        )

    async def get_summary(self) -> NotificationSummaryResponse:
        """Get high-level summary metrics for badges and headers."""
        col = await self.get_notifications_collection()
        total = await col.count_documents({})
        unread = await col.count_documents({"is_read": False})
        acknowledged = await col.count_documents({"is_acknowledged": True})
        critical = await col.count_documents({"severity": "Critical", "is_acknowledged": False})
        warning = await col.count_documents({"severity": "Warning", "is_acknowledged": False})
        informational = await col.count_documents({"severity": "Informational", "is_acknowledged": False})

        latest_item = await col.find_one({}, sort=[("created_at", -1)])
        last_ts = latest_item.get("created_at") if latest_item else None

        return NotificationSummaryResponse(
            status="success",
            total=total,
            unread=unread,
            acknowledged=acknowledged,
            critical=critical,
            warning=warning,
            informational=informational,
            last_event_timestamp=last_ts
        )

    async def mark_as_read(self, notification_id: str, read_by: str = "User") -> bool:
        """Mark a specific notification as read."""
        col = await self.get_notifications_collection()
        now_iso = datetime.now(timezone.utc).isoformat()
        res = await col.update_one(
            {"_id": notification_id},
            {"$set": {
                "is_read": True,
                "read_at": now_iso
            }}
        )
        if res.modified_count > 0:
            unread = await col.count_documents({"is_read": False})
            await ws_manager.broadcast("notification_read", {
                "id": notification_id,
                "unread_count": unread
            })
            return True
        return False

    async def mark_all_as_read(self) -> int:
        """Batch mark all unread notifications as read."""
        col = await self.get_notifications_collection()
        now_iso = datetime.now(timezone.utc).isoformat()
        res = await col.update_many(
            {"is_read": False},
            {"$set": {
                "is_read": True,
                "read_at": now_iso
            }}
        )
        await ws_manager.broadcast("notifications_all_read", {"read_count": res.modified_count})
        return res.modified_count

    async def acknowledge_notification(self, notification_id: str, acknowledged_by: str = "User") -> bool:
        """Acknowledge a specific notification, marking it read and acknowledged."""
        col = await self.get_notifications_collection()
        now_iso = datetime.now(timezone.utc).isoformat()

        doc = await col.find_one({"_id": notification_id})
        if not doc:
            return False

        res = await col.update_one(
            {"_id": notification_id},
            {"$set": {
                "is_read": True,
                "read_at": doc.get("read_at") or now_iso,
                "is_acknowledged": True,
                "acknowledged_at": now_iso,
                "acknowledged_by": acknowledged_by
            }}
        )

        if res.modified_count > 0:
            # If notification is linked to an alert, also acknowledge the alert in alert_service
            related_alert_id = doc.get("related_alert_id")
            if related_alert_id:
                try:
                    from services.alert_service import alert_service
                    await alert_service.acknowledge_alert(related_alert_id)
                except Exception:
                    pass

            await ws_manager.broadcast("notification_acknowledged", {"id": notification_id})
            return True
        return False

    async def acknowledge_all(self, acknowledged_by: str = "User") -> int:
        """Batch acknowledge all active notifications."""
        col = await self.get_notifications_collection()
        now_iso = datetime.now(timezone.utc).isoformat()
        res = await col.update_many(
            {"is_acknowledged": False},
            {"$set": {
                "is_read": True,
                "is_acknowledged": True,
                "acknowledged_at": now_iso,
                "acknowledged_by": acknowledged_by
            }}
        )
        await ws_manager.broadcast("notifications_all_acknowledged", {"count": res.modified_count})
        return res.modified_count

    async def clear_acknowledged(self) -> int:
        """Delete acknowledged notifications from the database."""
        col = await self.get_notifications_collection()
        res = await col.delete_many({"is_acknowledged": True})
        await ws_manager.broadcast("notifications_cleared", {"deleted_count": res.deleted_count})
        return res.deleted_count

notification_service = NotificationService()

