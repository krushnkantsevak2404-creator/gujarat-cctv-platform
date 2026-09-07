"""
Vendor SDK Stream Adapter Architecture Placeholder
Designed to integrate proprietary hardware manufacturer SDKs (e.g. Hikvision, Dahua, Axis, CP Plus Native SDK)
when direct RTSP transport is replaced by manufacturer binary libraries.
"""

from typing import Tuple, Optional, Dict, Any
from app.models.camera import Camera
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum
from app.streams.base import StreamAdapter
from app.streams.models import StreamSession, StreamHealthStatus


class SDKAdapter(StreamAdapter):
    """
    Architecture placeholder for vendor proprietary SDK camera integrations.
    """

    def __init__(self, camera: Camera):
        super().__init__(camera)
        self.sdk_source = camera.stream_url

    def validate_source(self) -> Tuple[bool, Optional[str]]:
        return (
            False,
            "Vendor SDK integration requires proprietary driver library and authorized device registration.",
        )

    def connect(self, session: StreamSession) -> StreamSession:
        session.status = StreamStatusEnum.NOT_CONFIGURED
        session.error_message = "Vendor SDK integration requires proprietary driver library."
        return session

    def disconnect(self, session: StreamSession) -> bool:
        session.status = StreamStatusEnum.DISCONNECTED
        session.is_active = False
        return True

    def get_status(self, session: Optional[StreamSession] = None) -> StreamStatusEnum:
        return StreamStatusEnum.NOT_CONFIGURED

    def get_stream_info(self) -> Dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "camera_code": self.camera_code,
            "connectivity_type": "SDK",
            "playback_mode": PlaybackModeEnum.UNAVAILABLE.value,
            "stream_status": StreamStatusEnum.NOT_CONFIGURED.value,
            "is_configured": False,
            "is_playable_in_browser": False,
            "relay_stream_url": None,
            "media_relay_status": "Vendor SDK Standby",
            "status_message": "Vendor SDK integration requires proprietary driver library.",
        }
