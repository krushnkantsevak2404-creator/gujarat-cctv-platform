"""
Watchlist Database Models
Stores configured vehicle registration plate watchlists, categories, priorities, and statuses.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base


class WatchlistCategory(str, enum.Enum):
    GENERAL = "GENERAL"
    STOLEN = "STOLEN"
    SUSPECT = "SUSPECT"
    WARRANT = "WARRANT"
    RESTRICTED = "RESTRICTED"
    EXPIRED = "EXPIRED"
    INVESTIGATION = "INVESTIGATION"
    DEMO = "DEMO"
    OTHER = "OTHER"


class WatchlistPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WatchlistStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class WatchlistEntry(Base):
    """
    Watchlist Entry Model
    Represents an authorized vehicle registration number monitored for real-time alerts.
    """
    __tablename__ = "watchlist_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Raw input plate string (e.g. "GJ 01 AB 1234")
    plate_text = Column(String(50), nullable=False)
    
    # Normalized plate string for fast indexed matching (e.g. "GJ01AB1234")
    normalized_plate_text = Column(String(50), nullable=False, index=True)
    
    description = Column(Text, nullable=True)
    
    category = Column(
        SQLEnum(WatchlistCategory, native_enum=False),
        default=WatchlistCategory.GENERAL,
        nullable=False,
        index=True,
    )
    priority = Column(
        SQLEnum(WatchlistPriority, native_enum=False),
        default=WatchlistPriority.HIGH,
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(WatchlistStatus, native_enum=False),
        default=WatchlistStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to generated vehicle alerts
    alerts = relationship(
        "VehicleAlert",
        back_populates="watchlist_entry",
        cascade="all, delete-orphan",
        lazy="select",
    )
