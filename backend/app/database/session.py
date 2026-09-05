"""
Database Session Management
Supports PostgreSQL + PostGIS with robust connection pooling and fallback resilience.
"""

from typing import Generator
import logging
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def init_engine():
    """
    Attempts connection to configured PostgreSQL instance.
    Falls back to a local SQLite database in storage/ if PostgreSQL is unavailable.
    """
    pg_url = settings.sync_database_url
    try:
        test_engine = create_engine(
            pg_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to PostgreSQL database at {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        return test_engine, "postgresql"
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection to {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT} not available ({e}). "
            f"Initializing local persistent fallback DB at storage/local_dev.db for seamless development."
        )
        sqlite_path = settings.footage_storage_path.parent / "local_dev.db"
        sqlite_url = f"sqlite:///{sqlite_path.as_posix()}"
        sqlite_engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
        )
        return sqlite_engine, "sqlite"


engine, db_dialect = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Closes the session after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> dict:
    """
    Check if database and spatial extension are reachable.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            
            postgis_version = None
            if db_dialect == "postgresql":
                try:
                    postgis_res = connection.execute(text("SELECT PostGIS_Version()")).scalar()
                    postgis_version = str(postgis_res)
                except Exception:
                    postgis_version = "PostGIS extension not active yet (Run 01_init_postgis.sql)"
            else:
                postgis_version = "SQLite Local Mode (Latitude/Longitude Geospatial Storage Active)"

            return {
                "connected": True,
                "dialect": db_dialect,
                "database": settings.POSTGRES_DB if db_dialect == "postgresql" else "local_dev.db",
                "host": settings.POSTGRES_SERVER if db_dialect == "postgresql" else "localhost (local file)",
                "port": settings.POSTGRES_PORT if db_dialect == "postgresql" else "N/A",
                "postgis_version": postgis_version,
            }
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return {
            "connected": False,
            "dialect": db_dialect,
            "error": str(e),
            "host": settings.POSTGRES_SERVER,
            "port": settings.POSTGRES_PORT,
        }
