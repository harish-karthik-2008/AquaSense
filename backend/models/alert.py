from typing import Optional
from pydantic import BaseModel, Field

class Alert(BaseModel):
    id: str
    timestamp: str
    alert_type: str = Field(..., description="Threshold, Range, Anomaly, or Connectivity")
    parameter: str = Field(..., description="TDS, pH, Turbidity, or System")
    reading_value: Optional[float] = None
    threshold_value: Optional[str] = None
    severity: str = Field("Warning", description="Normal, Warning, or Critical")
    title: str
    message: str
    suggested_action: str
    acknowledged: bool = False

class AcknowledgeRequest(BaseModel):
    acknowledged_by: Optional[str] = "User"

