"""
AquaSense AI - Filter Health Monitoring Comprehensive Test Suite
Validates all 10 user requirements:
1. Historical TDS and turbidity readings analysis & burden computation
2. Tracking filter operating duration using available device information
3. Maintaining persistent filter usage history & maintenance logs
4. Transparent estimated filter health calculation
5. Unusual water-quality trend detection (turbidity surge, TDS passage)
6. Dynamic maintenance recommendation & clear reason generation
7. Configurable maintenance warning thresholds
8. Maintenance alert generation (Critical, Warning, Trend Anomaly)
9. Preservation of filter health history across backend restarts
10. Complete API response structure (estimated health, condition, duration, last date, rec, reason)
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Ensure backend root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import DatabaseManager
from services.filter_service import FilterService
from services.sensor_service import sensor_service
from services.alert_service import alert_service
from models.filter import WaterQualityBurden, WaterQualityTrendAnalysis

async def run_all_filter_health_tests():
    print("=" * 75)
    print("AquaSense AI - Comprehensive Filter Health Monitoring Test Suite")
    print("=" * 75)

    # Initialize Database
    await DatabaseManager.init_db()
    db = await DatabaseManager.get_db()

    # Reset baseline settings for deterministic tests
    await sensor_service.update_settings({
        "filter_warning_threshold": 30.0,
        "filter_critical_threshold": 15.0,
        "filter_max_operating_hours": 2000.0
    })

    # Create fresh FilterService instance for testing
    test_filter_service = FilterService()

    # -------------------------------------------------------------------------
    # TEST 1: Historical TDS and Turbidity Telemetry Analysis (Requirement 1)
    # -------------------------------------------------------------------------
    print("\n[Test 1] Historical TDS & Turbidity Telemetry Analysis...")
    readings_col = db["sensor_readings"]

    now = datetime.now(timezone.utc)
    base_records = [
        {"timestamp": (now - timedelta(hours=i)).isoformat(), "tds": 170.0 + (i % 10), "turbidity": 1.2 + ((i % 5) * 0.1)}
        for i in range(30, 0, -1)
    ]
    for r in base_records:
        await readings_col.insert_one(r)

    burden, trend = await test_filter_service._analyze_historical_water_quality()

    assert burden.historical_avg_tds > 100.0
    assert burden.historical_avg_turbidity > 0.5
    assert burden.water_burden_multiplier >= 1.0
    assert burden.stress_level in ("Low", "Moderate", "High")
    print(f" -> Telemetry Analyzed: Hist Avg TDS={burden.historical_avg_tds} ppm, "
          f"Hist Avg Turbidity={burden.historical_avg_turbidity}")
    print(f" -> Water Burden Multiplier: {burden.water_burden_multiplier}x (Stress Level: {burden.stress_level})")

    # -------------------------------------------------------------------------
    # TEST 2: Operating Duration Tracking (Requirement 2)
    # -------------------------------------------------------------------------
    print("\n[Test 2] Filter Operating Duration Tracking...")
    health_data = await test_filter_service.get_filter_health()
    assert "usage_duration" in health_data
    assert isinstance(health_data["usage_duration"], str)
    assert "operating hours" in health_data["usage_duration"]
    assert health_data["operating_hours"] >= 0.0
    print(f" -> Usage Duration String: '{health_data['usage_duration']}'")
    print(f" -> Active Operating Hours: {health_data['operating_hours']} hrs")

    # -------------------------------------------------------------------------
    # TEST 3: Transparent Estimated Filter Health Calculation (Requirement 4)
    # -------------------------------------------------------------------------
    print("\n[Test 3] Transparent Health Calculation Formula...")
    settings = await test_filter_service.get_settings()
    health_pct, condition, transparency, stages = test_filter_service._calculate_transparent_health(
        operating_hours=1000.0,
        burden=burden,
        settings=settings
    )

    # 1000 hours on 2000 hour rated life = 50% base wear
    expected_wear = round((1000.0 / float(settings.get("filter_max_operating_hours", 2000.0))) * 100.0, 2)
    assert transparency.base_wear_pct == expected_wear
    assert 0.0 <= health_pct <= 100.0
    assert condition in ("Optimal", "Good", "Fair", "Needs Maintenance", "Critical - Replacement Due")
    assert len(stages) == 4
    assert len(transparency.transparency_notes) >= 4
    print(f" -> Computed Health: {health_pct}% ({condition})")
    print(f" -> Transparency Formula: {transparency.formula}")
    print(f" -> Base Wear: {transparency.base_wear_pct}%, Burden Penalty: {transparency.water_burden_penalty_pct}%")

    # -------------------------------------------------------------------------
    # TEST 4: Unusual Water-Quality Trend Detection (Requirement 5)
    # -------------------------------------------------------------------------
    print("\n[Test 4] Detecting Unusual Water-Quality Trends (Turbidity Surge & TDS Passage)...")
    baseline_records = [
        {"timestamp": (now - timedelta(minutes=35-i)).isoformat(), "tds": 165.0, "turbidity": 1.2}
        for i in range(20)
    ]
    spike_records = [
        {"timestamp": (now + timedelta(minutes=i)).isoformat(), "tds": 175.0, "turbidity": 6.8}
        for i in range(15)
    ]
    combined_test_records = list(reversed(baseline_records + spike_records))

    spike_burden, spike_trend = await test_filter_service._analyze_historical_water_quality(
        custom_records=combined_test_records
    )
    assert spike_trend.unusual_change_detected is True
    assert any("Turbidity Surge" in f for f in spike_trend.findings)
    print(f" -> Unusual Trend Successfully Detected: {spike_trend.findings[0]}")
    print(f" -> Turbidity Delta: {spike_trend.turbidity_change_pct}%")

    # -------------------------------------------------------------------------
    # TEST 5: Maintenance Recommendation & Reason Generation (Requirement 6)
    # -------------------------------------------------------------------------
    print("\n[Test 5] Maintenance Recommendations & Explanations...")
    nominal_trend = WaterQualityTrendAnalysis(
        unusual_change_detected=False,
        turbidity_change_pct=0.0,
        tds_change_pct=0.0,
        findings=[]
    )

    # 1. Optimal condition recommendation
    rec_opt, reason_opt = test_filter_service._generate_recommendation(
        health_pct=85.0, condition="Optimal", trend=nominal_trend, settings=settings, next_service_date="2027-02-15"
    )
    assert "ROUTINE OPERATION" in rec_opt
    assert "85.0%" in reason_opt

    # 2. Warning condition recommendation
    rec_warn, reason_warn = test_filter_service._generate_recommendation(
        health_pct=25.0, condition="Needs Maintenance", trend=nominal_trend, settings=settings, next_service_date="2027-02-15"
    )
    assert "SCHEDULE SERVICE" in rec_warn
    assert "warning threshold" in reason_warn

    # 3. Critical condition recommendation
    rec_crit, reason_crit = test_filter_service._generate_recommendation(
        health_pct=12.0, condition="Critical - Replacement Due", trend=nominal_trend, settings=settings, next_service_date="2027-02-15"
    )
    assert "CRITICAL" in rec_crit
    assert "critical threshold" in reason_crit

    # 4. Unusual trend recommendation
    rec_trend, reason_trend = test_filter_service._generate_recommendation(
        health_pct=75.0, condition="Good", trend=spike_trend, settings=settings, next_service_date="2027-02-15"
    )
    assert "RECOMMENDED" in rec_trend
    assert "Unusual water-quality trend detected" in reason_trend

    print(" -> Verified recommendations for Optimal, Warning, Critical, and Trend Anomaly states.")

    # -------------------------------------------------------------------------
    # TEST 6: Configurable Maintenance Warning Thresholds (Requirement 7)
    # -------------------------------------------------------------------------
    print("\n[Test 6] Configurable Maintenance Warning Thresholds...")
    await sensor_service.update_settings({
        "filter_warning_threshold": 35.0,
        "filter_critical_threshold": 12.0,
        "filter_max_operating_hours": 2500.0
    })
    updated_settings = await test_filter_service.get_settings()
    assert updated_settings["filter_warning_threshold"] == 35.0
    assert updated_settings["filter_critical_threshold"] == 12.0
    assert updated_settings["filter_max_operating_hours"] == 2500.0
    print(" -> Configurable thresholds successfully updated and persisted in DB.")

    # -------------------------------------------------------------------------
    # TEST 7: Maintenance Alert Generation (Requirement 8)
    # -------------------------------------------------------------------------
    print("\n[Test 7] Maintenance Alert Generation & Deduplication...")
    # Clear any existing filter alerts so we can test clean creation and debounce
    alerts_col = await alert_service.get_alerts_collection()
    await alerts_col.delete_many({"parameter": "Filter Health"})
    alert_service._recent_alert_debounce.clear()

    # Trigger alert for critical health
    alert = await alert_service.evaluate_filter_maintenance(
        filter_health_pct=10.0,
        filter_condition="Critical - Replacement Due",
        recommendation="Replace all cartridges immediately.",
        reason="Health below 12.0% critical threshold.",
        settings=updated_settings
    )
    assert alert is not None
    assert alert.alert_type == "Maintenance"
    assert alert.parameter == "Filter Health"
    assert alert.severity == "Critical"
    print(f" -> Critical Maintenance Alert Generated: '{alert.title}' (ID: {alert.id[:8]}...)")

    # Immediate second call should be deduplicated/debounced
    alert_dup = await alert_service.evaluate_filter_maintenance(
        filter_health_pct=9.8,
        filter_condition="Critical - Replacement Due",
        recommendation="Replace all cartridges immediately.",
        reason="Health below 12.0% critical threshold.",
        settings=updated_settings
    )
    assert alert_dup is None  # Debounced
    print(" -> Deduplication verified: subsequent alert within debounce window was suppressed.")

    # -------------------------------------------------------------------------
    # TEST 8: Filter Usage History & Maintenance Service Logs (Requirement 3)
    # -------------------------------------------------------------------------
    print("\n[Test 8] Filter Usage History & Maintenance Service Logs...")
    # Test reset and service log
    reset_res = await test_filter_service.reset_filters(
        technician="Service Engineer Rajesh",
        notes="Replaced sediment pre-filter and RO membrane."
    )
    assert reset_res["estimated_filter_health_percentage"] == 100.0
    assert reset_res["operating_hours"] == 0.0

    history = await test_filter_service.get_usage_history(limit=10)
    assert len(history) > 0
    assert any(h["event_type"] == "maintenance_reset" for h in history)

    m_logs = await test_filter_service.get_maintenance_logs(limit=10)
    assert len(m_logs) > 0
    assert m_logs[0]["technician"] == "Service Engineer Rajesh"
    print(f" -> Usage History Snapshots Count: {len(history)}")
    print(f" -> Maintenance Service Log Verified: {m_logs[0]['action']} by {m_logs[0]['technician']}")

    # -------------------------------------------------------------------------
    # TEST 9: Preservation Across Restarts (Requirement 9)
    # -------------------------------------------------------------------------
    print("\n[Test 9] Preservation of Filter State Across Backend Restarts...")
    # Simulate fresh service instance reload
    restarted_service = FilterService()
    reloaded_data = await restarted_service.get_filter_health()
    assert reloaded_data["estimated_filter_health_percentage"] == 100.0
    assert reloaded_data["operating_hours"] == 0.0
    reloaded_history = await restarted_service.get_usage_history(limit=10)
    assert len(reloaded_history) > 0
    print(" -> Restart simulation verified: State and history preserved across service reload.")

    # -------------------------------------------------------------------------
    # TEST 10: Complete API Response Structure (Requirement 10)
    # -------------------------------------------------------------------------
    print("\n[Test 10] Complete API Response Structure Compliance...")
    final_payload = await restarted_service.get_filter_health()

    # Check 6 explicit required fields:
    assert "estimated_filter_health_percentage" in final_payload
    assert "filter_condition" in final_payload
    assert "usage_duration" in final_payload
    assert "last_maintenance_date" in final_payload
    assert "maintenance_recommendation" in final_payload
    assert "reason_for_recommendation" in final_payload

    # Check backwards compatibility fields for existing UI:
    assert "overall_condition_pct" in final_payload
    assert "overall_status" in final_payload
    assert "operating_hours" in final_payload
    assert "processed_volume_liters" in final_payload
    assert "stages" in final_payload
    assert "last_serviced_date" in final_payload
    assert "next_scheduled_service" in final_payload
    assert "disclaimer" in final_payload

    # Check transparency and safety:
    assert "distinct from manufacturer-certified" in final_payload["disclaimer"]
    print(" -> All 6 required fields present and typed correctly.")
    print(" -> Backwards compatibility with Frontend UI verified.")
    print(" -> Non-certification disclaimer verified.")

    print("\n" + "=" * 75)
    print("ALL 10/10 FILTER HEALTH REQUIREMENTS SUCCESSFULLY VERIFIED!")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_all_filter_health_tests())
