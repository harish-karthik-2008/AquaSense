"""
AquaSense AI - Filter Health Data Models
Defines structured schemas for multi-stage purifier filter analytics,
transparency breakdowns, trend analysis, usage history, and maintenance logs.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FilterStage(BaseModel):
    id: str
    name: str
    stage_number: int
    type: str
    condition_pct: float
    status: str  # Optimal, Good, Fair, Replace Soon, Critical
    lifespan_days: int
    days_remaining: int
    description: str
    target_contaminants: str
    replacement_model: str

class WaterQualityBurden(BaseModel):
    historical_avg_tds: float
    historical_avg_turbidity: float
    recent_avg_tds: float
    recent_avg_turbidity: float
    turbidity_stress_factor: float
    tds_stress_factor: float
    water_burden_multiplier: float
    stress_level: str  # Low, Moderate, High

class WaterQualityTrendAnalysis(BaseModel):
    unusual_change_detected: bool
    turbidity_change_pct: float
    tds_change_pct: float
    findings: List[str]

class CalculationTransparency(BaseModel):
    formula: str
    rated_lifespan_hours: float
    base_wear_pct: float
    water_burden_penalty_pct: float
    raw_computed_pct: float
    transparency_notes: List[str]

class FilterMaintenanceThresholds(BaseModel):
    warning_threshold_pct: float
    critical_threshold_pct: float
    rated_lifespan_hours: float

class FilterHealthResponse(BaseModel):
    # Core User Requirements (Item 10):
    estimated_filter_health_percentage: float
    filter_condition: str
    usage_duration: str
    last_maintenance_date: Optional[str] = None
    maintenance_recommendation: str
    reason_for_recommendation: str

    # Backwards compatibility fields for frontend (FilterHealth.jsx & Overview.jsx):
    overall_condition_pct: float
    overall_status: str
    operating_hours: float
    processed_volume_liters: float
    stages: List[FilterStage]
    last_serviced_date: str
    next_scheduled_service: str
    is_demo_data: bool = True
    disclaimer: str = (
        "Estimated Health Indicator: Purifier filter condition is computed from operational runtime "
        "and telemetry-derived water quality burden factors. This indicator represents a transparent "
        "operational estimate for IoT demonstration and is distinct from manufacturer-certified cartridge wear."
    )

    # Detailed Analytical Context
    water_quality_burden: Optional[WaterQualityBurden] = None
    trend_analysis: Optional[WaterQualityTrendAnalysis] = None
    calculation_transparency: Optional[CalculationTransparency] = None
    maintenance_thresholds: Optional[FilterMaintenanceThresholds] = None

class FilterUsageHistoryEntry(BaseModel):
    timestamp: str
    operating_hours: float
    processed_volume_liters: float
    estimated_filter_health_percentage: float
    filter_condition: str
    tds_recent_avg: float
    turbidity_recent_avg: float
    water_burden_multiplier: float
    event_type: str  # telemetry_update, periodic_snapshot, maintenance_reset, threshold_alert
    note: Optional[str] = None

class MaintenanceLogEntry(BaseModel):
    id: str
    timestamp: str
    action: str  # Cartridge Service, Inspection, Filter Reset
    technician: str
    operating_hours_at_service: float
    previous_condition_pct: float
    notes: str
