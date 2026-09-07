"""
Unified CCTV Viewer REST API Endpoints
Provides stream capability inspection, playback readiness metadata,
available footage listing, and viewer aggregate metrics.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.camera import Camera
from app.schemas.stream import CameraStreamInfoResponse, ViewerStatsResponse
from app.services import stream_service

router = APIRouter()


@router.get(
    "/stats",
    response_model=ViewerStatsResponse,
    summary="Get Unified Viewer Aggregate Statistics",
    description="Returns real-time platform statistics for the Unified Multi-Camera Viewer (total cameras, online, recorded/live breakdown, total footage, active alerts).",
)
def get_viewer_statistics(db: Session = Depends(get_db)):
    return stream_service.get_viewer_stats(db)


@router.get(
    "/cameras/{camera_id}/stream-info",
    response_model=CameraStreamInfoResponse,
    summary="Get Camera Stream Info & Playback Mode",
    description="Inspects camera source type, available recorded footage, and stream capabilities to determine genuine browser playback readiness.",
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
    return stream_service.get_camera_stream_info(db, camera)
