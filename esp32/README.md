# AquaSense AI – ESP32 Sensor Integration Guide

This directory contains the firmware, schematic wiring diagram, and test simulation tools for connecting the simulated ESP32 microcontroller to the **AquaSense AI** backend.

---

## 1. Hardware & Sensor Pin Mapping

| Sensor Parameter | Microcontroller Pin | ADC Channel | Simulated Physical Range |
| :--- | :--- | :--- | :--- |
| **TDS (Total Dissolved Solids)** | `GPIO 34` | ADC1_CH6 | 0 – 1000 ppm |
| **pH (Acidity / Alkalinity)** | `GPIO 35` | ADC1_CH7 | 0.0 – 14.0 pH |
| **Turbidity (Simulated Scale)** | `GPIO 32` | ADC1_CH4 | 0.0 – 100.0 (Simulated index) |
| **Transmission LED** | `GPIO 2` | Digital Out | Flashes on HTTP POST |

> **IMPORTANT Note on Turbidity**: The Wokwi simulator uses an illustrative conversion formula from potentiometer input. It is explicitly labeled in the UI as **Simulated Turbidity** and not scientifically calibrated NTU until physical photodiode calibration is completed.

---

## 2. Wokwi Simulator Setup

### Step A: Opening in Wokwi
1. Visit [Wokwi ESP32 Simulator](https://wokwi.com/projects/new/esp32).
2. Paste the contents of `sketch.ino` into the code editor.
3. Replace the `diagram.json` tab with `diagram.json` from this folder to automatically wire the three potentiometers.

### Step B: Networking Architecture (Wokwi to Backend)
Because the Wokwi browser simulator runs in a sandboxed WebAssembly environment, it connects to a virtual network (`Wokwi-GUEST`) with IP `10.0.1.2`. It cannot directly reach `http://localhost:8000` on your physical machine without a bridge or tunnel.

Choose one of the three supported networking methods below:

#### Method 1: Local Tunnel (Easiest for Wokwi Web)
1. Start your AquaSense backend:
   ```bash
   cd backend
   python main.py
   ```
2. Open a tunnel using localtunnel or ngrok:
   ```bash
   npx localtunnel --port 8000
   # OR
   ngrok http 8000
   ```
3. Copy the generated URL (e.g., `https://smart-water-atom.loca.lt`).
4. In `sketch.ino`, set:
   ```cpp
   const char* serverUrl = "https://smart-water-atom.loca.lt/api/sensor-data";
   ```
5. Click **Start Simulation** in Wokwi. Adjust any potentiometer and watch the dashboard update live!

#### Method 2: Wokwi IoT Gateway (For VS Code Extension)
1. Download the [Wokwi IoT Gateway](https://github.com/wokwi/wokwi-iot-gateway/releases).
2. Run the gateway on your computer.
3. Find your PC's local IP address (e.g. `192.168.1.45`).
4. In `sketch.ino`, set:
   ```cpp
   const char* serverUrl = "http://192.168.1.45:8000/api/sensor-data";
   ```

#### Method 3: Built-in Python ESP32 Hardware Simulator (`simulate_esp32.py`)
If you want to immediately test live dashboard updates, threshold triggers, and AI anomaly detection without setting up a tunnel:
```bash
# 1. Continuous smooth potentiometer walk
python esp32/simulate_esp32.py --mode stream

# 2. Automated slider sweep (TDS -> pH -> Turbidity)
python esp32/simulate_esp32.py --mode sweep

# 3. Trigger specific alert conditions:
python esp32/simulate_esp32.py --mode high_tds   # Triggers >500 ppm alert
python esp32/simulate_esp32.py --mode acidic     # Triggers <6.5 pH alert
python esp32/simulate_esp32.py --mode turbid     # Triggers >10 turbidity alert
python esp32/simulate_esp32.py --mode anomaly    # Triggers AI Anomaly Isolation Forest
```

---

## 3. Communication Protocol

### HTTP POST Request
- **URL**: `POST /api/sensor-data`
- **Headers**: `Content-Type: application/json`
- **Payload**:
  ```json
  {
    "tds": 245.0,
    "ph": 7.20,
    "turbidity": 2.5,
    "device_id": "AquaSense-ESP32"
  }
  ```

### Backend Processing
1. Backend validates and stores the reading with UTC timestamp in MongoDB.
2. Checks fixed thresholds for TDS, pH, and Turbidity.
3. Evaluates Scikit-Learn Isolation Forest & Z-Score anomaly detector.
4. Emits real-time WebSocket packet to all connected dashboard browsers.

