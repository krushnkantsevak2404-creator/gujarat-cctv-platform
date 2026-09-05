"""
Camera Model
Represents registered CCTV assets across Gujarat Police jurisdictions.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Text,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base


class CameraType(str, enum.Enum):
    FIXED = "FIXED"
    PTZ = "PTZ"
    DOME = "DOME"
    BULLET = "BULLET"
    OTHER = "OTHER"


class SourceType(str, enum.Enum):
    LIVE_CAMERA = "LIVE_CAMERA"
    RECORDED_FOOTAGE = "RECORDED_FOOTAGE"


class ConnectivityType(str, enum.Enum):
    RTSP = "RTSP"
    ONVIF = "ONVIF"
    VMS_API = "VMS_API"
    SDK = "SDK"
    FILE = "FILE"
    UNKNOWN = "UNKNOWN"


class CameraStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_name = Column(String(150), nullable=False, index=True)
    camera_code = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100), index=True, nullable=False)
    location_name = Column(String(255), nullable=False)
    
    # Coordinates: latitude (North/South), longitude (East/West)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    camera_type = Column(
        SQLEnum(CameraType, native_enum=False),
        default=CameraType.FIXED,
        nullable=False,
    )
    source_type = Column(
        SQLEnum(SourceType, native_enum=False),
        default=SourceType.LIVE_CAMERA,
        nullable=False,
    )
    connectivity_type = Column(
        SQLEnum(ConnectivityType, native_enum=False),
        default=ConnectivityType.UNKNOWN,
        nullable=False,
    )
    stream_url = Column(String(500), nullable=True)
    status = Column(
        SQLEnum(CameraStatus, native_enum=False),
        default=CameraStatus.UNKNOWN,
        nullable=False,
    )
    installation_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 1-to-many relationship with recorded CCTV footage
    footage = relationship(
        "CameraFootage",
        back_populates="camera",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
