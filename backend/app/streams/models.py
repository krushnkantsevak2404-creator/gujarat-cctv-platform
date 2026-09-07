"""
Stream Internal Models & Session State
Defines data structures representing active stream sessions, capture threads, and health states.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import threading
from app.models.camera import SourceType, ConnectivityType
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum


@dataclass
class StreamHealthStatus:
    """Represents a periodic stream health check evaluation."""
    status: StreamStatusEnum
    latency_ms: Optional[float] = None
    last_checked: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    error: Optional[str] = None


@dataclass
class StreamSession:
    """
    Represents an active server-side stream session.
    Maintains adapter instance, frame buffers, thread locks, and client subscriptions.
    """
    session_id: str
    camera_id: int
    camera_code: str
    source_type: SourceType
    connectivity_type: ConnectivityType
    playback_mode: PlaybackModeEnum
    status: StreamStatusEnum = StreamStatusEnum.CONNECTING
    
    # Timing & Metrics
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    frame_count: int = 0
    fps: float = 0.0
    error_message: Optional[str] = None
    
    # Internal runtime state (not exposed in API)
    client_count: int = 0
    is_active: bool = True
    stop_event: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    latest_frame_jpeg: Optional[bytes] = None
    capture_object: Any = None
    worker_thread: Any = None

    def update_frame(self, jpeg_bytes: bytes):
        """Thread-safe update of latest video frame buffer."""
        with self.lock:
            self.latest_frame_jpeg = jpeg_bytes
            self.frame_count += 1
            self.last_active = datetime.utcnow()

    def get_latest_frame(self) -> Optional[bytes]:
        """Thread-safe retrieval of latest video frame buffer."""
        with self.lock:
            return self.latest_frame_jpeg

    def to_summary_dict(self) -> dict:
        """Returns safe serializable summary of the active session (zero secrets)."""
        return {
            "session_id": self.session_id,
            "camera_id": self.camera_id,
            "camera_code": self.camera_code,
            "source_type": self.source_type.value,
            "connectivity_type": self.connectivity_type.value,
            "playback_mode": self.playback_mode.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "frame_count": self.frame_count,
            "fps": round(self.fps, 2),
            "client_count": self.client_count,
            "error_message": self.error_message,
        }
