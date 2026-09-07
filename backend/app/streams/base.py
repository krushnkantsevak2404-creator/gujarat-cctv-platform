"""
Stream Adapter Base Interface
Defines the standard contract for all source connectivity adapters (RTSP, Recorded, VMS, ONVIF, SDK).
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any, Generator
from app.models.camera import Camera
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum
from app.streams.models import StreamSession, StreamHealthStatus


class StreamAdapter(ABC):
    """
    Abstract base adapter defining connection lifecycle and stream metadata retrieval.
    Each protocol/source type implements this contract cleanly without leaking protocol-specific
    secrets or internal connection endpoints to caller layers.
    """

    def __init__(self, camera: Camera):
        self.camera = camera
        self.camera_id = camera.id
        self.camera_code = camera.camera_code

    @abstractmethod
    def validate_source(self) -> Tuple[bool, Optional[str]]:
        """
        Validates source configuration and credentials syntax without initiating connection.
        Returns (is_valid, error_reason).
        """
        pass

    @abstractmethod
    def connect(self, session: StreamSession) -> StreamSession:
        """
        Attempts connection to the authorized CCTV source.
        Updates session status and begins media acquisition if reachable.
        """
        pass

    @abstractmethod
    def disconnect(self, session: StreamSession) -> bool:
        """
        Cleanly closes connections and terminates capture threads/processes.
        Guarantees zero orphaned media resources.
        """
        pass

    @abstractmethod
    def get_status(self, session: Optional[StreamSession] = None) -> StreamStatusEnum:
        """
        Determines current connection/operational status.
        """
        pass

    @abstractmethod
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Returns sanitized stream metadata, supported playback mode, and relay endpoints.
        """
        pass

    def generate_mjpeg_frames(self, session: StreamSession) -> Generator[bytes, None, None]:
        """
        Generates multipart JPEG frames for browser-compatible HTTP video streaming.
        Default implementation yields empty or placeholder frames if unsupported.
        """
        yield b""

    def health_check(self, session: StreamSession) -> StreamHealthStatus:
        """
        Lightweight health verification for an active stream session.
        """
        return StreamHealthStatus(status=self.get_status(session))
