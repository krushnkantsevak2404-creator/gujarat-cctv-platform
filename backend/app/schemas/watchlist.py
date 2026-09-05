"""
Watchlist Pydantic Schemas
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.watchlist import WatchlistCategory, WatchlistPriority, WatchlistStatus


class WatchlistEntryBase(BaseModel):
    plate_text: str = Field(..., min_length=2, max_length=50, description="Raw vehicle license plate string (e.g. GJ 01 AB 1234)")
    description: Optional[str] = Field(None, description="Reason for monitoring / case notes")
    category: WatchlistCategory = WatchlistCategory.GENERAL
    priority: WatchlistPriority = WatchlistPriority.HIGH
    status: WatchlistStatus = WatchlistStatus.ACTIVE


class WatchlistEntryCreate(WatchlistEntryBase):
    pass


class WatchlistEntryUpdate(BaseModel):
    plate_text: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    category: Optional[WatchlistCategory] = None
    priority: Optional[WatchlistPriority] = None
    status: Optional[WatchlistStatus] = None


class WatchlistStatusUpdate(BaseModel):
    status: WatchlistStatus


class WatchlistEntryResponse(WatchlistEntryBase):
    id: int
    normalized_plate_text: str
    created_at: datetime
    updated_at: datetime
    alert_count: int = 0

    class Config:
        from_attributes = True
