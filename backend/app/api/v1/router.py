"""
API v1 Router Configuration
Aggregates health, camera registry, recorded footage, and AI vehicle analytics endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, cameras, footage, analytics, anpr, watchlist, alerts, vehicle_search, viewer, streams

api_router = APIRouter()

# Health endpoints
api_router.include_router(health.router, tags=["Health"])

# Camera Registry endpoints
api_router.include_router(cameras.router, prefix="/cameras", tags=["CCTV Registry"])

# Footage endpoints
api_router.include_router(footage.router, tags=["Recorded Footage"])

# Milestone 4 & 5: AI Vehicle Detection & Tracking endpoints
api_router.include_router(analytics.router, tags=["AI Vehicle Detection & Tracking"])

# Milestone 6: ANPR & OCR endpoints
api_router.include_router(anpr.router, tags=["ANPR & OCR"])

# Milestone 7: Watchlist & Automatic Alerts endpoints
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist Management"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Vehicle Alerts"])

# Milestone 8: Vehicle Search & Movement History endpoints
api_router.include_router(vehicle_search.router, prefix="/vehicle-search", tags=["Vehicle Search & Detection Sequence"])

# Milestone 9: Unified Multi-Camera CCTV Viewer endpoints
api_router.include_router(viewer.router, prefix="/viewer", tags=["Unified CCTV Viewer"])

# Milestone 10: Authorized RTSP / Stream Adapter endpoints
api_router.include_router(streams.router, prefix="/streams", tags=["Authorized CCTV Stream Management"])

