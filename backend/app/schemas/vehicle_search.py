"""
Vehicle Search & Observed Camera Detection Sequence Schemas
Provides data transfer objects for vehicle plate queries, chronological observations,
camera detection sequence steps, summary analytics, and linked watchlist alert history.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.anpr import AnprStatus, PlateFormatStatus
from app.models.alert import AlertType, AlertSeverity, AlertStatus


class VehicleObservationItem(BaseModel):
    id: int
    anpr_detection_id: int
    footage_id: int
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    department: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_valid_coordinates: bool = False
    
    # Timing & Video context
    timestamp_seconds: float
    formatted_timestamp: str
    observed_at: Optional[datetime] = None
    formatted_datetime: str
    footage_filename: str
    video_stream_url: str
    
    # Vehicle & ANPR details
    plate_text: str
    plate_number_raw: Optional[str] = None
    plate_number_normalized: Optional[str] = None
    vehicle_class: str
    track_id: Optional[int] = None
    
    # Confidence metrics
    confidence: float
    confidence_percent: str
    ocr_confidence: Optional[float] = None
    ocr_confidence_percent: str
    detection_confidence: Optional[float] = None
    status: AnprStatus
    format_status: PlateFormatStatus
    
    # Visual evidence
    plate_crop_url: Optional[str] = None
    has_crop: bool = False

    class Config:
        from_attributes = True


class ObservedCameraSequenceStep(BaseModel):
    step_number: int
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    department: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_valid_coordinates: bool = False
    
    # Sequence timing
    first_timestamp_seconds: float
    formatted_first_timestamp: str
    first_observed_at: Optional[datetime] = None
    last_timestamp_seconds: float
    formatted_last_timestamp: str
    last_observed_at: Optional[datetime] = None
    time_window_display: str
    
    # Aggregated encounter stats
    sighting_count: int = 1
    primary_vehicle_class: str
    track_ids: List[int] = []
    best_confidence: float
    best_confidence_percent: str
    best_ocr_confidence: Optional[float] = None
    best_ocr_confidence_percent: str
    
    # Primary representative evidence
    primary_anpr_id: int
    primary_footage_id: int
    primary_crop_url: Optional[str] = None
    video_stream_url: str


class VehicleSearchSummary(BaseModel):
    total_observations: int = 0
    unique_cameras_count: int = 0
    departments_count: int = 0
    first_observed_at: Optional[str] = None
    last_observed_at: Optional[str] = None
    duration_span: Optional[str] = None


class VehicleAlertHistoryItem(BaseModel):
    id: int
    watchlist_entry_id: Optional[int] = None
    watchlist_category: Optional[str] = None
    watchlist_description: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    message: str
    camera_code: str
    camera_name: str
    location_name: str
    timestamp_seconds: float
    formatted_timestamp: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class VehicleSearchResponse(BaseModel):
    query_plate_raw: str
    query_plate_normalized: str
    total_observations: int = 0
    disclaimer: str = "Observed camera detections based on available CCTV/ANPR records. Does not represent continuous vehicle route tracking."
    summary: VehicleSearchSummary
    observations: List[VehicleObservationItem] = []
    observed_sequence: List[ObservedCameraSequenceStep] = []
    alerts_history: List[VehicleAlertHistoryItem] = []
