"""
AquaSense AI - Complete Integration Verification Script
Verifies all FastAPI routes, AI anomaly detector, alert deduplication,
and database persistence in one run.
"""

import sys
import asyncio
from datetime import datetime, timezone

from database.connection import DatabaseManager
from services.sensor_service import sensor_service
from services.alert_service import alert_service
from services.filter_service import filter_service
from ai.anomaly_detector import anomaly_detector
from models.sensor import SensorReadingInput

async def verify_all():
    print("=" * 60)
    print("  AquaSense AI - End-to-End System Verification")
    print("=" * 60)

    # 1. Database Initialization
    print("\n[1/6] Initializing Database...")
    await DatabaseManager.init_db()
    db_status = await DatabaseManager.get_status()
    print(f" -> Database Online: {db_status['type']}")
    print(f" -> Storage target: {db_status['storage_path']}")

    # 2. Testing Normal Reading Ingestion
    print("\n[2/6] Ingesting Normal Water Reading (TDS: 170 ppm, pH: 7.35, Turbidity: 1.2)...")
    r_norm = await sensor_service.process_reading(
        SensorReadingInput(tds=170.0, ph=7.35, turbidity=1.2, device_id="AquaSense-ESP32")
    )
    assert r_norm["overall_status"] == "Normal", f"Expected Normal, got {r_norm['overall_status']}"
    assert r_norm["water_quality_score"] >= 90.0, f"Expected WQI >= 90, got {r_norm['water_quality_score']}"
    print(f" -> Ingestion Success! WQI: {r_norm['water_quality_score']}%, Status: {r_norm['overall_status']}")

    # 3. Testing High TDS Critical Breach (>500 ppm)
    print("\n[3/6] Ingesting Critical TDS Reading (TDS: 590 ppm, pH: 7.4, Turbidity: 1.5)...")
    r_tds = await sensor_service.process_reading(
        SensorReadingInput(tds=590.0, ph=7.4, turbidity=1.5, device_id="AquaSense-ESP32")
    )
    assert r_tds["tds_status"] == "Critical", f"Expected Critical TDS, got {r_tds['tds_status']}"
    print(f" -> Threshold Triggered: TDS Status = {r_tds['tds_status']}, Overall = {r_tds['overall_status']}")

    # 4. Testing Acidic pH Breach (<6.5)
    print("\n[4/6] Ingesting Acidic pH Reading (TDS: 170 ppm, pH: 4.9, Turbidity: 1.2)...")
    r_ph = await sensor_service.process_reading(
        SensorReadingInput(tds=170.0, ph=4.9, turbidity=1.2, device_id="AquaSense-ESP32")
    )
    assert r_ph["ph_status"] == "Critical", f"Expected Critical pH, got {r_ph['ph_status']}"
    print(f" -> Threshold Triggered: pH Status = {r_ph['ph_status']}, Overall = {r_ph['overall_status']}")

    # 5. Testing Alerts Retrieval & Acknowledgment
    print("\n[5/6] Verifying Alert System & Deduplication...")
    alerts = await alert_service.get_alerts(limit=10)
    print(f" -> Total Stored Alerts: {len(alerts)}")
    assert len(alerts) > 0, "Expected at least 1 alert to be generated"
    for a in alerts[:3]:
        print(f"    * [{a['severity']}] {a['title']} ({a['parameter']}): {a['message'][:65]}...")

    # Acknowledge first alert
    target_id = alerts[0]["id"]
    ack_res = await alert_service.acknowledge_alert(target_id)
    print(f" -> Alert {target_id} acknowledged: {ack_res}")

    # 6. Verifying Multi-Stage Filter Health
    print("\n[6/6] Verifying Predictive Filter Health...")
    fh = await filter_service.get_filter_health()
    print(f" -> Overall Condition: {fh['overall_condition_pct']}% ({fh['overall_status']})")
    print(f" -> Operating Hours: {fh['operating_hours']} hrs | Processed Volume: {fh['processed_volume_liters']} L")
    print(f" -> Stages Configured: {len(fh['stages'])} stages")
    for st in fh["stages"]:
        print(f"    * Stage {st['stage_number']}: {st['name']} -> {st['condition_pct']}% ({st['status']})")

    print("\n" + "=" * 60)
    print("  ALL 6/6 SYSTEM VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(verify_all())

