"""
Stream DTO Schemas
Provides data transfer objects for stream operations, session lifecycle, and sanitized status.
Strict Security Rule: No passwords, tokens, or raw credential-bearing URLs are ever exposed.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.camera import SourceType, ConnectivityType, CameraStatus, CameraType
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum, CameraFootageItem


class StreamConnectRequest(BaseModel):
    """Optional payload when connecting to a stream."""
    preferred_playback_mode: Optional[PlaybackModeEnum] = None
    force_reconnect: bool = False


class StreamSessionResponse(BaseModel):
    """Sanitized session information returned upon connection."""
    session_id: str
    camera_id: int
    camera_code: str
    camera_name: str
    department: str
    source_type: SourceType
    connectivity_type: ConnectivityType
    playback_mode: PlaybackModeEnum
    status: StreamStatusEnum
    started_at: datetime
    is_live_active: bool
    relay_stream_url: Optional[str] = None
    message: str
    error: Optional[str] = None


class StreamStatusResponse(BaseModel):
    """Sanitized stream status response (Requirement 16)."""
    camera_id: int
    camera_code: str
    status: StreamStatusEnum
    connectivity_type: ConnectivityType
    source_type: SourceType
    playback_mode: PlaybackModeEnum
    started_at: Optional[datetime] = None
    is_live_active: bool = False
    relay_stream_url: Optional[str] = None
    media_relay_status: str
    error: Optional[str] = None


class StreamHealthResponse(BaseModel):
    """Health check evaluation for an authorized stream source."""
    camera_id: int
    status: StreamStatusEnum
    latency_ms: Optional[float] = None
    last_checked: datetime
    message: str


class StreamInfoResponse(BaseModel):
    """Comprehensive stream and source capability info."""
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
    
    # Determined playback capabilities
    playback_mode: PlaybackModeEnum
    stream_status: StreamStatusEnum
    is_playable_in_browser: bool
    status_message: str
    media_relay_available: bool = False
    media_relay_details: str
    
    # Safe stream endpoint (sanitized / relative proxy URL)
    relay_stream_url: Optional[str] = None
    
    # Available recorded footage count
    footage_count: int = 0
    available_footage: List[CameraFootageItem] = []
    
    # Active Watchlist alert context
    active_alerts_count: int = 0
    latest_alert_message: Optional[str] = None


class ActiveSessionItem(BaseModel):
    """Active stream session item for platform diagnostics."""
    session_id: str
    camera_id: int
    camera_code: str
    connectivity_type: ConnectivityType
    status: StreamStatusEnum
    started_at: datetime
    last_active: datetime
    frame_count: int
    fps: float
    client_count: int
    error_message: Optional[str] = None


class StreamStatsResponse(BaseModel):
    """Aggregate statistics for all registered camera stream sources."""
    total_cameras: int = 0
    live_cameras: int = 0
    recorded_sources: int = 0
    connected_live_streams: int = 0
    disconnected_live_streams: int = 0
    unconfigured_live_streams: int = 0
    active_stream_sessions: int = 0
    media_relay_ready: bool = False
    media_relay_info: str
