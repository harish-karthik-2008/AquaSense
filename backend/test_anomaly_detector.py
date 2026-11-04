"""
AquaSense AI - Comprehensive Anomaly Detector Unit & Regression Tests
Tests:
- Fix 1: Counter-based retraining cadence (no retraining every request at 150 items)
- Fix 2: Buffer contamination prevention & clean baseline separation
- Fix 3: False-positive suppression for flat readings & noise vs genuine deviation detection
- Warmup safety & sustained anomaly adaptation
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.anomaly_detector import SensorAnomalyDetector

def test_warmup_and_basic_ingestion():
    print("[Test 1/5] Testing Warmup Behavior (12 samples)...")
    detector = SensorAnomalyDetector(min_samples_for_ml=12, max_buffer_size=150)
    assert detector.model is None
    assert detector.total_samples_analyzed == 0

    # Ingest 11 samples (warmup phase)
    for i in range(11):
        res = detector.analyze_reading(tds=165.0, ph=7.35, turbidity=1.2)
        assert res["anomaly_detected"] is False
        assert res["anomaly_score"] == 0.0
        assert "Establishing baseline" in res["explanation"]
        assert detector.total_samples_analyzed == i + 1

    assert detector.model is None  # Still in warmup
    assert len(detector.history_buffer) == 11

    # 12th sample completes warmup and triggers initial model fit
    res12 = detector.analyze_reading(tds=166.0, ph=7.34, turbidity=1.25)
    assert detector.model is not None
    assert len(detector.history_buffer) == 12
    assert detector.total_samples_analyzed == 12
    print(" -> Warmup successfully completed: initial model trained cleanly.")

def test_flat_sensor_readings_and_jitter_suppression():
    print("\n[Test 2/5] Testing Flat Readings & Potentiometer Jitter Suppression (Fix 3)...")
    detector = SensorAnomalyDetector(min_samples_for_ml=12, max_buffer_size=150)
    
    # Establish steady baseline with 20 readings of identical/flat values
    for _ in range(20):
        detector.analyze_reading(tds=170.0, ph=7.40, turbidity=1.2)

    assert detector.baseline_stats["tds"]["std"] >= detector.min_std_floors["tds"]
    assert detector.baseline_stats["ph"]["std"] >= detector.min_std_floors["ph"]
    assert detector.baseline_stats["turbidity"]["std"] >= detector.min_std_floors["turbidity"]

    # Test small potentiometer noise/jitter that previously caused false positives
    jitter_tests = [
        (173.0, 7.42, 1.3),   # +3 ppm TDS, +0.02 pH
        (168.0, 7.36, 1.15),  # -2 ppm TDS, -0.04 pH
        (172.5, 7.45, 1.4),   # +2.5 ppm TDS, +0.05 pH, +0.2 turb
        (167.0, 7.38, 1.1),   # -3 ppm TDS
    ]

    for tds, ph, turb in jitter_tests:
        res = detector.analyze_reading(tds=tds, ph=ph, turbidity=turb, sensitivity="medium")
        assert res["anomaly_detected"] is False, (
            f"False positive triggered for minor jitter ({tds}, {ph}, {turb}): "
            f"Z-scores={res['z_scores']}, explanation={res['explanation']}"
        )
    print(" -> Minor potentiometer jitters correctly ignored without false positives.")

def test_genuine_anomaly_detection():
    print("\n[Test 3/5] Testing Genuine Anomaly Detection...")
    detector = SensorAnomalyDetector(min_samples_for_ml=12, max_buffer_size=150)

    # Establish baseline around 165 ppm TDS, 7.35 pH, 1.2 Turbidity
    for _ in range(25):
        detector.analyze_reading(tds=165.0, ph=7.35, turbidity=1.2)

    # 1. Severe TDS Spike
    res_tds = detector.analyze_reading(tds=450.0, ph=7.35, turbidity=1.2)
    assert res_tds["anomaly_detected"] is True
    assert res_tds["parameter"] == "TDS"
    assert res_tds["z_scores"]["TDS"] > 2.5
    print(f" -> Large TDS spike detected: {res_tds['parameter']} (Z={res_tds['z_scores']['TDS']:.1f})")

    # 2. Severe pH Drop (acidic contamination)
    res_ph = detector.analyze_reading(tds=165.0, ph=4.8, turbidity=1.2)
    assert res_ph["anomaly_detected"] is True
    assert res_ph["parameter"] == "pH"
    assert res_ph["z_scores"]["pH"] > 2.5
    print(f" -> Severe pH drop detected: {res_ph['parameter']} (Z={res_ph['z_scores']['pH']:.1f})")

    # 3. Severe Turbidity Spike
    res_turb = detector.analyze_reading(tds=165.0, ph=7.35, turbidity=8.5)
    assert res_turb["anomaly_detected"] is True
    assert res_turb["parameter"] == "Turbidity"
    assert res_turb["z_scores"]["Turbidity"] > 2.5
    print(f" -> High Turbidity spike detected: {res_turb['parameter']} (Z={res_turb['z_scores']['Turbidity']:.1f})")

def test_buffer_contamination_prevention():
    print("\n[Test 4/5] Testing Anomaly Baseline Contamination Prevention (Fix 2)...")
    detector = SensorAnomalyDetector(min_samples_for_ml=12, max_buffer_size=150)

    # Establish clean baseline
    for _ in range(20):
        detector.analyze_reading(tds=170.0, ph=7.4, turbidity=1.2)

    initial_buffer_len = len(detector.history_buffer)
    initial_tds_mean = detector.baseline_stats["tds"]["mean"]

    # Send 15 consecutive abnormal spike readings (e.g. muddy contaminated water: TDS 480, Turb 9.0)
    for _ in range(15):
        res = detector.analyze_reading(tds=480.0, ph=7.4, turbidity=9.0)
        assert res["anomaly_detected"] is True

    # Crucial assertion: the clean baseline buffer length must NOT have grown from anomalies
    assert len(detector.history_buffer) == initial_buffer_len, (
        f"Contamination error! History buffer grew from {initial_buffer_len} to {len(detector.history_buffer)}"
    )
    # The mean must still reflect clean municipal water, not contaminated water
    assert abs(detector.baseline_stats["tds"]["mean"] - initial_tds_mean) < 1.0, (
        f"Baseline TDS mean contaminated! Was {initial_tds_mean}, now {detector.baseline_stats['tds']['mean']}"
    )
    print(" -> Anomaly contamination successfully prevented: baseline buffer remains pure.")

def test_sustained_abnormal_readings_and_adaptation():
    print("\n[Test 5/6] Testing Sustained Abnormal Readings & Adaptation...")
    detector = SensorAnomalyDetector(min_samples_for_ml=12, max_buffer_size=150)

    # Establish clean baseline (TDS 165 ppm)
    for _ in range(25):
        detector.analyze_reading(tds=165.0, ph=7.35, turbidity=1.2)

    initial_mean = detector.baseline_stats["tds"]["mean"]
    assert abs(initial_mean - 165.0) < 1.0

    # Sustained shift to new source water (TDS 260 ppm)
    # 1. Readings 1 to 40 are rejected from buffer to protect from transient incidents
    for i in range(40):
        res = detector.analyze_reading(tds=260.0, ph=7.35, turbidity=1.2)
        assert res["anomaly_detected"] is True
        assert detector.consecutive_anomalies == i + 1

    assert abs(detector.baseline_stats["tds"]["mean"] - initial_mean) < 1.0
    print(" -> First 40 sustained abnormal readings isolated from clean baseline.")

    # 2. Readings 41+ begin gradual baseline adaptation to prevent permanent freezing
    for _ in range(25):
        detector.analyze_reading(tds=260.0, ph=7.35, turbidity=1.2)

    # The baseline should now adapt towards the new sustained level
    new_mean = detector.baseline_stats["tds"]["mean"]
    assert new_mean > initial_mean + 15.0, (
        f"Baseline failed to adapt! Old: {initial_mean}, New: {new_mean}"
    )
    print(f" -> Sustained adaptation verified: baseline shifted from {initial_mean:.1f} to {new_mean:.1f} ppm.")

def test_counter_retraining_cadence_at_capacity():
    print("\n[Test 6/6] Testing Retraining Cadence and 150-Sample Capacity (Fix 1)...")
    detector = SensorAnomalyDetector(min_samples_for_ml=12, max_buffer_size=150)

    # Fill buffer to capacity (150 normal samples)
    for i in range(150):
        detector.analyze_reading(tds=165.0 + (i % 5), ph=7.35, turbidity=1.2)

    assert len(detector.history_buffer) == 150
    assert detector.total_samples_analyzed == 150

    # Instrument _retrain to monitor calls
    detector.eligible_samples_since_retrain = 0
    retrain_count = 0
    original_retrain = detector._retrain
    def monitored_retrain():
        nonlocal retrain_count
        retrain_count += 1
        original_retrain()
    detector._retrain = monitored_retrain

    # Send 25 normal samples
    # Under the old code (len % 10 == 0 when len is always 150), it retrained 25 times!
    # Under Fix 1, it should retrain exactly 2 times (at sample 10 and sample 20)
    for i in range(25):
        detector.analyze_reading(tds=166.0, ph=7.36, turbidity=1.22)

    assert retrain_count == 2, (
        f"Retraining cadence bug! Expected exactly 2 retrains over 25 samples, got {retrain_count} retrains."
    )
    assert len(detector.history_buffer) == 150, "Rolling buffer must not exceed 150 items"
    assert detector.total_samples_analyzed == 175
    print(f" -> Retraining verified: exactly {retrain_count} retrains over 25 samples at full 150 capacity.")

def run_all_tests():
    print("=" * 60)
    print("  AquaSense AI - Anomaly Detector Verification Suite")
    print("=" * 60)
    test_warmup_and_basic_ingestion()
    test_flat_sensor_readings_and_jitter_suppression()
    test_genuine_anomaly_detection()
    test_buffer_contamination_prevention()
    test_sustained_abnormal_readings_and_adaptation()
    test_counter_retraining_cadence_at_capacity()
    print("\n" + "=" * 60)
    print("  ALL 6/6 ANOMALY DETECTOR TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
