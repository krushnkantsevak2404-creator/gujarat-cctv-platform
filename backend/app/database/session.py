"""
Database Session Management
Configures SQLAlchemy engine, session maker, and dependency for PostgreSQL + PostGIS.
"""

from typing import Generator
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

# SQLAlchemy database engine
# pool_pre_ping=True tests connections for liveness upon checkout from the pool
engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# Session local factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Closes the session after the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> dict:
    """
    Check if PostgreSQL and PostGIS extension are reachable.
    Returns status dictionary for diagnostics and health monitoring.
    """
    try:
        with engine.connect() as connection:
            # Check basic connection
            result = connection.execute(text("SELECT 1")).scalar()
            
            # Check PostGIS extension
            postgis_version = None
            try:
                postgis_res = connection.execute(text("SELECT PostGIS_Version()")).scalar()
                postgis_version = str(postgis_res)
            except Exception:
                postgis_version = "PostGIS extension not installed yet"

            return {
                "connected": True,
                "database": settings.POSTGRES_DB,
                "host": settings.POSTGRES_SERVER,
                "port": settings.POSTGRES_PORT,
                "postgis_version": postgis_version,
            }
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return {
            "connected": False,
            "error": str(e),
            "host": settings.POSTGRES_SERVER,
            "port": settings.POSTGRES_PORT,
        }
