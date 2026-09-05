"""
Pydantic Schemas Package
Exports all schemas for validation and API documentation.
"""

from app.schemas.health import HealthResponse
from app.schemas.camera import (
    CameraBase,
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraStatsResponse,
)
from app.schemas.footage import (
    FootageBase,
    FootageResponse,
)
from app.schemas.detection import (
    DetectionResponse,
    ProcessingJobResponse,
    DetectionSummaryResponse,
    VehicleTrackResponse,
    VehicleTrackDetailResponse,
    TrackSummaryResponse,
)
from app.schemas.anpr import (
    AnprDetectionResponse,
    AnprSummaryResponse,
    AnprSearchResultItem,
    AnprSearchResponse,
)

__all__ = [
    "HealthResponse",
    "CameraBase",
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraStatsResponse",
    "FootageBase",
    "FootageResponse",
    "DetectionResponse",
    "ProcessingJobResponse",
    "DetectionSummaryResponse",
    "VehicleTrackResponse",
    "VehicleTrackDetailResponse",
    "TrackSummaryResponse",
    "AnprDetectionResponse",
    "AnprSummaryResponse",
    "AnprSearchResultItem",
    "AnprSearchResponse",
]
