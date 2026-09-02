"""
Health Check Schemas
Pydantic schemas for API health and diagnostics responses.
"""

from typing import Optional, Dict, Any
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

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "service": "Gujarat CCTV Intelligence Platform",
                "version": "1.0.0",
                "database": {
                    "connected": False,
                    "host": "localhost",
                    "port": 5432
                }
            }
        }
