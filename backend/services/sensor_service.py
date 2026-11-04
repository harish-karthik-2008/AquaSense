"""
Sensor Service for AquaSense AI
Processes, enriches, validates and persists incoming sensor readings,
evaluates water quality scores, triggers alerts, and updates live telemetry.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np

from database.connection import DatabaseManager
from models.sensor import SensorReadingInput, SensorReading
from ai.anomaly_detector import anomaly_detector
from services.alert_service import alert_service
from services.filter_service import filter_service
from services.websocket_manager import ws_manager
from services.analytics_service import analytics_service

class SensorService:
    def __init__(self):
        self.device_heartbeats: Dict[str, Dict[str, Any]] = {}
        self._default_settings = {
            "tds_warning_threshold": 300.0,
            "tds_critical_threshold": 500.0,
            "ph_min_acceptable": 6.5,
            "ph_max_acceptable": 8.5,
            "turbidity_warning_threshold": 5.0,
            "turbidity_critical_threshold": 10.0,
            "anomaly_sensitivity": "medium",
            "heartbeat_timeout_seconds": 25,
            "filter_warning_threshold": 30.0,
            "filter_critical_threshold": 15.0,
            "filter_max_operating_hours": 2000.0
        }

    async def get_readings_collection(self):
        db = await DatabaseManager.get_db()
        return db["sensor_readings"]

    async def get_settings(self) -> Dict[str, Any]:
        db = await DatabaseManager.get_db()
        settings_col = db["settings"]
        doc = await settings_col.find_one({"_id": "threshold_settings"})
        if not doc:
            doc = dict(self._default_settings)
            doc["_id"] = "threshold_settings"
            await settings_col.insert_one(doc)
        return doc

    async def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        db = await DatabaseManager.get_db()
        settings_col = db["settings"]
        await settings_col.update_one(
            {"_id": "threshold_settings"},
            {"$set": new_settings}
        )
        return await self.get_settings()

    def calculate_water_quality_score(self, tds: float, ph: float, turbidity: float) -> float:
        """
        Compute an aggregate water purity index from 0 to 100 based on standard
        drinking water criteria (WHO/BIS parameters).
        """
        score = 100.0

        # TDS penalty (Optimal: 50-250 ppm)
        if tds > 300:
            score -= min(35.0, (tds - 300) * 0.12)
        elif tds < 30:
            score -= 10.0  # demineralized / overly low minerals

        # pH penalty (Optimal: 7.0 - 7.8)
        if ph < 6.5:
            score -= min(35.0, (6.5 - ph) * 20.0)
        elif ph > 8.5:
            score -= min(35.0, (ph - 8.5) * 20.0)

        # Turbidity penalty (Optimal: < 1.0; acceptable < 5.0)
        if turbidity > 5.0:
            score -= min(30.0, (turbidity - 5.0) * 3.5)
        elif turbidity > 2.0:
            score -= min(10.0, (turbidity - 2.0) * 2.0)

        return round(float(np.clip(score, 5.0, 100.0)), 1)

    async def process_reading(self, input_data: SensorReadingInput) -> Dict[str, Any]:
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        settings = await self.get_settings()
        tds = input_data.tds
        ph = input_data.ph
        turbidity = input_data.turbidity
        device_id = input_data.device_id or "AquaSense-ESP32"

        # Determine individual parameter statuses
        tds_status = "Normal"
        if tds >= settings.get("tds_critical_threshold", 500.0):
            tds_status = "Critical"
        elif tds >= settings.get("tds_warning_threshold", 300.0):
            tds_status = "Warning"

        ph_status = "Normal"
        ph_min = settings.get("ph_min_acceptable", 6.5)
        ph_max = settings.get("ph_max_acceptable", 8.5)
        if ph < (ph_min - 1.0) or ph > (ph_max + 1.0):
            ph_status = "Critical"
        elif ph < ph_min or ph > ph_max:
            ph_status = "Warning"

        turbidity_status = "Normal"
        if turbidity >= settings.get("turbidity_critical_threshold", 10.0):
            turbidity_status = "Critical"
        elif turbidity >= settings.get("turbidity_warning_threshold", 5.0):
            turbidity_status = "Warning"

        # Overall Status
        if "Critical" in (tds_status, ph_status, turbidity_status):
            overall_status = "Critical"
        elif "Warning" in (tds_status, ph_status, turbidity_status):
            overall_status = "Warning"
        else:
            overall_status = "Normal"

        # Water Quality Index Score
        wqi = self.calculate_water_quality_score(tds, ph, turbidity)

        # AI Anomaly Detection (Separate from fixed thresholds)
        sensitivity = settings.get("anomaly_sensitivity", "medium")
        ai_res = anomaly_detector.analyze_reading(tds, ph, turbidity, sensitivity=sensitivity)

        # Alerts evaluation & deduplication
        await alert_service.evaluate_reading(tds, ph, turbidity, settings, ai_res)

        # Filter usage increment
        await filter_service.increment_usage(liters=0.2, tds=tds, turbidity=turbidity, device_id=device_id)

        # Intelligent Recommendation Engine synthesis
        try:
            from services.recommendation_service import recommendation_service
            await recommendation_service.evaluate_and_generate_recommendations(
                current_reading={
                    "tds": tds,
                    "ph": ph,
                    "turbidity": turbidity,
                    "overall_status": overall_status,
                    "water_quality_score": wqi,
                    "anomaly_detected": ai_res.get("anomaly_detected", False),
                    "anomaly_score": ai_res.get("anomaly_score", 0.0),
                    "anomaly_reason": ai_res.get("explanation"),
                    "anomaly_parameter": ai_res.get("parameter")
                },
                trigger_broadcast=True
            )
        except Exception:
            pass

        # Update Device Heartbeat
        self.device_heartbeats[device_id] = {
            "last_seen": now_iso,
            "last_tds": tds,
            "last_ph": ph,
            "last_turbidity": turbidity,
            "status": "online"
        }

        # Build reading record
        reading_doc = {
            "device_id": device_id,
            "timestamp": now_iso,
            "tds": tds,
            "ph": ph,
            "turbidity": turbidity,
            "tds_status": tds_status,
            "ph_status": ph_status,
            "turbidity_status": turbidity_status,
            "overall_status": overall_status,
            "water_quality_score": wqi,
            "anomaly_detected": ai_res.get("anomaly_detected", False),
            "anomaly_score": ai_res.get("anomaly_score", 0.0),
            "anomaly_reason": ai_res.get("explanation"),
            "note": "Turbidity values are simulated based on potentiometer input."
        }

        # Save to DB
        col = await self.get_readings_collection()
        insert_res = await col.insert_one(reading_doc)
        reading_doc["id"] = getattr(insert_res, "inserted_id", None) or reading_doc.get("_id")
        if "_id" in reading_doc:
            reading_doc["_id"] = str(reading_doc["_id"])

        # Broadcast via WebSocket
        await ws_manager.broadcast("sensor_update", reading_doc)

        return reading_doc

    async def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        col = await self.get_readings_collection()
        doc = await col.find_one(sort=[("timestamp", -1)])
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
        return doc

    async def get_history(
        self,
        limit: int = 100,
        timeframe: Optional[str] = "all"
    ) -> List[Dict[str, Any]]:
        col = await self.get_readings_collection()
        filter_dict = {}

        now = datetime.now(timezone.utc)
        if timeframe == "1h":
            since = (now - timedelta(hours=1)).isoformat()
            filter_dict["timestamp"] = {"$gte": since}
        elif timeframe == "24h" or timeframe == "today":
            since = (now - timedelta(hours=24)).isoformat()
            filter_dict["timestamp"] = {"$gte": since}
        elif timeframe == "7d":
            since = (now - timedelta(days=7)).isoformat()
            filter_dict["timestamp"] = {"$gte": since}

        cursor = col.find(filter_dict).sort("timestamp", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        # return in chronological order for graphs
        items.reverse()
        for item in items:
            if "_id" in item:
                item["id"] = str(item["_id"])
        return items

    async def get_analytics_summary(
        self,
        timeframe: Optional[str] = "24h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return await analytics_service.compute_analytics(
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )

    async def get_device_status(self, device_id: str = "AquaSense-ESP32") -> Dict[str, Any]:
        """Check if device is currently sending heartbeats."""
        settings = await self.get_settings()
        timeout = settings.get("heartbeat_timeout_seconds", 25)

        info = self.device_heartbeats.get(device_id)
        is_online = False
        last_seen = None

        if info and "last_seen" in info:
            last_seen = info["last_seen"]
            try:
                delta = (datetime.now(timezone.utc) - datetime.fromisoformat(last_seen)).total_seconds()
                is_online = delta <= timeout
            except Exception:
                is_online = False
        else:
            # Check latest reading from DB as fallback
            latest = await self.get_latest_reading()
            if latest and "timestamp" in latest:
                last_seen = latest["timestamp"]
                try:
                    delta = (datetime.now(timezone.utc) - datetime.fromisoformat(last_seen)).total_seconds()
                    is_online = delta <= timeout
                except Exception:
                    is_online = False

        return {
            "device_id": device_id,
            "status": "online" if is_online else "offline",
            "is_online": is_online,
            "last_seen": last_seen,
            "simulation_mode": True,
            "simulator_source": "Wokwi ESP32 DevKit V1",
            "protocol": "HTTP POST /api/sensor-data + WebSocket",
            "wifi_network": "Wokwi-GUEST",
            "firmware_version": "v1.2.4-atomQUEST",
            "hardware": "ESP32 (3x Potentiometer on GPIO 34, 35, 32)",
            "heartbeat_timeout_seconds": timeout
        }

# Global singleton
sensor_service = SensorService()

