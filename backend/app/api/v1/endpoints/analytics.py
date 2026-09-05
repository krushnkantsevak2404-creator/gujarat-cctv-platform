"""
Vehicle Analytics, Detection & Multi-Object Tracking Endpoints
Handles on-demand YOLO + ByteTrack vehicle tracking, live job tracking, track query APIs,
representative crop streaming, and processed video streaming.
"""

from typing import List, Optional
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    Path as FastPath,
    Query,
    Header,
    HTTPException,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.footage import CameraFootage
from app.models.detection import (
    VehicleDetection,
    VehicleTrack,
    ProcessingJob,
    JobStatus,
    JobType,
)
from app.schemas.detection import (
    ProcessingJobResponse,
    DetectionResponse,
    DetectionSummaryResponse,
    VehicleTrackResponse,
    VehicleTrackDetailResponse,
    TrackSummaryResponse,
)
from app.services import yolo_service, video_service
from app.core.config import settings

router = APIRouter()


def build_job_response(job: ProcessingJob) -> ProcessingJobResponse:
    processed_url = None
    processed_dir = settings.processed_storage_path / f"footage_{job.footage_id}"
    tracking_path = processed_dir / "vehicle_tracking.mp4"
    detection_path = processed_dir / "vehicle_detection.mp4"
    
    if tracking_path.exists() or detection_path.exists():
        processed_url = f"/api/footage/{job.footage_id}/processed/stream"

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
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        created_at=job.created_at,
        processed_video_stream_url=processed_url,
    )


@router.post(
    "/footage/{footage_id}/analyze",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start Vehicle Detection & Tracking Analysis",
    description="Launches an asynchronous YOLO + ByteTrack inference job on recorded CCTV footage to detect and track vehicles with temporary Track IDs.",
)
def start_analysis(
    footage_id: int = FastPath(..., ge=1),
    job_type: str = Query(default="VEHICLE_TRACKING", description="VEHICLE_TRACKING or VEHICLE_DETECTION"),
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source video file does not exist in storage",
        )

    selected_job_type = JobType.VEHICLE_TRACKING if job_type.upper() == "VEHICLE_TRACKING" else JobType.VEHICLE_DETECTION
    job = yolo_service.trigger_video_analysis(db=db, footage_id=footage.id, job_type=selected_job_type)
    return build_job_response(job)


@router.get(
    "/analysis/jobs/{job_id}",
    response_model=ProcessingJobResponse,
    summary="Get Analysis Job Status",
    description="Returns live progress, detected vehicle counts, and active track counts for a background tracking job.",
)
def get_job_status(
    job_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing job #{job_id} not found",
        )
    return build_job_response(job)


@router.get(
    "/footage/{footage_id}/tracks",
    response_model=TrackSummaryResponse,
    summary="Get Vehicle Tracks Summary",
    description="Returns all unique vehicles tracked across consecutive frames in the selected CCTV footage, with first/last seen timestamps and crop previews.",
)
def get_tracks(
    footage_id: int = FastPath(..., ge=1),
    vehicle_class: Optional[str] = Query(default=None, description="Filter tracks by vehicle class (car, motorcycle, bus, truck)"),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    query = db.query(VehicleTrack).filter(VehicleTrack.footage_id == footage.id)
    if vehicle_class:
        query = query.filter(VehicleTrack.vehicle_class == vehicle_class.lower().strip())

    tracks = query.order_by(VehicleTrack.track_id.asc()).all()
    all_tracks = db.query(VehicleTrack).filter(VehicleTrack.footage_id == footage.id).all()
    total_detections_count = db.query(VehicleDetection).filter(VehicleDetection.footage_id == footage.id).count()

    car_tracks_count = sum(1 for t in all_tracks if t.vehicle_class == "car")
    bike_tracks_count = sum(1 for t in all_tracks if t.vehicle_class == "motorcycle")
    bus_tracks_count = sum(1 for t in all_tracks if t.vehicle_class == "bus")
    truck_tracks_count = sum(1 for t in all_tracks if t.vehicle_class == "truck")

    processed_dir = settings.processed_storage_path / f"footage_{footage.id}"
    tracking_path = processed_dir / "vehicle_tracking.mp4"
    detection_path = processed_dir / "vehicle_detection.mp4"
    has_processed = tracking_path.exists() or detection_path.exists()
    processed_url = f"/api/footage/{footage.id}/processed/stream" if has_processed else None

    latest_job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.footage_id == footage.id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )

    track_items = []
    for t in tracks:
        duration = max(0.0, round(t.last_seen_seconds - t.first_seen_seconds, 2))
        crop_url = None
        has_crop = False
        if t.best_crop_path:
            crop_file = Path(settings.STORAGE_DIR) / t.best_crop_path if not Path(t.best_crop_path).is_absolute() else Path(t.best_crop_path)
            if crop_file.exists():
                has_crop = True
                crop_url = f"/api/footage/{footage.id}/tracks/{t.track_id}/crop"

        track_items.append(
            VehicleTrackResponse(
                id=t.id,
                footage_id=t.footage_id,
                track_id=t.track_id,
                vehicle_class=t.vehicle_class,
                first_seen_seconds=t.first_seen_seconds,
                first_seen_formatted=yolo_service.format_timestamp(t.first_seen_seconds),
                last_seen_seconds=t.last_seen_seconds,
                last_seen_formatted=yolo_service.format_timestamp(t.last_seen_seconds),
                duration_seconds=duration,
                first_seen_frame=t.first_seen_frame,
                last_seen_frame=t.last_seen_frame,
                detection_count=t.detection_count,
                avg_confidence=t.avg_confidence,
                avg_confidence_percent=f"{int(t.avg_confidence * 100)}%",
                crop_url=crop_url,
                has_crop=has_crop,
                created_at=t.created_at,
            )
        )

    return TrackSummaryResponse(
        footage_id=footage.id,
        camera_id=footage.camera.id if footage.camera else 0,
        camera_code=footage.camera.camera_code if footage.camera else "UNKNOWN",
        camera_name=footage.camera.camera_name if footage.camera else "Unknown Camera",
        location_name=footage.camera.location_name if footage.camera else "Unknown Location",
        original_file_name=footage.original_file_name,
        original_video_stream_url=f"/api/footage/{footage.id}/stream",
        processed_video_stream_url=processed_url,
        has_processed_video=has_processed,
        latest_job=build_job_response(latest_job) if latest_job else None,
        total_tracks=len(all_tracks),
        car_tracks=car_tracks_count,
        motorcycle_tracks=bike_tracks_count,
        bus_tracks=bus_tracks_count,
        truck_tracks=truck_tracks_count,
        total_detections=total_detections_count,
        tracks=track_items,
    )


@router.get(
    "/footage/{footage_id}/tracks/{track_id}",
    response_model=VehicleTrackDetailResponse,
    summary="Get Vehicle Track Details & Sightings",
    description="Returns detailed information and frame-by-frame sightings for a specific Track ID within the CCTV footage.",
)
def get_track_detail(
    footage_id: int = FastPath(..., ge=1),
    track_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    track = (
        db.query(VehicleTrack)
        .filter(VehicleTrack.footage_id == footage.id, VehicleTrack.track_id == track_id)
        .first()
    )
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track #{track_id} not found in footage #{footage_id}",
        )

    detections = (
        db.query(VehicleDetection)
        .filter(VehicleDetection.footage_id == footage.id, VehicleDetection.track_id == track_id)
        .order_by(VehicleDetection.frame_number.asc())
        .all()
    )

    duration = max(0.0, round(track.last_seen_seconds - track.first_seen_seconds, 2))
    crop_url = None
    has_crop = False
    if track.best_crop_path:
        crop_file = Path(settings.STORAGE_DIR) / track.best_crop_path if not Path(track.best_crop_path).is_absolute() else Path(track.best_crop_path)
        if crop_file.exists():
            has_crop = True
            crop_url = f"/api/footage/{footage.id}/tracks/{track.track_id}/crop"

    det_items = [
        DetectionResponse(
            id=d.id,
            footage_id=d.footage_id,
            frame_number=d.frame_number,
            timestamp_seconds=d.timestamp_seconds,
            formatted_timestamp=yolo_service.format_timestamp(d.timestamp_seconds),
            vehicle_class=d.vehicle_class,
            confidence=d.confidence,
            confidence_percent=f"{int(d.confidence * 100)}%",
            track_id=d.track_id,
            x1=d.x1,
            y1=d.y1,
            x2=d.x2,
            y2=d.y2,
            created_at=d.created_at,
        )
        for d in detections
    ]

    return VehicleTrackDetailResponse(
        id=track.id,
        footage_id=track.footage_id,
        track_id=track.track_id,
        vehicle_class=track.vehicle_class,
        first_seen_seconds=track.first_seen_seconds,
        first_seen_formatted=yolo_service.format_timestamp(track.first_seen_seconds),
        last_seen_seconds=track.last_seen_seconds,
        last_seen_formatted=yolo_service.format_timestamp(track.last_seen_seconds),
        duration_seconds=duration,
        first_seen_frame=track.first_seen_frame,
        last_seen_frame=track.last_seen_frame,
        detection_count=track.detection_count,
        avg_confidence=track.avg_confidence,
        avg_confidence_percent=f"{int(track.avg_confidence * 100)}%",
        crop_url=crop_url,
        has_crop=has_crop,
        created_at=track.created_at,
        camera_id=footage.camera.id if footage.camera else 0,
        camera_code=footage.camera.camera_code if footage.camera else "UNKNOWN",
        camera_name=footage.camera.camera_name if footage.camera else "Unknown Camera",
        location_name=footage.camera.location_name if footage.camera else "Unknown Location",
        original_file_name=footage.original_file_name,
        detections=det_items,
    )


@router.get(
    "/footage/{footage_id}/tracks/{track_id}/crop",
    summary="Get Representative Vehicle Crop Image",
    description="Returns the high-confidence JPEG crop of the tracked vehicle.",
)
def get_track_crop(
    footage_id: int = FastPath(..., ge=1),
    track_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    track = (
        db.query(VehicleTrack)
        .filter(VehicleTrack.footage_id == footage_id, VehicleTrack.track_id == track_id)
        .first()
    )
    if not track or not track.best_crop_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Representative crop for Track #{track_id} not found",
        )

    crop_path = Path(settings.STORAGE_DIR) / track.best_crop_path if not Path(track.best_crop_path).is_absolute() else Path(track.best_crop_path)
    if not crop_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop image file missing from storage disk",
        )

    return FileResponse(str(crop_path), media_type="image/jpeg")


@router.get(
    "/footage/{footage_id}/detections",
    response_model=DetectionSummaryResponse,
    summary="Get Vehicle Detection Results",
    description="Returns frame-by-frame vehicle detections, timestamps, bounding boxes, Track IDs, and summary statistics.",
)
def get_detections(
    footage_id: int = FastPath(..., ge=1),
    vehicle_class: Optional[str] = Query(default=None, description="Filter by vehicle class (car, motorcycle, bus, truck)"),
    db: Session = Depends(get_db),
):
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Footage with ID {footage_id} not found",
        )

    query = db.query(VehicleDetection).filter(VehicleDetection.footage_id == footage.id)
    if vehicle_class:
        query = query.filter(VehicleDetection.vehicle_class == vehicle_class.lower().strip())

    detections = query.order_by(VehicleDetection.frame_number.asc()).all()

    # Calculate breakdown
    all_dets = db.query(VehicleDetection).filter(VehicleDetection.footage_id == footage.id).all()
    cars = sum(1 for d in all_dets if d.vehicle_class == "car")
    motorcycles = sum(1 for d in all_dets if d.vehicle_class == "motorcycle")
    buses = sum(1 for d in all_dets if d.vehicle_class == "bus")
    trucks = sum(1 for d in all_dets if d.vehicle_class == "truck")
    total_tracks_count = db.query(VehicleTrack).filter(VehicleTrack.footage_id == footage.id).count()

    processed_dir = settings.processed_storage_path / f"footage_{footage.id}"
    tracking_path = processed_dir / "vehicle_tracking.mp4"
    detection_path = processed_dir / "vehicle_detection.mp4"
    has_processed = tracking_path.exists() or detection_path.exists()
    processed_url = f"/api/footage/{footage.id}/processed/stream" if has_processed else None

    latest_job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.footage_id == footage.id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )

    det_items = [
        DetectionResponse(
            id=d.id,
            footage_id=d.footage_id,
            frame_number=d.frame_number,
            timestamp_seconds=d.timestamp_seconds,
            formatted_timestamp=yolo_service.format_timestamp(d.timestamp_seconds),
            vehicle_class=d.vehicle_class,
            confidence=d.confidence,
            confidence_percent=f"{int(d.confidence * 100)}%",
            track_id=d.track_id,
            x1=d.x1,
            y1=d.y1,
            x2=d.x2,
            y2=d.y2,
            created_at=d.created_at,
        )
        for d in detections
    ]

    return DetectionSummaryResponse(
        footage_id=footage.id,
        camera_id=footage.camera.id if footage.camera else 0,
        camera_code=footage.camera.camera_code if footage.camera else "UNKNOWN",
        camera_name=footage.camera.camera_name if footage.camera else "Unknown Camera",
        location_name=footage.camera.location_name if footage.camera else "Unknown Location",
        original_file_name=footage.original_file_name,
        original_video_stream_url=f"/api/footage/{footage.id}/stream",
        processed_video_stream_url=processed_url,
        has_processed_video=has_processed,
        latest_job=build_job_response(latest_job) if latest_job else None,
        total_detections=len(all_dets),
        cars_count=cars,
        motorcycles_count=motorcycles,
        buses_count=buses,
        trucks_count=trucks,
        total_tracks=total_tracks_count,
        detections=det_items,
    )


@router.get(
    "/footage/{footage_id}/processed/stream",
    summary="Stream Annotated Processed Tracking Video",
    description="Streams YOLO + ByteTrack vehicle tracking annotated video with HTTP 206 Partial Content support.",
)
def stream_processed_video(
    footage_id: int = FastPath(..., ge=1),
    range_header: Optional[str] = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
):
    processed_dir = settings.processed_storage_path / f"footage_{footage_id}"
    tracking_path = processed_dir / "vehicle_tracking.mp4"
    detection_path = processed_dir / "vehicle_detection.mp4"

    target_video = tracking_path if tracking_path.exists() else detection_path

    if not target_video.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed annotated tracking video does not exist yet. Please run vehicle tracking analysis first.",
        )

    return video_service.create_range_streaming_response(
        file_path=target_video,
        range_header=range_header,
        mime_type="video/mp4",
    )
