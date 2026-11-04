"""
AquaSense AI - Intelligent Water Quality Recommendation Engine
Unifies real-time sensor telemetry, historical trend analytics, ML anomaly detection,
and predictive filter health modeling to generate prioritized, understandable,
and actionable water quality guidance with persistent storage and deduplication.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

from database.connection import DatabaseManager
from models.recommendation import (
    Recommendation,
    RecommendationSummaryResponse,
    DismissRecommendationRequest
)
from services.websocket_manager import ws_manager
from services.sensor_service import sensor_service
from services.analytics_service import analytics_service
from services.filter_service import filter_service
from services.alert_service import alert_service
from ai.anomaly_detector import anomaly_detector

class RecommendationService:
    def __init__(self):
        # In-memory debounce cache: deduplication_key -> last_evaluated_iso
        self._debounce_cache: Dict[str, str] = {}
        self.debounce_seconds = 30 # Avoid regenerating identical recommendations within 30 seconds

    async def get_recommendations_collection(self):
        db = await DatabaseManager.get_db()
        return db["water_quality_recommendations"]

    async def get_history_collection(self):
        db = await DatabaseManager.get_db()
        return db["recommendation_history_log"]

    async def evaluate_and_generate_recommendations(
        self,
        current_reading: Optional[Dict[str, Any]] = None,
        trigger_broadcast: bool = True
    ) -> List[Recommendation]:
        """
        Synthesizes multiple subsystems:
        1. Current sensor readings (TDS, pH, Turbidity)
        2. 24h Historical Analytics (trend direction, status percentages, frequent abnormal parameters)
        3. ML Anomaly Detection (multivariate pattern deviation)
        4. Filter Health Service (estimated health %, stage condition, water quality burden)
        5. Active Alerts Registry
        """
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        # 1. Fetch current telemetry if not provided
        if not current_reading:
            current_reading = await sensor_service.get_latest_reading()

        # If still no reading available (empty database), return early
        if not current_reading:
            return []

        tds = float(current_reading.get("tds", 165.0))
        ph = float(current_reading.get("ph", 7.35))
        turbidity = float(current_reading.get("turbidity", 1.2))
        reading_overall_status = str(current_reading.get("overall_status", "Normal"))

        # 2. Fetch system threshold settings
        settings = await sensor_service.get_settings()
        tds_crit = float(settings.get("tds_critical_threshold", 500.0))
        tds_warn = float(settings.get("tds_warning_threshold", 300.0))
        ph_min = float(settings.get("ph_min_acceptable", 6.5))
        ph_max = float(settings.get("ph_max_acceptable", 8.5))
        turb_crit = float(settings.get("turbidity_critical_threshold", 10.0))
        turb_warn = float(settings.get("turbidity_warning_threshold", 5.0))

        # 3. Fetch 24h Historical Analytics (Requirement 2)
        try:
            analytics = await analytics_service.compute_analytics(timeframe="24h")
        except Exception:
            analytics = {"has_data": False, "trend_direction": "stable"}

        trend_dir = analytics.get("trend_direction", "stable")
        top_abnormal_param = analytics.get("most_frequently_abnormal_parameter", {}).get("parameter", "None")
        hist_status_counts = analytics.get("status_counts", {"normal": 0, "warning": 0, "critical": 0})

        # 4. Fetch AI Anomaly Detection Results (Requirement 3)
        # Check if latest reading already has anomaly results or evaluate directly
        ai_detected = bool(current_reading.get("anomaly_detected", False))
        ai_score = float(current_reading.get("anomaly_score", 0.0))
        ai_explanation = str(current_reading.get("anomaly_reason") or "Pattern anomaly deviation")
        ai_parameter = current_reading.get("anomaly_parameter")

        if not ai_detected:
            # Quick check through anomaly detector
            sensitivity = settings.get("anomaly_sensitivity", "medium")
            ai_eval = anomaly_detector.analyze_reading(tds, ph, turbidity, sensitivity=sensitivity)
            ai_detected = ai_eval.get("anomaly_detected", False)
            ai_score = float(ai_eval.get("anomaly_score", 0.0))
            ai_explanation = ai_eval.get("explanation", "")
            ai_parameter = ai_eval.get("parameter")

        # 5. Fetch Filter Health Information (Requirement 4)
        try:
            filter_data = await filter_service.get_filter_health()
        except Exception:
            filter_data = {
                "estimated_filter_health_percentage": 78.0,
                "filter_condition": "Good",
                "usage_duration": "1420 operating hours",
                "next_scheduled_service": "2027-02-15",
                "stages": []
            }

        filter_health_pct = float(filter_data.get("estimated_filter_health_percentage", 78.0))
        filter_condition = filter_data.get("filter_condition", "Good")
        filter_duration = filter_data.get("usage_duration", "1420 operating hours")
        next_service_date = filter_data.get("next_scheduled_service", "2027-02-15")
        filter_crit_th = float(settings.get("filter_critical_threshold", 15.0))
        filter_warn_th = float(settings.get("filter_warning_threshold", 30.0))

        # Check individual stage conditions
        stages = filter_data.get("stages", [])
        st1_sediment = next((s for s in stages if s.get("id") == "stage-1-sediment"), {})
        st3_ro = next((s for s in stages if s.get("id") == "stage-3-ro"), {})
        st4_alkaline = next((s for s in stages if s.get("id") == "stage-4-postcarbon"), {})

        # 6. Fetch Active Alerts to link IDs (Requirement 12)
        active_alerts = await alert_service.get_alerts(status="active", limit=20)
        def find_related_alert(param: str, severity: Optional[str] = None) -> Optional[str]:
            for a in active_alerts:
                if a.get("parameter") == param:
                    if severity is None or a.get("severity") == severity:
                        return a.get("id")
            return None

        # ---------------------------------------------------------------------
        # GENERATE RECOMMENDATIONS ACCORDING TO DOMAIN RULES
        # ---------------------------------------------------------------------
        generated_candidates: List[Dict[str, Any]] = []

        # --- Rule 1: Critical TDS Ingress / Mineral Contamination ---
        if tds >= tds_crit or (analytics.get("has_data") and analytics.get("tds", {}).get("avg", 0) >= tds_crit):
            generated_candidates.append({
                "deduplication_key": "water_quality:tds:critical:excessive_dissolved_solids",
                "priority": "Critical",
                "category": "Water Quality",
                "title": "Critical TDS Level - High Dissolved Mineral Ingress",
                "message": (
                    f"Purifier output TDS reached {tds:.1f} ppm, crossing the critical limit ({tds_crit:.1f} ppm). "
                    f"Water contains excessive dissolved mineral content. Immediate filtration check is advised."
                ),
                "reason": (
                    f"Measured TDS ({tds:.1f} ppm) exceeded critical limit ({tds_crit:.1f} ppm). "
                    f"24h historical average is {analytics.get('tds', {}).get('avg', tds):.1f} ppm with a {trend_dir} trend."
                ),
                "source_factors": ["current_reading", "historical_analytics", "settings_threshold"],
                "action": "Inspect RO membrane rejection efficiency and verify inlet flow restrictor valve.",
                "action_steps": [
                    "Turn off purifier power and test raw feed water TDS to check for municipal supply surges.",
                    "Inspect RO reject water discharge line to ensure brine is flowing freely without flow restriction.",
                    "Flush RO membrane system for 3 to 5 minutes.",
                    "If TDS remains elevated above 500 ppm after flush, service RO membrane cartridge."
                ],
                "parameter": "TDS",
                "current_value": tds,
                "threshold_or_baseline": f"> {tds_crit:.1f} ppm",
                "related_alert_id": find_related_alert("TDS", "Critical")
            })

        # --- Rule 2: Warning TDS Elevation ---
        elif tds >= tds_warn or (trend_dir == "degrading" and top_abnormal_param == "TDS"):
            generated_candidates.append({
                "deduplication_key": "water_quality:tds:warning:elevated_mineral_hardness",
                "priority": "Warning",
                "category": "Water Quality",
                "title": "Elevated TDS Level - Water Hardness Advisory",
                "message": (
                    f"Water TDS is at {tds:.1f} ppm, above the recommended drinking threshold ({tds_warn:.1f} ppm). "
                    f"Water hardness may impart a distinct mineral taste."
                ),
                "reason": (
                    f"Current TDS reading ({tds:.1f} ppm) crossed the warning baseline ({tds_warn:.1f} ppm). "
                    f"Historical analytics indicates {trend_dir} mineral stability over the past 24 hours."
                ),
                "source_factors": ["current_reading", "historical_analytics"],
                "action": "Monitor purifier output TDS and check raw water hardness.",
                "action_steps": [
                    "Check raw water source hardness; seasonal shifts can elevate feed salinity.",
                    "Verify TDS modulator valve setting on purifier if equipped.",
                    "Dispense 1 liter to purge stale reservoir water and re-check output reading."
                ],
                "parameter": "TDS",
                "current_value": tds,
                "threshold_or_baseline": f"> {tds_warn:.1f} ppm",
                "related_alert_id": find_related_alert("TDS", "Warning")
            })

        # --- Rule 3: Acidic pH Detected ---
        if ph < ph_min:
            prio = "Critical" if ph < (ph_min - 1.0) else "Warning"
            st4_cond = st4_alkaline.get("condition_pct", 70.0)
            generated_candidates.append({
                "deduplication_key": f"water_quality:ph:{prio.lower()}:acidic_balance",
                "priority": prio,
                "category": "Water Quality",
                "title": "Acidic Water Quality - Remineralizer Inspection Advised",
                "message": (
                    f"Drinking water pH has dropped to {ph:.2f}, below the safe alkaline balance ({ph_min:.1f}). "
                    f"Acidic water can impart a tart taste and may indicate depleted remineralization media."
                ),
                "reason": (
                    f"Measured pH is {ph:.2f} (safe minimum: {ph_min:.1f}). "
                    f"Post-Carbon Alkaline cartridge condition is currently at {st4_cond:.1f}%."
                ),
                "source_factors": ["current_reading", "filter_health", "settings_threshold"],
                "action": "Inspect Stage 4 Post-Carbon Alkaline Mineralizer cartridge and calibrate pH electrode.",
                "action_steps": [
                    "Rinse pH sensor electrode with distilled water to ensure no surface residue is skewing the probe.",
                    f"Inspect Stage 4 mineralizer cartridge condition (estimated remaining life: {st4_cond:.1f}%).",
                    "Perform a fresh 60-second purge cycle to test if reservoir stagnation caused acidity accumulation."
                ],
                "parameter": "pH",
                "current_value": ph,
                "threshold_or_baseline": f"< {ph_min:.1f}",
                "related_alert_id": find_related_alert("pH", prio)
            })

        # --- Rule 4: Alkaline pH Detected ---
        elif ph > ph_max:
            prio = "Critical" if ph > (ph_max + 1.0) else "Warning"
            generated_candidates.append({
                "deduplication_key": f"water_quality:ph:{prio.lower()}:alkaline_balance",
                "priority": prio,
                "category": "Water Quality",
                "title": "Elevated Alkaline pH - Mineral Dissolution Advisory",
                "message": (
                    f"Water pH has increased to {ph:.2f}, above the recommended drinking maximum ({ph_max:.1f}). "
                    f"Excessive alkalinity can impart a bitter or slippery taste."
                ),
                "reason": (
                    f"Measured pH is {ph:.2f} (recommended maximum: {ph_max:.1f}). "
                    f"Historical analytics shows pH variance across the analyzed timeframe."
                ),
                "source_factors": ["current_reading", "settings_threshold"],
                "action": "Flush purifier storage tank and inspect alkaline media dissolution rate.",
                "action_steps": [
                    "Empty the storage tank to discard water with excessive dissolved minerals.",
                    "Inspect the remineralization cartridge bypass ratio.",
                    "Verify raw input water pH to confirm whether municipal water source has shifted."
                ],
                "parameter": "pH",
                "current_value": ph,
                "threshold_or_baseline": f"> {ph_max:.1f}",
                "related_alert_id": find_related_alert("pH", prio)
            })

        # --- Rule 5: Turbidity Elevation & Pre-Filter Particulate Loading ---
        if turbidity >= turb_warn:
            prio = "Critical" if turbidity >= turb_crit else "Warning"
            st1_cond = st1_sediment.get("condition_pct", 74.0)
            generated_candidates.append({
                "deduplication_key": f"filter_maintenance:turbidity:{prio.lower()}:sediment_particulate_stress",
                "priority": prio,
                "category": "Filter Maintenance",
                "title": "Elevated Turbidity - Sediment Pre-Filter Service Recommended",
                "message": (
                    f"Simulated turbidity index reached {turbidity:.1f}, crossing the warning limit ({turb_warn:.1f}). "
                    f"Suspended particulates can increase resistance and foul the downstream RO membrane."
                ),
                "reason": (
                    f"Turbidity reading ({turbidity:.1f}) exceeds baseline threshold ({turb_warn:.1f}). "
                    f"Stage 1 Sediment Pre-Filter estimated condition is at {st1_cond:.1f}%."
                ),
                "source_factors": ["current_reading", "filter_health", "settings_threshold"],
                "action": "Flush purifier inlet line and inspect Stage 1 Sediment Pre-Filter bowl.",
                "action_steps": [
                    "Visually inspect external spun sediment pre-filter bowl for visible silt, rust, or discoloration.",
                    "Execute manual flush for 2 minutes to clear inlet pipeline particles.",
                    f"Prepare replacement PP-5M spun sediment pre-filter cartridge (current condition: {st1_cond:.1f}%)."
                ],
                "parameter": "Turbidity",
                "current_value": turbidity,
                "threshold_or_baseline": f"> {turb_warn:.1f} (sim)",
                "related_alert_id": find_related_alert("Turbidity", prio)
            })

        # --- Rule 6: AI Anomaly Pattern Resolution ---
        if ai_detected:
            generated_candidates.append({
                "deduplication_key": "anomaly_resolution:ai:warning:multivariate_correlation_divergence",
                "priority": "Warning",
                "category": "Anomaly Resolution",
                "title": "AI Multivariate Pattern Anomaly Detected",
                "message": (
                    f"Machine learning anomaly detector flagged unusual water correlation patterns: {ai_explanation}"
                ),
                "reason": (
                    f"Isolation Forest identified statistical departure from calibrated baseline "
                    f"(Anomaly score: {ai_score:.1f}/100. Primary diverging parameter: {ai_parameter or 'Multi-factor'})."
                ),
                "source_factors": ["anomaly_detector", "current_reading"],
                "action": "Check for aerated flow, probe bubbles, or municipal source switching.",
                "action_steps": [
                    "Inspect probe measurement vessel for micro-bubbles or intermittent water flow.",
                    "Verify if tap water supply switched between municipal surface and borewell sources.",
                    "Monitor live dashboard graph to observe whether readings return to learned baseline."
                ],
                "parameter": ai_parameter or "Multi-parameter",
                "current_value": ai_score,
                "threshold_or_baseline": "Statistical Anomaly Deviation",
                "related_alert_id": find_related_alert("AI Anomaly") or find_related_alert("Profile")
            })

        # --- Rule 7: Persistent Historical Degrading Trend ---
        if trend_dir == "degrading" and hist_status_counts.get("critical", 0) + hist_status_counts.get("warning", 0) >= 3:
            generated_candidates.append({
                "deduplication_key": "water_quality:system:warning:persistent_degrading_trend",
                "priority": "Warning",
                "category": "Water Quality",
                "title": "Persistent Degrading Water Quality Trend Identified",
                "message": (
                    f"Historical analytics detected a continuous declining purity trend across the past 24 hours. "
                    f"Most frequent abnormal parameter: {top_abnormal_param}."
                ),
                "reason": (
                    f"Overall purity score has trended downwards across historical readings. "
                    f"{hist_status_counts.get('warning', 0)} warning and {hist_status_counts.get('critical', 0)} critical records logged."
                ),
                "source_factors": ["historical_analytics"],
                "action": "Review historical trend charts and inspect raw feed water quality.",
                "action_steps": [
                    "Review Analytics page charts to identify timestamp of initial purity score decline.",
                    "Verify whether raw feed water quality has deteriorated or pre-filtration pressure has dropped.",
                    "Plan preventative cartridge servicing before complete threshold breach."
                ],
                "parameter": top_abnormal_param if top_abnormal_param != "None" else "Water Quality Index",
                "current_value": None,
                "threshold_or_baseline": "Historical 24h Trend",
                "related_alert_id": None
            })

        # --- Rule 8: Purifier Filter Consumable Depletion ---
        if filter_health_pct <= filter_crit_th:
            generated_candidates.append({
                "deduplication_key": "filter_maintenance:filter:critical:cartridges_depleted",
                "priority": "Critical",
                "category": "Filter Maintenance",
                "title": "Purifier Filter Cartridges Depleted - Immediate Replacement Due",
                "message": (
                    f"Estimated filter health has declined to {filter_health_pct:.1f}% ({filter_condition}). "
                    f"Filtration media capacity is exhausted; continued operation risks membrane fouling."
                ),
                "reason": (
                    f"Estimated filter condition reached {filter_health_pct:.1f}%, below critical threshold ({filter_crit_th:.1f}%). "
                    f"Usage duration: {filter_duration}."
                ),
                "source_factors": ["filter_health", "settings_threshold"],
                "action": "Order replacement cartridge pack and schedule technician maintenance.",
                "action_steps": [
                    "Procure replacement 4-stage filter set (Atomberg ProClean PP, PureCarb, DuraFlow RO, AlkiPure).",
                    "Avoid continuous high-volume water dispensing until cartridges are serviced.",
                    "After replacing cartridges, trigger 'Simulate Cartridge Service' to reset operating hours to 0."
                ],
                "parameter": "Filter Health",
                "current_value": filter_health_pct,
                "threshold_or_baseline": f"<= {filter_crit_th:.1f}%",
                "related_alert_id": find_related_alert("Filter Health", "Critical")
            })
        elif filter_health_pct <= filter_warn_th:
            generated_candidates.append({
                "deduplication_key": "filter_maintenance:filter:warning:cartridges_wear_advisory",
                "priority": "Warning",
                "category": "Filter Maintenance",
                "title": "Routine Purifier Filter Maintenance Due Soon",
                "message": (
                    f"Estimated filter health is at {filter_health_pct:.1f}% ({filter_condition}). "
                    f"Cartridges should be scheduled for servicing within 14 days."
                ),
                "reason": (
                    f"Estimated filter health reached warning threshold ({filter_warn_th:.1f}%). "
                    f"Usage duration: {filter_duration}. Next scheduled routine service: {next_service_date}."
                ),
                "source_factors": ["filter_health", "settings_threshold"],
                "action": "Plan replacement cartridge procurement and schedule routine servicing.",
                "action_steps": [
                    "Order replacement cartridge set in advance to prevent service interruption.",
                    "Inspect booster pump sound and vibration during operation.",
                    "Perform routine pre-filter flush to extend remaining membrane life."
                ],
                "parameter": "Filter Health",
                "current_value": filter_health_pct,
                "threshold_or_baseline": f"<= {filter_warn_th:.1f}%",
                "related_alert_id": find_related_alert("Filter Health", "Warning")
            })

        # --- Rule 9: Periodic Sensor Hygiene & Calibration Advisory ---
        # Generate informational advice periodically if no other critical warnings active
        if float(current_reading.get("water_quality_score", 100)) >= 85.0 and filter_health_pct > filter_warn_th:
            generated_candidates.append({
                "deduplication_key": "routine_advisory:system:informational:sensor_hygiene_guidance",
                "priority": "Informational",
                "category": "System & Calibration",
                "title": "Periodic Sensor Probe Maintenance & Rinsing Guidance",
                "message": (
                    "Water quality monitoring sensors maintain optimal measurement precision when probe electrodes are periodically inspected and rinsed."
                ),
                "reason": (
                    "Routine preventative advice: optical turbidity quartz windows and pH glass electrodes benefit from periodic rinsing."
                ),
                "source_factors": ["settings_threshold", "routine_schedule"],
                "action": "Inspect probe chamber and gently rinse electrodes with clean water.",
                "action_steps": [
                    "Inspect the optical turbidity sensor chamber for mineral scale or fine sediment coating.",
                    "Rinse probe ends with clean drinking water; avoid abrasive cloths on the pH glass bulb.",
                    "Ensure sensor probe cable connections to ESP32 are secure."
                ],
                "parameter": "Sensor Hardware",
                "current_value": None,
                "threshold_or_baseline": "Preventative Maintenance",
                "related_alert_id": None
            })

        # --- Rule 10: Optimal Operation & Purity Assurance ---
        if reading_overall_status == "Normal" and not ai_detected and filter_health_pct > filter_warn_th:
            generated_candidates.append({
                "deduplication_key": "routine_advisory:water_quality:informational:optimal_purity_assurance",
                "priority": "Informational",
                "category": "Routine Advisory",
                "title": "Optimal Drinking Water Quality & Stable Operation",
                "message": (
                    f"All monitored parameters (TDS: {tds:.1f} ppm, pH: {ph:.2f}, Turbidity: {turbidity:.1f}) "
                    f"and purifier filter stages ({filter_health_pct:.1f}% health) are operating within target drinking specifications."
                ),
                "reason": (
                    f"Instantaneous telemetry is Normal. 24h trend direction is {trend_dir}. "
                    f"Filter health condition is {filter_condition}. Next routine service projected for {next_service_date}."
                ),
                "source_factors": ["current_reading", "historical_analytics", "filter_health"],
                "action": "Continue standard purifier operation and regular hydration.",
                "action_steps": [
                    "Maintain consistent domestic purifier operating flow.",
                    f"Next routine preventative service projected for {next_service_date}."
                ],
                "parameter": "Composite Quality",
                "current_value": float(current_reading.get("water_quality_score", 96.0)),
                "threshold_or_baseline": "Optimal Target Profile",
                "related_alert_id": None
            })

        # ---------------------------------------------------------------------
        # DEDUPLICATION & PERSISTENT STORAGE (Requirements 9 & 10)
        # ---------------------------------------------------------------------
        rec_col = await self.get_recommendations_collection()
        hist_col = await self.get_history_collection()
        persisted_recommendations: List[Recommendation] = []

        for cand in generated_candidates:
            dedup_key = cand["deduplication_key"]

            # Check if active un-dismissed recommendation with this deduplication_key exists in DB
            existing = await rec_col.find_one({
                "deduplication_key": dedup_key,
                "is_dismissed": False
            })

            if existing:
                # Update occurrence count and timestamp without creating duplicate clutter
                updated_count = int(existing.get("occurrence_count", 1)) + 1
                await rec_col.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "last_updated_at": now_iso,
                        "current_value": cand["current_value"],
                        "occurrence_count": updated_count,
                        "message": cand["message"],
                        "reason": cand["reason"],
                        "related_alert_id": cand.get("related_alert_id")
                    }}
                )
                existing["last_updated_at"] = now_iso
                existing["current_value"] = cand["current_value"]
                existing["occurrence_count"] = updated_count
                existing["message"] = cand["message"]
                existing["reason"] = cand["reason"]
                existing["related_alert_id"] = cand.get("related_alert_id")
                if "_id" in existing:
                    existing["id"] = str(existing["_id"])
                persisted_recommendations.append(Recommendation(**existing))
            else:
                # Check memory debounce
                last_time = self._debounce_cache.get(dedup_key)
                if last_time:
                    try:
                        delta = (datetime.fromisoformat(now_iso) - datetime.fromisoformat(last_time)).total_seconds()
                        if delta < self.debounce_seconds:
                            continue
                    except Exception:
                        pass

                self._debounce_cache[dedup_key] = now_iso

                rec_id = str(uuid.uuid4())
                cand_doc = {
                    "_id": rec_id,
                    "id": rec_id,
                    "created_at": now_iso,
                    "last_updated_at": now_iso,
                    "priority": cand["priority"],
                    "category": cand["category"],
                    "title": cand["title"],
                    "message": cand["message"],
                    "reason": cand["reason"],
                    "source_factors": cand["source_factors"],
                    "action": cand["action"],
                    "action_steps": cand["action_steps"],
                    "parameter": cand.get("parameter"),
                    "current_value": cand.get("current_value"),
                    "threshold_or_baseline": cand.get("threshold_or_baseline"),
                    "is_dismissed": False,
                    "dismissed_at": None,
                    "occurrence_count": 1,
                    "deduplication_key": dedup_key,
                    "related_alert_id": cand.get("related_alert_id")
                }
                await rec_col.insert_one(cand_doc)
                await hist_col.insert_one(dict(cand_doc))
                persisted_recommendations.append(Recommendation(**cand_doc))

                # Connect notification event (Requirement 4)
                if cand_doc["priority"] in ("Critical", "Warning"):
                    try:
                        from services.notification_service import notification_service
                        await notification_service.create_notification(
                            title=cand_doc["title"],
                            message=cand_doc["message"],
                            severity=cand_doc["priority"],
                            category=cand_doc["category"],
                            parameter=cand_doc.get("parameter"),
                            reading_value=cand_doc.get("current_value"),
                            threshold_value=cand_doc.get("threshold_or_baseline"),
                            suggested_action=cand_doc.get("action"),
                            related_recommendation_id=cand_doc["id"],
                            related_alert_id=cand_doc.get("related_alert_id"),
                            source_event="recommendation_engine"
                        )
                    except Exception:
                        pass

        # ---------------------------------------------------------------------
        # REAL-TIME BROADCAST (Requirement 12)
        # ---------------------------------------------------------------------
        if trigger_broadcast and persisted_recommendations:
            summary = self._build_summary_response(persisted_recommendations)
            await ws_manager.broadcast("recommendation_updated", summary.model_dump())

        return persisted_recommendations

    def _build_summary_response(self, recs: List[Recommendation]) -> RecommendationSummaryResponse:
        """Construct the high-level summary response with priority counts and overall assessment."""
        crit = sum(1 for r in recs if r.priority == "Critical" and not r.is_dismissed)
        warn = sum(1 for r in recs if r.priority == "Warning" and not r.is_dismissed)
        info = sum(1 for r in recs if r.priority == "Informational" and not r.is_dismissed)
        active = [r for r in recs if not r.is_dismissed]

        # Prioritize list: Critical first, then Warning, then Informational
        priority_order = {"Critical": 0, "Warning": 1, "Informational": 2}
        active.sort(key=lambda r: priority_order.get(r.priority, 3))

        if crit > 0:
            verdict = (
                f"Critical Action Required: {crit} critical condition(s) detected. "
                f"Immediate filter inspection or water parameter remediation recommended."
            )
        elif warn > 0:
            verdict = (
                f"Advisory Warning: {warn} warning condition(s) identified. "
                f"Review suggested maintenance steps to prevent filter fouling or purity decline."
            )
        else:
            verdict = (
                "Normal Operational State: Water telemetry and purifier filter condition "
                "meet calibrated domestic drinking standards."
            )

        return RecommendationSummaryResponse(
            active_recommendations=active,
            total_active=len(active),
            critical_count=crit,
            warning_count=warn,
            informational_count=info,
            overall_water_assessment=verdict,
            synthesis_timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def get_active_recommendations(
        self,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        include_dismissed: bool = False
    ) -> RecommendationSummaryResponse:
        """
        Retrieves active recommendations from persistent storage.
        Evaluates real-time telemetry if persistent collection is empty.
        """
        col = await self.get_recommendations_collection()
        query: Dict[str, Any] = {}
        if not include_dismissed:
            query["is_dismissed"] = False
        if priority:
            query["priority"] = priority
        if category:
            query["category"] = category

        cursor = col.find(query).sort("last_updated_at", -1)
        items = await cursor.to_list(length=100)

        # If zero recommendations exist, trigger initial evaluation
        if not items and not query:
            evaluated = await self.evaluate_and_generate_recommendations(trigger_broadcast=False)
            return self._build_summary_response(evaluated)

        recs = []
        for it in items:
            if "_id" in it:
                it["id"] = str(it["_id"])
            recs.append(Recommendation(**it))

        return self._build_summary_response(recs)

    async def dismiss_recommendation(self, rec_id: str, dismissed_by: str = "User") -> bool:
        """Acknowledge or dismiss an active recommendation."""
        col = await self.get_recommendations_collection()
        now_iso = datetime.now(timezone.utc).isoformat()
        res = await col.update_one(
            {"_id": rec_id},
            {"$set": {
                "is_dismissed": True,
                "dismissed_at": now_iso,
                "dismissed_by": dismissed_by
            }}
        )
        if res.modified_count > 0:
            await ws_manager.broadcast("recommendation_dismissed", {"id": rec_id})
            return True
        return False

    async def get_recommendation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch historical log of all recommendations generated over time (Requirement 10)."""
        hist_col = await self.get_history_collection()
        cursor = hist_col.find().sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        for it in items:
            if "_id" in it:
                it["id"] = str(it["_id"])
        return items

recommendation_service = RecommendationService()
