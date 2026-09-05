"""
Camera Pydantic Schemas
Defines request validation and response models for CCTV asset registry.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from app.models.camera import CameraType, SourceType, ConnectivityType, CameraStatus


class CameraBase(BaseModel):
    camera_name: str = Field(..., min_length=2, max_length=150, description="Name/Label of CCTV camera")
    camera_code: str = Field(..., min_length=2, max_length=50, description="Unique alphanumeric identifier (e.g. GJ-AHM-001)")
    department: str = Field(..., min_length=2, max_length=100, description="Police department / Jurisdiction (e.g. Traffic, Crime Branch, Vastrapur PS)")
    location_name: str = Field(..., min_length=2, max_length=255, description="Physical location or junction name")
    
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic Latitude (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic Longitude (-180 to +180)")
    
    camera_type: CameraType = Field(default=CameraType.FIXED, description="Hardware form factor")
    source_type: SourceType = Field(default=SourceType.LIVE_CAMERA, description="LIVE_CAMERA or RECORDED_FOOTAGE")
    connectivity_type: ConnectivityType = Field(default=ConnectivityType.UNKNOWN, description="Protocol/connectivity metadata")
    stream_url: Optional[str] = Field(default=None, max_length=500, description="Stream URL (reserved for future milestones)")
    status: CameraStatus = Field(default=CameraStatus.UNKNOWN, description="Current operational status")
    installation_date: Optional[date] = Field(default=None, description="Date of physical installation")
    description: Optional[str] = Field(default=None, description="Additional context or notes")

    @field_validator("camera_code")
    @classmethod
    def sanitize_camera_code(cls, v: str) -> str:
        code = v.strip().upper()
        if not code:
            raise ValueError("Camera code cannot be empty")
        return code


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    camera_name: Optional[str] = Field(None, min_length=2, max_length=150)
    camera_code: Optional[str] = Field(None, min_length=2, max_length=50)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    location_name: Optional[str] = Field(None, min_length=2, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    camera_type: Optional[CameraType] = None
    source_type: Optional[SourceType] = None
    connectivity_type: Optional[ConnectivityType] = None
    stream_url: Optional[str] = None
    status: Optional[CameraStatus] = None
    installation_date: Optional[date] = None
    description: Optional[str] = None


class FootageSummary(BaseModel):
    id: int
    file_name: str
    original_file_name: str
    file_size: int
    mime_type: str
    duration_seconds: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CameraResponse(CameraBase):
    id: int
    created_at: datetime
    updated_at: datetime
    footage_count: int = 0
    footage: List[FootageSummary] = []

    class Config:
        from_attributes = True


class CameraStatsResponse(BaseModel):
    total_cameras: int
    live_cameras: int
    recorded_cameras: int
    online_cameras: int
    offline_cameras: int
    maintenance_cameras: int
    unknown_cameras: int
    total_footage_files: int
