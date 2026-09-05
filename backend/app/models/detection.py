"""
Vehicle Detection & Processing Job Models
Stores frame-by-frame YOLO detections and async processing job metadata.
"""

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base


class JobType(str, enum.Enum):
    VEHICLE_DETECTION = "VEHICLE_DETECTION"
    VEHICLE_TRACKING = "VEHICLE_TRACKING"
    ANPR_OCR = "ANPR_OCR"


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    footage_id = Column(
        Integer,
        ForeignKey("camera_footage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    frame_number = Column(Integer, nullable=False, index=True)
    timestamp_seconds = Column(Float, nullable=False, index=True)
    vehicle_class = Column(String(50), nullable=False, index=True)  # car, motorcycle, bus, truck
    confidence = Column(Float, nullable=False)
    track_id = Column(Integer, nullable=True, index=True)  # Temporary Track ID within footage
    
    # Bounding box coordinates (pixel coordinates)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to parent footage
    footage = relationship("CameraFootage", back_populates="detections")


class VehicleTrack(Base):
    """
    Vehicle Track Summary Model
    Represents an identified physical vehicle tracked across consecutive frames in a specific video footage.
    """
    __tablename__ = "vehicle_tracks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    footage_id = Column(
        Integer,
        ForeignKey("camera_footage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    track_id = Column(Integer, nullable=False, index=True)  # Track ID assigned by ByteTrack
    vehicle_class = Column(String(50), nullable=False, index=True)  # car, motorcycle, bus, truck
    
    first_seen_seconds = Column(Float, nullable=False)
    last_seen_seconds = Column(Float, nullable=False)
    first_seen_frame = Column(Integer, nullable=False)
    last_seen_frame = Column(Integer, nullable=False)
    detection_count = Column(Integer, default=1, nullable=False)
    avg_confidence = Column(Float, nullable=False)
    
    # Path to representative vehicle image crop
    best_crop_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to parent footage
    footage = relationship("CameraFootage", back_populates="tracks")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    footage_id = Column(
        Integer,
        ForeignKey("camera_footage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    job_type = Column(
        SQLEnum(JobType, native_enum=False),
        default=JobType.VEHICLE_TRACKING,
        nullable=False,
    )
    status = Column(
        SQLEnum(JobStatus, native_enum=False),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )
    progress = Column(Integer, default=0, nullable=False)  # 0 to 100
    device = Column(String(20), default="CPU", nullable=False)  # CPU or GPU
    
    total_frames = Column(Integer, nullable=True)
    processed_frames = Column(Integer, nullable=True)
    
    # Summary counters
    total_detections = Column(Integer, default=0, nullable=False)
    cars_count = Column(Integer, default=0, nullable=False)
    motorcycles_count = Column(Integer, default=0, nullable=False)
    buses_count = Column(Integer, default=0, nullable=False)
    trucks_count = Column(Integer, default=0, nullable=False)

    # Tracking counters
    total_tracks = Column(Integer, default=0, nullable=False)
    car_tracks = Column(Integer, default=0, nullable=False)
    motorcycle_tracks = Column(Integer, default=0, nullable=False)
    bus_tracks = Column(Integer, default=0, nullable=False)
    truck_tracks = Column(Integer, default=0, nullable=False)
    
    # ANPR counters
    total_plates_detected = Column(Integer, default=0, nullable=False)
    successful_ocr_count = Column(Integer, default=0, nullable=False)
    valid_format_count = Column(Integer, default=0, nullable=False)
    unique_plates_count = Column(Integer, default=0, nullable=False)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to parent footage
    footage = relationship("CameraFootage", back_populates="jobs")
