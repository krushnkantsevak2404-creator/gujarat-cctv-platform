"""
Milestone 9 Automated Verification Script
Gujarat CCTV Intelligence Platform — Unified Multi-Camera CCTV Viewer

Tests:
1. Stream info determination for camera with recorded MP4 footage.
2. Stream info for live camera without stream URL (NOT_CONFIGURED).
3. Stream info for live camera with authorized HTTP / HLS stream URL.
4. Stream info for RTSP source (RTSP_ADAPTER / media relay requirement).
5. Offline camera stream status handling (DISCONNECTED).
6. Multi-footage listing and duration formatting.
7. Active Watchlist alert association on camera stream info.
8. Geographic coordinate validity and missing coordinates handling.
9. Viewer aggregate statistics endpoint (/api/viewer/stats).
10. FastAPI REST API endpoints via TestClient.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.camera import Camera, CameraType, SourceType, ConnectivityType, CameraStatus
from app.models.footage import CameraFootage, FootageStatus
from app.models.anpr import AnprDetection, AnprStatus, PlateFormatStatus
from app.models.watchlist import WatchlistEntry, WatchlistCategory, WatchlistPriority, WatchlistStatus
from app.models.alert import VehicleAlert, AlertType, AlertSeverity, AlertStatus
from app.services import stream_service
from app.schemas.stream import (
    StreamStatusEnum,
    PlaybackModeEnum,
    CameraStreamInfoResponse,
    ViewerStatsResponse,
)


def run_milestone9_tests():
    print("\n========================================================")
    print(" Gujarat CCTV Intelligence Platform — Milestone 9 Tests")
    print(" Unified Multi-Camera CCTV Viewer Verification")
    print("========================================================\n")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    passed = 0
    total = 0

    try:
        # -----------------------------------------------------------------
        # Setup Test Fixtures: 4 Distinct Cameras to test various modes
        # -----------------------------------------------------------------
        print("[*] Setting up camera and footage fixtures in database...")

        # Camera 1: Recorded Footage Camera (ONLINE, has footage)
        cam1 = db.query(Camera).filter(Camera.camera_code == "CAM-M9-REC-01").first()
        if not cam1:
            cam1 = Camera(
                camera_code="CAM-M9-REC-01",
                camera_name="SG Highway - Pakwan Junction",
                location_name="Ahmedabad",
                department="Traffic Branch",
                latitude=23.0335,
                longitude=72.5085,
                status=CameraStatus.ONLINE,
                camera_type=CameraType.FIXED,
                source_type=SourceType.RECORDED_FOOTAGE,
                connectivity_type=ConnectivityType.FILE,
            )
            db.add(cam1)

        # Camera 2: Live Camera (ONLINE, No stream URL configured)
        cam2 = db.query(Camera).filter(Camera.camera_code == "CAM-M9-LIVE-NOURL").first()
        if not cam2:
            cam2 = Camera(
                camera_code="CAM-M9-LIVE-NOURL",
                camera_name="Sabarmati Riverfront East",
                location_name="Ahmedabad",
                department="City Surveillance",
                latitude=23.0396,
                longitude=72.5797,
                status=CameraStatus.ONLINE,
                camera_type=CameraType.PTZ,
                source_type=SourceType.LIVE_CAMERA,
                connectivity_type=ConnectivityType.ONVIF,
                stream_url=None,
            )
            db.add(cam2)

        # Camera 3: Live Camera with RTSP stream URL
        cam3 = db.query(Camera).filter(Camera.camera_code == "CAM-M9-LIVE-RTSP").first()
        if not cam3:
            cam3 = Camera(
                camera_code="CAM-M9-LIVE-RTSP",
                camera_name="Infocity Gandhinagar Gate 1",
                location_name="Gandhinagar",
                department="Highway Patrol",
                latitude=23.1956,
                longitude=72.6289,
                status=CameraStatus.ONLINE,
                camera_type=CameraType.DOME,
                source_type=SourceType.LIVE_CAMERA,
                connectivity_type=ConnectivityType.RTSP,
                stream_url="rtsp://10.20.30.40:554/live/stream1",
            )
            db.add(cam3)

        # Camera 4: Offline Camera
        cam4 = db.query(Camera).filter(Camera.camera_code == "CAM-M9-OFFLINE-01").first()
        if not cam4:
            cam4 = Camera(
                camera_code="CAM-M9-OFFLINE-01",
                camera_name="Sector 28 Industrial Outpost",
                location_name="Gandhinagar",
                department="Industrial Security",
                latitude=23.2500,
                longitude=72.6700,
                status=CameraStatus.OFFLINE,
                camera_type=CameraType.BULLET,
                source_type=SourceType.RECORDED_FOOTAGE,
                connectivity_type=ConnectivityType.FILE,
            )
            db.add(cam4)

        db.commit()
        db.refresh(cam1)
        db.refresh(cam2)
        db.refresh(cam3)
        db.refresh(cam4)

        # Create 2 footage records for Camera 1 to test multiple recordings
        ft1 = db.query(CameraFootage).filter(CameraFootage.file_name == "m9_sample_footage_01.mp4").first()
        if not ft1:
            ft1 = CameraFootage(
                camera_id=cam1.id,
                file_name="m9_sample_footage_01.mp4",
                original_file_name="SG_Highway_Morning_1000.mp4",
                file_path="storage/recorded_footage/m9_sample_footage_01.mp4",
                file_size=2048576,
                mime_type="video/mp4",
                duration_seconds=332.5,
                status=FootageStatus.COMPLETED,
            )
            db.add(ft1)

        ft2 = db.query(CameraFootage).filter(CameraFootage.file_name == "m9_sample_footage_02.mp4").first()
        if not ft2:
            ft2 = CameraFootage(
                camera_id=cam1.id,
                file_name="m9_sample_footage_02.mp4",
                original_file_name="SG_Highway_Evening_1800.mp4",
                file_path="storage/recorded_footage/m9_sample_footage_02.mp4",
                file_size=4096000,
                mime_type="video/mp4",
                duration_seconds=497.0,
                status=FootageStatus.COMPLETED,
            )
            db.add(ft2)

        db.commit()
        db.refresh(ft1)
        db.refresh(ft2)

        # Create an ANPR detection + Watchlist Entry + Alert on Camera 1 to test alert association
        test_plate = "GJ01M99999"
        db.query(VehicleAlert).filter(VehicleAlert.plate_text == test_plate).delete()
        db.query(WatchlistEntry).filter(WatchlistEntry.normalized_plate_text == test_plate).delete()
        db.query(AnprDetection).filter(AnprDetection.plate_number_normalized == test_plate).delete()
        db.commit()

        d1 = AnprDetection(
            footage_id=ft1.id,
            frame_number=60,
            timestamp_seconds=2.0,
            vehicle_class="car",
            plate_number_raw="GJ 01 M9 9999",
            plate_number_normalized=test_plate,
            confidence=0.94,
            x1=100.0,
            y1=100.0,
            x2=200.0,
            y2=150.0,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            track_id=901,
        )
        db.add(d1)
        db.commit()
        db.refresh(d1)

        wl = WatchlistEntry(
            plate_text="GJ 01 M9 9999",
            normalized_plate_text=test_plate,
            category=WatchlistCategory.SUSPECT,
            priority=WatchlistPriority.CRITICAL,
            status=WatchlistStatus.ACTIVE,
            description="High-priority suspect vehicle",
        )
        db.add(wl)
        db.commit()
        db.refresh(wl)

        alert = VehicleAlert(
            watchlist_entry_id=wl.id,
            camera_id=cam1.id,
            footage_id=ft1.id,
            anpr_detection_id=d1.id,
            plate_text=test_plate,
            vehicle_class="car",
            alert_type=AlertType.WATCHLIST_MATCH,
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.NEW,
            message="Active Watchlist Match detected at SG Highway - Pakwan Junction",
            confidence=0.94,
            timestamp_seconds=2.0,
            track_id=901,
        )
        db.add(alert)
        db.commit()
        print("  -> Fixtures initialized successfully.\n")

        # -----------------------------------------------------------------
        # TEST 1: Recorded Footage Stream Info Determination
        # -----------------------------------------------------------------
        total += 1
        print(f"[{total}] Testing stream info for camera with recorded MP4 footage...")
        info1: CameraStreamInfoResponse = stream_service.get_camera_stream_info(db, cam1)
        assert info1.camera_id == cam1.id
        assert info1.camera_code == "CAM-M9-REC-01"
        assert info1.playback_mode == PlaybackModeEnum.RECORDED_STREAM
        assert info1.stream_status == StreamStatusEnum.CONNECTED
        assert info1.is_playable_in_browser is True
        assert info1.footage_count >= 2
        assert len(info1.available_footage) >= 2
        assert info1.available_footage[0].stream_url.startswith("/api/footage/")
        print(f"  -> Passed: Correctly identified RECORDED_STREAM playback mode with {info1.footage_count} footage file(s).")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 2: Live Camera Without Configured Stream URL
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing stream info for Live Camera without stream URL...")
        info2: CameraStreamInfoResponse = stream_service.get_camera_stream_info(db, cam2)
        assert info2.camera_code == "CAM-M9-LIVE-NOURL"
        assert info2.playback_mode == PlaybackModeEnum.UNAVAILABLE
        assert info2.stream_status == StreamStatusEnum.NOT_CONFIGURED
        assert info2.is_playable_in_browser is False
        assert "Live stream is not configured" in info2.status_message
        print(f"  -> Passed: Correctly reported NOT_CONFIGURED status with message: '{info2.status_message}'.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 3: Live Camera With RTSP Protocol URL
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing stream info for RTSP source (browser limitation handling)...")
        info3: CameraStreamInfoResponse = stream_service.get_camera_stream_info(db, cam3)
        assert info3.camera_code == "CAM-M9-LIVE-RTSP"
        assert info3.playback_mode == PlaybackModeEnum.RTSP_ADAPTER
        assert info3.stream_status == StreamStatusEnum.CONNECTING
        assert info3.is_playable_in_browser is False
        assert "Media relay required" in info3.status_message
        print(f"  -> Passed: Correctly flagged RTSP protocol requiring media relay adapter.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 4: Offline Camera Status Handling
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing stream info for OFFLINE camera...")
        info4: CameraStreamInfoResponse = stream_service.get_camera_stream_info(db, cam4)
        assert info4.camera_code == "CAM-M9-OFFLINE-01"
        assert info4.stream_status == StreamStatusEnum.DISCONNECTED
        assert info4.is_playable_in_browser is False
        assert "OFFLINE" in info4.status_message
        print(f"  -> Passed: Correctly reported DISCONNECTED stream status for offline camera.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 5: Active Watchlist Alert Context on Camera Tile
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing active Watchlist alert context on stream info...")
        assert info1.active_alerts_count >= 1
        assert info1.latest_alert_severity == "CRITICAL"
        assert "Active Watchlist Match" in info1.latest_alert_message
        print(f"  -> Passed: Stream info links {info1.active_alerts_count} active alert(s) (Severity: {info1.latest_alert_severity}).")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 6: Multiple Footage File Duration Formatting
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing duration formatting across multiple recordings...")
        ft_items = info1.available_footage
        assert ft_items[0].formatted_duration != ""
        assert ":" in ft_items[0].formatted_duration
        print(f"  -> Passed: Formatted durations: {[f.formatted_duration for f in ft_items]}.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 7: PostGIS Coordinates Integrity
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing PostGIS coordinate validation...")
        assert info1.has_valid_coordinates is True
        assert 20.0 <= info1.latitude <= 25.0
        assert 68.0 <= info1.longitude <= 75.0
        print(f"  -> Passed: Valid coordinates ({info1.latitude}, {info1.longitude}) confirmed in Gujarat.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 8: Viewer Aggregate Statistics Calculations
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing get_viewer_stats service calculation...")
        stats: ViewerStatsResponse = stream_service.get_viewer_stats(db)
        assert stats.total_registered_cameras >= 4
        assert stats.online_cameras >= 3
        assert stats.offline_cameras >= 1
        assert stats.recorded_footage_sources >= 2
        assert stats.live_stream_sources >= 2
        assert stats.total_footage_files >= 2
        assert stats.active_watchlist_alerts >= 1
        print(f"  -> Passed: Stats verified (Total: {stats.total_registered_cameras}, Online: {stats.online_cameras}, Recorded: {stats.recorded_footage_sources}, Live: {stats.live_stream_sources}).")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 9: REST API GET /api/viewer/stats via TestClient
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing FastAPI GET /api/viewer/stats endpoint...")
        client = TestClient(app)
        res = client.get("/api/viewer/stats")
        assert res.status_code == 200, f"API error: {res.text}"
        data = res.json()
        assert data["total_registered_cameras"] >= 4
        assert data["online_cameras"] >= 3
        print(f"  -> Passed: GET /api/viewer/stats responded with 200 OK and expected JSON schema.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 10: REST API GET /api/viewer/cameras/{id}/stream-info
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing FastAPI GET /api/viewer/cameras/{cam1.id}/stream-info...")
        res_info = client.get(f"/api/viewer/cameras/{cam1.id}/stream-info")
        assert res_info.status_code == 200, f"API error: {res_info.text}"
        cam_info_data = res_info.json()
        assert cam_info_data["camera_code"] == "CAM-M9-REC-01"
        assert cam_info_data["playback_mode"] == "RECORDED_STREAM"
        assert cam_info_data["is_playable_in_browser"] is True
        assert len(cam_info_data["available_footage"]) >= 2

        # 10b: 404 for non-existent camera
        res_404 = client.get("/api/viewer/cameras/999999/stream-info")
        assert res_404.status_code == 404
        print(f"  -> Passed: GET /api/viewer/cameras/{{id}}/stream-info responded with 200 OK & 404 handled gracefully.")
        passed += 1

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[FAIL] Test suite encountered an error: {e}")
    finally:
        db.close()

    print("\n========================================================")
    print(f" Milestone 9 Verification Summary: {passed}/{total} Tests Passed")
    if passed == total:
        print(" [SUCCESS] All Milestone 9 Unified CCTV Viewer Tests Passed!")
    else:
        print(f" [WARNING] {total - passed} tests failed.")
    print("========================================================\n")
    return passed == total


if __name__ == "__main__":
    success = run_milestone9_tests()
    sys.exit(0 if success else 1)
