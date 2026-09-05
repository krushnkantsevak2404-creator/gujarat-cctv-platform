"""
ANPR & OCR Pydantic Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.anpr import AnprStatus, PlateFormatStatus
from app.schemas.detection import ProcessingJobResponse


class AnprDetectionResponse(BaseModel):
    id: int
    footage_id: int
    track_id: Optional[int] = None
    frame_number: int
    timestamp_seconds: float
    formatted_timestamp: str = Field(description="Formatted mm:ss.s timestamp")
    vehicle_class: str
    plate_number_raw: Optional[str] = None
    plate_number_normalized: Optional[str] = None
    confidence: float
    confidence_percent: str
    ocr_confidence: Optional[float] = None
    detection_confidence: Optional[float] = None
    status: AnprStatus
    format_status: PlateFormatStatus
    x1: float
    y1: float
    x2: float
    y2: float
    vehicle_x1: Optional[float] = None
    vehicle_y1: Optional[float] = None
    vehicle_x2: Optional[float] = None
    vehicle_y2: Optional[float] = None
    plate_crop_url: Optional[str] = None
    has_crop: bool = False
    is_consolidated: bool = True
    sighting_count: int = 1
    created_at: datetime

    class Config:
        from_attributes = True


class AnprSummaryResponse(BaseModel):
    footage_id: int
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    original_file_name: str
    original_video_stream_url: str
    latest_job: Optional[ProcessingJobResponse] = None
    total_plates_detected: int = 0
    successful_ocr_count: int = 0
    valid_format_count: int = 0
    unique_plates_count: int = 0
    detections: List[AnprDetectionResponse] = []


class AnprSearchResultItem(BaseModel):
    id: int
    footage_id: int
    camera_id: int
    camera_code: str
    camera_name: str
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp_seconds: float
    formatted_timestamp: str
    plate_number_normalized: Optional[str] = None
    plate_number_raw: Optional[str] = None
    vehicle_class: str
    status: AnprStatus
    format_status: PlateFormatStatus
    confidence: float
    confidence_percent: str
    plate_crop_url: Optional[str] = None
    has_crop: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AnprSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[AnprSearchResultItem] = []
