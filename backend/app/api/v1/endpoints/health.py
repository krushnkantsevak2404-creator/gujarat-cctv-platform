"""
Health Check Endpoint
Provides basic service availability and database connectivity diagnostic endpoints.
"""

from fastapi import APIRouter, Query
from app.schemas.health import HealthResponse
from app.core.config import settings
from app.database.session import check_database_connection

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns current health status of the Gujarat CCTV Intelligence Platform backend.",
)
def get_health(
    check_db: bool = Query(
        default=False,
        description="Optional flag to include live PostgreSQL/PostGIS connectivity check.",
    )
):
    """
    Health check endpoint returning status and service name.
    """
    db_status = check_database_connection() if check_db else None

    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version="1.0.0",
        database=db_status,
    )
