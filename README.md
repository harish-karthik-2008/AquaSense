# AquaSense AI – Intelligent Water Quality Monitoring Ecosystem
### Developed for Atomberg atomQUEST 2026 – Track 2: Water Purifier

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?logo=react)](https://react.dev)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32_Wokwi-E7352C?logo=espressif)](https://wokwi.com)
[![Scikit-Learn](https://img.shields.io/badge/AI-Scikit--Learn-F7931E?logo=scikit-learn)](https://scikit-learn.org)
[![Atomberg Design](https://img.shields.io/badge/Brand_Theme-Atomberg_Purple-2E0854)](https://atomberg.com)

**AquaSense AI** is a commercial-grade IoT water quality monitoring dashboard and analytics platform engineered to integrate with smart household water purifiers. Built around Atomberg's consumer electronics aesthetic, AquaSense AI streams real-time telemetry from a simulated ESP32 microcontroller, analyzes multi-parameter water health using machine learning anomaly detection, manages predictive purifier filter maintenance, and delivers actionable incident alerts.

---

## 1. Monitored Parameters

| Parameter | Unit / Scale | Sensor Hardware | Standard Safe Range | Purifier Filtration Role |
| :--- | :--- | :--- | :--- | :--- |
| **TDS (Total Dissolved Solids)** | `ppm` | Potentiometer on `GPIO 34` | < 300 ppm (Warning: 300–500, Critical: >500) | Validates Stage 3 RO membrane salt rejection |
| **pH (Acidity / Alkalinity)** | `pH (0 – 14)` | Potentiometer on `GPIO 35` | 6.5 – 8.5 pH | Validates Stage 4 alkaline mineralizer balance |
| **Turbidity (Simulated Scale)** | `Arbitrary units` | Potentiometer on `GPIO 32` | < 5.0 (Warning: 5.0–10.0, Critical: >10.0) | Validates Stage 1 PP sediment pre-filter clarity |

> **IMPORTANT Note on Turbidity**: The Wokwi simulator uses an illustrative conversion formula from potentiometer input. The dashboard explicitly labels this as **Simulated Turbidity** rather than scientifically calibrated NTU.

---

## 2. System Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                   Wokwi ESP32 Node                     │
       │  • ESP32 DevKit V1 (3x Potentiometers on GPIO 34,35,32)│
       │  • WiFi "Wokwi-GUEST"                                  │
       └───────────────────────────┬────────────────────────────┘
                                   │ HTTP POST /api/sensor-data
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 FastAPI Python Backend                 │
       │  • Ingestion & Pydantic Data Validation                │
       │  • Scikit-Learn IsolationForest Anomaly Detection      │
       │  • Smart Alert Engine & Deduplication Debounce         │
       │  • Predictive Multi-Stage Filter Lifecycle Calculator  │
       └──────────────┬──────────────────────────┬──────────────┘
                      │                          │
        Persistent DB │                          │ WebSocket (/ws) & REST
                      ▼                          ▼
       ┌────────────────────────┐      ┌────────────────────────┐
       │   MongoDB / Fallback   │      │    React Dashboard     │
       │  • sensor_readings     │      │  • Atomberg UI Theme   │
       │  • alerts              │      │  • Live Waveforms      │
       │  • filter_health       │      │  • Filter Telemetry    │
       │  • device_status       │      │  • Hardware Simulator  │
       └────────────────────────┘      └────────────────────────┘
```

---

## 3. Key Dashboard Features

### 🌟 Atomberg Brand Identity
- **Primary Palette**: Atomberg deep regal purple (`#2E0854`), sleek violet accents (`#7B2CBF`), clean neutral backgrounds (`#F8F9FC`), and dark charcoal typography (`#191C24`).
- **Typography & Components**: Inter geometric sans-serif, rounded cards (`border-radius: 16px`), subtle drop shadows, and responsive layouts across desktop, tablet, and mobile.

### 📊 1. Water Quality Overview
- Three large sensor cards for **TDS**, **pH**, and **Simulated Turbidity** with:
  - Tabular high-contrast numeric values.
  - Interactive SVG circular and bar gauges.
  - Dynamic status pills (**Normal** green, **Warning** amber, **Critical** red).
  - Previous reading comparison (`+2.5 ppm vs prev`).
  - Visual 0–14 pH scale with pinpoint marker.
- Overall Water Quality Index (0–100%) score.
- Live system status and active alerts summary.

### ⚡ 2. Live Sensor Telemetry
- Real-time line charts updating smoothly over WebSocket as ESP32 data arrives.
- Metric selector: view all three curves or isolate TDS, pH, or Turbidity.
- Controls to pause/resume waveform streaming or reset the point buffer.
- Live Ingestion Table logging every incoming reading with millisecond timestamps.

### 📈 3. Water Quality Analytics
- Historical trend visualization with timeframe filters: **1 Hour**, **24 Hours**, **7 Days**, **All Time**.
- Calculated statistical summary cards: **Minimum**, **Maximum**, and **Average** for each parameter.
- Searchable, paginated measurements log with **1-click CSV export**.
- Empty states when historical data is insufficient.

### 🚨 4. Smart Alerts & Notifications
- Detects threshold breaches, pH range violations, turbidity cloudiness spikes, and sensor disconnects.
- **AI Anomaly Alarms**: Powered by Scikit-Learn Isolation Forest, detecting subtle multi-parameter correlation divergence even when individual readings are below fixed thresholds.
- **Smart Deduplication**: Automatically debounces repetitive alerts for continuous conditions to eliminate spam.
- Individual and batch alert acknowledgement with persistent state.

### 💧 5. Predictive Filter Health
- Multi-stage purifier breakdown:
  1. *Stage 1: Sediment Pre-Filter (PP Spun)* – Traps visible turbidity & suspended particles.
  2. *Stage 2: Pre-Carbon Block Filter* – Adsorbs chlorine, pesticides, and foul odors.
  3. *Stage 3: RO Membrane (High Recovery)* – Rejects dissolved mineral salts and heavy metals.
  4. *Stage 4: Post-Carbon & Alkaline Mineralizer* – Balances pH (6.5–8.5) and enriches essential minerals.
- Estimated remaining life percentage, operating hours counter, and processed water volume (Liters).
- "Simulate Cartridge Service" action to simulate technician filter replacement.
- Clearly labeled demonstration telemetry model ready for hardware drop-in.

### 🕹️ 6. Device Management & Built-in Hardware Simulator
- Complete hardware pinout and Wokwi setup guide.
- **Interactive UI Potentiometer Simulator**: Allows hackathon judges to simulate potentiometer sweeps and test alerts right from the web browser!

---

## 4. Quick Start Guide

### Prerequisites
- Python 3.10+ (FastAPI, Scikit-learn, Uvicorn, Pydantic, Motor)
- Node.js 18+ & npm

---

### Step 1: Start the Backend Server

```bash
cd backend
python main.py
```
The FastAPI backend will start at `http://localhost:8000`.
- API Documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

> **Database Note**: The backend connects to MongoDB if running. If MongoDB is offline, it automatically initializes a high-performance persistent JSON document store (`backend/data/aquasense_db.json`), guaranteeing 100% zero-configuration startup.

---

### Step 2: Start the Frontend Application

```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

### Step 3: Connect ESP32 Sensor Readings

Choose **Option A** (Wokwi simulator) or **Option B** (Built-in Python simulator):

#### Option A: Wokwi Online ESP32 Simulator
1. Open the [Wokwi ESP32 Simulator](https://wokwi.com/projects/new/esp32).
2. Paste the C++ code from `esp32/sketch.ino` into the code editor.
3. Replace the `diagram.json` tab with `esp32/diagram.json` to auto-wire the potentiometers.
4. Expose your local backend port:
   ```bash
   npx localtunnel --port 8000
   ```
5. In `sketch.ino`, set:
   ```cpp
   const char* serverUrl = "https://your-localtunnel-url.loca.lt/api/sensor-data";
   ```
6. Click **Play** in Wokwi. Turn the potentiometers and watch the dashboard update live!

#### Option B: Built-in Python ESP32 Simulator (Instant Demo)
```bash
# Continuous smooth potentiometer random walk
python esp32/simulate_esp32.py --mode stream

# Automated potentiometer sweep (TDS -> pH -> Turbidity)
python esp32/simulate_esp32.py --mode sweep

# Trigger specific test alerts:
python esp32/simulate_esp32.py --mode high_tds   # > 500 ppm critical breach
python esp32/simulate_esp32.py --mode acidic     # < 6.5 pH breach
python esp32/simulate_esp32.py --mode turbid     # > 10.0 turbidity breach
python esp32/simulate_esp32.py --mode anomaly    # AI anomaly pattern detection
```

---

## 5. REST & WebSocket API Specification

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/sensor-data` | Ingests ESP32 reading `{"tds": 245.0, "ph": 7.2, "turbidity": 2.5}` |
| `GET` | `/api/sensor-data/latest` | Returns most recent water quality reading and status |
| `GET` | `/api/sensor-data/history` | Historical readings (`?limit=50&timeframe=24h`) |
| `GET` | `/api/sensor-data/analytics` | Statistical calculations (Min, Max, Avg) |
| `GET` | `/api/alerts` | List of alerts (`?status=active` or `?status=acknowledged`) |
| `POST` | `/api/alerts/{id}/acknowledge` | Acknowledges an active alert |
| `POST` | `/api/alerts/acknowledge-all` | Batch acknowledges all active alerts |
| `DELETE`| `/api/alerts/clear-acknowledged` | Clears acknowledged alert history |
| `GET` | `/api/device/status` | Microcontroller connectivity & heartbeat status |
| `GET` | `/api/filter-health` | Purifier multi-stage filter condition and operating hours |
| `POST` | `/api/filter-health/reset` | Resets filter condition to 100% (maintenance simulation) |
| `GET` | `/api/settings` | Gets warning/critical threshold limits |
| `POST` | `/api/settings` | Updates threshold limits and AI sensitivity |
| `WS` | `/ws` | Real-time WebSocket event stream (`sensor_update`, `alert_triggered`) |

---

## 6. Project File Structure

```text
AquaSense/
├── backend/
│   ├── main.py                  # FastAPI server entrypoint & WebSocket endpoint
│   ├── routes/
│   │   ├── sensor.py            # /api/sensor-data routes
│   │   ├── alerts.py            # /api/alerts routes
│   │   ├── device.py            # /api/device/status route
│   │   ├── filter.py            # /api/filter-health route
│   │   └── settings.py          # /api/settings routes
│   ├── models/
│   │   ├── sensor.py            # Pydantic schemas for readings
│   │   ├── alert.py             # Alert models
│   │   ├── filter.py            # Multi-stage purifier schemas
│   │   └── settings.py          # Threshold configuration schemas
│   ├── services/
│   │   ├── sensor_service.py    # Ingestion, scoring, and telemetry logic
│   │   ├── alert_service.py     # Threshold & anomaly evaluation with deduplication
│   │   ├── filter_service.py    # Purifier wear and volume modeling
│   │   └── websocket_manager.py # Real-time pub/sub client broadcaster
│   ├── database/
│   │   └── connection.py        # MongoDB client + local JSON fallback store
│   ├── ai/
│   │   └── anomaly_detector.py  # Scikit-Learn IsolationForest & Z-score detector
│   ├── data/                    # Persistent storage directory
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment configuration template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      # Atomberg collapsible navigation
│   │   │   ├── Topbar.jsx       # Header with status pills and alerts bell
│   │   │   ├── SensorCard.jsx   # TDS, pH, and Turbidity cards
│   │   │   ├── PhScaleGauge.jsx # Interactive 0-14 pH gradient scale
│   │   │   ├── CircularGauge.jsx# SVG circular progress gauge
│   │   │   └── StatusBadge.jsx  # Reusable status indicator
│   │   ├── pages/
│   │   │   ├── Overview.jsx     # Main overview dashboard
│   │   │   ├── LiveMonitoring.jsx # Real-time waveform streaming page
│   │   │   ├── Analytics.jsx    # Historical charts, stats, and CSV export
│   │   │   ├── Alerts.jsx       # Incident management & alert resolution
│   │   │   ├── FilterHealth.jsx # Multi-stage purifier maintenance cockpit
│   │   │   ├── DeviceManagement.jsx # Telemetry & built-in hardware simulator
│   │   │   └── Settings.jsx     # Threshold tuning interface
│   │   ├── charts/
│   │   │   ├── LiveLineChart.jsx # Recharts real-time multi-metric waveform
│   │   │   └── AnalyticsChart.jsx # Recharts historical trend area graph
│   │   ├── services/
│   │   │   ├── api.js           # REST API client
│   │   │   └── websocket.js     # Resilient WebSocket streaming manager
│   │   ├── styles/
│   │   │   ├── theme.css        # Atomberg brand tokens & color variables
│   │   │   ├── layout.css       # App shell, sidebar, and topbar styling
│   │   │   └── components.css   # Cards, gauges, tables, and buttons
│   │   ├── App.jsx              # Main React container & WebSocket listeners
│   │   └── main.jsx             # React DOM entrypoint
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── esp32/
│   ├── sketch.ino               # Arduino C++ firmware for Wokwi ESP32
│   ├── diagram.json             # Wokwi wiring diagram (ESP32 + 3 potentiometers)
│   ├── simulate_esp32.py        # CLI simulator for automated testing & sweeps
│   └── README.md                # Hardware pinout & networking guide
└── README.md                    # Project documentation
```

---

## 7. Atomberg Hackathon Alignment

- **Track 2: Water Purifier Focus**: Directly addresses smart household water purifier maintenance, consumable cartridge tracking, and drinking safety.
- **Brand Consistency**: Adheres strictly to Atomberg's deep purple aesthetic, minimalism, and premium consumer electronics interface design.
- **Industrial Readiness**: Fixed thresholds are cleanly separated from Scikit-learn multivariate anomaly models; sensor telemetry is decoupled from physical cartridge wear models.
- **Disclaimers**: Explicitly acknowledges that the 3 potentiometers measure TDS, pH, and simulated turbidity and do not detect biological pathogens (bacteria/viruses) or specific heavy metals, maintaining scientific integrity.

---

© 2026 AquaSense AI Team – Developed for Atomberg atomQUEST 2026.

