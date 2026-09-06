"""
Vehicle Search & Movement History Service
Provides cross-camera ANPR observation searching, Indian plate normalization,
chronological sorting, observed camera sequence aggregation, and watchlist alert history integration.
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, asc, desc, func

from app.core.config import settings
from app.models.anpr import AnprDetection, AnprStatus, PlateFormatStatus
from app.models.footage import CameraFootage
from app.models.camera import Camera
from app.models.alert import VehicleAlert
from app.models.watchlist import WatchlistEntry
from app.schemas.vehicle_search import (
    VehicleObservationItem,
    ObservedCameraSequenceStep,
    VehicleSearchSummary,
    VehicleAlertHistoryItem,
    VehicleSearchResponse,
)
from app.services import yolo_service

logger = logging.getLogger("uvicorn.error")


def normalize_plate_query(raw_text: str) -> str:
    """
    Normalizes search plate input using the same domain logic as ANPR/Watchlist services.
    Strips whitespace, hyphens, and non-alphanumerics; converts to uppercase.
    """
    if not raw_text:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", raw_text).upper()


def format_duration(seconds: float) -> str:
    """Formats duration seconds into human readable duration string."""
    if seconds < 0:
        seconds = 0
    total_sec = int(round(seconds))
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60

    parts = []
    if hrs > 0:
        parts.append(f"{hrs}h")
    if mins > 0 or hrs > 0:
        parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def search_vehicle_history(
    db: Session,
    plate_text: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    department: Optional[str] = None,
    camera_id: Optional[int] = None,
    location: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> VehicleSearchResponse:
    """
    Searches all recorded CCTV ANPR detection records for a vehicle registration number.
    Returns chronological observations, observed camera detection sequence, summary metrics,
    and prior watchlist alert history.
    """
    raw_plate = (plate_text or "").strip()
    norm_plate = normalize_plate_query(raw_plate)

    # If no search term provided, return empty structured response
    if not norm_plate:
        return VehicleSearchResponse(
            query_plate_raw=raw_plate,
            query_plate_normalized=norm_plate,
            total_observations=0,
            summary=VehicleSearchSummary(),
            observations=[],
            observed_sequence=[],
            alerts_history=[],
        )

    # 1. Build Query joining AnprDetection -> CameraFootage -> Camera
    q = (
        db.query(AnprDetection, CameraFootage, Camera)
        .join(CameraFootage, AnprDetection.footage_id == CameraFootage.id)
        .join(Camera, CameraFootage.camera_id == Camera.id)
    )

    # Match normalized plate text or raw plate text
    q = q.filter(
        or_(
            AnprDetection.plate_number_normalized == norm_plate,
            AnprDetection.plate_number_raw.ilike(f"%{norm_plate}%"),
        )
    )

    # Exclude completely unreadable OCR artifacts if raw text is empty
    q = q.filter(AnprDetection.status != AnprStatus.OCR_UNREADABLE)

    # Optional Filters
    if department and department.strip():
        q = q.filter(Camera.department == department.strip())

    if camera_id is not None:
        q = q.filter(Camera.id == camera_id)

    if location and location.strip():
        q = q.filter(
            or_(
                Camera.location_name.ilike(f"%{location.strip()}%"),
                Camera.camera_name.ilike(f"%{location.strip()}%"),
            )
        )

    if start_time:
        q = q.filter(
            or_(
                CameraFootage.recording_start_time >= start_time,
                and_(
                    CameraFootage.recording_start_time.is_(None),
                    CameraFootage.created_at >= start_time,
                ),
                AnprDetection.created_at >= start_time,
            )
        )

    if end_time:
        q = q.filter(
            or_(
                CameraFootage.recording_end_time <= end_time,
                and_(
                    CameraFootage.recording_end_time.is_(None),
                    CameraFootage.created_at <= end_time,
                ),
                AnprDetection.created_at <= end_time,
            )
        )

    # Chronological Ordering (footage start time / created_at + detection timestamp)
    q = q.order_by(
        CameraFootage.recording_start_time.asc().nullsfirst(),
        CameraFootage.created_at.asc(),
        AnprDetection.timestamp_seconds.asc(),
        AnprDetection.frame_number.asc(),
        AnprDetection.id.asc(),
    )

    total_count = q.count()
    records = q.offset(skip).limit(limit).all()

    # 2. Build Observation Items
    observation_items: List[VehicleObservationItem] = []
    unique_camera_ids = set()
    unique_departments = set()
    first_obs_dt: Optional[datetime] = None
    last_obs_dt: Optional[datetime] = None

    for det, footage, camera in records:
        unique_camera_ids.add(camera.id)
        unique_departments.add(camera.department)

        # Calculate estimated real-world observation datetime
        base_time = footage.recording_start_time or footage.created_at or det.created_at
        if base_time:
            obs_dt = base_time + timedelta(seconds=det.timestamp_seconds)
        else:
            obs_dt = det.created_at or datetime.now(timezone.utc)

        if first_obs_dt is None or obs_dt < first_obs_dt:
            first_obs_dt = obs_dt
        if last_obs_dt is None or obs_dt > last_obs_dt:
            last_obs_dt = obs_dt

        # Check plate crop image file
        crop_url = None
        has_crop = False
        if det.plate_crop_path:
            crop_file = Path(settings.STORAGE_DIR) / det.plate_crop_path
            if crop_file.exists():
                crop_url = f"/api/anpr/{det.id}/crop"
                has_crop = True

        # Coordinate validity check
        has_valid_coords = (
            camera.latitude is not None
            and camera.longitude is not None
            and (camera.latitude != 0.0 or camera.longitude != 0.0)
        )

        item = VehicleObservationItem(
            id=det.id,
            anpr_detection_id=det.id,
            footage_id=footage.id,
            camera_id=camera.id,
            camera_code=camera.camera_code,
            camera_name=camera.camera_name,
            location_name=camera.location_name,
            department=camera.department,
            latitude=camera.latitude if has_valid_coords else None,
            longitude=camera.longitude if has_valid_coords else None,
            has_valid_coordinates=has_valid_coords,
            timestamp_seconds=det.timestamp_seconds,
            formatted_timestamp=yolo_service.format_timestamp(det.timestamp_seconds),
            observed_at=obs_dt,
            formatted_datetime=obs_dt.strftime("%d-%b-%Y %H:%M:%S") if obs_dt else "N/A",
            footage_filename=footage.original_file_name or footage.file_name,
            video_stream_url=f"/api/footage/{footage.id}/stream",
            plate_text=det.plate_number_normalized or det.plate_number_raw or norm_plate,
            plate_number_raw=det.plate_number_raw,
            plate_number_normalized=det.plate_number_normalized,
            vehicle_class=det.vehicle_class,
            track_id=det.track_id,
            confidence=det.confidence,
            confidence_percent=f"{det.confidence * 100:.1f}%",
            ocr_confidence=det.ocr_confidence,
            ocr_confidence_percent=f"{det.ocr_confidence * 100:.1f}%" if det.ocr_confidence is not None else "N/A",
            detection_confidence=det.detection_confidence,
            status=det.status,
            format_status=det.format_status,
            plate_crop_url=crop_url,
            has_crop=has_crop,
        )
        observation_items.append(item)

    # 3. Aggregate Observed Camera Detection Sequence
    # Groups consecutive sightings on the same camera into sequential encounter steps
    observed_sequence: List[ObservedCameraSequenceStep] = []
    if observation_items:
        current_step_items: List[VehicleObservationItem] = [observation_items[0]]
        
        for item in observation_items[1:]:
            prev = current_step_items[-1]
            # Group if same camera and within close timeframe (e.g. <= 120s apart)
            if item.camera_id == prev.camera_id and abs(item.timestamp_seconds - prev.timestamp_seconds) <= 120:
                current_step_items.append(item)
            else:
                # Seal current sequence step
                step = _build_sequence_step(len(observed_sequence) + 1, current_step_items)
                observed_sequence.append(step)
                current_step_items = [item]
        
        if current_step_items:
            step = _build_sequence_step(len(observed_sequence) + 1, current_step_items)
            observed_sequence.append(step)

    # 4. Summary Metrics
    duration_str = None
    if first_obs_dt and last_obs_dt:
        diff_sec = (last_obs_dt - first_obs_dt).total_seconds()
        duration_str = format_duration(diff_sec)

    summary = VehicleSearchSummary(
        total_observations=total_count,
        unique_cameras_count=len(unique_camera_ids),
        departments_count=len(unique_departments),
        first_observed_at=first_obs_dt.strftime("%d-%b-%Y %H:%M:%S") if first_obs_dt else None,
        last_observed_at=last_obs_dt.strftime("%d-%b-%Y %H:%M:%S") if last_obs_dt else None,
        duration_span=duration_str,
    )

    # 5. Query Prior Watchlist Alert History (Milestone 7 Integration)
    alerts_history: List[VehicleAlertHistoryItem] = []
    alert_records = (
        db.query(VehicleAlert, Camera)
        .join(Camera, VehicleAlert.camera_id == Camera.id)
        .filter(
            or_(
                VehicleAlert.plate_text == norm_plate,
                VehicleAlert.plate_text.ilike(f"%{norm_plate}%"),
            )
        )
        .order_by(desc(VehicleAlert.created_at))
        .all()
    )

    for alert, cam in alert_records:
        watchlist_desc = None
        watchlist_cat = None
        if alert.watchlist_entry_id:
            wl_entry = db.query(WatchlistEntry).filter(WatchlistEntry.id == alert.watchlist_entry_id).first()
            if wl_entry:
                watchlist_desc = wl_entry.description
                watchlist_cat = wl_entry.category.value if wl_entry.category else None

        alerts_history.append(
            VehicleAlertHistoryItem(
                id=alert.id,
                watchlist_entry_id=alert.watchlist_entry_id,
                watchlist_category=watchlist_cat,
                watchlist_description=watchlist_desc,
                alert_type=alert.alert_type,
                severity=alert.severity,
                status=alert.status,
                message=alert.message,
                camera_code=cam.camera_code,
                camera_name=cam.camera_name,
                location_name=cam.location_name,
                timestamp_seconds=alert.timestamp_seconds,
                formatted_timestamp=yolo_service.format_timestamp(alert.timestamp_seconds),
                created_at=alert.created_at,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at,
            )
        )

    return VehicleSearchResponse(
        query_plate_raw=raw_plate,
        query_plate_normalized=norm_plate,
        total_observations=total_count,
        summary=summary,
        observations=observation_items,
        observed_sequence=observed_sequence,
        alerts_history=alerts_history,
    )


def _build_sequence_step(
    step_num: int, items: List[VehicleObservationItem]
) -> ObservedCameraSequenceStep:
    """Helper to aggregate consecutive sightings on a single camera into a sequence step."""
    first = items[0]
    last = items[-1]

    # Best representative item (highest confidence or crop availability)
    best_item = max(items, key=lambda x: (x.has_crop, x.confidence, x.ocr_confidence or 0.0))

    track_ids = list({item.track_id for item in items if item.track_id is not None})
    
    if len(items) == 1 or first.formatted_timestamp == last.formatted_timestamp:
        time_display = first.formatted_timestamp
    else:
        time_display = f"{first.formatted_timestamp} – {last.formatted_timestamp}"

    return ObservedCameraSequenceStep(
        step_number=step_num,
        camera_id=first.camera_id,
        camera_code=first.camera_code,
        camera_name=first.camera_name,
        location_name=first.location_name,
        department=first.department,
        latitude=first.latitude,
        longitude=first.longitude,
        has_valid_coordinates=first.has_valid_coordinates,
        first_timestamp_seconds=first.timestamp_seconds,
        formatted_first_timestamp=first.formatted_timestamp,
        first_observed_at=first.observed_at,
        last_timestamp_seconds=last.timestamp_seconds,
        formatted_last_timestamp=last.formatted_timestamp,
        last_observed_at=last.observed_at,
        time_window_display=time_display,
        sighting_count=len(items),
        primary_vehicle_class=best_item.vehicle_class,
        track_ids=track_ids,
        best_confidence=best_item.confidence,
        best_confidence_percent=best_item.confidence_percent,
        best_ocr_confidence=best_item.ocr_confidence,
        best_ocr_confidence_percent=best_item.ocr_confidence_percent,
        primary_anpr_id=best_item.anpr_detection_id,
        primary_footage_id=best_item.footage_id,
        primary_crop_url=best_item.plate_crop_url,
        video_stream_url=best_item.video_stream_url,
    )
