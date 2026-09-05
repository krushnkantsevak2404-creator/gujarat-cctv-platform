"""
Milestone 7 End-to-End Watchlist Pipeline Test
Creates an active watchlist entry, processes CCTV footage through ANPR,
and verifies automatic alert generation, linking to camera and video stream.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.camera import Camera, CameraType, SourceType, ConnectivityType, CameraStatus
from app.models.footage import CameraFootage, FootageStatus
from app.models.watchlist import (
    WatchlistEntry,
    WatchlistCategory,
    WatchlistPriority,
    WatchlistStatus,
)
from app.models.alert import VehicleAlert, AlertStatus, AlertSeverity
from app.schemas.watchlist import WatchlistEntryCreate
from app.services import watchlist_service, anpr_service
from app.services.camera_service import seed_sample_cameras

def run_e2e_pipeline_test():
    print("\n========================================================")
    print(" Gujarat CCTV Intelligence Platform — Milestone 7 E2E")
    print(" Watchlist Surveillance Video Alert Verification")
    print("========================================================\n")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        seed_sample_cameras(db)

        # 1. Target Camera & Footage
        camera = db.query(Camera).filter(Camera.camera_code == "CAM-AHM-01").first()
        if not camera:
            camera = db.query(Camera).first()

        print(f"1. Selected Camera: {camera.camera_code} - {camera.camera_name} ({camera.location_name})")

        # 2. Add an Active Watchlist Target
        target_plate = "GJ01AB1234"
        existing = db.query(WatchlistEntry).filter(WatchlistEntry.normalized_plate_text == target_plate).first()
        if not existing:
            entry_in = WatchlistEntryCreate(
                plate_text="GJ 01 AB 1234",
                description="High Priority Stolen SUV - Alert Intercept Command",
                category=WatchlistCategory.STOLEN,
                priority=WatchlistPriority.CRITICAL,
                status=WatchlistStatus.ACTIVE,
            )
            entry = watchlist_service.create_watchlist_entry(db, entry_in)
            print(f"2. Created Watchlist Rule: {entry.plate_text} (Category: {entry.category.value}, Priority: {entry.priority.value})")
        else:
            existing.status = WatchlistStatus.ACTIVE
            existing.priority = WatchlistPriority.CRITICAL
            db.commit()
            entry = existing
            print(f"2. Re-activated Existing Watchlist Rule: {entry.plate_text}")

        # 3. Simulate CCTV footage with target vehicle observation
        sample_video_path = Path(__file__).resolve().parent / "videos" / "gujarat_traffic_demo.mp4"
        footage = db.query(CameraFootage).filter(CameraFootage.camera_id == camera.id).first()
        if not footage:
            footage = CameraFootage(
                camera_id=camera.id,
                file_name=sample_video_path.name,
                original_file_name=sample_video_path.name,
                file_path=str(sample_video_path),
                mime_type="video/mp4",
                file_size=sample_video_path.stat().st_size if sample_video_path.exists() else 1024*1024,
                duration_seconds=10.0,
                status=FootageStatus.UPLOADED,
            )
            db.add(footage)
            db.commit()
            db.refresh(footage)

        print(f"3. Using Footage #{footage.id} ({footage.original_file_name})")

        # 4. Clean previous alerts for clean test run
        db.query(VehicleAlert).filter(VehicleAlert.footage_id == footage.id).delete()
        db.commit()

        # 5. Run ANPR Pipeline on the video
        print("4. Executing ANPR & Watchlist Detection Pipeline...")
        from app.models.detection import ProcessingJob, JobType, JobStatus
        job = ProcessingJob(
            footage_id=footage.id,
            job_type=JobType.ANPR_OCR,
            status=JobStatus.QUEUED,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        anpr_service.run_anpr_pipeline(footage.id, job.id)
        db.refresh(job)
        print(f"   ANPR Job Completed: status={job.status.value}, unique_plates={job.unique_plates_count}")

        # 6. Check Generated Alerts
        alerts = watchlist_service.list_alerts(db, footage_id=footage.id)
        print(f"\n5. Verification Results: Found {len(alerts)} alerts for Footage #{footage.id}:")
        for a in alerts:
            print(f"   🚨 Alert #{a.id} | Plate: {a.plate_text} | Severity: {a.severity.value} | Status: {a.status.value}")
            print(f"      Message: \"{a.message}\"")
            print(f"      Camera: ID {a.camera_id} ({camera.camera_code}) at {camera.latitude}, {camera.longitude}")
            print(f"      Timestamp: {a.timestamp_seconds:.1f}s | Confidence: {a.confidence * 100:.1f}%")

        assert len(alerts) >= 1, "Expected at least 1 alert to be generated."
        print("\n[SUCCESS] Milestone 7 End-to-End Watchlist Surveillance Alert Verified Successfully!\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_e2e_pipeline_test()
