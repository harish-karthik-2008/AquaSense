# AquaSense AI – ESP32 Wokwi Simulation Guide

This folder contains the complete, shareable **Wokwi ESP32 simulation project** for AquaSense AI. It allows any developer to clone this repository, run the simulation in their web browser or VS Code, and stream live potentiometer sensor readings directly into their local AquaSense AI backend and React dashboard.

---

## Folder Structure

```
AquaSense/
├── wokwi/
│   ├── diagram.json      # Wokwi circuit schematic (ESP32 DevKit + 3 potentiometers)
│   ├── wokwi.toml        # Wokwi project configuration mapping
│   ├── sketch.ino        # ESP32 Arduino firmware source code
│   └── README.md         # This setup and execution guide
```

---

## Circuit Schematic & GPIO Pin Mapping

| Sensor Parameter | Potentiometer ID | ESP32 GPIO Pin | ADC Channel | Simulated Physical Scale |
| :--- | :--- | :--- | :--- | :--- |
| **TDS (Dissolved Solids)** | `pot_tds` | **GPIO 34** | ADC1_CH6 | `0.0 – 1000.0 ppm` |
| **pH (Acidity/Alkalinity)** | `pot_ph` | **GPIO 35** | ADC1_CH7 | `0.00 – 14.00 pH` |
| **Turbidity (Cloudiness)** | `pot_turb` | **GPIO 32** | ADC1_CH4 | `0.0 – 100.0` (Simulated index) |
| **Transmission LED** | Onboard LED | **GPIO 2** | Digital Output | Flashes on each HTTP POST |

* **Power rails:** Potentiometer VCC pins connect to `3V3`, GND pins connect to `GND`.
* **Serial Monitor:** ESP32 TX/RX connect to the virtual Serial Monitor at `115200` baud.

---

## Step-by-Step Setup Guide (For Another Developer)

Follow these 7 steps to run the simulation on your laptop:

### Step 1: Start the AquaSense AI Backend
In your terminal, navigate to the `backend` folder and start the FastAPI server:

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "data/*"
```

Verify that the backend is running by opening: [http://localhost:8000](http://localhost:8000) (should return `{"status": "operational"}`).

---

### Step 2: Start an ngrok Tunnel
Because the Wokwi browser simulation runs in a sandboxed WebAssembly environment on `Wokwi-GUEST` virtual WiFi, it cannot access `localhost:8000` on your physical laptop directly. Use ngrok to expose your local port 8000:

```bash
ngrok http 8000
```

ngrok will display a public forwarding URL such as:
```
Forwarding   https://abc-123-xyz.ngrok-free.app -> http://localhost:8000
```
Copy your forwarding domain (e.g. `https://abc-123-xyz.ngrok-free.app`).

---

### Step 3: Configure `serverUrl` in `wokwi/sketch.ino`
Open [`wokwi/sketch.ino`](sketch.ino) and update line 38 with your ngrok forwarding URL:

```cpp
// Replace with YOUR active ngrok forwarding domain:
const char* serverUrl = "https://abc-123-xyz.ngrok-free.app/api/sensor-data";
```

> **Note:** Always keep `/api/sensor-data` at the end of the URL.

---

### Step 4: Open the Wokwi Project in Your Browser
You can open and run this simulation in one of two ways:

#### Option A: Wokwi Web Editor (Zero installation)
1. Navigate to: [https://wokwi.com/projects/new/esp32](https://wokwi.com/projects/new/esp32)
2. In the code tab (`sketch.ino`), select all and paste the contents of [`wokwi/sketch.ino`](sketch.ino).
3. Switch to the `diagram.json` tab (click the `diagram.json` tab or create one), and paste the contents of [`wokwi/diagram.json`](diagram.json).
4. All three potentiometers (TDS, pH, Turbidity) and wiring will immediately appear on the canvas.

#### Option B: VS Code with Wokwi Extension
1. Install the **Wokwi Simulator** extension in VS Code.
2. Open the `AquaSense/wokwi` folder in VS Code.
3. Open `diagram.json` and press `F1` -> `Wokwi: Start Simulator`.

---

### Step 5: Start the Simulation & Observe Serial Logs
1. Click the green **Play / Start Simulation** button in Wokwi.
2. Watch the Serial Monitor (bottom-right). You should observe:
   ```text
   ==========================================
     AquaSense AI - ESP32 Wokwi Sensor Node  
     Atomberg atomQUEST 2026 Purifier Monitor
   ==========================================
   [WiFi] Connecting to: Wokwi-GUEST
   .....
   [WiFi] Connected successfully!
   [WiFi] Virtual IP Address: 10.0.1.2
   [HTTP] Target Endpoint: https://abc-123-xyz.ngrok-free.app/api/sensor-data
   ==========================================
   ```

---

### Step 6: Verify HTTP 200 Responses
When the ESP32 takes a reading, it serializes the data into JSON and posts to your backend:

```text
[Sensor Telemetry]: {"tds":245.0,"ph":7.20,"turbidity":2.5,"device_id":"AquaSense-ESP32","simulated":true}
[HTTP] Success (Status 200)
[HTTP] Backend accepted reading.
```

If you see `Status 200`:
* The packet was received and validated by FastAPI (`POST /api/sensor-data`).
* TDS, pH, and Turbidity were checked against alert thresholds.
* The Scikit-Learn IsolationForest AI evaluated multivariate anomaly probability.
* Real-time WebSocket updates were broadcast to connected dashboards.

---

### Step 7: Verify Live Telemetry on the React Dashboard
1. In another terminal, start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
2. Open [http://localhost:5173](http://localhost:5173).
3. The top bar will show `AquaSense ESP32` with a green **online** indicator.
4. In Wokwi, turn any potentiometer knob:
   * **TDS knob (GPIO 34):** Turn clockwise (> 500 ppm) -> Triggers **Critical TDS Alert**.
   * **pH knob (GPIO 35):** Turn counter-clockwise (< 6.5 pH) -> Triggers **Acidic Water Warning**.
   * **Turbidity knob (GPIO 32):** Turn clockwise (> 10 index) -> Triggers **Elevated Turbidity Warning**.
5. Observe the live waveforms and gauges updating immediately without page refresh!

---

## Troubleshooting & FAQ

| Problem | Root Cause | Solution |
| :--- | :--- | :--- |
| `[HTTP] POST failed, error: connection refused` | ngrok is not running or URL is mistyped | Restart `ngrok http 8000` and ensure the URL in `sketch.ino` matches exactly. |
| `[HTTP] POST failed, error: -1` | Insecure HTTP blocked or TLS handshake issue | Use the `https://` version of your ngrok domain. |
| ngrok returns HTML interstitial warning | ngrok free tier browser verification page | The sketch includes `http.addHeader("ngrok-skip-browser-warning", "true");` which bypasses this automatically. |
| Status LED does not blink | Virtual board LED | The onboard blue LED on GPIO 2 flashes briefly during each HTTP send. |
| Missing Arduino libraries | External library dependency | The sketch only uses `<WiFi.h>` and `<HTTPClient.h>`, which are built directly into the ESP32 Arduino core. No library installations are required. |

---

## Security & Sharing Notes
* **No credentials exposed:** `sketch.ino` contains only the placeholder `https://YOUR-NGROK-SUBDOMAIN.ngrok-free.app/api/sensor-data`. Each developer supplies their own tunnel URL.
* **No hardcoded secrets:** Wokwi's virtual WiFi requires no password (`Wokwi-GUEST` with `""`).
* **Safe for public git:** All files in this folder are safe to commit and push to public GitHub repositories.

