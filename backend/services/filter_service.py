"""
Predictive Filter Health Service for AquaSense AI
Provides multi-stage purifier filter condition analytics, operating life metrics,
and maintenance reminders.
Explicitly labeled demonstration data ready for telemetry integration.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from database.connection import DatabaseManager
from models.filter import FilterHealthResponse, FilterStage

class FilterService:
    def __init__(self):
        self._default_state = {
            "operating_hours": 1420.5,
            "processed_volume_liters": 4850.0,
            "last_serviced_date": "2026-08-15",
            "next_scheduled_service": "2027-02-15",
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
                    "description": "Semi-permeable thin-film composite membrane rejecting dissolved salts (TDS) and heavy metals.",
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

    async def get_filter_health(self) -> Dict[str, Any]:
        col = await self.get_filter_collection()
        doc = await col.find_one({"_id": "filter_state_01"})
        if not doc:
            doc = dict(self._default_state)
            doc["_id"] = "filter_state_01"
            await col.insert_one(doc)

        stages_list = [FilterStage(**st) for st in doc.get("stages", self._default_state["stages"])]
        
        # Calculate overall condition as weighted average
        weights = [0.2, 0.2, 0.45, 0.15]
        overall = sum(s.condition_pct * w for s, w in zip(stages_list, weights))
        overall_pct = round(overall, 1)

        overall_status = "Optimal"
        if overall_pct < 50:
            overall_status = "Replace Soon"
        elif overall_pct < 75:
            overall_status = "Good"

        response = FilterHealthResponse(
            overall_condition_pct=overall_pct,
            overall_status=overall_status,
            operating_hours=round(doc.get("operating_hours", 1420.5), 1),
            processed_volume_liters=round(doc.get("processed_volume_liters", 4850.0), 1),
            stages=stages_list,
            last_serviced_date=doc.get("last_serviced_date", "2026-08-15"),
            next_scheduled_service=doc.get("next_scheduled_service", "2027-02-15"),
            is_demo_data=True
        )
        return response.model_dump()

    async def increment_usage(self, liters: float = 0.5):
        """Simulate incremental water processing and microscopic wear on filters."""
        col = await self.get_filter_collection()
        doc = await col.find_one({"_id": "filter_state_01"})
        if not doc:
            doc = dict(self._default_state)
            doc["_id"] = "filter_state_01"
            await col.insert_one(doc)

        new_vol = doc.get("processed_volume_liters", 4850.0) + liters
        new_hours = doc.get("operating_hours", 1420.5) + (liters / 12.0) # approx 12 L/hr

        stages = doc.get("stages", self._default_state["stages"])
        for st in stages:
            # Slow wear
            wear_rate = 0.002
            st["condition_pct"] = max(5.0, round(st["condition_pct"] - (liters * wear_rate), 2))
            if st["condition_pct"] > 80:
                st["status"] = "Optimal"
            elif st["condition_pct"] > 60:
                st["status"] = "Good"
            elif st["condition_pct"] > 40:
                st["status"] = "Fair"
            else:
                st["status"] = "Replace Soon"

        await col.update_one(
            {"_id": "filter_state_01"},
            {"$set": {
                "processed_volume_liters": new_vol,
                "operating_hours": new_hours,
                "stages": stages
            }}
        )

    async def reset_filters(self) -> Dict[str, Any]:
        """Simulate filter cartridge replacement and maintenance reset."""
        col = await self.get_filter_collection()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        next_service = (datetime.now(timezone.utc) + timedelta(days=180)).strftime("%Y-%m-%d")

        refreshed_stages = [
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
                "description": "Semi-permeable thin-film composite membrane rejecting dissolved salts (TDS) and heavy metals.",
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

        doc = {
            "_id": "filter_state_01",
            "operating_hours": 0.0,
            "processed_volume_liters": 0.0,
            "last_serviced_date": now_str,
            "next_scheduled_service": next_service,
            "stages": refreshed_stages
        }
        await col.update_one({"_id": "filter_state_01"}, {"$set": doc})
        return await self.get_filter_health()

filter_service = FilterService()

