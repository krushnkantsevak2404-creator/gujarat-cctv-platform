"""
Gujarat CCTV Intelligence Platform - Backend Main Application
Gujarat Police Innovation Hackathon 2026
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Gujarat CCTV Intelligence Platform - Model 2 (Unified Viewing & Selective Analytics)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS middleware to allow React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if isinstance(settings.BACKEND_CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
# Mounts at /api (so /api/health works)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also mount at root for direct /health access
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming developers to the platform."""
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
