"""
Camera Footage Model
Represents recorded CCTV video clips associated with registered cameras.
"""

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base


class FootageStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CameraFootage(Base):
    __tablename__ = "camera_footage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(
        Integer,
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Secure storage file details
    file_name = Column(String(255), nullable=False)  # Safe generated UUID filename
    original_file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative or absolute storage path
    file_size = Column(BigInteger, nullable=False)  # File size in bytes
    mime_type = Column(String(100), nullable=False)
    
    # Video metadata
    duration_seconds = Column(Float, nullable=True)
    video_width = Column(Integer, nullable=True)
    video_height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    frame_count = Column(Integer, nullable=True)
    
    # Recording time interval
    recording_start_time = Column(DateTime(timezone=True), nullable=True)
    recording_end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Lifecycle status
    status = Column(
        SQLEnum(FootageStatus, native_enum=False),
        default=FootageStatus.UPLOADED,
        nullable=False,
    )
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to parent camera
    camera = relationship("Camera", back_populates="footage")

    # Milestone 4 & 5: Relationships to vehicle detections, tracks & processing jobs
    detections = relationship(
        "VehicleDetection",
        back_populates="footage",
        cascade="all, delete-orphan",
        lazy="select",
    )
    tracks = relationship(
        "VehicleTrack",
        back_populates="footage",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="VehicleTrack.track_id",
    )
    anpr_detections = relationship(
        "AnprDetection",
        back_populates="footage",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="desc(AnprDetection.confidence)",
    )
    jobs = relationship(
        "ProcessingJob",
        back_populates="footage",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(ProcessingJob.created_at)",
    )
