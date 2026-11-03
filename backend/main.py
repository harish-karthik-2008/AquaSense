"""
AquaSense AI - Backend Application Entrypoint
FastAPI application providing REST endpoints, WebSockets, MongoDB/persistent storage,
AI anomaly detection, and real-time IoT integration for Wokwi ESP32.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from database.connection import DatabaseManager
from routes import sensor, alerts, device, filter as filter_route, settings as settings_route
from services.websocket_manager import ws_manager
from services.sensor_service import sensor_service
from ai.anomaly_detector import anomaly_detector

async def seed_initial_data_if_empty():
    """Seed a clean baseline of initial readings if database is empty."""
    db = await DatabaseManager.get_db()
    readings_col = db["sensor_readings"]
    count = await readings_col.count_documents()
    
    if count == 0:
        print("[AquaSense AI] Initializing empty database with realistic baseline records...")
        now = datetime.now(timezone.utc)
        baseline_samples = []

        # Generate 25 recent baseline readings over the last 2 hours
        for i in range(25, 0, -1):
            ts = (now - timedelta(minutes=i * 4)).isoformat()
            # Clean municipal purified water baseline
            tds = round(165.0 + random.uniform(-15.0, 15.0), 1)
            ph = round(7.35 + random.uniform(-0.15, 0.15), 2)
            turbidity = round(1.2 + random.uniform(-0.3, 0.4), 2)

            doc = {
                "device_id": "AquaSense-ESP32",
                "timestamp": ts,
                "tds": tds,
                "ph": ph,
                "turbidity": turbidity,
                "tds_status": "Normal",
                "ph_status": "Normal",
                "turbidity_status": "Normal",
                "overall_status": "Normal",
                "water_quality_score": sensor_service.calculate_water_quality_score(tds, ph, turbidity),
                "anomaly_detected": False,
                "anomaly_score": round(random.uniform(5.0, 18.0), 1),
                "anomaly_reason": "Baseline operating state within calibrated parameters.",
                "note": "Turbidity values are simulated based on potentiometer input."
            }
            await readings_col.insert_one(doc)
            baseline_samples.append([tds, ph, turbidity])

        # Pre-seed AI anomaly detector buffer
        anomaly_detector.add_historical_samples(baseline_samples)
        print(f"[AquaSense AI] Successfully pre-seeded {len(baseline_samples)} baseline records.")
    else:
        # Load existing readings into AI buffer
        cursor = readings_col.find().sort("timestamp", -1).limit(60)
        existing = await cursor.to_list(length=60)
        samples = [[r["tds"], r["ph"], r["turbidity"]] for r in reversed(existing) if "tds" in r]
        if samples:
            anomaly_detector.add_historical_samples(samples)
            print(f"[AquaSense AI] Loaded {len(samples)} historical readings into AI anomaly detector.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[AquaSense AI] Starting server...")
    await DatabaseManager.init_db()
    await seed_initial_data_if_empty()
    yield
    # Shutdown
    print("[AquaSense AI] Shutting down...")

app = FastAPI(
    title="AquaSense AI Backend",
    description="Intelligent Water Quality Monitoring Ecosystem API for Atomberg atomQUEST 2026",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend and local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(sensor.router)
app.include_router(alerts.router)
app.include_router(device.router)
app.include_router(filter_route.router)
app.include_router(settings_route.router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time bi-directional WebSocket connection for instant UI updates."""
    await ws_manager.connect(websocket)
    try:
        # Send initial device connection packet
        status = await sensor_service.get_device_status()
        latest = await sensor_service.get_latest_reading()
        await websocket.send_json({
            "type": "connection_established",
            "device": status,
            "latest_reading": latest
        })
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
            # Client can ping or send commands
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        ws_manager.disconnect(websocket)

@app.get("/", summary="API Root and Health Check")
async def root():
    db_status = await DatabaseManager.get_status()
    dev_status = await sensor_service.get_device_status()
    return {
        "project": "AquaSense AI",
        "description": "Intelligent Water Quality Monitoring Ecosystem for Atomberg atomQUEST 2026",
        "status": "operational",
        "device_connected": dev_status.get("is_online", False),
        "database": db_status,
        "endpoints": {
            "post_sensor_data": "POST /api/sensor-data",
            "get_latest_reading": "GET /api/sensor-data/latest",
            "get_history": "GET /api/sensor-data/history",
            "get_analytics": "GET /api/sensor-data/analytics",
            "get_alerts": "GET /api/alerts",
            "get_device_status": "GET /api/device/status",
            "get_filter_health": "GET /api/filter-health",
            "settings": "GET|POST /api/settings",
            "websocket": "ws://localhost:8000/ws"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

