"""
Vehicle Alert Pydantic Schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.alert import AlertType, AlertSeverity, AlertStatus


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


class AlertResponse(BaseModel):
    id: int
    watchlist_entry_id: Optional[int] = None
    watchlist_description: Optional[str] = None
    watchlist_category: Optional[str] = None
    anpr_detection_id: int
    footage_id: int
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    track_id: Optional[int] = None
    plate_text: str
    vehicle_class: str
    timestamp_seconds: float
    formatted_timestamp: str
    confidence: float
    confidence_percent: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    message: str
    plate_crop_url: Optional[str] = None
    has_crop: bool = False
    video_stream_url: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertStatsResponse(BaseModel):
    total_alerts: int = 0
    new_alerts: int = 0
    acknowledged_alerts: int = 0
    resolved_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
