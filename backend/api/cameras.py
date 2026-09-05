import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from cctv.camera_catalog import fetch_catalogue, get_camera_metadata
from database import get_recent_events

router = APIRouter(prefix="/api", tags=["cameras"])

class StartCameraPayload(BaseModel):
    custom_rtsp_url: Optional[str] = None

# Active Stream Registry
active_streams_registry = {}

def get_active_streams():
    return active_streams_registry

@router.get("/ingest")
def catalogue_ingest_proxy():
    """Section 1 Ingest contract endpoint."""
    cameras = fetch_catalogue()
    return {
        "cctv_mode": os.getenv("CCTV_MODE", "mock"),
        "gateway_host": os.getenv("CCTV_GATEWAY_HOST", "localhost:8000"),
        "total_cameras": len(cameras),
        "cameras": cameras
    }

@router.get("/cameras")
def list_cameras():
    """Lists available camera catalogue to frontend."""
    catalogue = fetch_catalogue()
    for cam in catalogue:
        cam_id = str(cam.get("id"))
        cam["is_actively_consuming"] = cam_id in active_streams_registry
    return {"cameras": catalogue, "mode": os.getenv("CCTV_MODE", "mock")}

@router.get("/cameras/{camera_id}")
def get_camera(camera_id: str):
    """Returns camera metadata for camera_id."""
    meta = get_camera_metadata(camera_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Camera #{camera_id} not found")
    meta["is_actively_consuming"] = str(camera_id) in active_streams_registry
    return meta

@router.get("/cameras/{camera_id}/status")
def get_camera_status(camera_id: str):
    """Returns telemetry, connection state, and PTS timestamps."""
    cam_id = str(camera_id)
    if cam_id in active_streams_registry:
        stream_obj = active_streams_registry[cam_id]
        return stream_obj.get_telemetry()
    return {
        "id": camera_id,
        "is_actively_consuming": False,
        "is_connected": False,
        "pts_ms": 0.0,
        "delta_pts_ms": 0.0
    }

@router.post("/cameras/{camera_id}/start")
def start_camera_stream(camera_id: str, payload: Optional[StartCameraPayload] = None):
    """Load Management: Start capture ONLY when requested."""
    from cctv_manager import cctv_service
    custom_url = payload.custom_rtsp_url if payload else None
    stream = cctv_service.start_camera(camera_id, custom_rtsp_url=custom_url)
    active_streams_registry[str(camera_id)] = stream
    return {"message": f"Started Camera #{camera_id}", "status": stream.get_telemetry()}

@router.post("/cameras/{camera_id}/stop")
def stop_camera_stream(camera_id: str):
    """Load Management: Stop capture and release resources when finished."""
    from cctv_manager import cctv_service
    cam_id = str(camera_id)
    if cam_id in active_streams_registry:
        del active_streams_registry[cam_id]
    cctv_service.stop_camera(camera_id)
    return {"message": f"Stopped Camera #{camera_id} and released resources"}

@router.get("/events")
def get_events(limit: int = 50):
    """Returns logged detection events from SQLite database."""
    events = get_recent_events(limit=limit)
    return {"total": len(events), "events": events}
