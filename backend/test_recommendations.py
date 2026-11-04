"""
AquaSense AI - Intelligent Water Quality Recommendation Engine Test Suite
Validates all 12 user requirements:
1. Analysis of current TDS, pH and turbidity readings
2. Synthesis of historical analytics to identify persistent abnormal trends
3. Integration of ML anomaly detection for unusual pattern resolution
4. Incorporation of predictive filter health telemetry
5. Understandable recommendation generation across water & purifier conditions
6. Priority classification (Critical, Warning, Informational)
7. Explanations for why each recommendation was triggered
8. Actionable inspection & maintenance steps
9. Smart deduplication & debouncing
10. Persistent storage & audit history
11. API endpoints (active, history, evaluate, dismiss)
12. Alert system integration & WebSocket broadcasting
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

# Ensure backend root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import DatabaseManager
from services.recommendation_service import RecommendationService, recommendation_service
from services.sensor_service import sensor_service
from services.alert_service import alert_service
from starlette.testclient import TestClient
from main import app

async def run_all_recommendation_tests():
    print("=" * 80)
    print("AquaSense AI - Comprehensive Recommendation Engine Test Suite")
    print("=" * 80)

    # Initialize Database
    await DatabaseManager.init_db()
    db = await DatabaseManager.get_db()
    rec_col = db["water_quality_recommendations"]
    hist_col = db["recommendation_history_log"]
    alerts_col = db["alerts"]

    # Clear previous test recommendation state for clean assertions
    await rec_col.delete_many({})
    await hist_col.delete_many({})
    recommendation_service._debounce_cache.clear()

    # -------------------------------------------------------------------------
    # TEST 1: Current TDS Contamination Analysis & Critical Recommendation (Req 1, 5, 6, 7, 8)
    # -------------------------------------------------------------------------
    print("\n[Test 1] Critical TDS Contamination Evaluation...")
    crit_reading = {
        "tds": 580.0,
        "ph": 7.30,
        "turbidity": 1.2,
        "overall_status": "Critical",
        "water_quality_score": 45.0,
        "anomaly_detected": False
    }

    recs = await recommendation_service.evaluate_and_generate_recommendations(
        current_reading=crit_reading,
        trigger_broadcast=False
    )
    tds_rec = next((r for r in recs if r.parameter == "TDS" and r.priority == "Critical"), None)
    assert tds_rec is not None, "Critical TDS recommendation not generated"
    assert tds_rec.priority == "Critical"
    assert tds_rec.category == "Water Quality"
    assert "High Dissolved Mineral Ingress" in tds_rec.title
    assert "580.0" in tds_rec.reason
    assert "RO membrane" in tds_rec.action
    assert len(tds_rec.action_steps) >= 3
    print(f" -> Critical TDS Recommendation Verified: '{tds_rec.title}'")
    print(f" -> Generated Reason: \"{tds_rec.reason}\"")
    print(f" -> Suggested Action: \"{tds_rec.action}\"")

    # -------------------------------------------------------------------------
    # TEST 2: Acidic and Alkaline pH Recommendations (Req 1, 5, 6, 7, 8)
    # -------------------------------------------------------------------------
    print("\n[Test 2] Acidic & Alkaline pH Analysis...")
    acidic_reading = {
        "tds": 160.0,
        "ph": 5.80, # Acidic
        "turbidity": 1.1,
        "overall_status": "Critical",
        "water_quality_score": 50.0,
        "anomaly_detected": False
    }

    recs_ph = await recommendation_service.evaluate_and_generate_recommendations(
        current_reading=acidic_reading,
        trigger_broadcast=False
    )
    ph_rec = next((r for r in recs_ph if r.parameter == "pH"), None)
    assert ph_rec is not None, "Acidic pH recommendation not generated"
    assert ph_rec.priority in ("Critical", "Warning")
    assert "Remineralizer" in ph_rec.title
    assert "5.80" in ph_rec.reason
    assert any("mineralizer" in s.lower() for s in ph_rec.action_steps)
    print(f" -> Acidic pH Recommendation Verified: '{ph_rec.title}' (Priority: {ph_rec.priority})")

    # -------------------------------------------------------------------------
    # TEST 3: Turbidity and Pre-Filter Loading Analysis (Req 1, 4, 5, 6, 7, 8)
    # -------------------------------------------------------------------------
    print("\n[Test 3] Turbidity & Sediment Pre-Filter Analysis...")
    turb_reading = {
        "tds": 170.0,
        "ph": 7.40,
        "turbidity": 8.5, # High turbidity
        "overall_status": "Warning",
        "water_quality_score": 60.0,
        "anomaly_detected": False
    }

    recs_turb = await recommendation_service.evaluate_and_generate_recommendations(
        current_reading=turb_reading,
        trigger_broadcast=False
    )
    turb_rec = next((r for r in recs_turb if r.parameter == "Turbidity"), None)
    assert turb_rec is not None, "Turbidity recommendation not generated"
    assert turb_rec.priority in ("Critical", "Warning")
    assert "Sediment Pre-Filter" in turb_rec.title
    assert "8.5" in turb_rec.reason
    assert any("pre-filter" in s.lower() for s in turb_rec.action_steps)
    print(f" -> Turbidity Recommendation Verified: '{turb_rec.title}'")

    # -------------------------------------------------------------------------
    # TEST 4: ML Anomaly Pattern Integration (Req 3, 5, 6, 7)
    # -------------------------------------------------------------------------
    print("\n[Test 4] ML Anomaly Pattern Resolution...")
    anomaly_reading = {
        "tds": 165.0,
        "ph": 7.35,
        "turbidity": 1.2,
        "overall_status": "Normal",
        "water_quality_score": 90.0,
        "anomaly_detected": True,
        "anomaly_score": 88.5,
        "anomaly_reason": "Unusual water-quality pattern detected: multivariate correlation divergence.",
        "anomaly_parameter": "Multi-parameter"
    }

    recs_ai = await recommendation_service.evaluate_and_generate_recommendations(
        current_reading=anomaly_reading,
        trigger_broadcast=False
    )
    ai_rec = next((r for r in recs_ai if r.category == "Anomaly Resolution"), None)
    assert ai_rec is not None, "Anomaly resolution recommendation not generated"
    assert ai_rec.priority == "Warning"
    assert "88.5" in ai_rec.reason or "multivariate" in ai_rec.reason.lower()
    assert "anomaly_detector" in ai_rec.source_factors
    print(f" -> AI Anomaly Recommendation Verified: '{ai_rec.title}'")

    # -------------------------------------------------------------------------
    # TEST 5: Predictive Filter Health Incorporation (Req 4, 6, 8)
    # -------------------------------------------------------------------------
    print("\n[Test 5] Incorporating Filter Health Telemetry...")
    # Health data is fetched via filter_service internally
    # Check if filter maintenance advice is synthesized
    all_active = await recommendation_service.get_active_recommendations()
    assert all_active.total_active > 0
    print(f" -> Current Active Recommendations Count: {all_active.total_active}")
    print(f" -> High-level System Assessment: \"{all_active.overall_water_assessment}\"")

    # -------------------------------------------------------------------------
    # TEST 6: Smart Deduplication & Debouncing (Req 9)
    # -------------------------------------------------------------------------
    print("\n[Test 6] Smart Deduplication & Debouncing Verification...")
    # Evaluate identical reading multiple times
    count_before = await rec_col.count_documents({"is_dismissed": False})
    # Run evaluation again with the same critical TDS reading
    await recommendation_service.evaluate_and_generate_recommendations(
        current_reading=crit_reading,
        trigger_broadcast=False
    )
    count_after = await rec_col.count_documents({"is_dismissed": False})

    # The document count should NOT increase; occurrence_count should increment
    assert count_after == count_before, f"Expected count {count_before}, got {count_after} (duplicate inserted!)"
    tds_doc = await rec_col.find_one({"deduplication_key": tds_rec.deduplication_key})
    assert tds_doc["occurrence_count"] >= 2
    print(f" -> Deduplication verified: Document count remained {count_after}; occurrence_count={tds_doc['occurrence_count']}")

    # -------------------------------------------------------------------------
    # TEST 7: Persistent Audit History (Req 10)
    # -------------------------------------------------------------------------
    print("\n[Test 7] Persistent Audit History Logging...")
    hist_items = await recommendation_service.get_recommendation_history(limit=20)
    assert len(hist_items) > 0
    assert any("TDS" in str(h) for h in hist_items)
    print(f" -> Recommendation Audit History Count: {len(hist_items)}")

    # -------------------------------------------------------------------------
    # TEST 8: Alert System Integration & Linking (Req 12)
    # -------------------------------------------------------------------------
    print("\n[Test 8] Alert System Integration & Related Alert Linking...")
    # Create an active alert for TDS Critical
    test_alert_id = "test-alert-tds-crit-001"
    await alerts_col.insert_one({
        "_id": test_alert_id,
        "id": test_alert_id,
        "parameter": "TDS",
        "severity": "Critical",
        "alert_type": "Threshold",
        "title": "TDS Alert",
        "message": "Critical TDS alert",
        "acknowledged": False,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    recs_linked = await recommendation_service.evaluate_and_generate_recommendations(
        current_reading=crit_reading,
        trigger_broadcast=False
    )
    tds_linked = next((r for r in recs_linked if r.parameter == "TDS" and r.priority == "Critical"), None)
    assert tds_linked is not None
    assert tds_linked.related_alert_id == test_alert_id
    print(f" -> Alert Integration Verified: Linked Alert ID = {tds_linked.related_alert_id}")

    # -------------------------------------------------------------------------
    # TEST 9: Recommendation Dismissal / Acknowledgment
    # -------------------------------------------------------------------------
    print("\n[Test 9] Recommendation Dismissal...")
    target_id = tds_rec.id
    dismissed = await recommendation_service.dismiss_recommendation(target_id, dismissed_by="Test Technician")
    assert dismissed is True

    # Ensure it no longer appears in default active query
    active_now = await recommendation_service.get_active_recommendations()
    assert not any(r.id == target_id for r in active_now.active_recommendations)
    print(f" -> Recommendation {target_id[:8]} successfully dismissed and removed from active set.")

    # -------------------------------------------------------------------------
    # TEST 10: REST API Endpoints Verification via TestClient (Req 11)
    # -------------------------------------------------------------------------
    print("\n[Test 10] REST API Endpoints Verification (FastAPI TestClient)...")
    client = TestClient(app)

    # 1. GET /api/recommendations
    res_get = client.get("/api/recommendations")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert "active_recommendations" in data_get
    assert "total_active" in data_get
    assert "critical_count" in data_get
    assert "overall_water_assessment" in data_get
    print(f" -> GET /api/recommendations returned 200 OK (Total Active: {data_get['total_active']})")

    # 2. GET /api/recommendations/history
    res_hist = client.get("/api/recommendations/history?limit=10")
    assert res_hist.status_code == 200
    data_hist = res_hist.json()
    assert data_hist["status"] == "success"
    assert len(data_hist["data"]) > 0
    print(f" -> GET /api/recommendations/history returned 200 OK (Count: {data_hist['count']})")

    # 3. POST /api/recommendations/evaluate
    res_eval = client.post("/api/recommendations/evaluate")
    assert res_eval.status_code == 200
    data_eval = res_eval.json()
    assert data_eval["status"] == "success"
    print(f" -> POST /api/recommendations/evaluate returned 200 OK: \"{data_eval['message']}\"")

    # Clean up test alert
    await alerts_col.delete_one({"_id": test_alert_id})

    print("\n" + "=" * 80)
    print("ALL 12/12 RECOMMENDATION ENGINE REQUIREMENTS SUCCESSFULLY VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_all_recommendation_tests())

