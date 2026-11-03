"""
Alert Management Service for AquaSense AI
Evaluates fixed thresholds and AI anomaly detections, applies deduplication,
manages persistence, and notifies frontend clients in real time.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from database.connection import DatabaseManager
from models.alert import Alert
from services.websocket_manager import ws_manager

class AlertService:
    def __init__(self):
        # Cache of recently emitted alert keys: (parameter, severity) -> last_emitted_iso
        self._recent_alert_debounce: Dict[str, str] = {}
        self.debounce_seconds = 45 # Don't spam duplicates within 45 seconds

    async def get_alerts_collection(self):
        db = await DatabaseManager.get_db()
        return db["alerts"]

    async def evaluate_reading(
        self,
        tds: float,
        ph: float,
        turbidity: float,
        settings: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List[Alert]:
        """
        Evaluate sensor reading against fixed thresholds AND AI anomalies.
        Applies smart deduplication to prevent repetitive alert spamming.
        """
        alerts_to_create: List[Dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        tds_crit = settings.get("tds_critical_threshold", 500.0)
        tds_warn = settings.get("tds_warning_threshold", 300.0)
        ph_min = settings.get("ph_min_acceptable", 6.5)
        ph_max = settings.get("ph_max_acceptable", 8.5)
        turb_crit = settings.get("turbidity_critical_threshold", 10.0)
        turb_warn = settings.get("turbidity_warning_threshold", 5.0)

        # 1. TDS Thresholds
        if tds >= tds_crit:
            alerts_to_create.append({
                "alert_type": "Threshold",
                "parameter": "TDS",
                "reading_value": tds,
                "threshold_value": f"> {tds_crit} ppm",
                "severity": "Critical",
                "title": "Critical TDS Level Exceeded",
                "message": f"TDS reading reached {tds:.1f} ppm, exceeding the critical limit of {tds_crit:.1f} ppm. Purifier output water may contain excessive dissolved solids.",
                "suggested_action": "Inspect RO membrane rejection rate and flush RO cartridge immediately."
            })
        elif tds >= tds_warn:
            alerts_to_create.append({
                "alert_type": "Threshold",
                "parameter": "TDS",
                "reading_value": tds,
                "threshold_value": f"> {tds_warn} ppm",
                "severity": "Warning",
                "title": "High TDS Warning",
                "message": f"TDS reading reached {tds:.1f} ppm, crossing the recommended warning threshold of {tds_warn:.1f} ppm.",
                "suggested_action": "Check raw input water hardness and schedule sediment pre-filter inspection."
            })

        # 2. pH Acceptable Range
        if ph < ph_min:
            severity = "Critical" if ph < (ph_min - 1.0) else "Warning"
            alerts_to_create.append({
                "alert_type": "Range",
                "parameter": "pH",
                "reading_value": ph,
                "threshold_value": f"< {ph_min}",
                "severity": severity,
                "title": "Acidic Water Quality Alert",
                "message": f"pH level dropped to {ph:.2f}, below safe drinking minimum of {ph_min:.1f}. Water may be corrosive.",
                "suggested_action": "Check alkaline remineralizer cartridge and calibrate pH sensor electrode."
            })
        elif ph > ph_max:
            severity = "Critical" if ph > (ph_max + 1.0) else "Warning"
            alerts_to_create.append({
                "alert_type": "Range",
                "parameter": "pH",
                "reading_value": ph,
                "threshold_value": f"> {ph_max}",
                "severity": severity,
                "title": "Alkaline Water Quality Alert",
                "message": f"pH level elevated to {ph:.2f}, above safe drinking maximum of {ph_max:.1f}.",
                "suggested_action": "Inspect post-carbon filter stage and verify source water alkalinity."
            })

        # 3. Turbidity Thresholds (Simulated scale)
        if turbidity >= turb_crit:
            alerts_to_create.append({
                "alert_type": "Threshold",
                "parameter": "Turbidity",
                "reading_value": turbidity,
                "threshold_value": f"> {turb_crit}",
                "severity": "Critical",
                "title": "High Turbidity Alert (Simulated)",
                "message": f"Simulated turbidity index spiked to {turbidity:.1f}, exceeding critical threshold of {turb_crit:.1f}. Water clarity is compromised.",
                "suggested_action": "Replace Stage 1 Sediment Pre-Filter cartridge and check supply line clarity."
            })
        elif turbidity >= turb_warn:
            alerts_to_create.append({
                "alert_type": "Threshold",
                "parameter": "Turbidity",
                "reading_value": turbidity,
                "threshold_value": f"> {turb_warn}",
                "severity": "Warning",
                "title": "Elevated Turbidity Warning (Simulated)",
                "message": f"Simulated turbidity index is {turbidity:.1f}, above recommended baseline limit of {turb_warn:.1f}.",
                "suggested_action": "Inspect pre-filtration mesh and flush purifier inlet for 2 minutes."
            })

        # 4. AI Machine Learning Anomaly Detection (Separate from fixed thresholds)
        if ai_analysis.get("anomaly_detected"):
            param = ai_analysis.get("parameter", "Water Profile")
            alerts_to_create.append({
                "alert_type": "Anomaly",
                "parameter": param or "Profile",
                "reading_value": round(float(ai_analysis.get("anomaly_score", 85.0)), 1),
                "threshold_value": "Statistical deviation",
                "severity": "Warning",
                "title": "AI Pattern Anomaly Detected",
                "message": ai_analysis.get("explanation", "Multi-parameter statistical correlation divergence."),
                "suggested_action": "Perform sensory verification and check for sudden municipal water source switching."
            })

        generated_alerts: List[Alert] = []
        alerts_col = await self.get_alerts_collection()

        for alert_data in alerts_to_create:
            debounce_key = f"{alert_data['parameter']}_{alert_data['severity']}_{alert_data['alert_type']}"
            
            # Check if this exact condition has an active unacknowledged alert in DB
            existing_active = await alerts_col.find_one({
                "parameter": alert_data["parameter"],
                "severity": alert_data["severity"],
                "acknowledged": False
            })

            if existing_active:
                # Update timestamp and latest reading without creating duplicate alert clutter
                await alerts_col.update_one(
                    {"_id": existing_active["_id"]},
                    {"$set": {
                        "reading_value": alert_data["reading_value"],
                        "timestamp": now_iso
                    }}
                )
                continue

            # Also check memory debounce time window
            last_time = self._recent_alert_debounce.get(debounce_key)
            if last_time:
                try:
                    delta = (datetime.fromisoformat(now_iso) - datetime.fromisoformat(last_time)).total_seconds()
                    if delta < self.debounce_seconds:
                        continue
                except Exception:
                    pass

            self._recent_alert_debounce[debounce_key] = now_iso

            alert_obj = Alert(
                id=str(uuid.uuid4()),
                timestamp=now_iso,
                alert_type=alert_data["alert_type"],
                parameter=alert_data["parameter"],
                reading_value=alert_data["reading_value"],
                threshold_value=alert_data["threshold_value"],
                severity=alert_data["severity"],
                title=alert_data["title"],
                message=alert_data["message"],
                suggested_action=alert_data["suggested_action"],
                acknowledged=False
            )

            doc = alert_obj.model_dump()
            doc["_id"] = alert_obj.id
            await alerts_col.insert_one(doc)
            generated_alerts.append(alert_obj)

            # Broadcast new alert in real time via WebSocket
            await ws_manager.broadcast("alert_triggered", alert_obj.model_dump())

        return generated_alerts

    async def get_alerts(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        col = await self.get_alerts_collection()
        query = {}
        if status == "active":
            query["acknowledged"] = False
        elif status == "acknowledged":
            query["acknowledged"] = True

        cursor = col.find(query).sort("timestamp", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        for item in items:
            if "_id" in item:
                item["id"] = item["_id"]
        return items

    async def acknowledge_alert(self, alert_id: str) -> bool:
        col = await self.get_alerts_collection()
        res = await col.update_one({"_id": alert_id}, {"$set": {"acknowledged": True}})
        if res.modified_count > 0:
            await ws_manager.broadcast("alert_acknowledged", {"id": alert_id})
            return True
        return False

    async def acknowledge_all(self) -> int:
        col = await self.get_alerts_collection()
        res = await col.update_many({"acknowledged": False}, {"$set": {"acknowledged": True}})
        await ws_manager.broadcast("alerts_all_acknowledged", {})
        return res.modified_count

    async def clear_acknowledged(self) -> int:
        col = await self.get_alerts_collection()
        res = await col.delete_many({"acknowledged": True})
        return res.deleted_count

# Global singleton
alert_service = AlertService()

