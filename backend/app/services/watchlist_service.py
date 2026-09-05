"""
Watchlist & Automatic Vehicle Alert Service
Handles watchlist entry CRUD operations, Indian plate normalization,
active watchlist matching against ANPR observations, confidence filtering,
multi-frame alert deduplication, and alert status workflow.
"""

import re
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.core.config import settings
from app.models.watchlist import (
    WatchlistEntry,
    WatchlistCategory,
    WatchlistPriority,
    WatchlistStatus,
)
from app.models.alert import (
    VehicleAlert,
    AlertType,
    AlertSeverity,
    AlertStatus,
)
from app.models.anpr import (
    AnprDetection,
    AnprStatus,
    PlateFormatStatus,
)
from app.models.footage import CameraFootage
from app.models.camera import Camera
from app.schemas.watchlist import WatchlistEntryCreate, WatchlistEntryUpdate
from app.services import yolo_service

logger = logging.getLogger("uvicorn.error")


def normalize_plate_text(raw_text: str) -> str:
    """Strips whitespace, hyphens, and special characters; converts to uppercase."""
    if not raw_text:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", raw_text).upper()


def validate_plate_input(raw_text: str) -> Tuple[bool, str, str]:
    """
    Validates entered plate text.
    Returns (is_valid, normalized_text, error_message).
    """
    if not raw_text or not raw_text.strip():
        return False, "", "License plate number cannot be empty."
    
    normalized = normalize_plate_text(raw_text)
    if len(normalized) < 3:
        return False, normalized, "License plate must contain at least 3 alphanumeric characters."
    
    if len(normalized) > 20:
        return False, normalized, "License plate exceeds maximum allowed length of 20 characters."

    return True, normalized, ""


# -----------------------------------------------------------------------------
# Watchlist CRUD Operations
# -----------------------------------------------------------------------------

def list_watchlist_entries(
    db: Session,
    query: Optional[str] = None,
    category: Optional[WatchlistCategory] = None,
    priority: Optional[WatchlistPriority] = None,
    status: Optional[WatchlistStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[WatchlistEntry]:
    """Lists watchlist entries with optional search and metadata filters."""
    q = db.query(WatchlistEntry)

    if query:
        clean_q = normalize_plate_text(query)
        q = q.filter(
            or_(
                WatchlistEntry.normalized_plate_text.ilike(f"%{clean_q}%"),
                WatchlistEntry.plate_text.ilike(f"%{query}%"),
                WatchlistEntry.description.ilike(f"%{query}%"),
            )
        )

    if category:
        q = q.filter(WatchlistEntry.category == category)
    if priority:
        q = q.filter(WatchlistEntry.priority == priority)
    if status:
        q = q.filter(WatchlistEntry.status == status)

    return q.order_by(desc(WatchlistEntry.created_at)).offset(skip).limit(limit).all()


def get_watchlist_entry_by_id(db: Session, entry_id: int) -> Optional[WatchlistEntry]:
    """Retrieves a single watchlist entry by ID."""
    return db.query(WatchlistEntry).filter(WatchlistEntry.id == entry_id).first()


def get_watchlist_entry_by_normalized_plate(db: Session, normalized_plate: str) -> Optional[WatchlistEntry]:
    """Retrieves an active watchlist entry matching the normalized plate."""
    return (
        db.query(WatchlistEntry)
        .filter(
            WatchlistEntry.normalized_plate_text == normalized_plate,
            WatchlistEntry.status == WatchlistStatus.ACTIVE,
        )
        .first()
    )


def create_watchlist_entry(db: Session, entry_in: WatchlistEntryCreate) -> WatchlistEntry:
    """Creates a new watchlist entry with normalized plate string."""
    is_valid, norm_plate, err = validate_plate_input(entry_in.plate_text)
    if not is_valid:
        raise ValueError(err)

    entry = WatchlistEntry(
        plate_text=entry_in.plate_text.strip().upper(),
        normalized_plate_text=norm_plate,
        description=entry_in.description.strip() if entry_in.description else None,
        category=entry_in.category,
        priority=entry_in.priority,
        status=entry_in.status,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_watchlist_entry(
    db: Session, entry_id: int, entry_in: WatchlistEntryUpdate
) -> Optional[WatchlistEntry]:
    """Updates an existing watchlist entry."""
    entry = get_watchlist_entry_by_id(db, entry_id)
    if not entry:
        return None

    update_data = entry_in.dict(exclude_unset=True)
    if "plate_text" in update_data and update_data["plate_text"]:
        is_valid, norm_plate, err = validate_plate_input(update_data["plate_text"])
        if not is_valid:
            raise ValueError(err)
        entry.plate_text = update_data["plate_text"].strip().upper()
        entry.normalized_plate_text = norm_plate

    if "description" in update_data:
        entry.description = update_data["description"].strip() if update_data["description"] else None
    if "category" in update_data and update_data["category"]:
        entry.category = update_data["category"]
    if "priority" in update_data and update_data["priority"]:
        entry.priority = update_data["priority"]
    if "status" in update_data and update_data["status"]:
        entry.status = update_data["status"]

    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


def delete_watchlist_entry(db: Session, entry_id: int) -> bool:
    """Deletes a watchlist entry."""
    entry = get_watchlist_entry_by_id(db, entry_id)
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def toggle_watchlist_status(
    db: Session, entry_id: int, new_status: WatchlistStatus
) -> Optional[WatchlistEntry]:
    """Toggles status of a watchlist entry."""
    entry = get_watchlist_entry_by_id(db, entry_id)
    if not entry:
        return None
    entry.status = new_status
    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


# -----------------------------------------------------------------------------
# Watchlist Matching & Alert Generation Engine
# -----------------------------------------------------------------------------

def evaluate_footage_anpr_detections(
    db: Session, footage_id: int, anpr_records: List[AnprDetection]
) -> List[VehicleAlert]:
    """
    Evaluates newly produced ANPR detections for a CCTV footage against all active watchlist entries.
    Creates deduplicated VehicleAlert records when matches occur on eligible confidence observations.
    """
    if not anpr_records:
        return []

    # 1. Fetch all ACTIVE watchlist entries in a single fast query
    active_entries = (
        db.query(WatchlistEntry)
        .filter(WatchlistEntry.status == WatchlistStatus.ACTIVE)
        .all()
    )
    if not active_entries:
        logger.info("No active watchlist entries configured. Skipping alert matching.")
        return []

    # Build fast in-memory lookup map
    active_watchlist_map: Dict[str, WatchlistEntry] = {
        entry.normalized_plate_text.upper(): entry for entry in active_entries
    }

    # Fetch context footage and camera
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        logger.warning(f"Footage #{footage_id} not found during watchlist evaluation.")
        return []

    camera = db.query(Camera).filter(Camera.id == footage.camera_id).first()
    camera_name = camera.camera_name if camera else "Unknown Camera"
    camera_code = camera.camera_code if camera else "N/A"
    location_name = camera.location_name if camera else "Gujarat Location"

    min_confidence = getattr(settings, "WATCHLIST_MATCH_MIN_CONFIDENCE", 0.35)
    dedup_window = getattr(settings, "WATCHLIST_ALERT_DEDUPLICATION_WINDOW_SECONDS", 5.0)

    generated_alerts: List[VehicleAlert] = []
    
    # Priority to AlertSeverity mapping
    priority_severity_map = {
        WatchlistPriority.LOW: AlertSeverity.LOW,
        WatchlistPriority.MEDIUM: AlertSeverity.MEDIUM,
        WatchlistPriority.HIGH: AlertSeverity.HIGH,
        WatchlistPriority.CRITICAL: AlertSeverity.CRITICAL,
    }

    for det in anpr_records:
        # Rule 1: Do not create alerts for unreadable OCR observations
        if det.status == AnprStatus.OCR_UNREADABLE:
            continue

        # Rule 2: Minimum OCR / detection confidence threshold
        effective_conf = max(det.confidence or 0.0, det.ocr_confidence or 0.0)
        if effective_conf < min_confidence:
            logger.debug(f"ANPR detection #{det.id} confidence ({effective_conf:.2f}) below threshold {min_confidence}. Skipping.")
            continue

        # Rule 3: Match normalized plate text
        norm_plate = (det.plate_number_normalized or det.plate_number_raw or "").strip().upper()
        norm_plate = re.sub(r"[^A-Za-z0-9]", "", norm_plate)
        if not norm_plate:
            continue

        if norm_plate in active_watchlist_map:
            watchlist_entry = active_watchlist_map[norm_plate]
            severity = priority_severity_map.get(watchlist_entry.priority, AlertSeverity.HIGH)

            # Rule 4: Multi-frame deduplication
            # Check if an alert already exists for this watchlist entry in this footage on the same track or nearby time
            existing_alert = (
                db.query(VehicleAlert)
                .filter(
                    VehicleAlert.footage_id == footage_id,
                    VehicleAlert.watchlist_entry_id == watchlist_entry.id,
                    or_(
                        VehicleAlert.track_id == det.track_id if det.track_id is not None else False,
                        func.abs(VehicleAlert.timestamp_seconds - det.timestamp_seconds) <= dedup_window,
                    ),
                )
                .first()
            )

            # Check in-memory generated alerts in current batch
            if not existing_alert:
                for gen_a in generated_alerts:
                    if gen_a.watchlist_entry_id == watchlist_entry.id:
                        track_match = (gen_a.track_id is not None and gen_a.track_id == det.track_id)
                        time_match = abs(gen_a.timestamp_seconds - det.timestamp_seconds) <= dedup_window
                        if track_match or time_match:
                            existing_alert = gen_a
                            break

            if existing_alert:
                # If existing alert has lower confidence, update it to point to the stronger ANPR sighting
                if det.confidence > existing_alert.confidence:
                    existing_alert.confidence = det.confidence
                    existing_alert.anpr_detection_id = det.id
                    existing_alert.timestamp_seconds = det.timestamp_seconds
                    db.commit()
                continue

            # Format concise machine-generated alert message (No personal identification)
            time_str = yolo_service.format_timestamp(det.timestamp_seconds)
            message = (
                f"Watchlist vehicle {norm_plate} ({watchlist_entry.category.value}) "
                f"detected at {camera_name} ({camera_code}, {location_name}) at {time_str}."
            )

            alert = VehicleAlert(
                watchlist_entry_id=watchlist_entry.id,
                anpr_detection_id=det.id,
                footage_id=footage_id,
                camera_id=footage.camera_id,
                track_id=det.track_id,
                plate_text=norm_plate,
                vehicle_class=det.vehicle_class,
                timestamp_seconds=det.timestamp_seconds,
                confidence=det.confidence,
                alert_type=AlertType.WATCHLIST_MATCH,
                severity=severity,
                status=AlertStatus.NEW,
                message=message,
            )
            db.add(alert)
            generated_alerts.append(alert)
            logger.info(f"🚨 Created WATCHLIST_MATCH alert #{alert.id} for vehicle {norm_plate} on Camera {camera_code}")

    if generated_alerts:
        db.commit()
        for a in generated_alerts:
            db.refresh(a)

    return generated_alerts


# -----------------------------------------------------------------------------
# Alert Management & Workflow Operations
# -----------------------------------------------------------------------------

def list_alerts(
    db: Session,
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    plate: Optional[str] = None,
    camera_id: Optional[int] = None,
    footage_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[VehicleAlert]:
    """Lists alerts with comprehensive status, severity, and camera filters."""
    q = db.query(VehicleAlert)

    if status:
        q = q.filter(VehicleAlert.status == status)
    if severity:
        q = q.filter(VehicleAlert.severity == severity)
    if plate:
        clean_p = normalize_plate_text(plate)
        q = q.filter(VehicleAlert.plate_text.ilike(f"%{clean_p}%"))
    if camera_id is not None:
        q = q.filter(VehicleAlert.camera_id == camera_id)
    if footage_id is not None:
        q = q.filter(VehicleAlert.footage_id == footage_id)

    return q.order_by(desc(VehicleAlert.created_at)).offset(skip).limit(limit).all()


def get_alert_by_id(db: Session, alert_id: int) -> Optional[VehicleAlert]:
    """Retrieves single alert record by ID."""
    return db.query(VehicleAlert).filter(VehicleAlert.id == alert_id).first()


def acknowledge_alert(db: Session, alert_id: int) -> Optional[VehicleAlert]:
    """Transitions alert status from NEW to ACKNOWLEDGED."""
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        return None

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


def resolve_alert(db: Session, alert_id: int) -> Optional[VehicleAlert]:
    """Transitions alert status to RESOLVED."""
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        return None

    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.now(timezone.utc)
    if not alert.acknowledged_at:
        alert.acknowledged_at = alert.resolved_at
    db.commit()
    db.refresh(alert)
    return alert


def get_alert_statistics(db: Session) -> Dict[str, int]:
    """Computes dynamic alert summary statistics across all cameras."""
    total = db.query(VehicleAlert).count()
    new_count = db.query(VehicleAlert).filter(VehicleAlert.status == AlertStatus.NEW).count()
    ack_count = db.query(VehicleAlert).filter(VehicleAlert.status == AlertStatus.ACKNOWLEDGED).count()
    res_count = db.query(VehicleAlert).filter(VehicleAlert.status == AlertStatus.RESOLVED).count()
    
    crit_count = db.query(VehicleAlert).filter(VehicleAlert.severity == AlertSeverity.CRITICAL).count()
    high_count = db.query(VehicleAlert).filter(VehicleAlert.severity == AlertSeverity.HIGH).count()
    med_count = db.query(VehicleAlert).filter(VehicleAlert.severity == AlertSeverity.MEDIUM).count()
    low_count = db.query(VehicleAlert).filter(VehicleAlert.severity == AlertSeverity.LOW).count()

    return {
        "total_alerts": total,
        "new_alerts": new_count,
        "acknowledged_alerts": ack_count,
        "resolved_alerts": res_count,
        "critical_alerts": crit_count,
        "high_alerts": high_count,
        "medium_alerts": med_count,
        "low_alerts": low_count,
    }
