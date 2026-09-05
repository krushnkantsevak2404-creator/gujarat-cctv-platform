"""
ANPR & OCR Database Models
Stores localized license plate bounding boxes, OCR recognition results, 
Indian format validation, and deduplicated vehicle intelligence records.
"""

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base


class AnprStatus(str, enum.Enum):
    PLATE_DETECTED = "PLATE_DETECTED"          # Plate localized, OCR empty or unextracted
    OCR_SUCCESS = "OCR_SUCCESS"                # High/medium confidence OCR text
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"  # OCR text obtained but below high threshold
    OCR_UNREADABLE = "OCR_UNREADABLE"          # Blurry / occluded / unreadable plate


class PlateFormatStatus(str, enum.Enum):
    VALID_FORMAT = "VALID_FORMAT"        # Matches standard Indian plate syntax (e.g. GJ01AB1234, 22BH1234AA)
    POSSIBLE_FORMAT = "POSSIBLE_FORMAT"  # Partially conforming / clean alphanumeric pattern
    UNCERTAIN = "UNCERTAIN"              # Does not conform to standard plate patterns


class AnprDetection(Base):
    """
    ANPR Detection Model
    Represents an extracted and recognized vehicle license plate from recorded CCTV footage.
    """
    __tablename__ = "anpr_detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    footage_id = Column(
        Integer,
        ForeignKey("camera_footage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track_id = Column(Integer, nullable=True, index=True)  # Associated ByteTrack vehicle Track ID
    
    frame_number = Column(Integer, nullable=False, index=True)
    timestamp_seconds = Column(Float, nullable=False, index=True)
    vehicle_class = Column(String(50), nullable=False, index=True)  # car, motorcycle, bus, truck
    
    # OCR recognition strings
    plate_number_raw = Column(String(50), nullable=True)
    plate_number_normalized = Column(String(50), nullable=True, index=True)
    
    # Confidence metrics
    confidence = Column(Float, nullable=False, default=0.0)             # Overall combined score
    ocr_confidence = Column(Float, nullable=True)                        # Direct OCR engine confidence
    detection_confidence = Column(Float, nullable=True)                  # Vehicle / plate detection score
    
    # Classification statuses
    status = Column(
        SQLEnum(AnprStatus, native_enum=False),
        default=AnprStatus.PLATE_DETECTED,
        nullable=False,
        index=True,
    )
    format_status = Column(
        SQLEnum(PlateFormatStatus, native_enum=False),
        default=PlateFormatStatus.UNCERTAIN,
        nullable=False,
        index=True,
    )
    
    # Plate bounding box coordinates in video frame space
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    
    # Parent vehicle bounding box coordinates
    vehicle_x1 = Column(Float, nullable=True)
    vehicle_y1 = Column(Float, nullable=True)
    vehicle_x2 = Column(Float, nullable=True)
    vehicle_y2 = Column(Float, nullable=True)
    
    # Saved plate crop image path on disk
    plate_crop_path = Column(String(500), nullable=True)
    
    # Deduplication & aggregation flag
    is_consolidated = Column(Boolean, default=True, nullable=False, index=True)
    sighting_count = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to parent footage
    footage = relationship("CameraFootage", back_populates="anpr_detections")
