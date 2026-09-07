"""
Gujarat CCTV Intelligence Platform - Backend Main Application
Gujarat Police Innovation Hackathon 2026
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.api.v1.router import api_router
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.services.camera_service import seed_sample_cameras

from app.streams import stream_manager

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Creates database tables, applies incremental schema migrations, and seeds sample camera assets.
    """
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        
        # Incremental schema check / column migrations for local SQLite / Postgres
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check vehicle_detections.track_id
            try:
                conn.execute(text("ALTER TABLE vehicle_detections ADD COLUMN track_id INTEGER"))
                conn.commit()
            except Exception:
                pass

            # Check processing_jobs columns
            for col, col_type in [
                ("total_tracks", "INTEGER DEFAULT 0"),
                ("car_tracks", "INTEGER DEFAULT 0"),
                ("motorcycle_tracks", "INTEGER DEFAULT 0"),
                ("bus_tracks", "INTEGER DEFAULT 0"),
                ("truck_tracks", "INTEGER DEFAULT 0"),
                ("total_plates_detected", "INTEGER DEFAULT 0"),
                ("successful_ocr_count", "INTEGER DEFAULT 0"),
                ("valid_format_count", "INTEGER DEFAULT 0"),
                ("unique_plates_count", "INTEGER DEFAULT 0"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE processing_jobs ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass

        logger.info("Database tables initialized successfully.")
        
        # Seed initial sample Gujarat cameras if empty
        db = SessionLocal()
        try:
            seed_sample_cameras(db)
            logger.info("Sample Gujarat Police camera registry verified.")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")

    yield
    logger.info("Backend service shutting down - Releasing all active stream sessions and media relays.")
    try:
        stream_manager.shutdown_all()
    except Exception as e:
        logger.error(f"Error during stream manager shutdown: {e}")


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Gujarat CCTV Intelligence Platform - Model 2 (Unified Viewing & Selective Analytics)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
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
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming developers to the platform."""
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "cameras_endpoint": f"{settings.API_V1_STR}/cameras",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
