"""
Stream Manager Module
Central coordinator managing stream session lifecycles, adapter resolution, session deduplication,
health checks, and resource cleanup across the Gujarat CCTV platform.
"""

import uuid
import time
import logging
import threading
from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.models.camera import Camera, SourceType, ConnectivityType, CameraStatus
from app.models.footage import CameraFootage
from app.models.alert import VehicleAlert, AlertStatus
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum, CameraFootageItem
from app.streams.base import StreamAdapter
from app.streams.models import StreamSession, StreamHealthStatus
from app.streams.schemas import (
    StreamSessionResponse,
    StreamStatusResponse,
    StreamInfoResponse,
    StreamStatsResponse,
    ActiveSessionItem,
)
from app.streams.rtsp_adapter import RTSPAdapter, check_media_relay_status
from app.streams.recorded_adapter import RecordedFootageAdapter
from app.streams.vms_adapter import VMSAdapter
from app.streams.onvif_adapter import ONVIFAdapter
from app.streams.sdk_adapter import SDKAdapter
from app.services import yolo_service

logger = logging.getLogger("uvicorn.error")


class StreamManager:
    """
    Singleton Manager for CCTV Stream Sessions.
    Guarantees thread-safe session tracking, resource deallocation, and adapter factory routing.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StreamManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._sessions: Dict[int, StreamSession] = {}
        self._adapters: Dict[int, StreamAdapter] = {}
        self._manager_lock = threading.Lock()
        self._initialized = True
        logger.info("[StreamManager] Initialized Stream Manager instance.")

    def get_adapter(self, camera: Camera, db: Optional[Session] = None) -> StreamAdapter:
        """Factory method resolving the appropriate adapter for a given camera."""
        conn = camera.connectivity_type
        src = camera.source_type

        if conn == ConnectivityType.FILE or src == SourceType.RECORDED_FOOTAGE:
            return RecordedFootageAdapter(camera, db=db)
        elif conn == ConnectivityType.VMS_API:
            return VMSAdapter(camera)
        elif conn == ConnectivityType.ONVIF:
            return ONVIFAdapter(camera)
        elif conn == ConnectivityType.SDK:
            return SDKAdapter(camera)
        elif conn == ConnectivityType.RTSP or src == SourceType.LIVE_CAMERA:
            return RTSPAdapter(camera)
        else:
            return RTSPAdapter(camera)

    def connect_stream(
        self,
        camera: Camera,
        db: Session,
        force_reconnect: bool = False,
    ) -> StreamSessionResponse:
        """
        Connects to an authorized CCTV source.
        Reuses existing active session if available to avoid unnecessary duplicate processes.
        """
        with self._manager_lock:
            existing_session = self._sessions.get(camera.id)
            if existing_session and existing_session.is_active and not force_reconnect:
                logger.info(f"[StreamManager] Reusing active session for camera {camera.camera_code} ({existing_session.session_id})")
                return self._build_session_response(camera, existing_session, "Reconnected to existing active stream session.")

            # If force reconnect or existing session was inactive, clean it up first
            if existing_session:
                adapter = self._adapters.get(camera.id)
                if adapter:
                    try:
                        adapter.disconnect(existing_session)
                    except Exception as e:
                        logger.warning(f"[StreamManager] Error cleaning previous session for {camera.camera_code}: {e}")

            # Resolve appropriate adapter
            adapter = self.get_adapter(camera, db=db)
            self._adapters[camera.id] = adapter

            # Determine playback mode
            playback_mode = PlaybackModeEnum.RECORDED_STREAM if camera.source_type == SourceType.RECORDED_FOOTAGE else PlaybackModeEnum.RTSP_ADAPTER

            # Create new session
            session = StreamSession(
                session_id=f"sess-{camera.id}-{uuid.uuid4().hex[:8]}",
                camera_id=camera.id,
                camera_code=camera.camera_code,
                source_type=camera.source_type,
                connectivity_type=camera.connectivity_type,
                playback_mode=playback_mode,
                status=StreamStatusEnum.CONNECTING,
            )

            # Store in session registry
            self._sessions[camera.id] = session

            # Connect via adapter
            session = adapter.connect(session)

            msg = "Connected to authorized stream." if session.status == StreamStatusEnum.CONNECTED else (session.error_message or "Connecting to stream...")
            return self._build_session_response(camera, session, msg)

    def disconnect_stream(self, camera_id: int, camera_code: Optional[str] = None) -> StreamStatusResponse:
        """Disconnects an active stream session and releases all associated resources."""
        with self._manager_lock:
            session = self._sessions.get(camera_id)
            adapter = self._adapters.get(camera_id)

            if adapter and session:
                try:
                    adapter.disconnect(session)
                except Exception as e:
                    logger.warning(f"[StreamManager] Error disconnecting camera {camera_id}: {e}")

            if session:
                session.status = StreamStatusEnum.DISCONNECTED
                session.is_active = False

            _, relay_info = check_media_relay_status()
            return StreamStatusResponse(
                camera_id=camera_id,
                camera_code=camera_code or (session.camera_code if session else f"CAM-{camera_id}"),
                status=StreamStatusEnum.DISCONNECTED,
                connectivity_type=session.connectivity_type if session else ConnectivityType.UNKNOWN,
                source_type=session.source_type if session else SourceType.LIVE_CAMERA,
                playback_mode=session.playback_mode if session else PlaybackModeEnum.UNAVAILABLE,
                started_at=session.started_at if session else None,
                is_live_active=False,
                relay_stream_url=None,
                media_relay_status=relay_info,
                error=None,
            )

    def get_stream_status(self, camera: Camera, db: Optional[Session] = None) -> StreamStatusResponse:
        """Returns the current operational status for a camera without initiating connection."""
        with self._manager_lock:
            session = self._sessions.get(camera.id)
            adapter = self._adapters.get(camera.id) or self.get_adapter(camera, db=db)
            status = adapter.get_status(session)
            
            _, relay_info = check_media_relay_status()
            is_live_active = bool(session and session.is_active and session.status == StreamStatusEnum.CONNECTED)
            
            return StreamStatusResponse(
                camera_id=camera.id,
                camera_code=camera.camera_code,
                status=status,
                connectivity_type=camera.connectivity_type,
                source_type=camera.source_type,
                playback_mode=session.playback_mode if session else (
                    PlaybackModeEnum.RECORDED_STREAM if camera.source_type == SourceType.RECORDED_FOOTAGE else PlaybackModeEnum.RTSP_ADAPTER
                ),
                started_at=session.started_at if session else None,
                is_live_active=is_live_active,
                relay_stream_url=f"/api/streams/{camera.id}/live" if is_live_active else None,
                media_relay_status=relay_info,
                error=session.error_message if session else None,
            )

    def get_stream_info(self, camera: Camera, db: Session) -> StreamInfoResponse:
        """Returns comprehensive stream and playback capability metadata."""
        adapter = self.get_adapter(camera, db=db)
        info_dict = adapter.get_stream_info()
        session = self._sessions.get(camera.id)

        # Coordinate check
        has_coords = (
            camera.latitude is not None
            and camera.longitude is not None
            and (camera.latitude != 0.0 or camera.longitude != 0.0)
        )

        # Query footage items
        footage_records = (
            db.query(CameraFootage)
            .filter(CameraFootage.camera_id == camera.id)
            .order_by(desc(CameraFootage.created_at))
            .all()
        )
        available_footage = []
        for ft in footage_records:
            dur = ft.duration_seconds or 0.0
            available_footage.append(
                CameraFootageItem(
                    id=ft.id,
                    file_name=ft.file_name,
                    original_file_name=ft.original_file_name or ft.file_name,
                    duration_seconds=ft.duration_seconds,
                    formatted_duration=yolo_service.format_timestamp(dur) if dur > 0 else "00:00.0",
                    file_size_bytes=ft.file_size or 0,
                    recording_start_time=ft.recording_start_time,
                    recording_end_time=ft.recording_end_time,
                    stream_url=f"/api/footage/{ft.id}/stream",
                    created_at=ft.created_at,
                )
            )

        # Check active alerts
        active_alerts = (
            db.query(VehicleAlert)
            .filter(
                VehicleAlert.camera_id == camera.id,
                VehicleAlert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]),
            )
            .order_by(desc(VehicleAlert.created_at))
            .all()
        )

        relay_ready, relay_info = check_media_relay_status()
        current_status = adapter.get_status(session)

        return StreamInfoResponse(
            camera_id=camera.id,
            camera_code=camera.camera_code,
            camera_name=camera.camera_name,
            department=camera.department,
            location_name=camera.location_name,
            latitude=camera.latitude if has_coords else None,
            longitude=camera.longitude if has_coords else None,
            has_valid_coordinates=has_coords,
            camera_type=camera.camera_type,
            source_type=camera.source_type,
            connectivity_type=camera.connectivity_type,
            camera_status=camera.status,
            playback_mode=PlaybackModeEnum(info_dict.get("playback_mode", PlaybackModeEnum.UNAVAILABLE.value)),
            stream_status=current_status,
            is_playable_in_browser=info_dict.get("is_playable_in_browser", False),
            status_message=info_dict.get("status_message", "Source configured."),
            media_relay_available=relay_ready,
            media_relay_details=relay_info,
            relay_stream_url=f"/api/streams/{camera.id}/live" if session and session.status == StreamStatusEnum.CONNECTED else (
                f"/api/footage/{available_footage[0].id}/stream" if available_footage else None
            ),
            footage_count=len(available_footage),
            available_footage=available_footage,
            active_alerts_count=len(active_alerts),
            latest_alert_message=active_alerts[0].message if active_alerts else None,
        )

    def get_stream_feed(self, camera_id: int):
        """Yields continuous multipart JPEG stream for an active camera session."""
        session = self._sessions.get(camera_id)
        adapter = self._adapters.get(camera_id)
        if not session or not adapter:
            # Generate empty or disconnected frame generator
            adapter = RTSPAdapter(Camera(id=camera_id, camera_code=f"CAM-{camera_id}", status=CameraStatus.OFFLINE))
            dummy_session = StreamSession(
                session_id=f"dummy-{camera_id}",
                camera_id=camera_id,
                camera_code=f"CAM-{camera_id}",
                source_type=SourceType.LIVE_CAMERA,
                connectivity_type=ConnectivityType.RTSP,
                playback_mode=PlaybackModeEnum.RTSP_ADAPTER,
                status=StreamStatusEnum.DISCONNECTED,
            )
            return adapter.generate_mjpeg_frames(dummy_session)
        return adapter.generate_mjpeg_frames(session)

    def get_active_sessions(self) -> List[ActiveSessionItem]:
        """Returns list of currently active stream sessions."""
        items = []
        with self._manager_lock:
            for cam_id, sess in self._sessions.items():
                if sess.is_active:
                    items.append(
                        ActiveSessionItem(
                            session_id=sess.session_id,
                            camera_id=sess.camera_id,
                            camera_code=sess.camera_code,
                            connectivity_type=sess.connectivity_type,
                            status=sess.status,
                            started_at=sess.started_at,
                            last_active=sess.last_active,
                            frame_count=sess.frame_count,
                            fps=sess.fps,
                            client_count=sess.client_count,
                            error_message=sess.error_message,
                        )
                    )
        return items

    def get_stats(self, db: Session) -> StreamStatsResponse:
        """Returns aggregate stream statistics across registered cameras and active sessions."""
        all_cameras = db.query(Camera).all()
        total_cams = len(all_cameras)
        live_cams = sum(1 for c in all_cameras if c.source_type == SourceType.LIVE_CAMERA)
        recorded_sources = sum(1 for c in all_cameras if c.source_type == SourceType.RECORDED_FOOTAGE)

        connected_live = 0
        disconnected_live = 0
        unconfigured_live = 0

        with self._manager_lock:
            active_sessions_count = sum(1 for s in self._sessions.values() if s.is_active and s.status == StreamStatusEnum.CONNECTED)
            for c in all_cameras:
                if c.source_type == SourceType.LIVE_CAMERA:
                    if not c.stream_url or not c.stream_url.strip():
                        unconfigured_live += 1
                    else:
                        sess = self._sessions.get(c.id)
                        if sess and sess.status == StreamStatusEnum.CONNECTED:
                            connected_live += 1
                        else:
                            disconnected_live += 1

        relay_ready, relay_info = check_media_relay_status()
        return StreamStatsResponse(
            total_cameras=total_cams,
            live_cameras=live_cams,
            recorded_sources=recorded_sources,
            connected_live_streams=connected_live,
            disconnected_live_streams=disconnected_live,
            unconfigured_live_streams=unconfigured_live,
            active_stream_sessions=active_sessions_count,
            media_relay_ready=relay_ready,
            media_relay_info=relay_info,
        )

    def shutdown_all(self):
        """Gracefully disconnects all stream sessions on application shutdown."""
        logger.info("[StreamManager] Commencing graceful shutdown of all stream sessions...")
        with self._manager_lock:
            for cam_id, session in list(self._sessions.items()):
                adapter = self._adapters.get(cam_id)
                if adapter and session:
                    try:
                        adapter.disconnect(session)
                    except Exception as e:
                        logger.warning(f"[StreamManager] Error shutting down session {cam_id}: {e}")
            self._sessions.clear()
            self._adapters.clear()
        logger.info("[StreamManager] All stream sessions terminated cleanly.")

    def _build_session_response(self, camera: Camera, session: StreamSession, message: str) -> StreamSessionResponse:
        is_live = bool(session.is_active and session.status == StreamStatusEnum.CONNECTED)
        return StreamSessionResponse(
            session_id=session.session_id,
            camera_id=camera.id,
            camera_code=camera.camera_code,
            camera_name=camera.camera_name,
            department=camera.department,
            source_type=camera.source_type,
            connectivity_type=camera.connectivity_type,
            playback_mode=session.playback_mode,
            status=session.status,
            started_at=session.started_at,
            is_live_active=is_live,
            relay_stream_url=f"/api/streams/{camera.id}/live" if is_live else None,
            message=message,
            error=session.error_message,
        )


# Global singleton instance
stream_manager = StreamManager()
