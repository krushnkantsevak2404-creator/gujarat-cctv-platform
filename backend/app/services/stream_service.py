"""
Stream & Unified Viewer Service
Provides stream capability inspection, playback mode determination,
available footage aggregation, and platform-wide viewer metrics.
"""

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.camera import Camera, SourceType, ConnectivityType, CameraStatus, CameraType
from app.models.footage import CameraFootage, FootageStatus
from app.models.alert import VehicleAlert, AlertStatus
from app.schemas.stream import (
    StreamStatusEnum,
    PlaybackModeEnum,
    CameraFootageItem,
    CameraStreamInfoResponse,
    ViewerStatsResponse,
)
from app.services import yolo_service

logger = logging.getLogger("uvicorn.error")


def get_camera_stream_info(db: Session, camera: Camera) -> CameraStreamInfoResponse:
    """
    Evaluates camera source type, available recorded footage, and stream capabilities.
    Determines genuine browser playback mode and stream status without guessing or faking.
    """
    # 1. Inspect recorded footage records for this camera
    footage_records = (
        db.query(CameraFootage)
        .filter(CameraFootage.camera_id == camera.id)
        .order_by(desc(CameraFootage.created_at))
        .all()
    )

    available_footage: List[CameraFootageItem] = []
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

    # 2. Check active Watchlist alerts for this camera
    active_alerts = (
        db.query(VehicleAlert)
        .filter(
            VehicleAlert.camera_id == camera.id,
            VehicleAlert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]),
        )
        .order_by(desc(VehicleAlert.created_at))
        .all()
    )
    active_alerts_count = len(active_alerts)
    latest_alert_message = active_alerts[0].message if active_alerts else None
    latest_alert_severity = active_alerts[0].severity.value if active_alerts else None

    # 3. Coordinate validation
    has_valid_coords = (
        camera.latitude is not None
        and camera.longitude is not None
        and (camera.latitude != 0.0 or camera.longitude != 0.0)
    )

    # 4. Determine Playback Mode & Stream Status
    playback_mode = PlaybackModeEnum.UNAVAILABLE
    stream_status = StreamStatusEnum.NOT_CONFIGURED
    is_playable = False
    status_message = "Source not configured."
    stream_url = camera.stream_url

    if camera.status == CameraStatus.OFFLINE:
        playback_mode = PlaybackModeEnum.UNAVAILABLE
        stream_status = StreamStatusEnum.DISCONNECTED
        is_playable = False
        status_message = "Camera is currently OFFLINE in CCTV Registry."
    elif camera.source_type == SourceType.RECORDED_FOOTAGE:
        if available_footage:
            playback_mode = PlaybackModeEnum.RECORDED_STREAM
            stream_status = StreamStatusEnum.CONNECTED
            is_playable = True
            status_message = f"{len(available_footage)} recorded footage file(s) available."
        else:
            playback_mode = PlaybackModeEnum.UNAVAILABLE
            stream_status = StreamStatusEnum.NOT_CONFIGURED
            is_playable = False
            status_message = "No recorded footage available for this camera."
    elif camera.source_type == SourceType.LIVE_CAMERA:
        if not stream_url or not stream_url.strip():
            playback_mode = PlaybackModeEnum.UNAVAILABLE
            stream_status = StreamStatusEnum.NOT_CONFIGURED
            is_playable = False
            status_message = "Live stream is not configured for this camera."
        else:
            clean_url = stream_url.strip().lower()
            if clean_url.startswith("rtsp://"):
                # RTSP stream: browsers cannot natively play RTSP without relay
                playback_mode = PlaybackModeEnum.RTSP_ADAPTER
                stream_status = StreamStatusEnum.CONNECTING
                is_playable = False
                status_message = "RTSP source configured. Media relay required for browser playback."
            elif clean_url.endswith(".m3u8"):
                playback_mode = PlaybackModeEnum.HLS_RELAY
                stream_status = StreamStatusEnum.CONNECTED
                is_playable = True
                status_message = "Authorized HLS live stream ready."
            elif clean_url.endswith(".mp4") or clean_url.startswith("http://") or clean_url.startswith("https://"):
                playback_mode = PlaybackModeEnum.DIRECT_HTTP
                stream_status = StreamStatusEnum.CONNECTED
                is_playable = True
                status_message = "Authorized HTTP video stream ready."
            else:
                playback_mode = PlaybackModeEnum.DIRECT_HTTP
                stream_status = StreamStatusEnum.CONNECTED
                is_playable = True
                status_message = "Live stream source configured."

    return CameraStreamInfoResponse(
        camera_id=camera.id,
        camera_code=camera.camera_code,
        camera_name=camera.camera_name,
        department=camera.department,
        location_name=camera.location_name,
        latitude=camera.latitude if has_valid_coords else None,
        longitude=camera.longitude if has_valid_coords else None,
        has_valid_coordinates=has_valid_coords,
        camera_type=camera.camera_type,
        source_type=camera.source_type,
        connectivity_type=camera.connectivity_type,
        camera_status=camera.status,
        playback_mode=playback_mode,
        stream_status=stream_status,
        stream_url=stream_url,
        is_playable_in_browser=is_playable,
        status_message=status_message,
        footage_count=len(available_footage),
        available_footage=available_footage,
        active_alerts_count=active_alerts_count,
        latest_alert_message=latest_alert_message,
        latest_alert_severity=latest_alert_severity,
    )


def get_viewer_stats(db: Session) -> ViewerStatsResponse:
    """
    Computes real-time platform statistics for the Unified Multi-Camera Viewer.
    """
    total_cameras = db.query(func.count(Camera.id)).scalar() or 0
    online_cameras = db.query(func.count(Camera.id)).filter(Camera.status == CameraStatus.ONLINE).scalar() or 0
    offline_cameras = db.query(func.count(Camera.id)).filter(Camera.status == CameraStatus.OFFLINE).scalar() or 0
    recorded_sources = db.query(func.count(Camera.id)).filter(Camera.source_type == SourceType.RECORDED_FOOTAGE).scalar() or 0
    live_sources = db.query(func.count(Camera.id)).filter(Camera.source_type == SourceType.LIVE_CAMERA).scalar() or 0
    total_footage = db.query(func.count(CameraFootage.id)).scalar() or 0
    active_alerts = (
        db.query(func.count(VehicleAlert.id))
        .filter(VehicleAlert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]))
        .scalar()
        or 0
    )

    return ViewerStatsResponse(
        total_registered_cameras=total_cameras,
        online_cameras=online_cameras,
        offline_cameras=offline_cameras,
        recorded_footage_sources=recorded_sources,
        live_stream_sources=live_sources,
        total_footage_files=total_footage,
        active_watchlist_alerts=active_alerts,
    )
