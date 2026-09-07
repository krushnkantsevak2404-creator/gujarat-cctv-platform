"""
Application Configuration Module
Loads settings from environment variables and .env file.
"""

from typing import List, Set, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

# Base directory for the backend & project
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Gujarat CCTV Intelligence Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # Server Settings
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    # Database Configuration (PostgreSQL + PostGIS)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "gujarat_cctv_db"
    DATABASE_URL: Union[str, None] = None

    # Storage Configuration
    STORAGE_DIR: str = str(PROJECT_ROOT / "storage")
    FOOTAGE_DIR_NAME: str = "footage"
    PROCESSED_DIR_NAME: str = "processed"
    PLATE_CROPS_DIR_NAME: str = "plate_crops"
    MODELS_DIR_NAME: str = "ai"
    MAX_VIDEO_UPLOAD_MB: int = 500
    
    ALLOWED_VIDEO_EXTENSIONS: Set[str] = {"mp4", "avi", "mov", "mkv", "webm"}
    ALLOWED_VIDEO_MIME_TYPES: Set[str] = {
        "video/mp4",
        "video/x-msvideo",
        "video/quicktime",
        "video/x-matroska",
        "video/webm",
        "application/octet-stream",
    }

    # AI & YOLO Vehicle Detection & Tracking Configuration
    YOLO_MODEL_NAME: str = "yolov8n.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.35
    DETECTION_FRAME_INTERVAL: int = 2
    TRACKER_TYPE: str = "bytetrack.yaml"
    TARGET_VEHICLE_CLASSES: Set[str] = {"car", "motorcycle", "bus", "truck"}

    # ANPR & OCR Configuration
    ANPR_OCR_CONFIDENCE_THRESHOLD: float = 0.30
    ANPR_FRAME_INTERVAL: int = 3
    ANPR_MIN_PLATE_WIDTH: int = 60
    ANPR_MIN_PLATE_HEIGHT: int = 18

    # Watchlist & Automatic Alerting Configuration
    WATCHLIST_MATCH_MIN_CONFIDENCE: float = 0.35
    WATCHLIST_ALERT_DEDUPLICATION_WINDOW_SECONDS: float = 5.0

    # Milestone 10: Authorized RTSP & Stream Adapter Configuration
    STREAM_CONNECT_TIMEOUT_SECONDS: int = 10
    STREAM_READ_TIMEOUT_SECONDS: int = 15
    STREAM_HEALTH_CHECK_INTERVAL_SECONDS: int = 30
    STREAM_MAX_ACTIVE_SESSIONS: int = 20
    FFMPEG_BIN_PATH: Union[str, None] = None
    MEDIAMTX_BIN_PATH: Union[str, None] = None
    RTSP_DEFAULT_USERNAME: Union[str, None] = None
    RTSP_DEFAULT_PASSWORD: Union[str, None] = None

    @property
    def footage_storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR) / self.FOOTAGE_DIR_NAME
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def processed_storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR) / self.PROCESSED_DIR_NAME
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def plate_crops_storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR) / self.PLATE_CROPS_DIR_NAME
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def models_storage_path(self) -> Path:
        p = PROJECT_ROOT / self.MODELS_DIR_NAME
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_VIDEO_UPLOAD_MB * 1024 * 1024

    @property
    def sync_database_url(self) -> str:
        """Construct database connection string if not explicitly set."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
# Ensure storage directories exist
settings.footage_storage_path.mkdir(parents=True, exist_ok=True)
settings.processed_storage_path.mkdir(parents=True, exist_ok=True)
settings.plate_crops_storage_path.mkdir(parents=True, exist_ok=True)
settings.models_storage_path.mkdir(parents=True, exist_ok=True)
