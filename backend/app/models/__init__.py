"""
Database Models Package
Exports all SQLAlchemy models for application tables.
"""

from app.models.camera import (
    Camera,
    CameraType,
    SourceType,
    ConnectivityType,
    CameraStatus,
)
from app.models.footage import (
    CameraFootage,
    FootageStatus,
)
from app.models.detection import (
    VehicleDetection,
    VehicleTrack,
    ProcessingJob,
    JobType,
    JobStatus,
)
from app.models.anpr import (
    AnprDetection,
    AnprStatus,
    PlateFormatStatus,
)
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

__all__ = [
    "Camera",
    "CameraType",
    "SourceType",
    "ConnectivityType",
    "CameraStatus",
    "CameraFootage",
    "FootageStatus",
    "VehicleDetection",
    "VehicleTrack",
    "ProcessingJob",
    "JobType",
    "JobStatus",
    "AnprDetection",
    "AnprStatus",
    "PlateFormatStatus",
    "WatchlistEntry",
    "WatchlistCategory",
    "WatchlistPriority",
    "WatchlistStatus",
    "VehicleAlert",
    "AlertType",
    "AlertSeverity",
    "AlertStatus",
]
