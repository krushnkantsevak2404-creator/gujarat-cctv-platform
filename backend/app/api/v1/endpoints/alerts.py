"""
Vehicle Alerts REST API Endpoints
Provides endpoints for monitoring, filtering, and resolving automated vehicle watchlist match alerts.
"""

from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Query, Path as FastPath, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.alert import (
    AlertResponse,
    AlertStatsResponse,
    AlertStatusUpdate,
)
from app.models.alert import (
    VehicleAlert,
    AlertType,
    AlertSeverity,
    AlertStatus,
)
from app.models.watchlist import WatchlistEntry
from app.models.anpr import AnprDetection
from app.models.footage import CameraFootage
from app.models.camera import Camera
from app.services import watchlist_service, yolo_service
from app.core.config import settings

router = APIRouter()


def _format_alert_response(alert: VehicleAlert, db: Session) -> AlertResponse:
    """Formats VehicleAlert ORM model into AlertResponse schema with camera, watchlist, and crop metadata."""
    camera = db.query(Camera).filter(Camera.id == alert.camera_id).first()
    camera_code = camera.camera_code if camera else "CAM-UNKNOWN"
    camera_name = camera.camera_name if camera else "Unknown Camera"
    location_name = camera.location_name if camera else "Gujarat Location"
    latitude = camera.latitude if camera else None
    longitude = camera.longitude if camera else None

    # Watchlist context
    watchlist_desc = None
    watchlist_cat = None
    if alert.watchlist_entry_id:
        entry = db.query(WatchlistEntry).filter(WatchlistEntry.id == alert.watchlist_entry_id).first()
        if entry:
            watchlist_desc = entry.description
            watchlist_cat = entry.category.value

    # Plate crop context
    plate_crop_url = None
    has_crop = False
    if alert.anpr_detection_id:
        det = db.query(AnprDetection).filter(AnprDetection.id == alert.anpr_detection_id).first()
        if det and det.plate_crop_path:
            crop_file = Path(settings.STORAGE_DIR) / det.plate_crop_path
            if crop_file.exists():
                plate_crop_url = f"/api/anpr/{det.id}/crop"
                has_crop = True

    video_stream_url = f"/api/footage/{alert.footage_id}/stream"

    return AlertResponse(
        id=alert.id,
        watchlist_entry_id=alert.watchlist_entry_id,
        watchlist_description=watchlist_desc,
        watchlist_category=watchlist_cat,
        anpr_detection_id=alert.anpr_detection_id,
        footage_id=alert.footage_id,
        camera_id=alert.camera_id,
        camera_code=camera_code,
        camera_name=camera_name,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        track_id=alert.track_id,
        plate_text=alert.plate_text,
        vehicle_class=alert.vehicle_class,
        timestamp_seconds=alert.timestamp_seconds,
        formatted_timestamp=yolo_service.format_timestamp(alert.timestamp_seconds),
        confidence=alert.confidence,
        confidence_percent=f"{alert.confidence * 100:.1f}%",
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        message=alert.message,
        plate_crop_url=plate_crop_url,
        has_crop=has_crop,
        video_stream_url=video_stream_url,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
    )


@router.get(
    "/stats",
    response_model=AlertStatsResponse,
    summary="Get Alert Statistics",
    description="Returns aggregate counts of alerts by status (NEW, ACKNOWLEDGED, RESOLVED) and severity.",
)
def get_stats(db: Session = Depends(get_db)):
    stats_dict = watchlist_service.get_alert_statistics(db)
    return AlertStatsResponse(**stats_dict)


@router.get(
    "/",
    response_model=List[AlertResponse],
    summary="List Vehicle Alerts",
    description="Retrieves a list of automated vehicle alerts with optional status, severity, plate, camera, and footage filters.",
)
def list_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by alert status (NEW, ACKNOWLEDGED, RESOLVED)"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    plate: Optional[str] = Query(None, description="Filter by vehicle license plate text"),
    camera_id: Optional[int] = Query(None, ge=1, description="Filter by camera ID"),
    footage_id: Optional[int] = Query(None, ge=1, description="Filter by footage ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    alerts = watchlist_service.list_alerts(
        db=db,
        status=status,
        severity=severity,
        plate=plate,
        camera_id=camera_id,
        footage_id=footage_id,
        skip=skip,
        limit=limit,
    )
    return [_format_alert_response(a, db) for a in alerts]


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get Alert Details",
    description="Retrieves details, camera geolocation, and evidence links for a single vehicle alert.",
)
def get_alert(
    alert_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    alert = watchlist_service.get_alert_by_id(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle alert #{alert_id} not found.",
        )
    return _format_alert_response(alert, db)


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge Alert",
    description="Transitions alert status from NEW to ACKNOWLEDGED.",
)
def acknowledge_alert_endpoint(
    alert_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    updated = watchlist_service.acknowledge_alert(db=db, alert_id=alert_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle alert #{alert_id} not found.",
        )
    return _format_alert_response(updated, db)


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Resolve Alert",
    description="Transitions alert status to RESOLVED.",
)
def resolve_alert_endpoint(
    alert_id: int = FastPath(..., ge=1),
    db: Session = Depends(get_db),
):
    updated = watchlist_service.resolve_alert(db=db, alert_id=alert_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle alert #{alert_id} not found.",
        )
    return _format_alert_response(updated, db)


@router.patch(
    "/{alert_id}/status",
    response_model=AlertResponse,
    summary="Update Alert Status",
    description="Explicitly updates alert status to NEW, ACKNOWLEDGED, or RESOLVED.",
)
def update_status_endpoint(
    alert_id: int = FastPath(..., ge=1),
    status_in: AlertStatusUpdate = ...,
    db: Session = Depends(get_db),
):
    if status_in.status == AlertStatus.ACKNOWLEDGED:
        updated = watchlist_service.acknowledge_alert(db=db, alert_id=alert_id)
    elif status_in.status == AlertStatus.RESOLVED:
        updated = watchlist_service.resolve_alert(db=db, alert_id=alert_id)
    else:
        alert = watchlist_service.get_alert_by_id(db=db, alert_id=alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle alert #{alert_id} not found.",
            )
        alert.status = status_in.status
        db.commit()
        db.refresh(alert)
        updated = alert

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle alert #{alert_id} not found.",
        )
    return _format_alert_response(updated, db)
