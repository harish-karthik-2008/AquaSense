"""
AquaSense AI - ESP32 Hardware Simulator & Test Sender
Simulates the ESP32 microcontroller and potentiometer hardware sweeps,
sending real HTTP POST requests directly to the FastAPI backend.
"""

import sys
import time
import json
import argparse
import random
import urllib.request
import urllib.error

DEFAULT_BACKEND = "http://localhost:8000/api/sensor-data"

PRESETS = {
    "normal": {
        "tds": 165.0,
        "ph": 7.35,
        "turbidity": 1.4,
        "description": "Standard optimal drinking water parameters (Safe)"
    },
    "high_tds": {
        "tds": 585.0,
        "ph": 7.45,
        "turbidity": 2.1,
        "description": "High Mineral / Hard Water spike (> 500 ppm critical limit)"
    },
    "acidic": {
        "tds": 140.0,
        "ph": 5.2,
        "turbidity": 1.5,
        "description": "Acidic Water breach (< 6.5 pH limit)"
    },
    "alkaline": {
        "tds": 195.0,
        "ph": 9.2,
        "turbidity": 1.8,
        "description": "Alkaline Water breach (> 8.5 pH limit)"
    },
    "turbid": {
        "tds": 220.0,
        "ph": 7.1,
        "turbidity": 14.8,
        "description": "High Turbidity cloudiness (> 10.0 critical limit)"
    },
    "anomaly": {
        "tds": 380.0,
        "ph": 8.9,
        "turbidity": 12.5,
        "description": "Multi-parameter correlation divergence (Triggers AI Anomaly Model)"
    }
}

def send_payload(url: str, tds: float, ph: float, turbidity: float, device_id: str = "AquaSense-ESP32"):
    payload = {
        "tds": round(tds, 1),
        "ph": round(ph, 2),
        "turbidity": round(turbidity, 1),
        "device_id": device_id
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "AquaSense-ESP32-Simulator"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            status = res_json.get("status", "ok")
            data = res_json.get("data", {})
            overall = data.get("overall_status", "Normal")
            wqi = data.get("water_quality_score", 100)
            anomaly = data.get("anomaly_detected", False)
            print(f"[{time.strftime('%H:%M:%S')}] SENT -> TDS: {tds:>5.1f} ppm | pH: {ph:>4.2f} | Turbidity: {turbidity:>4.1f} | Result: {overall:<8} (WQI: {wqi}%) {'[AI ANOMALY]' if anomaly else ''}")
            return True, res_json
    except urllib.error.URLError as e:
        print(f"[{time.strftime('%H:%M:%S')}] Connection failed to {url}: {e}")
        return False, None
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error: {e}")
        return False, None

def run_preset(url: str, preset_name: str, count: int = 1, interval: float = 2.0):
    preset = PRESETS.get(preset_name, PRESETS["normal"])
    print(f"\n>> Running Preset '{preset_name}': {preset['description']}")
    for i in range(count):
        # Add slight natural jitter
        tds = preset["tds"] + random.uniform(-1.5, 1.5)
        ph = preset["ph"] + random.uniform(-0.04, 0.04)
        turb = preset["turbidity"] + random.uniform(-0.1, 0.1)
        send_payload(url, tds, ph, turb)
        if i < count - 1:
            time.sleep(interval)

def run_continuous_stream(url: str, interval: float = 2.5):
    print(f"\n>> Starting continuous live streaming to {url} (Press Ctrl+C to stop)...")
    curr_tds = 160.0
    curr_ph = 7.30
    curr_turb = 1.2

    while True:
        # Smooth random walk
        curr_tds = max(50.0, min(800.0, curr_tds + random.uniform(-4.0, 4.0)))
        curr_ph = max(4.0, min(10.5, curr_ph + random.uniform(-0.06, 0.06)))
        curr_turb = max(0.2, min(25.0, curr_turb + random.uniform(-0.25, 0.25)))

        send_payload(url, curr_tds, curr_ph, curr_turb)
        time.sleep(interval)

def run_potentiometer_sweep(url: str):
    print("\n>> Executing Potentiometer Slider Sweep Test...")
    print("1. Sweeping TDS (100 -> 600 ppm)...")
    for tds in range(120, 620, 70):
        send_payload(url, float(tds), 7.3, 1.2)
        time.sleep(1.0)

    print("\n2. Sweeping pH (5.0 -> 9.5)...")
    for ph_x10 in range(55, 95, 6):
        send_payload(url, 180.0, ph_x10 / 10.0, 1.2)
        time.sleep(1.0)

    print("\n3. Sweeping Turbidity (1.0 -> 15.0)...")
    for turb in range(1, 16, 2):
        send_payload(url, 180.0, 7.3, float(turb))
        time.sleep(1.0)
    print("Sweep complete!\n")

def main():
    parser = argparse.ArgumentParser(description="AquaSense AI ESP32 Hardware Simulator")
    parser.add_argument("--url", default=DEFAULT_BACKEND, help="Backend endpoint URL")
    parser.add_argument("--mode", choices=["normal", "high_tds", "acidic", "alkaline", "turbid", "anomaly", "stream", "sweep"], default="normal")
    parser.add_argument("--count", type=int, default=1, help="Number of packets to send (for presets)")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval in seconds between packets")

    args = parser.parse_args()

    print("==================================================")
    print("       AquaSense AI - ESP32 Hardware Simulator     ")
    print("       Target: " + args.url)
    print("==================================================")

    try:
        if args.mode == "stream":
            run_continuous_stream(args.url, interval=args.interval)
        elif args.mode == "sweep":
            run_potentiometer_sweep(args.url)
        else:
            run_preset(args.url, args.mode, count=args.count, interval=args.interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")

if __name__ == "__main__":
    main()

