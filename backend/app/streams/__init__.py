"""
Stream Module Package
Provides modular stream adapters (RTSP, Recorded, VMS, ONVIF, SDK) and central StreamManager.
"""

from app.streams.models import StreamSession, StreamHealthStatus
from app.streams.schemas import (
    StreamConnectRequest,
    StreamSessionResponse,
    StreamStatusResponse,
    StreamInfoResponse,
    StreamStatsResponse,
    ActiveSessionItem,
    StreamHealthResponse,
)
from app.streams.base import StreamAdapter
from app.streams.rtsp_adapter import RTSPAdapter, mask_rtsp_url, check_media_relay_status
from app.streams.recorded_adapter import RecordedFootageAdapter
from app.streams.vms_adapter import VMSAdapter
from app.streams.onvif_adapter import ONVIFAdapter
from app.streams.sdk_adapter import SDKAdapter
from app.streams.manager import StreamManager, stream_manager

__all__ = [
    "StreamSession",
    "StreamHealthStatus",
    "StreamConnectRequest",
    "StreamSessionResponse",
    "StreamStatusResponse",
    "StreamInfoResponse",
    "StreamStatsResponse",
    "ActiveSessionItem",
    "StreamHealthResponse",
    "StreamAdapter",
    "RTSPAdapter",
    "RecordedFootageAdapter",
    "VMSAdapter",
    "ONVIFAdapter",
    "SDKAdapter",
    "StreamManager",
    "stream_manager",
    "mask_rtsp_url",
    "check_media_relay_status",
]
