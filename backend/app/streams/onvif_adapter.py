"""
ONVIF Camera Stream Adapter Architecture Placeholder
Designed to integrate authorized ONVIF Profile S/T compliant IP cameras without network scanning or unauthorized probing.
"""

from typing import Tuple, Optional, Dict, Any
from app.models.camera import Camera
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum
from app.streams.base import StreamAdapter
from app.streams.models import StreamSession, StreamHealthStatus


class ONVIFAdapter(StreamAdapter):
    """
    Architecture placeholder for authorized ONVIF Profile S/T devices.
    Strict Compliance: Zero network scanning or automatic device discovery.
    """

    def __init__(self, camera: Camera):
        super().__init__(camera)
        self.endpoint = camera.stream_url

    def validate_source(self) -> Tuple[bool, Optional[str]]:
        """Validates ONVIF device endpoint."""
        return (
            False,
            "ONVIF integration requires authorized device credentials and network endpoint configuration.",
        )

    def connect(self, session: StreamSession) -> StreamSession:
        """Attempts connection to ONVIF device service."""
        session.status = StreamStatusEnum.NOT_CONFIGURED
        session.error_message = "ONVIF integration requires authorized device credentials and network endpoint configuration."
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
            "connectivity_type": "ONVIF",
            "playback_mode": PlaybackModeEnum.UNAVAILABLE.value,
            "stream_status": StreamStatusEnum.NOT_CONFIGURED.value,
            "is_configured": False,
            "is_playable_in_browser": False,
            "relay_stream_url": None,
            "media_relay_status": "ONVIF Profile S/T Standby",
            "status_message": "ONVIF integration requires authorized device credentials and network endpoint configuration.",
        }
