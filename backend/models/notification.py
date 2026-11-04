"""
AquaSense AI - Notification and Event Data Models
Defines structured schemas for persistent notification events, read/unread states,
severity ratings, deduplication keys, and cross-system event linking.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Notification(BaseModel):
    id: str
    created_at: str
    updated_at: str
    title: str
    message: str
    severity: str = Field(..., description="Critical, Warning, or Informational")
    category: str = Field(..., description="Water Quality, AI Anomaly, Filter Maintenance, or System")
    parameter: Optional[str] = Field(None, description="TDS, pH, Turbidity, Filter Health, or System")
    reading_value: Optional[float] = None
    threshold_value: Optional[str] = None
    suggested_action: Optional[str] = None
    is_read: bool = False
    read_at: Optional[str] = None
    is_acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    occurrence_count: int = 1
    deduplication_key: str
    related_alert_id: Optional[str] = None
    related_recommendation_id: Optional[str] = None
    source_event: str = Field("alert_service", description="Originating event source")

class NotificationListResponse(BaseModel):
    status: str = "success"
    total: int
    unread_count: int
    critical_count: int
    warning_count: int
    data: List[Notification]

class NotificationSummaryResponse(BaseModel):
    status: str = "success"
    total: int
    unread: int
    acknowledged: int
    critical: int
    warning: int
    informational: int
    last_event_timestamp: Optional[str] = None

class MarkReadRequest(BaseModel):
    read_by: Optional[str] = "User"

class AcknowledgeNotificationRequest(BaseModel):
    acknowledged_by: Optional[str] = "User"

