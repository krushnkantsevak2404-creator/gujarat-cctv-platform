"""
Milestone 7 Automated Verification Script
Tests Watchlist CRUD, plate normalization, active matching engine,
multi-frame alert deduplication, confidence filtering, and alert lifecycle workflow.
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.camera import Camera, CameraType, SourceType, ConnectivityType, CameraStatus
from app.models.footage import CameraFootage, FootageStatus
from app.models.anpr import AnprDetection, AnprStatus, PlateFormatStatus
from app.models.watchlist import (
    WatchlistEntry,
    WatchlistCategory,
    WatchlistPriority,
    WatchlistStatus,
)
from app.models.alert import (
    VehicleAlert,
    AlertType,
    AlertSeverity,
    AlertStatus,
)
from app.schemas.watchlist import WatchlistEntryCreate, WatchlistEntryUpdate
from app.services import watchlist_service


def run_milestone7_tests():
    print("\n========================================================")
    print(" Gujarat CCTV Intelligence Platform — Milestone 7 Tests")
    print(" Watchlist + Automatic Vehicle Alerts Verification")
    print("========================================================\n")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Step 0: Ensure a test Camera and CameraFootage exist
        test_camera = db.query(Camera).filter(Camera.camera_code == "CAM-TST-07").first()
        if not test_camera:
            test_camera = Camera(
                camera_code="CAM-TST-07",
                camera_name="SG Highway Gandhinagar Junction",
                location_name="Gandhinagar",
                department="Traffic Branch",
                latitude=23.2156,
                longitude=72.6369,
                status=CameraStatus.ONLINE,
                camera_type=CameraType.FIXED,
                source_type=SourceType.RECORDED_FOOTAGE,
                connectivity_type=ConnectivityType.FILE,
            )
            db.add(test_camera)
            db.commit()
            db.refresh(test_camera)
            print(f"[*] Created test camera: {test_camera.camera_code} (ID: {test_camera.id})")
        else:
            print(f"[*] Using existing test camera: {test_camera.camera_code} (ID: {test_camera.id})")

        test_footage = db.query(CameraFootage).filter(CameraFootage.camera_id == test_camera.id).first()
        if not test_footage:
            test_footage = CameraFootage(
                camera_id=test_camera.id,
                file_name="m7_test_cctv.mp4",
                original_file_name="m7_test_cctv.mp4",
                file_path="footage/m7_test_cctv.mp4",
                mime_type="video/mp4",
                file_size=1024 * 1024 * 10,
                duration_seconds=30.0,
                status=FootageStatus.UPLOADED,
            )
            db.add(test_footage)
            db.commit()
            db.refresh(test_footage)
            print(f"[*] Created test footage record: ID #{test_footage.id}")
        else:
            print(f"[*] Using existing test footage record: ID #{test_footage.id}")

        # Clean previous test alerts and test watchlist entries
        db.query(VehicleAlert).filter(VehicleAlert.footage_id == test_footage.id).delete()
        db.query(WatchlistEntry).filter(WatchlistEntry.plate_text.in_(["GJ 01 AB 1234", "GJ 05 CD 5678", "MH 02 XY 9999", "GJ 27 ZZ 0001"])).delete()
        db.commit()

        # =====================================================================
        # TEST 1: Watchlist CRUD & Normalization
        # =====================================================================
        print("\n--- TEST 1: Watchlist CRUD & Indian Plate Normalization ---")
        entry_create_1 = WatchlistEntryCreate(
            plate_text="GJ-01-AB-1234",
            description="Stolen Hyundai Creta from Sector 21",
            category=WatchlistCategory.STOLEN,
            priority=WatchlistPriority.CRITICAL,
            status=WatchlistStatus.ACTIVE,
        )
        entry1 = watchlist_service.create_watchlist_entry(db, entry_create_1)
        assert entry1.normalized_plate_text == "GJ01AB1234", f"Expected GJ01AB1234, got {entry1.normalized_plate_text}"
        print(f" [PASS] Created Watchlist Entry #1: {entry1.plate_text} -> Normalized: {entry1.normalized_plate_text}")

        entry_create_2 = WatchlistEntryCreate(
            plate_text="GJ 05 CD 5678",
            description="Suspect vehicle in surveillance case",
            category=WatchlistCategory.SUSPECT,
            priority=WatchlistPriority.HIGH,
            status=WatchlistStatus.ACTIVE,
        )
        entry2 = watchlist_service.create_watchlist_entry(db, entry_create_2)
        assert entry2.normalized_plate_text == "GJ05CD5678"
        print(f" [PASS] Created Watchlist Entry #2: {entry2.plate_text} -> Normalized: {entry2.normalized_plate_text}")

        entry_create_3 = WatchlistEntryCreate(
            plate_text="MH 02 XY 9999",
            description="Muted/Inactive test vehicle",
            category=WatchlistCategory.GENERAL,
            priority=WatchlistPriority.LOW,
            status=WatchlistStatus.INACTIVE,
        )
        entry3 = watchlist_service.create_watchlist_entry(db, entry_create_3)
        assert entry3.status == WatchlistStatus.INACTIVE
        print(f" [PASS] Created Inactive Watchlist Entry #3: {entry3.plate_text} -> Status: {entry3.status}")

        # Test listing & filtering
        active_list = watchlist_service.list_watchlist_entries(db, status=WatchlistStatus.ACTIVE)
        assert any(e.id == entry1.id for e in active_list)
        assert not any(e.id == entry3.id for e in active_list)
        print(f" [PASS] Status filter correctly listed {len(active_list)} active entries.")

        # =====================================================================
        # TEST 2: ANPR Observation Matching & Alert Generation
        # =====================================================================
        print("\n--- TEST 2: Active Watchlist Matching & Alert Generation ---")
        
        # Sighting 1: Matching active plate "GJ 01 AB 1234" with high confidence (0.92)
        det_match_1 = AnprDetection(
            footage_id=test_footage.id,
            track_id=101,
            frame_number=30,
            timestamp_seconds=1.0,
            vehicle_class="car",
            plate_number_raw="GJ01AB1234",
            plate_number_normalized="GJ01AB1234",
            confidence=0.92,
            ocr_confidence=0.94,
            detection_confidence=0.90,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            x1=100, y1=100, x2=200, y2=150,
            vehicle_x1=50, vehicle_y1=50, vehicle_x2=350, vehicle_y2=250,
            is_consolidated=True,
            sighting_count=5,
        )
        db.add(det_match_1)
        db.commit()
        db.refresh(det_match_1)

        # Sighting 2: Non-matching plate "GJ 27 ZZ 0001"
        det_non_match = AnprDetection(
            footage_id=test_footage.id,
            track_id=102,
            frame_number=45,
            timestamp_seconds=1.5,
            vehicle_class="motorcycle",
            plate_number_raw="GJ27ZZ0001",
            plate_number_normalized="GJ27ZZ0001",
            confidence=0.88,
            ocr_confidence=0.90,
            detection_confidence=0.86,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            x1=120, y1=120, x2=220, y2=170,
            vehicle_x1=60, vehicle_y1=60, vehicle_x2=360, vehicle_y2=260,
            is_consolidated=True,
            sighting_count=3,
        )
        db.add(det_non_match)
        db.commit()
        db.refresh(det_non_match)

        # Sighting 3: Inactive watchlist plate "MH 02 XY 9999"
        det_inactive = AnprDetection(
            footage_id=test_footage.id,
            track_id=103,
            frame_number=60,
            timestamp_seconds=2.0,
            vehicle_class="truck",
            plate_number_raw="MH02XY9999",
            plate_number_normalized="MH02XY9999",
            confidence=0.91,
            ocr_confidence=0.92,
            detection_confidence=0.90,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            x1=130, y1=130, x2=230, y2=180,
            vehicle_x1=70, vehicle_y1=70, vehicle_x2=370, vehicle_y2=270,
            is_consolidated=True,
            sighting_count=4,
        )
        db.add(det_inactive)
        db.commit()
        db.refresh(det_inactive)

        # Sighting 4: Matching plate "GJ 05 CD 5678" with LOW confidence (0.22 < 0.35)
        det_low_conf = AnprDetection(
            footage_id=test_footage.id,
            track_id=104,
            frame_number=75,
            timestamp_seconds=2.5,
            vehicle_class="car",
            plate_number_raw="GJ05CD5678",
            plate_number_normalized="GJ05CD5678",
            confidence=0.22,
            ocr_confidence=0.22,
            detection_confidence=0.30,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            x1=140, y1=140, x2=240, y2=190,
            vehicle_x1=80, vehicle_y1=80, vehicle_x2=380, vehicle_y2=280,
            is_consolidated=True,
            sighting_count=2,
        )
        db.add(det_low_conf)
        db.commit()
        db.refresh(det_low_conf)

        # Execute Watchlist Evaluation
        batch_records = [det_match_1, det_non_match, det_inactive, det_low_conf]
        generated_alerts = watchlist_service.evaluate_footage_anpr_detections(db, test_footage.id, batch_records)

        # Assertions
        assert len(generated_alerts) == 1, f"Expected exactly 1 alert, got {len(generated_alerts)}"
        alert1 = generated_alerts[0]
        assert alert1.plate_text == "GJ01AB1234"
        assert alert1.severity == AlertSeverity.CRITICAL
        assert alert1.status == AlertStatus.NEW
        assert alert1.alert_type == AlertType.WATCHLIST_MATCH
        assert alert1.camera_id == test_camera.id
        assert alert1.timestamp_seconds == 1.0
        assert "SG Highway Gandhinagar" in alert1.message
        print(f" [PASS] Alert successfully created: Alert #{alert1.id} for plate {alert1.plate_text} with severity {alert1.severity.value}")
        print(f"        Message: \"{alert1.message}\"")

        # =====================================================================
        # TEST 3: Multi-Frame Alert Deduplication
        # =====================================================================
        print("\n--- TEST 3: Multi-Frame Alert Deduplication ---")
        
        # Sighting 5: Same vehicle GJ01AB1234 observed in next consecutive frames (t=1.5s, 2.0s) on Track 101
        det_match_frame2 = AnprDetection(
            footage_id=test_footage.id,
            track_id=101,
            frame_number=45,
            timestamp_seconds=1.5,
            vehicle_class="car",
            plate_number_raw="GJ01AB1234",
            plate_number_normalized="GJ01AB1234",
            confidence=0.96,  # Higher confidence
            ocr_confidence=0.97,
            detection_confidence=0.95,
            status=AnprStatus.OCR_SUCCESS,
            format_status=PlateFormatStatus.VALID_FORMAT,
            x1=105, y1=105, x2=205, y2=155,
            vehicle_x1=55, vehicle_y1=55, vehicle_x2=355, vehicle_y2=255,
            is_consolidated=True,
            sighting_count=6,
        )
        db.add(det_match_frame2)
        db.commit()
        db.refresh(det_match_frame2)

        # Evaluate duplicate batch
        dedup_alerts = watchlist_service.evaluate_footage_anpr_detections(db, test_footage.id, [det_match_frame2])
        assert len(dedup_alerts) == 0, f"Expected 0 new alerts due to deduplication, got {len(dedup_alerts)}"
        
        # Verify existing alert was upgraded to higher confidence
        db.refresh(alert1)
        assert alert1.confidence == 0.96, f"Expected alert confidence to update to 0.96, got {alert1.confidence}"
        print(f" [PASS] Deduplication verified: No duplicate alert created for same vehicle track. Alert confidence upgraded to {alert1.confidence * 100:.1f}%.")

        # =====================================================================
        # TEST 4: Alert Status Workflow (NEW -> ACKNOWLEDGED -> RESOLVED)
        # =====================================================================
        print("\n--- TEST 4: Alert Workflow Status Transitions ---")
        
        # Acknowledge
        ack_alert = watchlist_service.acknowledge_alert(db, alert1.id)
        assert ack_alert.status == AlertStatus.ACKNOWLEDGED
        assert ack_alert.acknowledged_at is not None
        print(f" [PASS] Acknowledged Alert #{ack_alert.id} at {ack_alert.acknowledged_at}")

        # Resolve
        res_alert = watchlist_service.resolve_alert(db, alert1.id)
        assert res_alert.status == AlertStatus.RESOLVED
        assert res_alert.resolved_at is not None
        print(f" [PASS] Resolved Alert #{res_alert.id} at {res_alert.resolved_at}")

        # Stats calculation
        stats = watchlist_service.get_alert_statistics(db)
        assert stats["total_alerts"] >= 1
        assert stats["resolved_alerts"] >= 1
        print(f" [PASS] Alert Statistics verified: {stats}")

        print("\n========================================================")
        print(" ALL MILESTONE 7 TEST SCENARIOS PASSED SUCCESSFULLY! ")
        print("========================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_milestone7_tests()
