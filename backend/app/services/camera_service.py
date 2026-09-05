"""
Camera Registry Service
Encapsulates CRUD business logic, search filters, statistics, and sample seed data.
"""

from typing import List, Optional, Tuple
import shutil
from datetime import date
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status
from app.models.camera import (
    Camera,
    CameraType,
    SourceType,
    ConnectivityType,
    CameraStatus,
)
from app.models.footage import CameraFootage
from app.schemas.camera import CameraCreate, CameraUpdate, CameraStatsResponse
from app.core.config import settings


def get_cameras(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department: Optional[str] = None,
    status_filter: Optional[CameraStatus] = None,
    source_type: Optional[SourceType] = None,
    camera_type: Optional[CameraType] = None,
    connectivity_type: Optional[ConnectivityType] = None,
) -> Tuple[List[Camera], int]:
    """Retrieves list of registered cameras with search and filters."""
    query = db.query(Camera)

    # Search filter across name, code, department, location
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Camera.camera_name.ilike(search_pattern),
                Camera.camera_code.ilike(search_pattern),
                Camera.department.ilike(search_pattern),
                Camera.location_name.ilike(search_pattern),
            )
        )

    # Specific category filters
    if department:
        query = query.filter(Camera.department.ilike(f"%{department.strip()}%"))
    if status_filter:
        query = query.filter(Camera.status == status_filter)
    if source_type:
        query = query.filter(Camera.source_type == source_type)
    if camera_type:
        query = query.filter(Camera.camera_type == camera_type)
    if connectivity_type:
        query = query.filter(Camera.connectivity_type == connectivity_type)

    total = query.count()
    cameras = query.order_by(Camera.created_at.desc()).offset(skip).limit(limit).all()
    return cameras, total


def get_camera_by_id(db: Session, camera_id: int) -> Camera:
    """Gets a single camera by ID or raises 404."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found",
        )
    return camera


def get_camera_by_code(db: Session, camera_code: str) -> Optional[Camera]:
    """Gets camera by unique alphanumeric code."""
    return db.query(Camera).filter(Camera.camera_code == camera_code.strip().upper()).first()


def create_camera(db: Session, camera_in: CameraCreate) -> Camera:
    """Registers a new camera asset in the registry."""
    existing = get_camera_by_code(db, camera_in.camera_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Camera code '{camera_in.camera_code}' already exists in registry",
        )

    # Auto-adjust connectivity type for recorded footage if not set
    connectivity = camera_in.connectivity_type
    if camera_in.source_type == SourceType.RECORDED_FOOTAGE and connectivity == ConnectivityType.UNKNOWN:
        connectivity = ConnectivityType.FILE

    camera = Camera(
        camera_name=camera_in.camera_name.strip(),
        camera_code=camera_in.camera_code.strip().upper(),
        department=camera_in.department.strip(),
        location_name=camera_in.location_name.strip(),
        latitude=camera_in.latitude,
        longitude=camera_in.longitude,
        camera_type=camera_in.camera_type,
        source_type=camera_in.source_type,
        connectivity_type=connectivity,
        stream_url=camera_in.stream_url.strip() if camera_in.stream_url else None,
        status=camera_in.status,
        installation_date=camera_in.installation_date,
        description=camera_in.description.strip() if camera_in.description else None,
    )

    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


def update_camera(db: Session, camera_id: int, camera_in: CameraUpdate) -> Camera:
    """Updates an existing camera record."""
    camera = get_camera_by_id(db, camera_id)

    update_data = camera_in.model_dump(exclude_unset=True)

    # Check code uniqueness if changing code
    if "camera_code" in update_data and update_data["camera_code"]:
        new_code = update_data["camera_code"].strip().upper()
        if new_code != camera.camera_code:
            existing = get_camera_by_code(db, new_code)
            if existing and existing.id != camera.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Camera code '{new_code}' is already used by another camera",
                )
            update_data["camera_code"] = new_code

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(camera, field, value)

    db.commit()
    db.refresh(camera)
    return camera


def delete_camera(db: Session, camera_id: int) -> dict:
    """Deletes a camera, its footage records, and physical storage directory."""
    camera = get_camera_by_id(db, camera_id)
    
    # Clean up physical storage folder for camera
    cam_storage = settings.footage_storage_path / f"camera_{camera_id}"
    if cam_storage.exists() and cam_storage.is_dir():
        try:
            shutil.rmtree(cam_storage)
        except Exception as e:
            pass

    db.delete(camera)
    db.commit()
    return {"status": "ok", "message": f"Camera {camera.camera_code} deleted successfully"}


def get_camera_statistics(db: Session) -> CameraStatsResponse:
    """Calculates live platform summary stats for dashboard cards."""
    total = db.query(Camera).count()
    live = db.query(Camera).filter(Camera.source_type == SourceType.LIVE_CAMERA).count()
    recorded = db.query(Camera).filter(Camera.source_type == SourceType.RECORDED_FOOTAGE).count()
    
    online = db.query(Camera).filter(Camera.status == CameraStatus.ONLINE).count()
    offline = db.query(Camera).filter(Camera.status == CameraStatus.OFFLINE).count()
    maintenance = db.query(Camera).filter(Camera.status == CameraStatus.MAINTENANCE).count()
    unknown = db.query(Camera).filter(Camera.status == CameraStatus.UNKNOWN).count()
    
    total_footage = db.query(CameraFootage).count()

    return CameraStatsResponse(
        total_cameras=total,
        live_cameras=live,
        recorded_cameras=recorded,
        online_cameras=online,
        offline_cameras=offline,
        maintenance_cameras=maintenance,
        unknown_cameras=unknown,
        total_footage_files=total_footage,
    )


def seed_sample_cameras(db: Session) -> List[Camera]:
    """Seeds 6 realistic Gujarat Police sample camera assets if registry is empty."""
    if db.query(Camera).count() > 0:
        return db.query(Camera).all()

    samples = [
        Camera(
            camera_name="SG Highway Iskcon Junction Cam 01",
            camera_code="SAMPLE-CAM-001",
            department="Traffic Police - Ahmedabad",
            location_name="Iskcon Cross Road, SG Highway, Ahmedabad",
            latitude=23.0287,
            longitude=72.5068,
            camera_type=CameraType.PTZ,
            source_type=SourceType.RECORDED_FOOTAGE,
            connectivity_type=ConnectivityType.FILE,
            status=CameraStatus.UNKNOWN,
            installation_date=date(2024, 1, 15),
            description="Sample Camera: Covers southbound traffic flow on SG Highway towards Gandhinagar.",
        ),
        Camera(
            camera_name="Alkapuri RC Dutt Road Cam 02",
            camera_code="SAMPLE-CAM-002",
            department="Vadodara City Police",
            location_name="RC Dutt Road, Alkapuri, Vadodara",
            latitude=22.3107,
            longitude=73.1812,
            camera_type=CameraType.DOME,
            source_type=SourceType.LIVE_CAMERA,
            connectivity_type=ConnectivityType.UNKNOWN,
            status=CameraStatus.UNKNOWN,
            installation_date=date(2023, 11, 20),
            description="Sample Camera: High-density commercial hub surveillance in Vadodara Central.",
        ),
        Camera(
            camera_name="Surat Ring Road Majura Gate Cam 03",
            camera_code="SAMPLE-CAM-003",
            department="Surat Traffic Branch",
            location_name="Majura Gate Junction, Ring Road, Surat",
            latitude=21.1764,
            longitude=72.8223,
            camera_type=CameraType.BULLET,
            source_type=SourceType.RECORDED_FOOTAGE,
            connectivity_type=ConnectivityType.FILE,
            status=CameraStatus.UNKNOWN,
            installation_date=date(2024, 3, 10),
            description="Sample Camera: Multi-lane ANPR vantage point on Surat inner ring road.",
        ),
        Camera(
            camera_name="Rajkot Yagnik Road Cam 04",
            camera_code="SAMPLE-CAM-004",
            department="Rajkot City Police",
            location_name="Dr. Yagnik Road, Jagnath Plot, Rajkot",
            latitude=22.2965,
            longitude=70.7983,
            camera_type=CameraType.FIXED,
            source_type=SourceType.LIVE_CAMERA,
            connectivity_type=ConnectivityType.UNKNOWN,
            status=CameraStatus.UNKNOWN,
            installation_date=date(2023, 8, 5),
            description="Sample Camera: City center junction monitoring.",
        ),
        Camera(
            camera_name="Gandhinagar CH Road Cam 05",
            camera_code="SAMPLE-CAM-005",
            department="Gandhinagar Police HQ",
            location_name="CH-0 Junction, Sector 1, Gandhinagar",
            latitude=23.2156,
            longitude=72.6369,
            camera_type=CameraType.PTZ,
            source_type=SourceType.RECORDED_FOOTAGE,
            connectivity_type=ConnectivityType.FILE,
            status=CameraStatus.UNKNOWN,
            installation_date=date(2024, 2, 1),
            description="Sample Camera: State secretariat and VIP corridor monitoring.",
        ),
        Camera(
            camera_name="Bhavnagar Waghawadi Road Cam 06",
            camera_code="SAMPLE-CAM-006",
            department="Bhavnagar Police",
            location_name="Waghawadi Road, Bhavnagar",
            latitude=21.7645,
            longitude=72.1519,
            camera_type=CameraType.FIXED,
            source_type=SourceType.RECORDED_FOOTAGE,
            connectivity_type=ConnectivityType.FILE,
            status=CameraStatus.UNKNOWN,
            installation_date=date(2024, 4, 18),
            description="Sample Camera: Main arterial commercial avenue in Bhavnagar.",
        ),
    ]

    for c in samples:
        db.add(c)
    db.commit()
    return db.query(Camera).all()
