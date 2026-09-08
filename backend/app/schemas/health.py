"""
Health Check & Operational Dashboard Schemas
Pydantic schemas for camera health monitoring, infrastructure metrics, and system diagnostics.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Current service health status")
    service: str = Field(
        default="Gujarat CCTV Intelligence Platform",
        description="Name of the service",
    )
    version: Optional[str] = Field(default="1.0.0", description="API version")
    database: Optional[Dict[str, Any]] = Field(
        default=None, description="Database connection status diagnostics"
    )


class HealthSummaryCounts(BaseModel):
    total: int = Field(default=0, description="Total registered cameras")
    online: int = Field(default=0, description="Cameras with ONLINE status")
    offline: int = Field(default=0, description="Cameras with OFFLINE status")
    maintenance: int = Field(default=0, description="Cameras under MAINTENANCE")
    unknown: int = Field(default=0, description="Cameras with UNKNOWN status")
    live_sources: int = Field(default=0, description="Cameras configured as LIVE_CAMERA")
    recorded_sources: int = Field(default=0, description="Cameras configured as RECORDED_FOOTAGE")
    connected_streams: int = Field(default=0, description="Active connected live stream sessions")
    disconnected_streams: int = Field(default=0, description="Live streams disconnected/standby")
    not_configured_streams: int = Field(default=0, description="Live cameras without configured stream URL")
    error_streams: int = Field(default=0, description="Live cameras with stream errors")
    active_alerts: int = Field(default=0, description="Count of active NEW/ACKNOWLEDGED watchlist alerts")
    total_observations: int = Field(default=0, description="Total recognized vehicle ANPR observations")


class CameraHealthItem(BaseModel):
    camera_id: int
    camera_code: str
    camera_name: str
    department: str
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_valid_coordinates: bool = False
    source_type: str
    connectivity_type: str
    status: str  # Permanent Registration Status: ONLINE, OFFLINE, MAINTENANCE, UNKNOWN
    stream_status: str  # Live Stream Session Status: CONNECTED, DISCONNECTED, NOT_CONFIGURED, ERROR
    footage_count: int = 0
    health_summary: str
    last_checked: str
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class DepartmentSummaryItem(BaseModel):
    department: str
    total_cameras: int = 0
    online_cameras: int = 0
    offline_cameras: int = 0
    live_cameras: int = 0
    recorded_cameras: int = 0
    active_alerts_count: int = 0


class VehicleAnalyticsSummary(BaseModel):
    total_anpr_observations: int = 0
    total_vehicles_detected: int = 0
    total_tracked_vehicles: int = 0
    total_watchlist_matches: int = 0
    unique_plates_count: int = 0


class RecentAlertItem(BaseModel):
    alert_id: int
    plate_text: str
    vehicle_class: str
    severity: str
    status: str
    message: str
    camera_id: int
    camera_code: str
    camera_name: str
    department: str
    location_name: str
    created_at: str
    timestamp_formatted: str


class ServiceHealthItem(BaseModel):
    service_name: str
    status: str  # HEALTHY, DEGRADED, NOT_CONFIGURED, ERROR, READY
    details: str
    latency_ms: Optional[float] = None


class SystemHealthResponse(BaseModel):
    status: str
    timestamp: str
    backend_api: ServiceHealthItem
    database: ServiceHealthItem
    gis: ServiceHealthItem
    ai_processing: ServiceHealthItem
    stream_service: ServiceHealthItem


class CameraHealthOverviewResponse(BaseModel):
    summary: HealthSummaryCounts
    departments: List[DepartmentSummaryItem]
    vehicle_analytics: VehicleAnalyticsSummary
    recent_alerts: List[RecentAlertItem]
    cameras: List[CameraHealthItem]
    system_health: SystemHealthResponse
    last_updated: str
