"""
Health Check & Operational Dashboard Endpoints
Provides infrastructure health monitoring, real-time camera fleet telemetry,
and system diagnostics for the Gujarat Police Command & Control Center.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db, check_database_connection
from app.core.config import settings
from app.schemas.health import (
    HealthResponse,
    CameraHealthOverviewResponse,
    SystemHealthResponse,
)
from app.services import camera_health_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns basic service availability and database connectivity diagnostic status.",
)
def get_health(
    check_db: bool = Query(
        default=False,
        description="Optional flag to include live database connectivity check.",
    )
):
    """
    Base health check endpoint returning service status.
    """
    db_status = check_database_connection() if check_db else None

    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version="1.0.0",
        database=db_status,
    )


@router.get(
    "/health/cameras",
    response_model=CameraHealthOverviewResponse,
    summary="Get Camera Health & Operational Dashboard Overview",
    description="Returns aggregate camera counts, stream statuses, department summaries, vehicle intelligence metrics, recent alerts, and filtered camera health records.",
)
def get_camera_health(
    search: Optional[str] = Query(default=None, description="Search by camera name, code, department, or location"),
    department: Optional[str] = Query(default=None, description="Filter by department"),
    status: Optional[str] = Query(default=None, description="Filter by registration status (ONLINE, OFFLINE, MAINTENANCE, UNKNOWN)"),
    source_type: Optional[str] = Query(default=None, description="Filter by source type (LIVE_CAMERA, RECORDED_FOOTAGE)"),
    connectivity_type: Optional[str] = Query(default=None, description="Filter by connectivity (RTSP, FILE, ONVIF, VMS_API, SDK, UNKNOWN)"),
    stream_status: Optional[str] = Query(default=None, description="Filter by stream status (CONNECTED, DISCONNECTED, NOT_CONFIGURED, ERROR)"),
    db: Session = Depends(get_db),
):
    """
    Main operational command endpoint powering the CCTV Infrastructure Dashboard.
    """
    return camera_health_service.get_camera_health_overview(
        db=db,
        search=search,
        department=department,
        status=status,
        source_type=source_type,
        connectivity_type=connectivity_type,
        stream_status=stream_status,
    )


@router.get(
    "/health/system",
    response_model=SystemHealthResponse,
    summary="Get System Diagnostics & Component Health",
    description="Evaluates operational health of core platform sub-systems without exposing credentials.",
)
def get_system_health(
    db: Session = Depends(get_db),
):
    """
    System diagnostic endpoint verifying backend, database, GIS, AI, and stream relay readiness.
    """
    return camera_health_service.get_system_health(db)
