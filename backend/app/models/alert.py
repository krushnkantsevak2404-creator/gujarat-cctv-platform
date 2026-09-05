"""
Vehicle Alert Database Models
Stores real-time alerts generated when recognized CCTV vehicle plates match active watchlist entries.
"""

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base


class AlertType(str, enum.Enum):
    WATCHLIST_MATCH = "WATCHLIST_MATCH"


class AlertSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class VehicleAlert(Base):
    """
    Vehicle Alert Model
    Represents an alert event triggered by an ANPR observation matching a watchlist vehicle registration.
    """
    __tablename__ = "vehicle_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Associated watchlist entry (nullable on delete)
    watchlist_entry_id = Column(
        Integer,
        ForeignKey("watchlist_entries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Associated ANPR detection observation
    anpr_detection_id = Column(
        Integer,
        ForeignKey("anpr_detections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Context footage and camera
    footage_id = Column(
        Integer,
        ForeignKey("camera_footage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    camera_id = Column(
        Integer,
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    track_id = Column(Integer, nullable=True, index=True)
    
    # Plate observation snapshot
    plate_text = Column(String(50), nullable=False, index=True)
    vehicle_class = Column(String(50), nullable=False)
    timestamp_seconds = Column(Float, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # Alert classification & workflow
    alert_type = Column(
        SQLEnum(AlertType, native_enum=False),
        default=AlertType.WATCHLIST_MATCH,
        nullable=False,
        index=True,
    )
    severity = Column(
        SQLEnum(AlertSeverity, native_enum=False),
        default=AlertSeverity.HIGH,
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(AlertStatus, native_enum=False),
        default=AlertStatus.NEW,
        nullable=False,
        index=True,
    )
    
    # Machine-generated alert description
    message = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    watchlist_entry = relationship("WatchlistEntry", back_populates="alerts")
    anpr_detection = relationship("AnprDetection")
    footage = relationship("CameraFootage")
    camera = relationship("Camera")
