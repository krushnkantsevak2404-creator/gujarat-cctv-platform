"""
Database Base Model
Declarative Base for all future SQLAlchemy models (Cameras, Jurisdictions, Analytics, etc.)
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
