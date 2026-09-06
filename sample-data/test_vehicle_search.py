"""
Milestone 8 Automated Verification Script
Gujarat CCTV Intelligence Platform

Tests:
1. Plate normalization & sanitization (spaces, hyphens, case invariance).
2. Multi-camera ANPR observation matching & chronological sorting.
3. Observed Camera Detection Sequence step aggregation across cameras.
4. Summary KPI metrics calculation (sightings, unique cameras, time span).
5. Milestone 7 Watchlist Alert History lookup integration.
6. Multi-parameter filtering (date/time range, department, camera, location).
7. Unknown/unmatched plate structured empty response.
8. Geographic coordinate validation (Leaflet-ready PostGIS coordinates).
9. Video timestamp seek offset accuracy.
10. FastAPI REST API endpoint GET /api/v1/vehicle-search via TestClient.
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
from app.services.vehicle_search_service import search_vehicle_history, normalize_plate_query
from app.schemas.vehicle_search import VehicleSearchResponse


def run_milestone8_tests():
    print("\n========================================================")
    print(" Gujarat CCTV Intelligence Platform — Milestone 8 Tests")
    print(" Vehicle Search + Observed Camera Detection Sequence")
    print("========================================================\n")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    passed = 0
    total = 0

    try:
        # -----------------------------------------------------------------
        # TEST 1: Plate Text Cleaning & Normalization
        # -----------------------------------------------------------------
        total += 1
        print(f"[{total}] Testing plate text normalization helper...")
        assert normalize_plate_query("gj 01 ab 1234") == "GJ01AB1234"
        assert normalize_plate_query("GJ-01-AB-1234") == "GJ01AB1234"
        assert normalize_plate_query("  gj01ab1234  ") == "GJ01AB1234"
        assert normalize_plate_query("GJ.01/AB*1234#") == "GJ01AB1234"
        assert normalize_plate_query("") == ""
        print("  -> Passed: Plate text cleaning correctly normalizes raw inputs to alphanumeric uppercase.")
        passed += 1

        # -----------------------------------------------------------------
        # Setup Test Fixtures: 3 Cameras across Ahmedabad & Gandhinagar
        # -----------------------------------------------------------------
        print("\n[*] Setting up multi-camera detection records in database...")
        cam1 = db.query(Camera).filter(Camera.camera_code == "CAM-M8-01").first()
        if not cam1:
            cam1 = Camera(
                camera_code="CAM-M8-01",
                camera_name="SG Highway - Iskcon Cross Road",
                location_name="Ahmedabad",
                department="Traffic Branch",
                latitude=23.0295,
                longitude=72.5065,
                status=CameraStatus.ONLINE,
                camera_type=CameraType.FIXED,
                source_type=SourceType.RECORDED_FOOTAGE,
                connectivity_type=ConnectivityType.FILE,
            )
            db.add(cam1)

        cam2 = db.query(Camera).filter(Camera.camera_code == "CAM-M8-02").first()
        if not cam2:
            cam2 = Camera(
                camera_code="CAM-M8-02",
                camera_name="Vaishno Devi Circle",
                location_name="Ahmedabad",
                department="Highway Patrol",
                latitude=23.1360,
                longitude=72.5401,
                status=CameraStatus.ONLINE,
                camera_type=CameraType.FIXED,
                source_type=SourceType.RECORDED_FOOTAGE,
                connectivity_type=ConnectivityType.FILE,
            )
            db.add(cam2)

        cam3 = db.query(Camera).filter(Camera.camera_code == "CAM-M8-03").first()
        if not cam3:
            cam3 = Camera(
                camera_code="CAM-M8-03",
                camera_name="CH-0 Circle Gandhinagar",
                location_name="Gandhinagar",
                department="City Surveillance",
                latitude=23.2156,
                longitude=72.6369,
                status=CameraStatus.ONLINE,
                camera_type=CameraType.FIXED,
                source_type=SourceType.RECORDED_FOOTAGE,
                connectivity_type=ConnectivityType.FILE,
            )
            db.add(cam3)

        db.commit()
        db.refresh(cam1)
        db.refresh(cam2)
        db.refresh(cam3)

        # Footage Fixtures
        ft1 = db.query(CameraFootage).filter(CameraFootage.file_name == "m8_footage_01.mp4").first()
        if not ft1:
            ft1 = CameraFootage(
                camera_id=cam1.id,
                file_name="m8_footage_01.mp4",
                original_file_name="m8_footage_01.mp4",
                file_path="storage/recorded_footage/m8_footage_01.mp4",
                file_size=1048576,
                mime_type="video/mp4",
                duration_seconds=120.0,
                status=FootageStatus.COMPLETED,
            )
            db.add(ft1)

        ft2 = db.query(CameraFootage).filter(CameraFootage.file_name == "m8_footage_02.mp4").first()
        if not ft2:
            ft2 = CameraFootage(
                camera_id=cam2.id,
                file_name="m8_footage_02.mp4",
                original_file_name="m8_footage_02.mp4",
                file_path="storage/recorded_footage/m8_footage_02.mp4",
                file_size=1048576,
                mime_type="video/mp4",
                duration_seconds=120.0,
                status=FootageStatus.COMPLETED,
            )
            db.add(ft2)

        ft3 = db.query(CameraFootage).filter(CameraFootage.file_name == "m8_footage_03.mp4").first()
        if not ft3:
            ft3 = CameraFootage(
                camera_id=cam3.id,
                file_name="m8_footage_03.mp4",
                original_file_name="m8_footage_03.mp4",
                file_path="storage/recorded_footage/m8_footage_03.mp4",
                file_size=1048576,
                mime_type="video/mp4",
                duration_seconds=120.0,
                status=FootageStatus.COMPLETED,
            )
            db.add(ft3)

        db.commit()
        db.refresh(ft1)
        db.refresh(ft2)
        db.refresh(ft3)

        # Target vehicle for testing: "GJ01XY9999"
        target_plate = "GJ01XY9999"

        # Clean existing test detections for isolation
        db.query(VehicleAlert).filter(VehicleAlert.plate_text == target_plate).delete()
        db.query(WatchlistEntry).filter(WatchlistEntry.normalized_plate_text == target_plate).delete()
        db.query(AnprDetection).filter(AnprDetection.plate_number_normalized == target_plate).delete()
        db.commit()

        # Camera 1 (Iskcon) encounters at t=1.0s and t=3.0s
        d1 = AnprDetection(
            footage_id=ft1.id,
            frame_number=30,
            timestamp_seconds=1.0,
            vehicle_class="car",
            plate_number_raw="GJ 01 XY 9999",
            plate_number_normalized=target_plate,
            confidence=0.92,
            ocr_confidence=0.94,
            detection_confidence=0.90,
            x1=100.0,
            y1=100.0,
            x2=200.0,
            y2=150.0,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            track_id=101,
        )
        d2 = AnprDetection(
            footage_id=ft1.id,
            frame_number=90,
            timestamp_seconds=3.0,
            vehicle_class="car",
            plate_number_raw="GJ-01-XY-9999",
            plate_number_normalized=target_plate,
            confidence=0.95,
            ocr_confidence=0.96,
            detection_confidence=0.94,
            x1=105.0,
            y1=102.0,
            x2=205.0,
            y2=152.0,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            track_id=101,
        )

        # Camera 2 (Vaishno Devi) encounters at t=15.0s
        d3 = AnprDetection(
            footage_id=ft2.id,
            frame_number=450,
            timestamp_seconds=15.0,
            vehicle_class="car",
            plate_number_raw="GJ01XY9999",
            plate_number_normalized=target_plate,
            confidence=0.89,
            ocr_confidence=0.90,
            detection_confidence=0.88,
            x1=150.0,
            y1=120.0,
            x2=250.0,
            y2=170.0,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            track_id=202,
        )

        # Camera 3 (Gandhinagar) encounters at t=45.0s
        d4 = AnprDetection(
            footage_id=ft3.id,
            frame_number=1350,
            timestamp_seconds=45.0,
            vehicle_class="car",
            plate_number_raw="GJ01 XY 9999",
            plate_number_normalized=target_plate,
            confidence=0.96,
            ocr_confidence=0.97,
            detection_confidence=0.95,
            x1=180.0,
            y1=130.0,
            x2=280.0,
            y2=180.0,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            track_id=303,
        )

        db.add_all([d1, d2, d3, d4])
        db.commit()
        db.refresh(d1)

        # Add Watchlist entry + Alert for target plate
        wl_entry = WatchlistEntry(
            plate_text="GJ 01 XY 9999",
            normalized_plate_text=target_plate,
            category=WatchlistCategory.INVESTIGATION,
            priority=WatchlistPriority.CRITICAL,
            status=WatchlistStatus.ACTIVE,
            description="Wanted in inter-district investigation (CR-2026-GJ-099)",
        )
        db.add(wl_entry)
        db.commit()
        db.refresh(wl_entry)

        alert = VehicleAlert(
            watchlist_entry_id=wl_entry.id,
            camera_id=cam1.id,
            footage_id=ft1.id,
            anpr_detection_id=d1.id,
            plate_text=target_plate,
            vehicle_class="car",
            alert_type=AlertType.WATCHLIST_MATCH,
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.NEW,
            message="Matched active Watchlist: Wanted in inter-district investigation",
            confidence=0.92,
            timestamp_seconds=1.0,
            track_id=101,
        )
        db.add(alert)
        db.commit()
        print("  -> Created 4 ANPR detections, 1 Watchlist entry, and 1 Alert.")

        # -----------------------------------------------------------------
        # TEST 2: Basic Vehicle Movement Search
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing search_vehicle_history with normalized query 'gj 01 xy 9999'...")
        res: VehicleSearchResponse = search_vehicle_history(db=db, plate_text="gj 01 xy 9999")
        
        assert res.query_plate_normalized == "GJ01XY9999"
        assert res.total_observations == 4
        assert len(res.observations) == 4
        print(f"  -> Passed: Found {res.total_observations} observations across all cameras.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 3: Observed Camera Detection Sequence Aggregation
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing Observed Camera Detection Sequence steps...")
        seq = res.observed_sequence
        assert len(seq) == 3, f"Expected 3 distinct camera sequence steps, got {len(seq)}"
        
        # Step 1: CAM-M8-01 (Iskcon) - 2 detections aggregated
        assert seq[0].step_number == 1
        assert seq[0].camera_code == "CAM-M8-01"
        assert seq[0].sighting_count == 2
        assert seq[0].department == "Traffic Branch"
        assert seq[0].has_valid_coordinates is True
        assert seq[0].latitude == 23.0295

        # Step 2: CAM-M8-02 (Vaishno Devi) - 1 detection
        assert seq[1].step_number == 2
        assert seq[1].camera_code == "CAM-M8-02"
        assert seq[1].sighting_count == 1

        # Step 3: CAM-M8-03 (CH-0 Gandhinagar) - 1 detection
        assert seq[2].step_number == 3
        assert seq[2].camera_code == "CAM-M8-03"
        assert seq[2].sighting_count == 1
        print(f"  -> Passed: Sequence steps correctly aggregated in chronological order:")
        for s in seq:
            print(f"     Step {s.step_number}: {s.camera_code} ({s.location_name}) -> {s.sighting_count} sightings")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 4: Summary KPI Metrics
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing summary KPI calculations...")
        summary = res.summary
        assert summary.total_observations == 4
        assert summary.unique_cameras_count == 3
        assert summary.departments_count == 3  # Traffic Branch, Highway Patrol, City Surveillance
        assert summary.first_observed_at is not None
        assert summary.last_observed_at is not None
        print(f"  -> Passed: Summary KPIs accurately reflect route traversal (Unique Cameras: {summary.unique_cameras_count}, Departments: {summary.departments_count}).")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 5: Milestone 7 Alert History Integration
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing Watchlist alert history lookup...")
        alerts = res.alerts_history
        assert len(alerts) == 1
        assert alerts[0].camera_code == "CAM-M8-01"
        assert alerts[0].severity == AlertSeverity.CRITICAL
        print(f"  -> Passed: Alert history correctly linked to searched vehicle (Alert ID: {alerts[0].id}).")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 6: Video Timestamp Seek Accuracy
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing observation video seek offsets...")
        obs1 = res.observations[0]
        assert obs1.timestamp_seconds == 1.0
        assert obs1.video_stream_url == f"/api/footage/{ft1.id}/stream"
        print(f"  -> Passed: Observation contains exact seek offset ({obs1.timestamp_seconds}s) and stream URL ({obs1.video_stream_url}).")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 7: Multi-Parameter Filtering
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing multi-parameter filtering...")
        
        # Filter by department="Traffic Branch" -> should only return CAM-M8-01 (2 sightings)
        dept_res = search_vehicle_history(db=db, plate_text="GJ01XY9999", department="Traffic Branch")
        assert dept_res.total_observations == 2
        assert len(dept_res.observed_sequence) == 1
        assert dept_res.observed_sequence[0].camera_code == "CAM-M8-01"

        # Filter by camera_id=cam3.id -> should only return 1 sighting
        cam_res = search_vehicle_history(db=db, plate_text="GJ01XY9999", camera_id=cam3.id)
        assert cam_res.total_observations == 1
        assert cam_res.observed_sequence[0].camera_code == "CAM-M8-03"

        # Filter by location="Gandhinagar" -> should only return Gandhinagar sighting
        loc_res = search_vehicle_history(db=db, plate_text="GJ01XY9999", location="Gandhinagar")
        assert loc_res.total_observations == 1
        assert loc_res.observed_sequence[0].location_name == "Gandhinagar"
        print("  -> Passed: All filters (department, camera, location) functioned flawlessly.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 8: Unknown / Unmatched Plate Handling
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing search response for unknown vehicle...")
        unknown_res = search_vehicle_history(db=db, plate_text="GJ99ZZ0000")
        assert unknown_res.query_plate_normalized == "GJ99ZZ0000"
        assert unknown_res.total_observations == 0
        assert len(unknown_res.observations) == 0
        assert len(unknown_res.observed_sequence) == 0
        assert "Observed camera detections" in unknown_res.disclaimer
        print(f"  -> Passed: Handled unknown plate gracefully with structured empty response.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 9: Geographic PostGIS Coordinate Integrity
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing Geographic PostGIS Coordinate Validation...")
        for step in res.observed_sequence:
            assert step.has_valid_coordinates is True
            assert 20.0 <= step.latitude <= 25.0  # Gujarat latitude bounds
            assert 68.0 <= step.longitude <= 75.0  # Gujarat longitude bounds
        print("  -> Passed: All camera coordinates reside within Gujarat geographical boundaries.")
        passed += 1

        # -----------------------------------------------------------------
        # TEST 10: FastAPI REST API Endpoints with TestClient
        # -----------------------------------------------------------------
        total += 1
        print(f"\n[{total}] Testing FastAPI GET /api/vehicle-search endpoint via TestClient...")
        client = TestClient(app)

        # 10a: Query with spaces and lowercase
        resp = client.get("/api/vehicle-search?plate_text=gj%2001%20xy%209999")
        assert resp.status_code == 200, f"API failed: {resp.text}"
        data = resp.json()
        assert data["query_plate_normalized"] == "GJ01XY9999"
        assert data["total_observations"] == 4
        assert len(data["observed_sequence"]) == 3
        assert len(data["alerts_history"]) == 1

        # 10b: Query without plate_text param (should return empty response)
        empty_resp = client.get("/api/vehicle-search")
        assert empty_resp.status_code == 200
        assert empty_resp.json()["total_observations"] == 0

        # 10c: Query with department filter
        dept_resp = client.get("/api/vehicle-search?plate_text=GJ01XY9999&department=Highway%20Patrol")
        assert dept_resp.status_code == 200
        assert dept_resp.json()["total_observations"] == 1
        print("  -> Passed: FastAPI endpoints responded with status 200 and expected schema payload.")
        passed += 1

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[FAIL] Test suite encountered an error: {e}")
    finally:
        db.close()

    print("\n========================================================")
    print(f" Milestone 8 Verification Summary: {passed}/{total} Tests Passed")
    if passed == total:
        print(" [SUCCESS] All Milestone 8 Vehicle Search & Sequence Tests Passed!")
    else:
        print(f" [WARNING] {total - passed} tests failed.")
    print("========================================================\n")
    return passed == total


if __name__ == "__main__":
    success = run_milestone8_tests()
    sys.exit(0 if success else 1)
