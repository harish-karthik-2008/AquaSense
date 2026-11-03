from typing import List, Optional
from pydantic import BaseModel, Field

class FilterStage(BaseModel):
    id: str
    name: str
    stage_number: int
    type: str
    condition_pct: float
    status: str  # Optimal, Good, Fair, Replace Soon
    lifespan_days: int
    days_remaining: int
    description: str
    target_contaminants: str
    replacement_model: str

class FilterHealthResponse(BaseModel):
    overall_condition_pct: float
    overall_status: str
    operating_hours: float
    processed_volume_liters: float
    stages: List[FilterStage]
    last_serviced_date: str
    next_scheduled_service: str
    is_demo_data: bool = True
    disclaimer: str = (
        "Demonstration data: Purifier filter degradation is modeled for IoT hackathon demonstration. "
        "The current ESP32 potentiometers simulate water parameters and not physical filter cartridge wear."
    )

