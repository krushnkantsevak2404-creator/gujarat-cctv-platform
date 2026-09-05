"""
ANPR & OCR Endpoints
Provides asynchronous ANPR processing initiation, plate query filtering,
plate crop image streaming, and global number plate search across all registered cameras.
"""

import threading
from typing import List, Optional
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    Path as FastPath,
    Query,
    HTTPException,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database.session import get_db
from app.models.footage import CameraFootage
from app.models.camera import Camera
from app.models.detection import (
    ProcessingJob,
    JobStatus,
    JobType,
)
from app.models.anpr import (
    AnprDetection,
    AnprStatus,
    PlateFormatStatus,
)
from app.schemas.anpr import (
    AnprDetectionResponse,
    AnprSummaryResponse,
    AnprSearchResultItem,
    AnprSearchResponse,
)
from app.schemas.detection import ProcessingJobResponse
from app.services import anpr_service, yolo_service
from app.core.config import settings

router = APIRouter()


def format_anpr_response(det: AnprDetection) -> AnprDetectionResponse:
    """Formats an AnprDetection ORM instance into an API response schema."""
    crop_url = None
    has_crop = False
    if det.plate_crop_path:
        crop_file = Path(settings.STORAGE_DIR) / det.plate_crop_path
        if crop_file.exists():
            crop_url = f"/api/anpr/{det.id}/crop"
            has_crop = True

    return AnprDetectionResponse(
        id=det.id,
        footage_id=det.footage_id,
        track_id=det.track_id,
        frame_number=det.frame_number,
        timestamp_seconds=det.timestamp_seconds,
        formatted_timestamp=yolo_service.format_timestamp(det.timestamp_seconds),
        vehicle_class=det.vehicle_class,
        plate_number_raw=det.plate_number_raw,
        plate_number_normalized=det.plate_number_normalized,
        confidence=det.confidence,
        confidence_percent=f"{det.confidence * 100:.1f}%",
        ocr_confidence=det.ocr_confidence,
        detection_confidence=det.detection_confidence,
        status=det.status,
        format_status=det.format_status,
        x1=det.x1,
        y1=det.y1,
        x2=det.x2,
        y2=det.y2,
        vehicle_x1=det.vehicle_x1,
        vehicle_y1=det.vehicle_y1,
        vehicle_x2=det.vehicle_x2,
        vehicle_y2=det.vehicle_y2,
        plate_crop_url=crop_url,
        has_crop=has_crop,
        is_consolidated=det.is_consolidated,
        sighting_count=det.sighting_count,
        created_at=det.created_at,
    )


def build_anpr_job_response(job: ProcessingJob) -> ProcessingJobResponse:
    """Builds ProcessingJobResponse schema from ProcessingJob ORM instance."""
    return ProcessingJobResponse(
        id=job.id,
        footage_id=job.footage_id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        device=job.device,
        total_frames=job.total_frames,
        processed_frames=job.processed_frames,
        total_detections=job.total_detections,
        cars_count=job.cars_count,
        motorcycles_count=job.motorcycles_count,
        buses_count=job.buses_count,
        trucks_count=job.trucks_count,
        total_tracks=job.total_tracks,
        car_tracks=job.car_tracks,
        motorcycle_tracks=job.motorcycle_tracks,
        bus_tracks=job.bus_tracks,
        truck_tracks=job.truck_tracks,
        total_plates_detected=job.total_plates_detected or 0,
        successful_ocr_count=job.successful_ocr_count or 0,
        valid_format_count=job.valid_format_count or 0,
        unique_plates_count=job.unique_plates_count or 0,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        created_at=job.created_at,
    )


@router.post(
    "/footage/{footage_id}/anpr",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start ANPR & OCR Video Processing",
    description="Launches an asynchronous job to localize number plates and extract plate characters via OCR on recorded CCTV footage.",
)
def start_anpr_processing(
    footage_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    # Check if video file exists on disk
    source_path = settings.footage_storage_path / f"camera_{footage.camera_id}" / footage.file_name
    if not source_path.exists():
        source_path = Path(settings.STORAGE_DIR) / footage.file_path
    if not source_path.exists():
        source_path = Path(footage.file_path)
    if not source_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage video file not found on disk at {source_path}",
        )

    # Check if there is an ongoing job
    active_job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.footage_id == footage_id,
            ProcessingJob.job_type == JobType.ANPR_OCR,
            ProcessingJob.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING]),
        )
        .first()
    )
    if active_job:
        return build_anpr_job_response(active_job)

    # Create new ANPR ProcessingJob record
    job = ProcessingJob(
        footage_id=footage_id,
        job_type=JobType.ANPR_OCR,
        status=JobStatus.QUEUED,
        progress=0,
        device=yolo_service.get_processing_device(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch processing in background thread
    thread = threading.Thread(
        target=anpr_service.run_anpr_pipeline,
        args=(footage_id, job.id),
        daemon=True,
    )
    thread.start()

    return build_anpr_job_response(job)


@router.get(
    "/footage/{footage_id}/anpr",
    response_model=List[AnprDetectionResponse],
    summary="Get ANPR Detections for Footage",
    description="Returns list of ANPR license plate detections for a specific footage with optional status and query filters.",
)
def get_footage_anpr_detections(
    footage_id: int = FastPath(..., ge=1),
    status_filter: Optional[AnprStatus] = Query(None, alias="status"),
    format_filter: Optional[PlateFormatStatus] = Query(None, alias="format_status"),
    query: Optional[str] = Query(None, description="Partial plate search string"),
    track_id: Optional[int] = Query(None, description="Filter by track ID"),
    consolidated_only: bool = Query(True, description="Return only consolidated deduplicated plate readings"),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    query_builder = db.query(AnprDetection).filter(AnprDetection.footage_id == footage_id)

    if consolidated_only:
        query_builder = query_builder.filter(AnprDetection.is_consolidated == True)
    if status_filter:
        query_builder = query_builder.filter(AnprDetection.status == status_filter)
    if format_filter:
        query_builder = query_builder.filter(AnprDetection.format_status == format_filter)
    if track_id is not None:
        query_builder = query_builder.filter(AnprDetection.track_id == track_id)
    if query:
        clean_q = anpr_service.clean_raw_plate_text(query)
        query_builder = query_builder.filter(
            or_(
                AnprDetection.plate_number_normalized.ilike(f"%{clean_q}%"),
                AnprDetection.plate_number_raw.ilike(f"%{query}%"),
            )
        )

    detections = query_builder.order_by(desc(AnprDetection.confidence), AnprDetection.timestamp_seconds).all()
    return [format_anpr_response(d) for d in detections]


@router.get(
    "/footage/{footage_id}/anpr/summary",
    response_model=AnprSummaryResponse,
    summary="Get ANPR Summary & Consolidated Detections",
    description="Returns summary statistics and consolidated ANPR detections for a footage.",
)
def get_footage_anpr_summary(
    footage_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    camera = db.query(Camera).filter(Camera.id == footage.camera_id).first()
    camera_code = camera.camera_code if camera else "N/A"
    camera_name = camera.camera_name if camera else "Unknown Camera"
    location_name = camera.location_name if camera else "Unknown Location"

    latest_job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.footage_id == footage_id,
            ProcessingJob.job_type == JobType.ANPR_OCR,
        )
        .order_by(desc(ProcessingJob.created_at))
        .first()
    )

    # Consolidated detections
    detections = (
        db.query(AnprDetection)
        .filter(AnprDetection.footage_id == footage_id, AnprDetection.is_consolidated == True)
        .order_by(desc(AnprDetection.confidence), AnprDetection.timestamp_seconds)
        .all()
    )

    total_plates = db.query(AnprDetection).filter(AnprDetection.footage_id == footage_id).count()
    success_count = sum(1 for d in detections if d.status == AnprStatus.OCR_SUCCESS)
    valid_format_count = sum(1 for d in detections if d.format_status == PlateFormatStatus.VALID_FORMAT)

    return AnprSummaryResponse(
        footage_id=footage.id,
        camera_id=footage.camera_id,
        camera_code=camera_code,
        camera_name=camera_name,
        location_name=location_name,
        original_file_name=footage.original_file_name,
        original_video_stream_url=f"/api/footage/{footage.id}/stream",
        latest_job=build_anpr_job_response(latest_job) if latest_job else None,
        total_plates_detected=total_plates,
        successful_ocr_count=success_count,
        valid_format_count=valid_format_count,
        unique_plates_count=len(detections),
        detections=[format_anpr_response(d) for d in detections],
    )


@router.get(
    "/anpr/search",
    response_model=AnprSearchResponse,
    summary="Global License Plate Search",
    description="Searches for vehicle license plates across all camera footage in the platform.",
)
def search_license_plates(
    query: str = Query(..., min_length=2, description="License plate query to search"),
    camera_id: Optional[int] = Query(None, description="Optional camera ID filter"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    clean_q = anpr_service.clean_raw_plate_text(query)

    query_builder = (
        db.query(AnprDetection, CameraFootage, Camera)
        .join(CameraFootage, AnprDetection.footage_id == CameraFootage.id)
        .join(Camera, CameraFootage.camera_id == Camera.id)
        .filter(
            or_(
                AnprDetection.plate_number_normalized.ilike(f"%{clean_q}%"),
                AnprDetection.plate_number_raw.ilike(f"%{query}%"),
            )
        )
    )

    if camera_id is not None:
        query_builder = query_builder.filter(Camera.id == camera_id)

    results_raw = query_builder.order_by(desc(AnprDetection.confidence), desc(AnprDetection.created_at)).limit(limit).all()

    items = []
    for det, foot, cam in results_raw:
        crop_url = None
        has_crop = False
        if det.plate_crop_path:
            crop_file = Path(settings.STORAGE_DIR) / det.plate_crop_path
            if crop_file.exists():
                crop_url = f"/api/anpr/{det.id}/crop"
                has_crop = True

        items.append(
            AnprSearchResultItem(
                id=det.id,
                footage_id=det.footage_id,
                camera_id=cam.id,
                camera_code=cam.camera_code,
                camera_name=cam.camera_name,
                location_name=cam.location_name,
                latitude=cam.latitude,
                longitude=cam.longitude,
                timestamp_seconds=det.timestamp_seconds,
                formatted_timestamp=yolo_service.format_timestamp(det.timestamp_seconds),
                plate_number_normalized=det.plate_number_normalized,
                plate_number_raw=det.plate_number_raw,
                vehicle_class=det.vehicle_class,
                status=det.status,
                format_status=det.format_status,
                confidence=det.confidence,
                confidence_percent=f"{det.confidence * 100:.1f}%",
                plate_crop_url=crop_url,
                has_crop=has_crop,
                created_at=det.created_at,
            )
        )

    return AnprSearchResponse(
        query=query,
        total_results=len(items),
        results=items,
    )


@router.get(
    "/anpr/{anpr_id}",
    response_model=AnprDetectionResponse,
    summary="Get ANPR Detection Detail",
    description="Returns detailed information for a single ANPR plate detection.",
)
def get_anpr_detection_detail(
    anpr_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    det = db.query(AnprDetection).filter(AnprDetection.id == anpr_id).first()
    if not det:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ANPR detection with ID {anpr_id} not found",
        )
    return format_anpr_response(det)


@router.get(
    "/anpr/{anpr_id}/crop",
    summary="Stream License Plate Crop Image",
    description="Streams the high-resolution cropped license plate image file.",
)
def stream_plate_crop(
    anpr_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    det = db.query(AnprDetection).filter(AnprDetection.id == anpr_id).first()
    if not det or not det.plate_crop_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plate crop for ANPR ID {anpr_id} not found",
        )

    crop_path = Path(settings.STORAGE_DIR) / det.plate_crop_path
    if not crop_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plate crop image file not found on disk at {crop_path}",
        )

    return FileResponse(
        path=str(crop_path),
        media_type="image/jpeg",
        filename=crop_path.name,
    )
