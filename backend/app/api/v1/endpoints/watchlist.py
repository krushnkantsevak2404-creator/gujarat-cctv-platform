"""
Watchlist REST API Endpoints
Provides management of monitored vehicle registration plates, priorities, categories, and active status.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.schemas.watchlist import (
    WatchlistEntryCreate,
    WatchlistEntryUpdate,
    WatchlistStatusUpdate,
    WatchlistEntryResponse,
)
from app.models.watchlist import (
    WatchlistEntry,
    WatchlistCategory,
    WatchlistPriority,
    WatchlistStatus,
)
from app.models.alert import VehicleAlert
from app.services import watchlist_service

router = APIRouter()


def _format_watchlist_response(entry: WatchlistEntry, db: Session) -> WatchlistEntryResponse:
    """Helper to enrich watchlist entry with alert count."""
    alert_count = (
        db.query(func.count(VehicleAlert.id))
        .filter(VehicleAlert.watchlist_entry_id == entry.id)
        .scalar()
        or 0
    )
    return WatchlistEntryResponse(
        id=entry.id,
        plate_text=entry.plate_text,
        normalized_plate_text=entry.normalized_plate_text,
        description=entry.description,
        category=entry.category,
        priority=entry.priority,
        status=entry.status,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        alert_count=alert_count,
    )


@router.get(
    "/",
    response_model=List[WatchlistEntryResponse],
    summary="List Watchlist Entries",
    description="Retrieves a list of watchlist entries with optional search, category, priority, and status filters.",
)
def list_entries(
    query: Optional[str] = Query(None, description="Search plate number or description"),
    category: Optional[WatchlistCategory] = Query(None, description="Filter by category"),
    priority: Optional[WatchlistPriority] = Query(None, description="Filter by priority"),
    status: Optional[WatchlistStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    entries = watchlist_service.list_watchlist_entries(
        db=db,
        query=query,
        category=category,
        priority=priority,
        status=status,
        skip=skip,
        limit=limit,
    )
    return [_format_watchlist_response(e, db) for e in entries]


@router.post(
    "/",
    response_model=WatchlistEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Watchlist Entry",
    description="Creates a new vehicle plate watchlist entry with normalized plate string.",
)
def create_entry(
    entry_in: WatchlistEntryCreate,
    db: Session = Depends(get_db),
):
    try:
        created = watchlist_service.create_watchlist_entry(db=db, entry_in=entry_in)
        return _format_watchlist_response(created, db)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create watchlist entry: {str(e)}",
        )


@router.get(
    "/{entry_id}",
    response_model=WatchlistEntryResponse,
    summary="Get Watchlist Entry",
    description="Retrieves a single watchlist entry by ID.",
)
def get_entry(
    entry_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    entry = watchlist_service.get_watchlist_entry_by_id(db=db, entry_id=entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist entry #{entry_id} not found.",
        )
    return _format_watchlist_response(entry, db)


@router.put(
    "/{entry_id}",
    response_model=WatchlistEntryResponse,
    summary="Update Watchlist Entry",
    description="Updates plate text, description, priority, category, or status of a watchlist entry.",
)
def update_entry(
    entry_id: int = Path(..., ge=1),
    entry_in: WatchlistEntryUpdate = ...,
    db: Session = Depends(get_db),
):
    try:
        updated = watchlist_service.update_watchlist_entry(
            db=db, entry_id=entry_id, entry_in=entry_in
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Watchlist entry #{entry_id} not found.",
            )
        return _format_watchlist_response(updated, db)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Watchlist Entry",
    description="Removes a watchlist entry from monitoring.",
)
def delete_entry(
    entry_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    success = watchlist_service.delete_watchlist_entry(db=db, entry_id=entry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist entry #{entry_id} not found.",
        )
    return None


@router.patch(
    "/{entry_id}/status",
    response_model=WatchlistEntryResponse,
    summary="Toggle Watchlist Entry Status",
    description="Sets a watchlist entry to ACTIVE or INACTIVE.",
)
def set_status(
    entry_id: int = Path(..., ge=1),
    status_in: WatchlistStatusUpdate = ...,
    db: Session = Depends(get_db),
):
    updated = watchlist_service.toggle_watchlist_status(
        db=db, entry_id=entry_id, new_status=status_in.status
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist entry #{entry_id} not found.",
        )
    return _format_watchlist_response(updated, db)
