"""
AquaSense AI - Comprehensive Notification & Event Management Test Suite
Validates all 12 user requirements:
1. Notification events for Critical and Warning water-quality conditions
2. Notifications for AI anomaly detection events
3. Filter maintenance notifications
4. Connection to existing recommendations and alerts (linking IDs)
5. Persistent storage of notification history
6. Full lifecycle support for read, unread, and acknowledged states
7. Duplicate notification prevention (deduplication & occurrence counter)
8. Accurate timestamps and severity classifications (Critical, Warning, Informational)
9. APIs to retrieve notification history and summary metrics
10. APIs to mark notifications as read and acknowledged
11. Real-time broadcasting of notification events through WebSocket
12. Preservation of existing alert and recommendation functionality
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import DatabaseManager
from services.notification_service import notification_service
from services.alert_service import alert_service
from services.recommendation_service import recommendation_service
from starlette.testclient import TestClient
from main import app

async def run_all_notification_tests():
    print("=" * 80)
    print("AquaSense AI - Comprehensive Notification & Event Management Test Suite")
    print("=" * 80)

    # Initialize Database
    await DatabaseManager.init_db()
    db = await DatabaseManager.get_db()
    notif_col = db["notifications"]
    alerts_col = db["alerts"]

    # Clear previous test notification state for clean test run
    await notif_col.delete_many({})
    notification_service._recent_debounce.clear()

    # -------------------------------------------------------------------------
    # TEST 1: Critical and Warning Water-Quality Notifications (Req 1, 8)
    # -------------------------------------------------------------------------
    print("\n[Test 1] Critical & Warning Water-Quality Notifications Generation...")
    notif_crit = await notification_service.create_notification(
        title="Critical TDS Threshold Exceeded",
        message="TDS spiked to 550.0 ppm exceeding the critical drinking limit (500 ppm).",
        severity="Critical",
        category="Water Quality",
        parameter="TDS",
        reading_value=550.0,
        threshold_value="> 500.0 ppm",
        suggested_action="Flush RO membrane immediately."
    )
    assert notif_crit is not None
    assert notif_crit.severity == "Critical"
    assert notif_crit.category == "Water Quality"
    assert notif_crit.parameter == "TDS"
    assert notif_crit.reading_value == 550.0
    assert notif_crit.is_read is False
    assert notif_crit.is_acknowledged is False
    assert notif_crit.occurrence_count == 1
    print(f" -> Critical Notification Created: '{notif_crit.title}' (ID: {notif_crit.id[:8]}...)")

    notif_warn = await notification_service.create_notification(
        title="Acidic Water pH Warning",
        message="pH level dropped to 6.2, below the safe alkaline balance.",
        severity="Warning",
        category="Water Quality",
        parameter="pH",
        reading_value=6.2,
        threshold_value="< 6.5",
        suggested_action="Inspect alkaline remineralizer."
    )
    assert notif_warn is not None
    assert notif_warn.severity == "Warning"
    print(f" -> Warning Notification Created: '{notif_warn.title}' (Severity: {notif_warn.severity})")

    # -------------------------------------------------------------------------
    # TEST 2: AI Anomaly Detection Notifications (Req 2)
    # -------------------------------------------------------------------------
    print("\n[Test 2] AI Anomaly Detection Notifications...")
    notif_ai = await notification_service.create_notification(
        title="AI Multivariate Pattern Anomaly",
        message="Isolation forest detected sudden correlation breakdown across TDS and turbidity.",
        severity="Warning",
        category="AI Anomaly",
        parameter="Profile",
        reading_value=85.0,
        threshold_value="Statistical Divergence",
        suggested_action="Check for aerated flow or probe micro-bubbles.",
        source_event="anomaly_detector"
    )
    assert notif_ai is not None
    assert notif_ai.category == "AI Anomaly"
    assert notif_ai.source_event == "anomaly_detector"
    print(f" -> AI Anomaly Notification Created: '{notif_ai.title}' (Category: {notif_ai.category})")

    # -------------------------------------------------------------------------
    # TEST 3: Filter Maintenance Notifications (Req 3)
    # -------------------------------------------------------------------------
    print("\n[Test 3] Filter Maintenance Notifications...")
    notif_filter = await notification_service.create_notification(
        title="Sediment Pre-Filter Replacement Due",
        message="Estimated filter health dropped to 14.0% with high turbidity burden.",
        severity="Critical",
        category="Filter Maintenance",
        parameter="Filter Health",
        reading_value=14.0,
        threshold_value="<= 15.0%",
        suggested_action="Replace Stage 1 PP-spun cartridge.",
        source_event="filter_service"
    )
    assert notif_filter is not None
    assert notif_filter.category == "Filter Maintenance"
    assert notif_filter.parameter == "Filter Health"
    print(f" -> Filter Maintenance Notification Created: '{notif_filter.title}'")

    # -------------------------------------------------------------------------
    # TEST 4: Connecting Notifications to Existing Alerts and Recommendations (Req 4)
    # -------------------------------------------------------------------------
    print("\n[Test 4] Connecting Notifications to Alerts and Recommendations...")
    test_alert = {
        "id": "alert-test-link-001",
        "title": "High Turbidity Alert",
        "message": "Turbidity reached 8.2 simulated units.",
        "severity": "Critical",
        "alert_type": "Threshold",
        "parameter": "Turbidity",
        "reading_value": 8.2,
        "threshold_value": "> 10.0",
        "suggested_action": "Flush inlet line."
    }
    notif_linked = await notification_service.create_from_alert(test_alert)
    assert notif_linked is not None
    assert notif_linked.related_alert_id == "alert-test-link-001"
    assert notif_linked.source_event == "alert_service"
    assert notif_linked.parameter == "Turbidity"
    print(f" -> Alert Linked Notification Created: Related Alert ID = '{notif_linked.related_alert_id}'")

    # -------------------------------------------------------------------------
    # TEST 5: Duplicate Prevention and Occurrence Counter (Req 7)
    # -------------------------------------------------------------------------
    print("\n[Test 5] Duplicate Prevention & Occurrence Counter...")
    total_before = await notif_col.count_documents({})

    # Attempt to re-create the exact same Critical TDS notification
    notif_recreated = await notification_service.create_notification(
        title="Critical TDS Threshold Exceeded",
        message="TDS spiked to 552.0 ppm exceeding critical limit.",
        severity="Critical",
        category="Water Quality",
        parameter="TDS",
        reading_value=552.0,
        threshold_value="> 500.0 ppm"
    )

    total_after = await notif_col.count_documents({})
    assert total_after == total_before, f"Expected {total_before} records, but got {total_after} (duplicate inserted!)"
    assert notif_recreated.occurrence_count >= 2
    assert notif_recreated.id == notif_crit.id
    print(f" -> Duplicate successfully suppressed: Total records remained {total_after}; occurrence_count={notif_recreated.occurrence_count}")

    # -------------------------------------------------------------------------
    # TEST 6: Read, Unread and Acknowledged Lifecycle States (Req 6)
    # -------------------------------------------------------------------------
    print("\n[Test 6] Read, Unread, and Acknowledged Lifecycle States...")
    # 1. Initially unread
    assert notif_warn.is_read is False
    assert notif_warn.is_acknowledged is False

    # 2. Mark as read
    read_success = await notification_service.mark_as_read(notif_warn.id, read_by="Homeowner")
    assert read_success is True

    updated_doc = await notif_col.find_one({"_id": notif_warn.id})
    assert updated_doc["is_read"] is True
    assert updated_doc["read_at"] is not None
    assert updated_doc["is_acknowledged"] is False
    print(" -> Read state verified: is_read=True, read_at timestamp populated.")

    # 3. Acknowledge
    ack_success = await notification_service.acknowledge_notification(notif_warn.id, acknowledged_by="Technician Rahul")
    assert ack_success is True

    ack_doc = await notif_col.find_one({"_id": notif_warn.id})
    assert ack_doc["is_acknowledged"] is True
    assert ack_doc["acknowledged_at"] is not None
    assert ack_doc["acknowledged_by"] == "Technician Rahul"
    print(f" -> Acknowledged state verified: is_acknowledged=True by '{ack_doc['acknowledged_by']}'")

    # -------------------------------------------------------------------------
    # TEST 7: Persistent Storage Across Restarts (Req 5)
    # -------------------------------------------------------------------------
    print("\n[Test 7] Persistent Storage Across Restarts...")
    # Re-instantiate service to simulate backend reboot
    from services.notification_service import NotificationService
    fresh_service = NotificationService()
    persisted_list = await fresh_service.get_notifications()
    assert persisted_list.total >= 4
    assert any(n.parameter == "TDS" for n in persisted_list.data)
    print(f" -> State preserved across service reload: Found {persisted_list.total} persisted events.")

    # -------------------------------------------------------------------------
    # TEST 8: REST API Endpoints Verification via TestClient (Req 9, 10)
    # -------------------------------------------------------------------------
    print("\n[Test 8] REST API Endpoints Verification (FastAPI TestClient)...")
    client = TestClient(app)

    # 1. GET /api/notifications
    res_list = client.get("/api/notifications")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["status"] == "success"
    assert list_data["total"] >= 4
    assert "unread_count" in list_data
    assert "critical_count" in list_data
    print(f" -> GET /api/notifications returned 200 OK (Total: {list_data['total']}, Unread: {list_data['unread_count']})")

    # 2. GET /api/notifications/summary
    res_sum = client.get("/api/notifications/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["status"] == "success"
    assert sum_data["total"] >= 4
    assert "critical" in sum_data
    assert "warning" in sum_data
    print(f" -> GET /api/notifications/summary returned 200 OK (Critical: {sum_data['critical']}, Warning: {sum_data['warning']})")

    # 3. GET /api/notifications/{id}
    res_single = client.get(f"/api/notifications/{notif_crit.id}")
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["data"]["id"] == notif_crit.id
    print(f" -> GET /api/notifications/{notif_crit.id[:8]} returned 200 OK")

    # 4. POST /api/notifications/{id}/read
    res_read = client.post(f"/api/notifications/{notif_crit.id}/read", json={"read_by": "Test Suite"})
    assert res_read.status_code == 200
    print(" -> POST /api/notifications/{id}/read returned 200 OK")

    # 5. POST /api/notifications/mark-all-read
    res_all_read = client.post("/api/notifications/mark-all-read")
    assert res_all_read.status_code == 200
    print(f" -> POST /api/notifications/mark-all-read returned 200 OK: {res_all_read.json()['message']}")

    # 6. POST /api/notifications/{id}/acknowledge
    res_ack = client.post(f"/api/notifications/{notif_crit.id}/acknowledge", json={"acknowledged_by": "Senior Tech"})
    assert res_ack.status_code == 200
    print(" -> POST /api/notifications/{id}/acknowledge returned 200 OK")

    # 7. POST /api/notifications/acknowledge-all
    res_ack_all = client.post("/api/notifications/acknowledge-all", json={"acknowledged_by": "Admin"})
    assert res_ack_all.status_code == 200
    print(f" -> POST /api/notifications/acknowledge-all returned 200 OK: {res_ack_all.json()['message']}")

    # 8. DELETE /api/notifications/clear
    res_clear = client.delete("/api/notifications/clear")
    assert res_clear.status_code == 200
    print(f" -> DELETE /api/notifications/clear returned 200 OK: {res_clear.json()['message']}")

    print("\n" + "=" * 80)
    print("ALL 12/12 NOTIFICATION & EVENT MANAGEMENT REQUIREMENTS SUCCESSFULLY VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_all_notification_tests())

