"""
Predictive Filter Health Monitoring Service for AquaSense AI
Provides multi-stage purifier filter condition analytics, operating duration tracking,
water-quality burden analysis, trend anomaly detection, maintenance recommendations,
and persistent usage history.

Strictly adheres to data accuracy:
- Estimated filter health is an engineering demonstration model based on runtime and telemetry burden.
- Clearly distinguishes estimated health from manufacturer-certified filter wear.
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta

from database.connection import DatabaseManager
from models.filter import (
    FilterHealthResponse,
    FilterStage,
    WaterQualityBurden,
    WaterQualityTrendAnalysis,
    CalculationTransparency,
    FilterMaintenanceThresholds,
    FilterUsageHistoryEntry,
    MaintenanceLogEntry
)

class FilterService:
    def __init__(self):
        self._default_state = {
            "_id": "filter_state_01",
            "operating_hours": 1420.5,
            "processed_volume_liters": 4850.0,
            "last_serviced_date": "2026-08-15",
            "next_scheduled_service": "2027-02-15",
            "telemetry_reading_count": 0,
            "last_telemetry_timestamp": None,
            "stages": [
                {
                    "id": "stage-1-sediment",
                    "name": "Sediment Pre-Filter (PP Spun)",
                    "stage_number": 1,
                    "type": "Mechanical Filtration (5 Micron)",
                    "condition_pct": 74.0,
                    "status": "Good",
                    "lifespan_days": 180,
                    "days_remaining": 48,
                    "description": "Traps suspended silt, sand, rust, and turbidity particles before entering delicate RO membrane.",
                    "target_contaminants": "Coarse sediment, rust, visible turbidity",
                    "replacement_model": "Atomberg ProClean PP-5M"
                },
                {
                    "id": "stage-2-precarbon",
                    "name": "Pre-Carbon Block Filter",
                    "stage_number": 2,
                    "type": "Adsorption (Activated Coconut Shell)",
                    "condition_pct": 81.0,
                    "status": "Optimal",
                    "lifespan_days": 180,
                    "days_remaining": 62,
                    "description": "Adsorbs chlorine, organic volatile compounds, pesticides, foul odor and taste.",
                    "target_contaminants": "Chlorine, odor, pesticides, VOCs",
                    "replacement_model": "Atomberg PureCarb Block-10"
                },
                {
                    "id": "stage-3-ro",
                    "name": "RO Membrane (High Recovery)",
                    "stage_number": 3,
                    "type": "Reverse Osmosis (0.0001 Micron)",
                    "condition_pct": 89.0,
                    "status": "Optimal",
                    "lifespan_days": 365,
                    "days_remaining": 178,
                    "description": "Semi-permeable thin-film composite membrane reducing dissolved solids (simulated TDS).",
                    "target_contaminants": "High TDS, salts, dissolved inorganics",
                    "replacement_model": "Atomberg DuraFlow RO-75GPD"
                },
                {
                    "id": "stage-4-postcarbon",
                    "name": "Post-Carbon & Alkaline Mineralizer",
                    "stage_number": 4,
                    "type": "Mineral Infusion & Polish",
                    "condition_pct": 68.0,
                    "status": "Good",
                    "lifespan_days": 180,
                    "days_remaining": 36,
                    "description": "Restores essential calcium/magnesium minerals, balances drinking pH (6.5-8.5), and enriches taste.",
                    "target_contaminants": "Taste polish, pH stabilization",
                    "replacement_model": "Atomberg AlkiPure Mineralizer"
                }
            ]
        }

    async def get_filter_collection(self):
        db = await DatabaseManager.get_db()
        return db["filter_health"]

    async def get_usage_history_collection(self):
        db = await DatabaseManager.get_db()
        return db["filter_usage_history"]

    async def get_maintenance_log_collection(self):
        db = await DatabaseManager.get_db()
        return db["filter_maintenance_log"]

    async def get_readings_collection(self):
        db = await DatabaseManager.get_db()
        return db["sensor_readings"]

    async def get_settings(self) -> Dict[str, Any]:
        """Fetch configurable maintenance warning thresholds from persistent settings."""
        db = await DatabaseManager.get_db()
        settings_col = db["settings"]
        doc = await settings_col.find_one({"_id": "threshold_settings"})
        if not doc:
            return {
                "filter_warning_threshold": 30.0,
                "filter_critical_threshold": 15.0,
                "filter_max_operating_hours": 2000.0
            }
        return doc

    async def _get_current_state(self) -> Dict[str, Any]:
        """Get or initialize the persistent filter health state document."""
        col = await self.get_filter_collection()
        doc = await col.find_one({"_id": "filter_state_01"})
        if not doc:
            doc = dict(self._default_state)
            await col.insert_one(doc)
            # Log initial seed event
            await self._record_usage_snapshot(
                doc=doc,
                event_type="initial_initialization",
                note="Initialized default baseline filter lifecycle state."
            )
        return doc

    async def _analyze_historical_water_quality(self, custom_records: Optional[List[Dict[str, Any]]] = None) -> Tuple[WaterQualityBurden, WaterQualityTrendAnalysis]:
        """
        Analyze historical TDS and simulated turbidity readings to compute
        water quality burden factors and detect unusual trend changes.
        """
        if custom_records is not None:
            recent_records = custom_records
        else:
            col = await self.get_readings_collection()
            cursor = col.find().sort("timestamp", -1).limit(300)
            recent_records = await cursor.to_list(length=300)

        # Baseline defaults if database has few or zero records
        if not recent_records:
            burden = WaterQualityBurden(
                historical_avg_tds=165.0,
                historical_avg_turbidity=1.2,
                recent_avg_tds=165.0,
                recent_avg_turbidity=1.2,
                turbidity_stress_factor=0.0,
                tds_stress_factor=0.0,
                water_burden_multiplier=1.0,
                stress_level="Low"
            )
            trend = WaterQualityTrendAnalysis(
                unusual_change_detected=False,
                turbidity_change_pct=0.0,
                tds_change_pct=0.0,
                findings=["Insufficient historical telemetry to determine water quality trends; nominal baseline assumed."]
            )
            return burden, trend

        # Chronological order
        records = list(reversed(recent_records))
        total = len(records)

        # Split baseline vs recent window (last 15 readings) if sufficient history exists
        if total >= 25:
            baseline_slice = records[:-15]
            recent_slice = records[-15:]
        else:
            baseline_slice = records
            recent_slice = records[-10:] if total >= 10 else records

        b_tds = [float(r["tds"]) for r in baseline_slice if "tds" in r and r["tds"] is not None]
        b_turb = [float(r["turbidity"]) for r in baseline_slice if "turbidity" in r and r["turbidity"] is not None]
        r_tds = [float(r["tds"]) for r in recent_slice if "tds" in r and r["tds"] is not None]
        r_turb = [float(r["turbidity"]) for r in recent_slice if "turbidity" in r and r["turbidity"] is not None]

        hist_avg_tds = round(sum(b_tds) / len(b_tds), 1) if b_tds else 165.0
        hist_avg_turb = round(sum(b_turb) / len(b_turb), 2) if b_turb else 1.2
        recent_avg_tds = round(sum(r_tds) / len(r_tds), 1) if r_tds else hist_avg_tds
        recent_avg_turb = round(sum(r_turb) / len(r_turb), 2) if r_turb else hist_avg_turb

        # Compute stress factors
        # Turbidity above 1.5 adds pre-filter mechanical load
        turb_stress = max(0.0, round((recent_avg_turb - 1.5) / 5.0, 3))
        # TDS above 200 ppm adds RO osmotic burden
        tds_stress = max(0.0, round((recent_avg_tds - 200.0) / 400.0, 3))

        multiplier = round(1.0 + (turb_stress * 0.4) + (tds_stress * 0.4), 2)
        multiplier = max(1.0, min(2.5, multiplier))

        stress_level = "Low"
        if multiplier >= 1.4:
            stress_level = "High"
        elif multiplier >= 1.15:
            stress_level = "Moderate"

        burden = WaterQualityBurden(
            historical_avg_tds=hist_avg_tds,
            historical_avg_turbidity=hist_avg_turb,
            recent_avg_tds=recent_avg_tds,
            recent_avg_turbidity=recent_avg_turb,
            turbidity_stress_factor=turb_stress,
            tds_stress_factor=tds_stress,
            water_burden_multiplier=multiplier,
            stress_level=stress_level
        )

        # Detect unusual trend changes
        unusual = False
        findings = []

        turb_change = 0.0
        if hist_avg_turb > 0:
            turb_change = round(((recent_avg_turb - hist_avg_turb) / hist_avg_turb) * 100.0, 1)

        tds_change = 0.0
        if hist_avg_tds > 0:
            tds_change = round(((recent_avg_tds - hist_avg_tds) / hist_avg_tds) * 100.0, 1)

        if (recent_avg_turb >= 4.0 and turb_change >= 25.0) or recent_avg_turb >= 5.0:
            unusual = True
            findings.append(
                f"Turbidity Surge: Recent simulated turbidity ({recent_avg_turb}) is {turb_change:+.1f}% "
                f"relative to baseline ({hist_avg_turb:.1f}). Indicates sediment pre-filter particulate stress."
            )

        if (recent_avg_tds >= 350.0 and tds_change >= 20.0) or recent_avg_tds >= 400.0:
            unusual = True
            findings.append(
                f"TDS Escalation: Recent TDS ({recent_avg_tds} ppm) is {tds_change:+.1f}% "
                f"relative to baseline ({hist_avg_tds:.1f} ppm). Indicates potential RO membrane fouling or raw feed salinity spike."
            )

        if not findings:
            findings.append(
                f"Water quality parameters remain stable within calibrated tolerances "
                f"(TDS delta: {tds_change:+.1f}%, Turbidity delta: {turb_change:+.1f}%)."
            )

        trend = WaterQualityTrendAnalysis(
            unusual_change_detected=unusual,
            turbidity_change_pct=turb_change,
            tds_change_pct=tds_change,
            findings=findings
        )

        return burden, trend

    def _calculate_transparent_health(
        self,
        operating_hours: float,
        burden: WaterQualityBurden,
        settings: Dict[str, Any]
    ) -> Tuple[float, str, CalculationTransparency, List[FilterStage]]:
        """
        Calculate transparent estimated filter health percentage and individual stage conditions.
        Health is computed formulaically from active runtime and telemetry water quality burden.
        """
        rated_lifespan = float(settings.get("filter_max_operating_hours", 2000.0))

        # Base wear purely from operating time
        base_wear_pct = min(92.0, (operating_hours / rated_lifespan) * 100.0)

        # Burden penalty from water quality stress
        burden_penalty_pct = base_wear_pct * (burden.water_burden_multiplier - 1.0)
        raw_health = 100.0 - base_wear_pct - burden_penalty_pct
        estimated_health_pct = round(max(5.0, min(100.0, raw_health)), 1)

        # Condition category
        if estimated_health_pct >= 80.0:
            condition = "Optimal"
        elif estimated_health_pct >= 60.0:
            condition = "Good"
        elif estimated_health_pct >= 40.0:
            condition = "Fair"
        elif estimated_health_pct >= 20.0:
            condition = "Needs Maintenance"
        else:
            condition = "Critical - Replacement Due"

        # Multi-stage breakdown with specific contaminant wear
        # Stage 1: PP Spun Sediment (heavily affected by turbidity)
        st1_wear = base_wear_pct * (1.0 + burden.turbidity_stress_factor * 1.5)
        st1_pct = round(max(5.0, min(100.0, 100.0 - st1_wear)), 1)
        st1_days = max(5, int((st1_pct / 100.0) * 180))

        # Stage 2: Pre-Carbon Block (adsorption wear)
        st2_wear = base_wear_pct * 1.05
        st2_pct = round(max(5.0, min(100.0, 100.0 - st2_wear)), 1)
        st2_days = max(5, int((st2_pct / 100.0) * 180))

        # Stage 3: RO Membrane (heavily affected by TDS)
        st3_wear = base_wear_pct * (1.0 + burden.tds_stress_factor * 1.8)
        st3_pct = round(max(5.0, min(100.0, 100.0 - st3_wear)), 1)
        st3_days = max(10, int((st3_pct / 100.0) * 365))

        # Stage 4: Post-Carbon Mineralizer (mineral release wear)
        st4_wear = base_wear_pct * 1.10
        st4_pct = round(max(5.0, min(100.0, 100.0 - st4_wear)), 1)
        st4_days = max(5, int((st4_pct / 100.0) * 180))

        def get_stage_status(pct: float) -> str:
            if pct >= 80: return "Optimal"
            if pct >= 60: return "Good"
            if pct >= 40: return "Fair"
            return "Replace Soon"

        stages = [
            FilterStage(
                id="stage-1-sediment",
                name="Sediment Pre-Filter (PP Spun)",
                stage_number=1,
                type="Mechanical Filtration (5 Micron)",
                condition_pct=st1_pct,
                status=get_stage_status(st1_pct),
                lifespan_days=180,
                days_remaining=st1_days,
                description="Traps suspended silt, sand, rust, and turbidity particles before entering delicate RO membrane.",
                target_contaminants="Coarse sediment, rust, visible turbidity",
                replacement_model="Atomberg ProClean PP-5M"
            ),
            FilterStage(
                id="stage-2-precarbon",
                name="Pre-Carbon Block Filter",
                stage_number=2,
                type="Adsorption (Activated Coconut Shell)",
                condition_pct=st2_pct,
                status=get_stage_status(st2_pct),
                lifespan_days=180,
                days_remaining=st2_days,
                description="Adsorbs chlorine, organic volatile compounds, pesticides, foul odor and taste.",
                target_contaminants="Chlorine, odor, pesticides, VOCs",
                replacement_model="Atomberg PureCarb Block-10"
            ),
            FilterStage(
                id="stage-3-ro",
                name="RO Membrane (High Recovery)",
                stage_number=3,
                type="Reverse Osmosis (0.0001 Micron)",
                condition_pct=st3_pct,
                status=get_stage_status(st3_pct),
                lifespan_days=365,
                days_remaining=st3_days,
                description="Semi-permeable thin-film composite membrane reducing dissolved solids (simulated TDS).",
                target_contaminants="High TDS, salts, dissolved inorganics",
                replacement_model="Atomberg DuraFlow RO-75GPD"
            ),
            FilterStage(
                id="stage-4-postcarbon",
                name="Post-Carbon & Alkaline Mineralizer",
                stage_number=4,
                type="Mineral Infusion & Polish",
                condition_pct=st4_pct,
                status=get_stage_status(st4_pct),
                lifespan_days=180,
                days_remaining=st4_days,
                description="Restores essential calcium/magnesium minerals, balances drinking pH (6.5-8.5), and enriches taste.",
                target_contaminants="Taste polish, pH stabilization",
                replacement_model="Atomberg AlkiPure Mineralizer"
            )
        ]

        transparency = CalculationTransparency(
            formula="Health% = max(5.0, 100.0 - Base_Wear% - Burden_Penalty%)",
            rated_lifespan_hours=rated_lifespan,
            base_wear_pct=round(base_wear_pct, 2),
            water_burden_penalty_pct=round(burden_penalty_pct, 2),
            raw_computed_pct=round(raw_health, 2),
            transparency_notes=[
                f"Rated service life: {rated_lifespan:.0f} operating hours.",
                f"Operational runtime wear deduction: {base_wear_pct:.1f}%.",
                f"Water quality stress multiplier: {burden.water_burden_multiplier}x (Stress Level: {burden.stress_level}).",
                f"Contaminant burden deduction: {burden_penalty_pct:.1f}%."
            ]
        )

        return estimated_health_pct, condition, transparency, stages

    def _generate_recommendation(
        self,
        health_pct: float,
        condition: str,
        trend: WaterQualityTrendAnalysis,
        settings: Dict[str, Any],
        next_service_date: str
    ) -> Tuple[str, str]:
        """Generate concrete maintenance recommendations and clear explanations."""
        crit_th = float(settings.get("filter_critical_threshold", 15.0))
        warn_th = float(settings.get("filter_warning_threshold", 30.0))

        if health_pct <= crit_th:
            rec = "CRITICAL: Immediate Purifier Filter Replacement Required."
            reason = (
                f"Estimated filter health has reached {health_pct:.1f}%, which is below the critical threshold ({crit_th:.1f}%). "
                f"Filtration performance is substantially depleted; continuing operation risks membrane scaling and contaminated drinking water."
            )
        elif health_pct <= warn_th:
            rec = "SCHEDULE SERVICE: Procure replacement cartridges and schedule filter maintenance within 14 days."
            reason = (
                f"Estimated filter health has declined to {health_pct:.1f}%, reaching the maintenance warning threshold ({warn_th:.1f}%). "
                f"Cartridges should be replaced soon to maintain high water purity and prevent pump strain."
            )
        elif trend.unusual_change_detected:
            rec = "RECOMMENDED: Inspect pre-filter mesh and verify raw input water parameters."
            reason = (
                f"Unusual water-quality trend detected: {trend.findings[0]} "
                f"Pre-filter inspection is advised to prevent premature membrane exhaustion."
            )
        else:
            rec = "ROUTINE OPERATION: Filter stages operating within normal tolerances. No immediate maintenance required."
            reason = (
                f"Purifier condition is {condition} ({health_pct:.1f}%). All stages exhibit steady flow resistance and mineral balance. "
                f"Next routine preventative service projected for {next_service_date}."
            )

        return rec, reason

    async def _record_usage_snapshot(
        self,
        doc: Dict[str, Any],
        event_type: str = "periodic_snapshot",
        note: Optional[str] = None,
        health_pct: Optional[float] = None,
        condition: Optional[str] = None,
        burden: Optional[WaterQualityBurden] = None
    ):
        """Persist a point-in-time filter usage snapshot to filter_usage_history collection."""
        history_col = await self.get_usage_history_collection()
        now_iso = datetime.now(timezone.utc).isoformat()

        entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now_iso,
            "operating_hours": round(doc.get("operating_hours", 1420.5), 1),
            "processed_volume_liters": round(doc.get("processed_volume_liters", 4850.0), 1),
            "estimated_filter_health_percentage": health_pct if health_pct is not None else 78.0,
            "filter_condition": condition or "Good",
            "tds_recent_avg": burden.recent_avg_tds if burden else 165.0,
            "turbidity_recent_avg": burden.recent_avg_turbidity if burden else 1.2,
            "water_burden_multiplier": burden.water_burden_multiplier if burden else 1.0,
            "event_type": event_type,
            "note": note
        }
        await history_col.insert_one(entry)

    async def get_filter_health(self) -> Dict[str, Any]:
        """
        Primary endpoint method computing all 10 requirements:
        historical analytics, operating duration, transparent health indicator,
        unusual trends, recommendations, and maintenance alerts.
        """
        doc = await self._get_current_state()
        settings = await self.get_settings()

        # 1. Historical TDS & Turbidity Analysis & Trend Detection (Requirements 1, 5)
        burden, trend = await self._analyze_historical_water_quality()

        # 2. Operating Duration Tracking (Requirement 2)
        operating_hours = round(float(doc.get("operating_hours", 1420.5)), 1)
        last_serviced_date = doc.get("last_serviced_date", "2026-08-15")
        next_scheduled_service = doc.get("next_scheduled_service", "2027-02-15")

        try:
            last_date = datetime.strptime(last_serviced_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_elapsed = (datetime.now(timezone.utc) - last_date).days
        except Exception:
            days_elapsed = 81

        usage_duration_str = f"{operating_hours} operating hours (~{days_elapsed} days elapsed since last maintenance)"

        # 3. Transparent Health Indicator Calculation (Requirement 4)
        estimated_health_pct, condition, transparency, stages = self._calculate_transparent_health(
            operating_hours=operating_hours,
            burden=burden,
            settings=settings
        )

        # 4. Maintenance Recommendation & Reason (Requirement 6)
        recommendation, reason = self._generate_recommendation(
            health_pct=estimated_health_pct,
            condition=condition,
            trend=trend,
            settings=settings,
            next_service_date=next_scheduled_service
        )

        # 5. Maintenance Alert Generation (Requirement 8)
        from services.alert_service import alert_service
        await alert_service.evaluate_filter_maintenance(
            filter_health_pct=estimated_health_pct,
            filter_condition=condition,
            recommendation=recommendation,
            reason=reason,
            settings=settings,
            unusual_change_detected=trend.unusual_change_detected,
            unusual_change_description=trend.findings[0] if trend.findings else None
        )

        # 6. Update cached state in DB if changed
        col = await self.get_filter_collection()
        await col.update_one(
            {"_id": "filter_state_01"},
            {"$set": {
                "stages": [s.model_dump() for s in stages],
                "last_evaluated_condition_pct": estimated_health_pct,
                "last_evaluated_status": condition
            }}
        )

        # 7. Construct API response adhering to Requirement 10 and existing UI contract
        thresholds = FilterMaintenanceThresholds(
            warning_threshold_pct=float(settings.get("filter_warning_threshold", 30.0)),
            critical_threshold_pct=float(settings.get("filter_critical_threshold", 15.0)),
            rated_lifespan_hours=float(settings.get("filter_max_operating_hours", 2000.0))
        )

        response = FilterHealthResponse(
            estimated_filter_health_percentage=estimated_health_pct,
            filter_condition=condition,
            usage_duration=usage_duration_str,
            last_maintenance_date=last_serviced_date,
            maintenance_recommendation=recommendation,
            reason_for_recommendation=reason,
            overall_condition_pct=estimated_health_pct,
            overall_status=condition,
            operating_hours=operating_hours,
            processed_volume_liters=round(float(doc.get("processed_volume_liters", 4850.0)), 1),
            stages=stages,
            last_serviced_date=last_serviced_date,
            next_scheduled_service=next_scheduled_service,
            is_demo_data=True,
            water_quality_burden=burden,
            trend_analysis=trend,
            calculation_transparency=transparency,
            maintenance_thresholds=thresholds
        )

        return response.model_dump()

    async def increment_usage(
        self,
        liters: float = 0.2,
        tds: Optional[float] = None,
        turbidity: Optional[float] = None,
        device_id: Optional[str] = None
    ):
        """
        Record operational telemetry wear on purifier filters from active readings.
        Increments operating runtime and volume, and periodically logs snapshots.
        """
        col = await self.get_filter_collection()
        doc = await self._get_current_state()

        # Each reading interval represents active operational pump runtime (~15 seconds = 0.0042 hours)
        delta_hours = liters / 12.0  # standard 12 L/hr domestic RO pump flow
        new_hours = round(doc.get("operating_hours", 1420.5) + delta_hours, 2)
        new_vol = round(doc.get("processed_volume_liters", 4850.0) + liters, 2)
        reading_count = doc.get("telemetry_reading_count", 0) + 1
        now_iso = datetime.now(timezone.utc).isoformat()

        await col.update_one(
            {"_id": "filter_state_01"},
            {"$set": {
                "operating_hours": new_hours,
                "processed_volume_liters": new_vol,
                "telemetry_reading_count": reading_count,
                "last_telemetry_timestamp": now_iso
            }}
        )

        # Log periodic snapshots into filter_usage_history every 25 readings
        if reading_count % 25 == 0:
            doc["operating_hours"] = new_hours
            doc["processed_volume_liters"] = new_vol
            burden, _ = await self._analyze_historical_water_quality()
            settings = await self.get_settings()
            health_pct, condition, _, _ = self._calculate_transparent_health(new_hours, burden, settings)
            await self._record_usage_snapshot(
                doc=doc,
                event_type="telemetry_update",
                note=f"Automated usage snapshot at {reading_count} telemetry cycles.",
                health_pct=health_pct,
                condition=condition,
                burden=burden
            )

    async def reset_filters(self, technician: str = "Simulated Service / User", notes: str = "Cartridge replacement completed.") -> Dict[str, Any]:
        """
        Reset filter conditions to 100% optimal condition, record a maintenance log entry,
        and log a reset event into filter_usage_history.
        """
        col = await self.get_filter_collection()
        curr_doc = await self._get_current_state()
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.strftime("%Y-%m-%d")
        next_service = (now_dt + timedelta(days=180)).strftime("%Y-%m-%d")

        # Record maintenance log entry (Requirement 3 & 9)
        m_col = await self.get_maintenance_log_collection()
        log_entry = MaintenanceLogEntry(
            id=str(uuid.uuid4()),
            timestamp=now_dt.isoformat(),
            action="Cartridge Replacement",
            technician=technician,
            operating_hours_at_service=float(curr_doc.get("operating_hours", 0.0)),
            previous_condition_pct=float(curr_doc.get("last_evaluated_condition_pct", 74.0)),
            notes=notes
        )
        await m_col.insert_one(log_entry.model_dump())

        # Reset state document
        doc = {
            "_id": "filter_state_01",
            "operating_hours": 0.0,
            "processed_volume_liters": 0.0,
            "last_serviced_date": now_str,
            "next_scheduled_service": next_service,
            "telemetry_reading_count": 0,
            "last_telemetry_timestamp": now_dt.isoformat(),
            "stages": [
                {
                    "id": "stage-1-sediment",
                    "name": "Sediment Pre-Filter (PP Spun)",
                    "stage_number": 1,
                    "type": "Mechanical Filtration (5 Micron)",
                    "condition_pct": 100.0,
                    "status": "Optimal",
                    "lifespan_days": 180,
                    "days_remaining": 180,
                    "description": "Traps suspended silt, sand, rust, and turbidity particles before entering delicate RO membrane.",
                    "target_contaminants": "Coarse sediment, rust, visible turbidity",
                    "replacement_model": "Atomberg ProClean PP-5M"
                },
                {
                    "id": "stage-2-precarbon",
                    "name": "Pre-Carbon Block Filter",
                    "stage_number": 2,
                    "type": "Adsorption (Activated Coconut Shell)",
                    "condition_pct": 100.0,
                    "status": "Optimal",
                    "lifespan_days": 180,
                    "days_remaining": 180,
                    "description": "Adsorbs chlorine, organic volatile compounds, pesticides, foul odor and taste.",
                    "target_contaminants": "Chlorine, odor, pesticides, VOCs",
                    "replacement_model": "Atomberg PureCarb Block-10"
                },
                {
                    "id": "stage-3-ro",
                    "name": "RO Membrane (High Recovery)",
                    "stage_number": 3,
                    "type": "Reverse Osmosis (0.0001 Micron)",
                    "condition_pct": 100.0,
                    "status": "Optimal",
                    "lifespan_days": 365,
                    "days_remaining": 365,
                    "description": "Semi-permeable thin-film composite membrane reducing dissolved solids (simulated TDS).",
                    "target_contaminants": "High TDS, salts, dissolved inorganics",
                    "replacement_model": "Atomberg DuraFlow RO-75GPD"
                },
                {
                    "id": "stage-4-postcarbon",
                    "name": "Post-Carbon & Alkaline Mineralizer",
                    "stage_number": 4,
                    "type": "Mineral Infusion & Polish",
                    "condition_pct": 100.0,
                    "status": "Optimal",
                    "lifespan_days": 180,
                    "days_remaining": 180,
                    "description": "Restores essential calcium/magnesium minerals, balances drinking pH (6.5-8.5), and enriches taste.",
                    "target_contaminants": "Taste polish, pH stabilization",
                    "replacement_model": "Atomberg AlkiPure Mineralizer"
                }
            ]
        }
        await col.update_one({"_id": "filter_state_01"}, {"$set": doc})

        # Log reset snapshot in usage history
        await self._record_usage_snapshot(
            doc=doc,
            event_type="maintenance_reset",
            note="Purifier filter cartridges serviced and operational runtime reset to 0.0 hrs.",
            health_pct=100.0,
            condition="Optimal"
        )

        return await self.get_filter_health()

    async def get_usage_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch historical usage records from persistent storage (Requirement 3)."""
        col = await self.get_usage_history_collection()
        cursor = col.find().sort("timestamp", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        for it in items:
            if "_id" in it:
                it["id"] = str(it["_id"])
        return items

    async def get_maintenance_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch maintenance service history records from persistent storage (Requirement 3)."""
        col = await self.get_maintenance_log_collection()
        cursor = col.find().sort("timestamp", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        for it in items:
            if "_id" in it:
                it["id"] = str(it["_id"])
        return items

filter_service = FilterService()
