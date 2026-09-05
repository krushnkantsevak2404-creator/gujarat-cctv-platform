"""
API v1 Router Configuration
Aggregates health, camera registry, recorded footage, and AI vehicle analytics endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, cameras, footage, analytics, anpr

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
