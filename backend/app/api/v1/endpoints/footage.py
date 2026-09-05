"""
Recorded CCTV Footage Endpoints
Handles video upload, metadata persistence, HTTP 206 partial streaming, and deletion.
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    Header,
    Path as FastPath,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.footage import CameraFootage, FootageStatus
from app.models.camera import SourceType
from app.schemas.footage import FootageResponse
from app.services import camera_service, video_service
from app.core.config import settings

router = APIRouter()


def build_footage_response(footage: CameraFootage) -> FootageResponse:
    """Helper to convert model to response schema with stream URL."""
    return FootageResponse(
        id=footage.id,
        camera_id=footage.camera_id,
        file_name=footage.file_name,
        original_file_name=footage.original_file_name,
        file_path=footage.file_path,
        file_size=footage.file_size,
        mime_type=footage.mime_type,
        duration_seconds=footage.duration_seconds,
        video_width=footage.video_width,
        video_height=footage.video_height,
        fps=footage.fps,
        frame_count=footage.frame_count,
        recording_start_time=footage.recording_start_time,
        recording_end_time=footage.recording_end_time,
        status=footage.status,
        description=footage.description,
        created_at=footage.created_at,
        stream_url=f"/api/footage/{footage.id}/stream",
    )


@router.get(
    "/cameras/{camera_id}/footage",
    response_model=List[FootageResponse],
    summary="List Recorded Footage for a Camera",
    description="Returns all recorded CCTV video clips associated with a specific camera.",
)
def list_camera_footage(
    camera_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    camera = camera_service.get_camera_by_id(db, camera_id)
    footages = (
        db.query(CameraFootage)
        .filter(CameraFootage.camera_id == camera.id)
        .order_by(CameraFootage.created_at.desc())
        .all()
    )
    return [build_footage_response(f) for f in footages]


@router.post(
    "/cameras/{camera_id}/footage",
    response_model=FootageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Recorded CCTV Footage",
    description="Uploads authorized video file, extracts metadata (duration, FPS, resolution), and associates it with the camera.",
)
async def upload_footage(
    camera_id: int = FastPath(..., ge=1),
    file: UploadFile = File(..., description="CCTV Video file (MP4, AVI, MOV, MKV)"),
    description: Optional[str] = Form(default=None, description="Optional description of the clip"),
    recording_start_time: Optional[datetime] = Form(default=None),
    recording_end_time: Optional[datetime] = Form(default=None),
    db: Session = Depends(get_db),
):
    # Verify camera exists
    camera = camera_service.get_camera_by_id(db, camera_id)

    # 1. Validate file extension
    original_filename = file.filename or "unknown.mp4"
    ext = Path(original_filename).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '.{ext}'. Allowed formats: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}",
        )

    # 2. Get safe target directory and filename
    cam_dir = video_service.get_camera_storage_dir(camera.id)
    safe_name = video_service.generate_safe_filename(original_filename)
    target_path = cam_dir / safe_name

    # 3. Stream upload to disk with size validation
    total_size = 0
    try:
        with open(target_path, "wb") as f_out:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > settings.max_upload_bytes:
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_VIDEO_UPLOAD_MB} MB",
                    )
                f_out.write(chunk)
    except Exception as e:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write video file: {e}",
        )

    # 4. Extract metadata (resolution, fps, duration)
    meta = video_service.extract_video_metadata(target_path)

    # 5. Create database record
    footage = CameraFootage(
        camera_id=camera.id,
        file_name=safe_name,
        original_file_name=original_filename,
        file_path=str(target_path.relative_to(settings.footage_storage_path.parent)),
        file_size=total_size,
        mime_type=file.content_type or "video/mp4",
        duration_seconds=meta.get("duration_seconds"),
        video_width=meta.get("width"),
        video_height=meta.get("height"),
        fps=meta.get("fps"),
        frame_count=meta.get("frame_count"),
        recording_start_time=recording_start_time,
        recording_end_time=recording_end_time,
        status=FootageStatus.UPLOADED,
        description=description,
    )

    db.add(footage)
    db.commit()
    db.refresh(footage)

    return build_footage_response(footage)


@router.get(
    "/footage/{footage_id}",
    response_model=FootageResponse,
    summary="Get Footage Details",
    description="Returns metadata for a specific recorded video file.",
)
def get_footage(
    footage_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )
    return build_footage_response(footage)


@router.get(
    "/footage/{footage_id}/stream",
    summary="Stream Recorded CCTV Footage",
    description="Streams video file with HTTP 206 Partial Content support for HTML5 playback and seeking.",
)
def stream_footage(
    footage_id: int = FastPath(..., ge=1),
    range_header: Optional[str] = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    full_path = Path(settings.STORAGE_DIR) / Path(footage.file_path).relative_to("storage") if footage.file_path.startswith("storage") else Path(settings.STORAGE_DIR) / footage.file_path
    
    # Fallback to direct check
    if not full_path.exists():
        direct = settings.footage_storage_path / f"camera_{footage.camera_id}" / footage.file_name
        if direct.exists():
            full_path = direct

    return video_service.create_range_streaming_response(
        file_path=full_path,
        range_header=range_header,
        mime_type=footage.mime_type,
    )


@router.delete(
    "/footage/{footage_id}",
    summary="Delete Recorded CCTV Footage",
    description="Permanently deletes footage record and stored video file from disk.",
)
def delete_footage(
    footage_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    # Delete physical file from disk
    cam_dir = settings.footage_storage_path / f"camera_{footage.camera_id}"
    file_path = cam_dir / footage.file_name
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    db.delete(footage)
    db.commit()

    return {
        "status": "ok",
        "message": f"Footage {footage.original_file_name} deleted successfully",
    }
