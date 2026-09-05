"""
Footage Pydantic Schemas
Defines request validation and response models for recorded CCTV footage.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.footage import FootageStatus


class FootageBase(BaseModel):
    description: Optional[str] = None
    recording_start_time: Optional[datetime] = None
    recording_end_time: Optional[datetime] = None


class FootageResponse(BaseModel):
    id: int
    camera_id: int
    file_name: str
    original_file_name: str
    file_path: str
    file_size: int
    mime_type: str
    
    duration_seconds: Optional[float] = None
    video_width: Optional[int] = None
    video_height: Optional[int] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    
    recording_start_time: Optional[datetime] = None
    recording_end_time: Optional[datetime] = None
    status: FootageStatus
    description: Optional[str] = None
    created_at: datetime
    
    stream_url: str = Field(description="URL for streaming video directly in browser")

    class Config:
        from_attributes = True
