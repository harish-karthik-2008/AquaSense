"""
AquaSense AI - Recommendation Data Models
Defines structured schemas for intelligent water quality recommendations,
priority rankings, contextual reasoning, action steps, and historical summaries.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Recommendation(BaseModel):
    id: str
    created_at: str
    last_updated_at: str
    priority: str = Field(..., description="Critical, Warning, or Informational")
    category: str = Field(..., description="Water Quality, Filter Maintenance, Anomaly Resolution, System & Calibration, Routine Advisory")
    title: str
    message: str
    reason: str
    source_factors: List[str] = Field(default_factory=list, description="Telemetry signals contributing to this recommendation")
    action: str
    action_steps: List[str] = Field(default_factory=list)
    parameter: Optional[str] = None
    current_value: Optional[float] = None
    threshold_or_baseline: Optional[str] = None
    is_dismissed: bool = False
    dismissed_at: Optional[str] = None
    occurrence_count: int = 1
    deduplication_key: str
    related_alert_id: Optional[str] = None

class RecommendationSummaryResponse(BaseModel):
    active_recommendations: List[Recommendation]
    total_active: int
    critical_count: int
    warning_count: int
    informational_count: int
    overall_water_assessment: str
    synthesis_timestamp: str
    disclaimer: str = (
        "Advisory Guidance: Recommendations are computed from real-time and historical sensor telemetry "
        "and predictive purifier maintenance models for domestic water treatment. This system does not certify "
        "potability or claim detection of microbiological pathogens (bacteria/viruses) or heavy metals."
    )

class DismissRecommendationRequest(BaseModel):
    dismissed_by: Optional[str] = "User"
    notes: Optional[str] = None

