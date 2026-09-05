"""
Camera Registry Endpoints
Provides REST API endpoints for managing CCTV assets, statistics, and GeoJSON export.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraStatsResponse,
)
from app.models.camera import (
    CameraType,
    SourceType,
    ConnectivityType,
    CameraStatus,
)
from app.services import camera_service

router = APIRouter()


@router.get(
    "/stats",
    response_model=CameraStatsResponse,
    summary="Get Camera Summary Statistics",
    description="Returns aggregate statistics for total, live, recorded, and status counts.",
)
def get_stats(db: Session = Depends(get_db)):
    return camera_service.get_camera_statistics(db)


@router.get(
    "/geojson",
    summary="Get Cameras as GeoJSON FeatureCollection",
    description="Exports camera assets as a standard GeoJSON FeatureCollection with Point geometries [longitude, latitude].",
)
def get_cameras_geojson(
    search: Optional[str] = Query(default=None, description="Search by name, code, department, or location"),
    department: Optional[str] = Query(default=None, description="Filter by department"),
    status_filter: Optional[CameraStatus] = Query(default=None, alias="status", description="Filter by status"),
    source_type: Optional[SourceType] = Query(default=None, description="Filter by source type"),
    camera_type: Optional[CameraType] = Query(default=None, description="Filter by camera type"),
    connectivity_type: Optional[ConnectivityType] = Query(default=None, description="Filter by connectivity"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    cameras, _ = camera_service.get_cameras(
        db=db,
        skip=0,
        limit=500,
        search=search,
        department=department,
        status_filter=status_filter,
        source_type=source_type,
        camera_type=camera_type,
        connectivity_type=connectivity_type,
    )

    features = []
    for cam in cameras:
        # Only include valid geographic coordinates in GeoJSON geometry
        if cam.latitude is not None and cam.longitude is not None:
            feature = {
                "type": "Feature",
                "id": cam.id,
                "geometry": {
                    "type": "Point",
                    # GeoJSON standard: [longitude (East/West), latitude (North/South)]
                    "coordinates": [float(cam.longitude), float(cam.latitude)],
                },
                "properties": {
                    "id": cam.id,
                    "camera_name": cam.camera_name,
                    "camera_code": cam.camera_code,
                    "department": cam.department,
                    "location_name": cam.location_name,
                    "latitude": float(cam.latitude),
                    "longitude": float(cam.longitude),
                    "camera_type": cam.camera_type,
                    "source_type": cam.source_type,
                    "connectivity_type": cam.connectivity_type,
                    "stream_url": cam.stream_url,
                    "status": cam.status,
                    "installation_date": str(cam.installation_date) if cam.installation_date else None,
                    "description": cam.description,
                    "footage_count": len(cam.footage) if cam.footage else 0,
                    "created_at": cam.created_at.isoformat() if cam.created_at else None,
                    "updated_at": cam.updated_at.isoformat() if cam.updated_at else None,
                },
            }
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_mapped_cameras": len(features),
            "crs": "urn:ogc:def:crs:OGC:1.3:CRS84",
            "srid": 4326,
        },
    }


@router.post(
    "/seed-sample-data",
    summary="Seed Sample Gujarat Police Cameras",
    description="Seeds fictional demo cameras with real Gujarat coordinates if the registry is empty.",
)
def seed_sample_data(db: Session = Depends(get_db)):
    seeded = camera_service.seed_sample_cameras(db)
    return {
        "status": "ok",
        "message": f"Seeded sample Gujarat cameras. Total: {len(seeded)}",
        "count": len(seeded),
    }


@router.get(
    "",
    response_model=List[CameraResponse],
    summary="List Registered Cameras",
    description="Query CCTV camera assets with keyword search and category filters.",
)
def list_cameras(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: Optional[str] = Query(default=None, description="Search by name, code, department, or location"),
    department: Optional[str] = Query(default=None, description="Filter by department"),
    status: Optional[CameraStatus] = Query(default=None, description="Filter by status (ONLINE, OFFLINE, MAINTENANCE, UNKNOWN)"),
    source_type: Optional[SourceType] = Query(default=None, description="Filter by source type (LIVE_CAMERA, RECORDED_FOOTAGE)"),
    camera_type: Optional[CameraType] = Query(default=None, description="Filter by camera type"),
    connectivity_type: Optional[ConnectivityType] = Query(default=None, description="Filter by connectivity"),
    db: Session = Depends(get_db),
):
    cameras, _ = camera_service.get_cameras(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        department=department,
        status_filter=status,
        source_type=source_type,
        camera_type=camera_type,
        connectivity_type=connectivity_type,
    )
    
    # Map footage count and footage list
    results = []
    for cam in cameras:
        cam_dict = {
            "id": cam.id,
            "camera_name": cam.camera_name,
            "camera_code": cam.camera_code,
            "department": cam.department,
            "location_name": cam.location_name,
            "latitude": cam.latitude,
            "longitude": cam.longitude,
            "camera_type": cam.camera_type,
            "source_type": cam.source_type,
            "connectivity_type": cam.connectivity_type,
            "stream_url": cam.stream_url,
            "status": cam.status,
            "installation_date": cam.installation_date,
            "description": cam.description,
            "created_at": cam.created_at,
            "updated_at": cam.updated_at,
            "footage_count": len(cam.footage) if cam.footage else 0,
            "footage": cam.footage or [],
        }
        results.append(CameraResponse.model_validate(cam_dict))
    return results


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a New Camera",
    description="Registers a new CCTV camera with geographic coordinates and metadata.",
)
def create_camera(
    camera_in: CameraCreate,
    db: Session = Depends(get_db),
):
    camera = camera_service.create_camera(db=db, camera_in=camera_in)
    return CameraResponse.model_validate(
        {
            **camera.__dict__,
            "footage_count": 0,
            "footage": [],
        }
    )


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Get Camera Details",
    description="Returns detailed metadata and associated recorded footage for a camera.",
)
def get_camera(
    camera_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    cam = camera_service.get_camera_by_id(db, camera_id)
    return CameraResponse.model_validate(
        {
            **cam.__dict__,
            "footage_count": len(cam.footage) if cam.footage else 0,
            "footage": cam.footage or [],
        }
    )


@router.put(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Update Camera Information",
    description="Updates existing camera asset metadata.",
)
def update_camera(
    camera_id: int = Path(..., ge=1),
    camera_in: CameraUpdate = ...,
    db: Session = Depends(get_db),
):
    cam = camera_service.update_camera(db=db, camera_id=camera_id, camera_in=camera_in)
    return CameraResponse.model_validate(
        {
            **cam.__dict__,
            "footage_count": len(cam.footage) if cam.footage else 0,
            "footage": cam.footage or [],
        }
    )


@router.delete(
    "/{camera_id}",
    summary="Delete Camera",
    description="Deletes a camera, its associated recorded footage records, and stored files.",
)
def delete_camera(
    camera_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    return camera_service.delete_camera(db=db, camera_id=camera_id)
