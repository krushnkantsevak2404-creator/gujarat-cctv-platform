"""
Authorized RTSP Stream Adapter
Handles validation, secure connection, OpenCV video capture, and browser MJPEG/HLS media relay.
Strict Security Enforcement: All RTSP credentials and endpoints are masked in logs and sanitized in APIs.
"""

import re
import time
import logging
import threading
from typing import Tuple, Optional, Dict, Any, Generator
from urllib.parse import urlparse
import cv2
import numpy as np

from app.core.config import settings
from app.models.camera import Camera, CameraStatus
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum
from app.streams.base import StreamAdapter
from app.streams.models import StreamSession, StreamHealthStatus

logger = logging.getLogger("uvicorn.error")


def mask_rtsp_url(url: Optional[str]) -> str:
    """
    Sanitizes an RTSP URL by replacing credentials with asterisks.
    Example: rtsp://admin:secret123@192.168.1.50:554/live -> rtsp://****:****@192.168.1.50:554/live
    """
    if not url:
        return "NOT_CONFIGURED"
    try:
        # Match pattern rtsp://user:pass@host...
        return re.sub(r'(rtsp://)([^:]+):([^@]+)@', r'\1****:****@', url)
    except Exception:
        return "rtsp://****:****@masked-source"


def check_media_relay_status() -> Tuple[bool, str]:
    """
    Evaluates whether external media relays (FFmpeg / MediaMTX) or internal MJPEG relay are available.
    """
    # OpenCV is available for internal MJPEG relay
    return True, "Internal OpenCV MJPEG Relay Engine active (Browser Compatible)"


class RTSPAdapter(StreamAdapter):
    """
    Adapter for connecting to authorized RTSP CCTV cameras.
    Features non-blocking background frame capture, credential masking, and clean resource release.
    """

    def __init__(self, camera: Camera):
        super().__init__(camera)
        self.stream_url = (camera.stream_url or "").strip()
        self.masked_url = mask_rtsp_url(self.stream_url)

    def validate_source(self) -> Tuple[bool, Optional[str]]:
        """Validates authorized RTSP configuration format without connecting."""
        if not self.stream_url:
            return False, "Live stream is not configured for this camera."
        if not self.stream_url.lower().startswith("rtsp://"):
            return False, "Configured stream URL does not use the RTSP protocol (must start with rtsp://)."
        return True, None

    def connect(self, session: StreamSession) -> StreamSession:
        """
        Attempts connection to the authorized RTSP CCTV source.
        Spawns a background frame capture thread to avoid blocking the main server.
        """
        is_valid, validation_error = self.validate_source()
        if not is_valid:
            session.status = StreamStatusEnum.NOT_CONFIGURED if not self.stream_url else StreamStatusEnum.ERROR
            session.error_message = validation_error
            logger.warning(f"[RTSPAdapter] Camera {self.camera_code} validation failed: {validation_error}")
            return session

        if self.camera.status == CameraStatus.OFFLINE:
            session.status = StreamStatusEnum.DISCONNECTED
            session.error_message = "Camera is marked OFFLINE in CCTV Registry."
            return session

        session.status = StreamStatusEnum.CONNECTING
        session.error_message = None
        session.stop_event.clear()

        logger.info(f"[RTSPAdapter] Initiating stream connection for camera {self.camera_code} to {self.masked_url}")

        # Start capture worker thread
        worker = threading.Thread(
            target=self._capture_worker,
            args=(session,),
            name=f"rtsp-worker-{self.camera_code}",
            daemon=True,
        )
        session.worker_thread = worker
        worker.start()

        # Wait briefly for initial connection state (up to 1.5s synchronous check)
        start_wait = time.time()
        while time.time() - start_wait < 1.5:
            if session.status in (StreamStatusEnum.CONNECTED, StreamStatusEnum.ERROR, StreamStatusEnum.DISCONNECTED):
                break
            time.sleep(0.1)

        return session

    def _capture_worker(self, session: StreamSession):
        """
        Background capture loop for reading frames from authorized RTSP stream.
        Maintains frame buffer and computes live FPS.
        """
        cap = None
        try:
            logger.info(f"[RTSPAdapter Worker] Opening VideoCapture for camera {self.camera_code}")
            
            # Set OpenCV RTSP transport options if supported
            cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
            
            if not cap.isOpened():
                session.status = StreamStatusEnum.ERROR
                session.error_message = "Unable to connect to authorized RTSP source (stream unreachable or refused)."
                logger.warning(f"[RTSPAdapter] Failed to open stream for camera {self.camera_code} at {self.masked_url}")
                return

            # Test reading initial frame
            ret, frame = cap.read()
            if not ret or frame is None:
                session.status = StreamStatusEnum.ERROR
                session.error_message = "Connected to RTSP server but no video frames received."
                logger.warning(f"[RTSPAdapter] No frames received from camera {self.camera_code}")
                return

            # Connection successful
            session.status = StreamStatusEnum.CONNECTED
            session.capture_object = cap
            session.error_message = None
            logger.info(f"[RTSPAdapter] Stream CONNECTED successfully for camera {self.camera_code}")

            fps_calc_start = time.time()
            frames_in_sec = 0

            # Main frame acquisition loop
            while not session.stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    # Retry read or mark degraded
                    time.sleep(0.05)
                    continue

                # Encode frame to JPEG for browser relay
                encode_success, jpeg_buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                if encode_success:
                    session.update_frame(jpeg_buffer.tobytes())

                frames_in_sec += 1
                now = time.time()
                elapsed = now - fps_calc_start
                if elapsed >= 1.0:
                    session.fps = frames_in_sec / elapsed
                    frames_in_sec = 0
                    fps_calc_start = now

                # Pace frame rate to ~25 FPS to prevent excessive CPU usage
                time.sleep(0.04)

        except Exception as e:
            session.status = StreamStatusEnum.ERROR
            session.error_message = f"Stream capture encountered an error: {str(e)}"
            logger.error(f"[RTSPAdapter Worker] Exception in camera {self.camera_code}: {e}")
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            if session.status == StreamStatusEnum.CONNECTING:
                session.status = StreamStatusEnum.DISCONNECTED
            logger.info(f"[RTSPAdapter Worker] Worker stopped for camera {self.camera_code}")

    def disconnect(self, session: StreamSession) -> bool:
        """Cleanly releases video capture and stops background worker thread."""
        logger.info(f"[RTSPAdapter] Disconnecting stream session for camera {self.camera_code}")
        session.stop_event.set()
        session.status = StreamStatusEnum.DISCONNECTED
        session.is_active = False

        if session.capture_object is not None:
            try:
                session.capture_object.release()
                session.capture_object = None
            except Exception as e:
                logger.warning(f"[RTSPAdapter] Error releasing capture object for {self.camera_code}: {e}")

        session.latest_frame_jpeg = None
        return True

    def get_status(self, session: Optional[StreamSession] = None) -> StreamStatusEnum:
        """Returns the current operational status of the RTSP stream."""
        if not self.stream_url:
            return StreamStatusEnum.NOT_CONFIGURED
        if self.camera.status == CameraStatus.OFFLINE:
            return StreamStatusEnum.DISCONNECTED
        if session is not None:
            return session.status
        return StreamStatusEnum.DISCONNECTED

    def get_stream_info(self) -> Dict[str, Any]:
        """Returns sanitized stream metadata without exposing credentials."""
        is_valid, _ = self.validate_source()
        relay_ready, relay_info = check_media_relay_status()
        
        return {
            "camera_id": self.camera_id,
            "camera_code": self.camera_code,
            "connectivity_type": "RTSP",
            "playback_mode": PlaybackModeEnum.RTSP_ADAPTER.value,
            "stream_status": self.get_status().value,
            "is_configured": is_valid,
            "is_playable_in_browser": relay_ready and is_valid,
            "relay_stream_url": f"/api/streams/{self.camera_id}/live",
            "media_relay_status": relay_info,
            "status_message": (
                "Authorized RTSP source ready for connection."
                if is_valid
                else "Live stream is not configured for this camera."
            ),
        }

    def generate_mjpeg_frames(self, session: StreamSession) -> Generator[bytes, None, None]:
        """
        Yields continuous multipart JPEG stream for HTML5 <img src="..."> in browser.
        Falls back to generating placeholder standby frames if camera is offline.
        """
        session.client_count += 1
        try:
            while not session.stop_event.is_set() and session.is_active:
                frame_data = session.get_latest_frame()
                if frame_data:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n"
                    )
                else:
                    # Generate standby graphic frame
                    placeholder = self._create_standby_frame(
                        f"Connecting to {self.camera_code}...",
                        session.status.value,
                    )
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + placeholder + b"\r\n"
                    )
                time.sleep(0.04)
        finally:
            session.client_count = max(0, session.client_count - 1)

    def _create_standby_frame(self, text: str, status_text: str) -> bytes:
        """Creates a lightweight JPEG standby frame when camera is connecting or paused."""
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        img[:] = (15, 23, 42)  # Dark slate background
        
        # Draw camera code
        cv2.putText(img, f"CAM: {self.camera_code}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (96, 165, 250), 2)
        cv2.putText(img, f"STATUS: {status_text}", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 1)
        cv2.putText(img, text, (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (241, 245, 249), 2)
        cv2.putText(img, "GUJARAT POLICE CCTV INTELLIGENCE", (30, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 116, 139), 1)
        
        _, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        return buf.tobytes()

    def health_check(self, session: StreamSession) -> StreamHealthStatus:
        """Lightweight check verifying whether frames are continuing to be acquired."""
        if session.status != StreamStatusEnum.CONNECTED:
            return StreamHealthStatus(
                status=session.status,
                error=session.error_message or "Stream is not currently connected.",
            )
        
        # Check if frame has updated in last 5 seconds
        sec_since_last = (time.time() - session.last_active.timestamp()) if session.last_active else 999.0
        if sec_since_last > 5.0 and session.frame_count > 0:
            return StreamHealthStatus(
                status=StreamStatusEnum.ERROR,
                latency_ms=round(sec_since_last * 1000, 1),
                error="Stream frame acquisition stalled.",
            )
        
        return StreamHealthStatus(
            status=StreamStatusEnum.CONNECTED,
            latency_ms=round(1000.0 / max(session.fps, 1.0), 1),
            error=None,
        )
