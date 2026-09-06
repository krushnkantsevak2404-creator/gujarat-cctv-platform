"""
Vehicle Search REST API Endpoints
Provides investigative queries for vehicle registration numbers, chronological sightings,
observed camera detection sequences, GIS spatial points, and linked watchlist alert history.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.vehicle_search import VehicleSearchResponse
from app.services import vehicle_search_service

router = APIRouter()


@router.get(
    "",
    response_model=VehicleSearchResponse,
    summary="Search Vehicle Movement History & Detection Sequence",
    description="Searches all recorded CCTV ANPR detection records for a vehicle registration number and returns chronologically ordered sightings, camera detection sequence, and GIS metadata.",
)
@router.get(
    "/",
    response_model=VehicleSearchResponse,
    include_in_schema=False,
)
def search_vehicle(
    plate_text: Optional[str] = Query(None, description="Vehicle license plate registration number (e.g. GJ 01 AB 1234)"),
    start_time: Optional[datetime] = Query(None, description="Filter sightings starting from ISO datetime"),
    end_time: Optional[datetime] = Query(None, description="Filter sightings up to ISO datetime"),
    department: Optional[str] = Query(None, description="Filter by police department or division"),
    camera_id: Optional[int] = Query(None, ge=1, description="Filter by specific camera asset ID"),
    location: Optional[str] = Query(None, description="Filter by location name or district"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Maximum observations to return"),
    db: Session = Depends(get_db),
):
    try:
        return vehicle_search_service.search_vehicle_history(
            db=db,
            plate_text=plate_text,
            start_time=start_time,
            end_time=end_time,
            department=department,
            camera_id=camera_id,
            location=location,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vehicle search failed: {str(e)}",
        )
