from pydantic import BaseModel, Field

class ThresholdSettings(BaseModel):
    tds_warning_threshold: float = Field(300.0, description="TDS warning limit in ppm", ge=50.0, le=2000.0)
    tds_critical_threshold: float = Field(500.0, description="TDS critical limit in ppm", ge=100.0, le=3000.0)
    ph_min_acceptable: float = Field(6.5, description="Minimum acceptable drinking water pH", ge=0.0, le=14.0)
    ph_max_acceptable: float = Field(8.5, description="Maximum acceptable drinking water pH", ge=0.0, le=14.0)
    turbidity_warning_threshold: float = Field(5.0, description="Turbidity warning threshold (simulated scale)", ge=1.0, le=50.0)
    turbidity_critical_threshold: float = Field(10.0, description="Turbidity critical threshold (simulated scale)", ge=2.0, le=100.0)
    anomaly_sensitivity: str = Field("medium", description="AI anomaly sensitivity: low, medium, or high")
    heartbeat_timeout_seconds: int = Field(25, description="Seconds without data before marking ESP32 offline", ge=5, le=120)
    filter_warning_threshold: float = Field(30.0, description="Filter health warning threshold (%)", ge=5.0, le=90.0)
    filter_critical_threshold: float = Field(15.0, description="Filter health critical replacement threshold (%)", ge=1.0, le=50.0)
    filter_max_operating_hours: float = Field(2000.0, description="Rated filter lifespan in operating hours", ge=100.0, le=10000.0)
