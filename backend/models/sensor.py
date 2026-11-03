from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class SensorReadingInput(BaseModel):
    tds: float = Field(..., description="Total Dissolved Solids in ppm", ge=0.0, le=5000.0)
    ph: float = Field(..., description="Acidity/Alkalinity on 0-14 scale", ge=0.0, le=14.0)
    turbidity: float = Field(..., description="Simulated turbidity value", ge=0.0, le=500.0)
    device_id: Optional[str] = Field("AquaSense-ESP32", description="Microcontroller unique device ID")

    @field_validator("tds", "ph", "turbidity", mode="before")
    @classmethod
    def round_values(cls, v):
        try:
            return round(float(v), 2)
        except (ValueError, TypeError):
            raise ValueError("Sensor reading must be a valid numeric value.")


class SensorReading(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    device_id: str = "AquaSense-ESP32"
    timestamp: str
    tds: float
    ph: float
    turbidity: float
    tds_status: str = "Normal"
    ph_status: str = "Normal"
    turbidity_status: str = "Normal"
    overall_status: str = "Normal"
    water_quality_score: float = 100.0
    anomaly_detected: bool = False
    anomaly_score: Optional[float] = None
    anomaly_reason: Optional[str] = None
    note: Optional[str] = "Turbidity values are simulated based on potentiometer input."

    class Config:
        populate_by_name = True

