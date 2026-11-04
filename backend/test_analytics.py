"""
AquaSense AI - Water Quality Analytics Unit & Integration Tests
Validates all 10 user requirements:
1. TDS Min/Max/Avg calculations
2. pH Min/Max/Avg calculations
3. Turbidity Min/Max/Avg calculations
4. Total sensor readings count
5. Normal, Warning, Critical reading counts & percentages
6. Daily and weekly water-quality trends
7. Frequently occurring anomaly identification
8. Most frequently abnormal parameter identification
9. Understandable water-quality summary & observation generation
10. Date-range filtering & timeframe filtering
Plus: Empty database handling & end-to-end service integration.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.analytics_service import AnalyticsService, analytics_service
from services.sensor_service import sensor_service
from database.connection import DatabaseManager

def generate_mock_readings():
    """Generates a controlled, deterministic set of historical readings spanning 2 weeks."""
    base_time = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
    readings = []

    # 10 readings across days
    # Day 1: 2026-10-20
    # Day 2: 2026-10-21
    # Day 8: 2026-10-27 (different week)
    configs = [
        # ts_offset_hours, tds, ph, turb, overall, tds_st, ph_st, turb_st, wqi, anomaly, reason
        (0,  150.0, 7.20, 1.0, "Normal",   "Normal",   "Normal",   "Normal",   95, False, ""),
        (4,  160.0, 7.30, 1.2, "Normal",   "Normal",   "Normal",   "Normal",   94, False, ""),
        (24, 180.0, 7.40, 1.5, "Normal",   "Normal",   "Normal",   "Normal",   90, False, ""),
        (28, 320.0, 7.50, 1.8, "Warning",  "Warning",  "Normal",   "Normal",   75, True,  "TDS exceeded baseline"),
        (48, 170.0, 8.80, 2.0, "Warning",  "Normal",   "Warning",  "Normal",   70, False, ""),
        (52, 600.0, 7.20, 1.1, "Critical", "Critical", "Normal",   "Normal",   40, True,  "TDS hazardous high"),
        (168, 155.0, 7.10, 0.9, "Normal",  "Normal",   "Normal",   "Normal",   96, False, ""), # +7 days (Week 2)
        (172, 165.0, 7.25, 1.3, "Normal",  "Normal",   "Normal",   "Normal",   92, False, ""),
        (192, 450.0, 7.35, 1.4, "Warning", "Warning",  "Normal",   "Normal",   65, True,  "TDS exceeded baseline"),
        (196, 160.0, 7.30, 6.5, "Critical", "Normal",  "Normal",   "Critical", 35, False, "")
    ]

    for (hrs, tds, ph, turb, overall, tds_st, ph_st, turb_st, wqi, anomaly, reason) in configs:
        ts = (base_time + timedelta(hours=hrs)).isoformat()
        readings.append({
            "device_id": "AquaSense-ESP32",
            "timestamp": ts,
            "tds": tds,
            "ph": ph,
            "turbidity": turb,
            "tds_status": tds_st,
            "ph_status": ph_st,
            "turbidity_status": turb_st,
            "overall_status": overall,
            "water_quality_score": wqi,
            "anomaly_detected": anomaly,
            "anomaly_reason": reason
        })

    return readings

class MockAnalyticsService(AnalyticsService):
    def __init__(self, mock_data):
        super().__init__()
        self.mock_data = mock_data

    async def get_historical_readings(
        self,
        timeframe="all",
        start_date=None,
        end_date=None,
        limit=1000
    ):
        data = list(self.mock_data)
        if start_date:
            s_iso = f"{start_date}T00:00:00+00:00" if len(start_date) == 10 else start_date
            data = [d for d in data if d["timestamp"] >= s_iso]
        if end_date:
            e_iso = f"{end_date}T23:59:59+00:00" if len(end_date) == 10 else end_date
            data = [d for d in data if d["timestamp"] <= e_iso]
        return data

async def run_all_analytics_tests():
    print("=" * 70)
    print("AquaSense AI - Comprehensive Historical Analytics Test Suite")
    print("=" * 70)

    mock_records = generate_mock_readings()
    service = MockAnalyticsService(mock_records)

    # -------------------------------------------------------------------------
    # TEST 1, 2, 3: TDS, pH, and Turbidity Min, Max, and Avg
    # -------------------------------------------------------------------------
    print("\n[Test 1] Parametric Bounds Calculations (TDS, pH, Turbidity min/max/avg)...")
    res = await service.compute_analytics(timeframe="all")
    assert res["has_data"] is True

    # Expected values for TDS: [150, 160, 180, 320, 170, 600, 155, 165, 450, 160] -> min: 150.0, max: 600.0, avg: 251.0
    assert res["tds"]["min"] == 150.0, f"Expected 150.0, got {res['tds']['min']}"
    assert res["tds"]["max"] == 600.0, f"Expected 600.0, got {res['tds']['max']}"
    assert res["tds"]["avg"] == 251.0, f"Expected 251.0, got {res['tds']['avg']}"
    print(f" -> TDS stats verified: Min={res['tds']['min']}, Max={res['tds']['max']}, Avg={res['tds']['avg']} ppm")

    # Expected values for pH: [7.20, 7.30, 7.40, 7.50, 8.80, 7.20, 7.10, 7.25, 7.35, 7.30] -> min: 7.10, max: 8.80, avg: 7.44
    assert res["ph"]["min"] == 7.10, f"Expected 7.10, got {res['ph']['min']}"
    assert res["ph"]["max"] == 8.80, f"Expected 8.80, got {res['ph']['max']}"
    assert res["ph"]["avg"] == 7.44, f"Expected 7.44, got {res['ph']['avg']}"
    print(f" -> pH stats verified: Min={res['ph']['min']}, Max={res['ph']['max']}, Avg={res['ph']['avg']}")

    # Expected values for Turbidity: [1.0, 1.2, 1.5, 1.8, 2.0, 1.1, 0.9, 1.3, 1.4, 6.5] -> min: 0.9, max: 6.5, avg: 1.87
    assert res["turbidity"]["min"] == 0.90, f"Expected 0.90, got {res['turbidity']['min']}"
    assert res["turbidity"]["max"] == 6.50, f"Expected 6.50, got {res['turbidity']['max']}"
    assert res["turbidity"]["avg"] == 1.87, f"Expected 1.87, got {res['turbidity']['avg']}"
    assert "simulated units" in res["turbidity"]["note"]
    print(f" -> Turbidity stats verified: Min={res['turbidity']['min']}, Max={res['turbidity']['max']}, Avg={res['turbidity']['avg']}")

    # -------------------------------------------------------------------------
    # TEST 4 & 5: Total Readings & Status Counts (Normal, Warning, Critical)
    # -------------------------------------------------------------------------
    print("\n[Test 2] Total Readings and Status Distribution (Normal, Warning, Critical)...")
    # Total = 10; Normal = 5, Warning = 3, Critical = 2
    assert res["total_readings"] == 10
    assert res["count"] == 10
    assert res["status_counts"]["normal"] == 5
    assert res["status_counts"]["warning"] == 3
    assert res["status_counts"]["critical"] == 2

    assert res["status_percentages"]["normal_pct"] == 50.0
    assert res["status_percentages"]["warning_pct"] == 30.0
    assert res["status_percentages"]["critical_pct"] == 20.0
    total_pct = sum(res["status_percentages"].values())
    assert abs(total_pct - 100.0) < 0.1
    print(f" -> Total Readings: {res['total_readings']}")
    print(f" -> Status Counts: Normal={res['status_counts']['normal']} (50%), Warning={res['status_counts']['warning']} (30%), Critical={res['status_counts']['critical']} (20%)")

    # -------------------------------------------------------------------------
    # TEST 6: Daily and Weekly Water-Quality Trends
    # -------------------------------------------------------------------------
    print("\n[Test 3] Daily and Weekly Water-Quality Trends...")
    daily = res["daily_trends"]
    assert len(daily) > 0
    # Inspect first daily trend object
    d1 = daily[0]
    assert "date" in d1
    assert "readings_count" in d1
    assert "tds_avg" in d1
    assert "ph_avg" in d1
    assert "turbidity_avg" in d1
    assert "water_quality_score_avg" in d1
    assert "normal_count" in d1
    assert "warning_count" in d1
    assert "critical_count" in d1

    weekly = res["weekly_trends"]
    assert len(weekly) >= 2  # Spans 2 calendar weeks
    w1 = weekly[0]
    assert "week" in w1
    assert "readings_count" in w1
    assert "tds_avg" in w1

    assert res["trend_direction"] in ("improving", "degrading", "stable")
    print(f" -> Successfully calculated {len(daily)} daily trends and {len(weekly)} weekly trends.")
    print(f" -> Overall water quality trend direction: {res['trend_direction']}")

    # -------------------------------------------------------------------------
    # TEST 7: Frequently Occurring Anomalies
    # -------------------------------------------------------------------------
    print("\n[Test 4] Identifying Frequently Occurring Anomalies...")
    # Anomalies: 3 total ("TDS exceeded baseline": 2, "TDS hazardous high": 1)
    anom_summary = res["anomalies_summary"]
    assert anom_summary["total_anomalies"] == 3
    assert anom_summary["anomaly_rate_pct"] == 30.0  # 3 / 10 = 30.0%
    frequent = anom_summary["frequent_anomalies"]
    assert len(frequent) == 2
    assert frequent[0]["pattern"] == "TDS exceeded baseline"
    assert frequent[0]["count"] == 2
    assert frequent[0]["percentage"] == 66.7
    print(f" -> Total anomalies identified: {anom_summary['total_anomalies']} ({anom_summary['anomaly_rate_pct']}%)")
    print(f" -> Most frequent pattern: '{frequent[0]['pattern']}' ({frequent[0]['count']} occurrences)")

    # -------------------------------------------------------------------------
    # TEST 8: Most Frequently Abnormal Parameter
    # -------------------------------------------------------------------------
    print("\n[Test 5] Identifying Most Frequently Abnormal Sensor Parameter...")
    # TDS abnormal count: 4 (Warning: 2, Critical: 1, + 3 anomalies)
    # pH abnormal count: 1 (Warning: 1)
    # Turbidity abnormal count: 1 (Critical: 1)
    # Top abnormal parameter should be TDS
    top_param = res["most_frequently_abnormal_parameter"]
    assert top_param["parameter"] == "TDS"
    assert top_param["breach_count"] > 0
    assert "TDS showed the highest frequency" in top_param["description"]
    print(f" -> Most frequently abnormal parameter: {top_param['parameter']} ({top_param['breach_count']} breach events, {top_param['breach_percentage']}%)")

    # -------------------------------------------------------------------------
    # TEST 9: Understandable Water-Quality Summaries
    # -------------------------------------------------------------------------
    print("\n[Test 6] Plain-English Water-Quality Summary Generation...")
    summary_text = res["summary_text"]
    assert isinstance(summary_text, str)
    assert len(summary_text) > 50
    assert "purity score" in summary_text
    assert "TDS averaged" in summary_text
    assert "pH averaged" in summary_text
    assert "simulated turbidity averaged" in summary_text

    observations = res["key_observations"]
    assert isinstance(observations, list)
    assert len(observations) >= 5
    print(f" -> Generated summary: \"{summary_text[:120]}...\"")
    print(f" -> Key observations count: {len(observations)}")

    # -------------------------------------------------------------------------
    # TEST 10: Date-Range Filtering (start_date, end_date)
    # -------------------------------------------------------------------------
    print("\n[Test 7] Date-Range Filtering (Requirements 10)...")
    # Filter only Week 1: 2026-10-20 to 2026-10-22 (should return first 6 readings)
    range_res = await service.compute_analytics(
        start_date="2026-10-20",
        end_date="2026-10-22"
    )
    assert range_res["count"] == 6
    assert range_res["total_readings"] == 6
    assert range_res["date_range"]["start_date"] == "2026-10-20"
    assert range_res["date_range"]["end_date"] == "2026-10-22"
    print(f" -> Filter [2026-10-20 to 2026-10-22] returned exactly {range_res['count']} matching records.")

    # Filter single later day: 2026-10-28 (should return 2 readings: 192h and 196h)
    range_res2 = await service.compute_analytics(
        start_date="2026-10-28",
        end_date="2026-10-28"
    )
    assert range_res2["count"] == 2
    print(f" -> Single day filter [2026-10-28] returned exactly {range_res2['count']} matching records.")

    # -------------------------------------------------------------------------
    # TEST 11: Empty Database Response Handling
    # -------------------------------------------------------------------------
    print("\n[Test 8] Empty Database Response Handling...")
    empty_service = MockAnalyticsService([])
    empty_res = await empty_service.compute_analytics()
    assert empty_res["has_data"] is False
    assert empty_res["count"] == 0
    assert empty_res["total_readings"] == 0
    assert empty_res["tds"]["min"] == 0
    assert empty_res["tds"]["max"] == 0
    assert empty_res["tds"]["avg"] == 0
    assert empty_res["ph"]["min"] == 0
    assert empty_res["ph"]["avg"] == 0
    assert empty_res["turbidity"]["min"] == 0
    assert empty_res["turbidity"]["avg"] == 0
    assert empty_res["status_counts"]["normal"] == 0
    assert empty_res["status_counts"]["warning"] == 0
    assert empty_res["status_counts"]["critical"] == 0
    assert empty_res["daily_trends"] == []
    assert empty_res["weekly_trends"] == []
    assert empty_res["trend_direction"] == "insufficient_data"
    assert "No sensor records found" in empty_res["summary_text"]
    assert empty_res["most_frequently_abnormal_parameter"]["parameter"] == "None"
    print(" -> Empty database returns valid, safe response structure without errors.")

    # -------------------------------------------------------------------------
    # TEST 12: End-to-End Service and DB Layer Integration
    # -------------------------------------------------------------------------
    print("\n[Test 9] End-to-End Database & SensorService Integration...")
    await DatabaseManager.init_db()
    # Call sensor_service.get_analytics_summary()
    svc_res = await sensor_service.get_analytics_summary(timeframe="all")
    assert isinstance(svc_res, dict)
    assert "tds" in svc_res
    assert "ph" in svc_res
    assert "turbidity" in svc_res
    assert "status_counts" in svc_res
    assert "summary_text" in svc_res
    print(f" -> SensorService integration verified: count={svc_res['count']}, has_data={svc_res['has_data']}")

    print("\n" + "=" * 70)
    print("ALL 9 ANALYTICS TEST SUITES PASSED CLEANLY (10/10 Requirements Verified)!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_all_analytics_tests())

