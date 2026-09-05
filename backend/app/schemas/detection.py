"""
Vehicle Detection & Processing Job Pydantic Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.detection import JobType, JobStatus


class DetectionResponse(BaseModel):
    id: int
    footage_id: int
    frame_number: int
    timestamp_seconds: float
    formatted_timestamp: str = Field(description="Formatted mm:ss.s timestamp")
    vehicle_class: str
    confidence: float
    confidence_percent: str
    track_id: Optional[int] = None
    x1: float
    y1: float
    x2: float
    y2: float
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessingJobResponse(BaseModel):
    id: int
    footage_id: int
    job_type: JobType
    status: JobStatus
    progress: int
    device: str
    total_frames: Optional[int] = None
    processed_frames: Optional[int] = None
    
    # Detection summary
    total_detections: int = 0
    cars_count: int = 0
    motorcycles_count: int = 0
    buses_count: int = 0
    trucks_count: int = 0
    
    # Tracking summary
    total_tracks: int = 0
    car_tracks: int = 0
    motorcycle_tracks: int = 0
    bus_tracks: int = 0
    truck_tracks: int = 0

    # ANPR summary
    total_plates_detected: int = 0
    successful_ocr_count: int = 0
    valid_format_count: int = 0
    unique_plates_count: int = 0

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_video_stream_url: Optional[str] = None

    class Config:
        from_attributes = True


class VehicleTrackResponse(BaseModel):
    id: int
    footage_id: int
    track_id: int
    vehicle_class: str
    first_seen_seconds: float
    first_seen_formatted: str
    last_seen_seconds: float
    last_seen_formatted: str
    duration_seconds: float
    first_seen_frame: int
    last_seen_frame: int
    detection_count: int
    avg_confidence: float
    avg_confidence_percent: str
    crop_url: Optional[str] = None
    has_crop: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class VehicleTrackDetailResponse(VehicleTrackResponse):
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    original_file_name: str
    detections: List[DetectionResponse] = []


class TrackSummaryResponse(BaseModel):
    footage_id: int
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    original_file_name: str
    original_video_stream_url: str
    processed_video_stream_url: Optional[str] = None
    has_processed_video: bool
    latest_job: Optional[ProcessingJobResponse] = None
    total_tracks: int
    car_tracks: int
    motorcycle_tracks: int
    bus_tracks: int
    truck_tracks: int
    total_detections: int
    tracks: List[VehicleTrackResponse] = []


class DetectionSummaryResponse(BaseModel):
    footage_id: int
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    original_file_name: str
    original_video_stream_url: str
    processed_video_stream_url: Optional[str] = None
    has_processed_video: bool
    latest_job: Optional[ProcessingJobResponse] = None
    total_detections: int
    cars_count: int
    motorcycles_count: int
    buses_count: int
    trucks_count: int
    total_tracks: int = 0
    detections: List[DetectionResponse] = []
