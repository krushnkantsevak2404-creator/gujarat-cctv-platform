"""
Authorized CCTV Stream Management REST API Endpoints
Provides stream connection lifecycle, sanitized status queries, media relay feeds, and aggregate statistics.
Strict Security Enforcement: No passwords, tokens, or raw credential-bearing URLs are exposed to client callers.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.camera import Camera
from app.streams import (
    stream_manager,
    StreamConnectRequest,
    StreamSessionResponse,
    StreamStatusResponse,
    StreamInfoResponse,
    StreamStatsResponse,
    ActiveSessionItem,
)

router = APIRouter()


@router.get(
    "/stats",
    response_model=StreamStatsResponse,
    summary="Get Stream Platform Aggregate Statistics",
    description="Returns aggregate stream telemetry (total cameras, live vs recorded breakdown, active live stream sessions, media relay status).",
)
def get_stream_statistics(db: Session = Depends(get_db)):
    return stream_manager.get_stats(db)


@router.get(
    "/active-sessions",
    response_model=List[ActiveSessionItem],
    summary="List Active Stream Sessions",
    description="Returns active server-side stream sessions, frame rates, client counts, and session durations.",
)
def get_active_stream_sessions():
    return stream_manager.get_active_sessions()


@router.get(
    "/{camera_id}/status",
    response_model=StreamStatusResponse,
    summary="Get Camera Stream Operational Status",
    description="Inspects real-time operational status for a camera source (CONNECTED, CONNECTING, DISCONNECTED, NOT_CONFIGURED, ERROR) without leaking credentials.",
)
def get_camera_stream_status(
    camera_id: int = Path(..., ge=1, description="Registered camera database ID"),
    db: Session = Depends(get_db),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found in CCTV Registry.",
        )
    return stream_manager.get_stream_status(camera, db=db)


@router.post(
    "/{camera_id}/connect",
    response_model=StreamSessionResponse,
    summary="Connect to Authorized Camera Stream",
    description="Initiates connection to the authorized CCTV source via StreamManager. Reuses active session if already connected to prevent duplicate relay overhead.",
)
def connect_camera_stream(
    camera_id: int = Path(..., ge=1, description="Registered camera database ID"),
    payload: Optional[StreamConnectRequest] = None,
    db: Session = Depends(get_db),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found in CCTV Registry.",
        )

    force_reconnect = payload.force_reconnect if payload else False
    return stream_manager.connect_stream(camera, db=db, force_reconnect=force_reconnect)


@router.post(
    "/{camera_id}/disconnect",
    response_model=StreamStatusResponse,
    summary="Disconnect Camera Stream",
    description="Terminates active stream capture session, releases OpenCV / media relay resources, and updates status.",
)
def disconnect_camera_stream(
    camera_id: int = Path(..., ge=1, description="Registered camera database ID"),
    db: Session = Depends(get_db),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found in CCTV Registry.",
        )
    return stream_manager.disconnect_stream(camera_id, camera_code=camera.camera_code)


@router.get(
    "/{camera_id}/info",
    response_model=StreamInfoResponse,
    summary="Get Camera Stream & Capability Info",
    description="Returns comprehensive stream capabilities, media relay details, available recorded footage, and active watchlist alerts.",
)
def get_camera_stream_info(
    camera_id: int = Path(..., ge=1, description="Registered camera database ID"),
    db: Session = Depends(get_db),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found in CCTV Registry.",
        )
    return stream_manager.get_stream_info(camera, db=db)


@router.get(
    "/{camera_id}/live",
    summary="Live Video Stream Feed (Browser-Compatible MJPEG Relay)",
    description="Streams multipart/x-mixed-replace JPEG video frames for browser-compatible HTML5 live viewing of authorized RTSP streams.",
)
def stream_live_feed(
    camera_id: int = Path(..., ge=1, description="Registered camera database ID"),
    db: Session = Depends(get_db),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found in CCTV Registry.",
        )

    # Auto-connect if not already connected
    stream_manager.connect_stream(camera, db=db, force_reconnect=False)

    return StreamingResponse(
        stream_manager.get_stream_feed(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
