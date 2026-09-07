"""
Stream & Unified Viewer Schemas
Provides data transfer objects for stream capabilities, playback mode determination,
available footage inspection, and viewer aggregate metrics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import enum
from app.models.camera import SourceType, ConnectivityType, CameraStatus, CameraType


class StreamStatusEnum(str, enum.Enum):
    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"
    DISCONNECTED = "DISCONNECTED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    ERROR = "ERROR"


class PlaybackModeEnum(str, enum.Enum):
    RECORDED_STREAM = "RECORDED_STREAM"    # HTTP 206 partial content streaming of local MP4 footage
    HLS_RELAY = "HLS_RELAY"                # Authorized HTTP Live Streaming (HLS) stream
    RTSP_ADAPTER = "RTSP_ADAPTER"          # RTSP stream requiring media relay/adapter layer
    DIRECT_HTTP = "DIRECT_HTTP"            # Direct browser-compatible HTTP video stream
    UNAVAILABLE = "UNAVAILABLE"            # No stream URL or footage available


class CameraFootageItem(BaseModel):
    id: int
    file_name: str
    original_file_name: str
    duration_seconds: Optional[float] = None
    formatted_duration: str
    file_size_bytes: int
    recording_start_time: Optional[datetime] = None
    recording_end_time: Optional[datetime] = None
    stream_url: str
    created_at: datetime


class CameraStreamInfoResponse(BaseModel):
    camera_id: int
    camera_code: str
    camera_name: str
    department: str
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_valid_coordinates: bool = False
    
    # Classification & Connectivity
    camera_type: CameraType
    source_type: SourceType
    connectivity_type: ConnectivityType
    camera_status: CameraStatus
    
    # Stream & Playback determination
    playback_mode: PlaybackModeEnum
    stream_status: StreamStatusEnum
    stream_url: Optional[str] = None
    is_playable_in_browser: bool
    status_message: str
    
    # Available recorded footage
    footage_count: int = 0
    available_footage: List[CameraFootageItem] = []
    
    # Active Watchlist alert context
    active_alerts_count: int = 0
    latest_alert_message: Optional[str] = None
    latest_alert_severity: Optional[str] = None


class ViewerStatsResponse(BaseModel):
    total_registered_cameras: int = 0
    online_cameras: int = 0
    offline_cameras: int = 0
    recorded_footage_sources: int = 0
    live_stream_sources: int = 0
    total_footage_files: int = 0
    active_watchlist_alerts: int = 0
