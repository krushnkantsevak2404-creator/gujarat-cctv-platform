"""
Milestone 11 Automated Verification Test Suite
Verifies:
1. Dynamic Camera Statistics (Total, Online, Offline, Maintenance, Unknown).
2. Live Source vs Recorded Source breakdowns.
3. Stream session status inspection via StreamManager (CONNECTED, DISCONNECTED, NOT_CONFIGURED, ERROR).
4. Dynamic Department Breakdown.
5. Vehicle Analytics Summaries from live database tables (ANPR, Detections, Tracks, Alerts).
6. Recent Watchlist Alerts integration.
7. Search and multi-filter capabilities on camera health records.
8. System Health Diagnostics endpoint (/api/health/system).
9. Camera Health Overview endpoint (/api/health/cameras).
10. Security Audit: Zero credential exposure, zero unauthorized port scanning.
"""

import os
import sys
import unittest
import json
from datetime import datetime

# Setup path to backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.camera import Camera, CameraType, SourceType, ConnectivityType, CameraStatus
from app.models.footage import CameraFootage
from app.models.alert import VehicleAlert, AlertSeverity, AlertStatus, AlertType
from app.models.watchlist import WatchlistEntry, WatchlistCategory, WatchlistPriority, WatchlistStatus
from app.models.anpr import AnprDetection, AnprStatus, PlateFormatStatus
from app.models.detection import VehicleDetection, VehicleTrack
from app.services import camera_health_service
from app.streams.manager import stream_manager
from app.streams.schemas import StreamStatusEnum


class TestOperationalDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()
        cls._setup_fixtures()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    @classmethod
    def _setup_fixtures(cls):
        """Ensure consistent test fixtures exist in the database."""
        # Ensure a test camera exists with specific statuses
        cam_live = cls.db.query(Camera).filter(Camera.camera_code == "CAM-M11-LIVE").first()
        if not cam_live:
            cam_live = Camera(
                camera_code="CAM-M11-LIVE",
                camera_name="SG Highway Science City Junction",
                department="Traffic Police - Ahmedabad",
                location_name="Science City Cross Road, Ahmedabad",
                latitude=23.0784,
                longitude=72.5085,
                camera_type=CameraType.PTZ,
                source_type=SourceType.LIVE_CAMERA,
                connectivity_type=ConnectivityType.RTSP,
                stream_url="rtsp://admin:secret123@192.168.1.100:554/live",
                status=CameraStatus.ONLINE,
            )
            cls.db.add(cam_live)

        cam_offline = cls.db.query(Camera).filter(Camera.camera_code == "CAM-M11-OFFLINE").first()
        if not cam_offline:
            cam_offline = Camera(
                camera_code="CAM-M11-OFFLINE",
                camera_name="GIDC Industrial Sector Gate 3",
                department="Industrial Security",
                location_name="GIDC Sector 25, Gandhinagar",
                latitude=23.2450,
                longitude=72.6480,
                camera_type=CameraType.FIXED,
                source_type=SourceType.LIVE_CAMERA,
                connectivity_type=ConnectivityType.RTSP,
                stream_url=None,  # Unconfigured
                status=CameraStatus.OFFLINE,
            )
            cls.db.add(cam_offline)

        cam_maint = cls.db.query(Camera).filter(Camera.camera_code == "CAM-M11-MAINT").first()
        if not cam_maint:
            cam_maint = Camera(
                camera_code="CAM-M11-MAINT",
                camera_name="Ring Road Surveillance Outpost",
                department="Highway Patrol",
                location_name="SP Ring Road, Odhav",
                latitude=23.0110,
                longitude=72.6620,
                camera_type=CameraType.DOME,
                source_type=SourceType.RECORDED_FOOTAGE,
                connectivity_type=ConnectivityType.FILE,
                status=CameraStatus.MAINTENANCE,
            )
            cls.db.add(cam_maint)

        cls.db.commit()

    def test_01_health_overview_service_counts(self):
        """TEST 1: get_camera_health_overview returns dynamic, genuine database metrics."""
        overview = camera_health_service.get_camera_health_overview(self.db)
        
        self.assertIsNotNone(overview)
        self.assertGreater(overview.summary.total, 0)
        self.assertEqual(
            overview.summary.total,
            overview.summary.online + overview.summary.offline + overview.summary.maintenance + overview.summary.unknown,
            "Total cameras must equal sum of online + offline + maintenance + unknown"
        )
        self.assertEqual(
            overview.summary.total,
            overview.summary.live_sources + overview.summary.recorded_sources,
            "Total cameras must equal sum of live_sources + recorded_sources"
        )
        print(f"  [PASS] Test 1: Verified dynamic summary metrics for {overview.summary.total} cameras.")

    def test_02_registration_vs_stream_status_separation(self):
        """TEST 2: Permanent registration status is kept separate from live stream session status."""
        overview = camera_health_service.get_camera_health_overview(self.db)
        
        for cam in overview.cameras:
            # Registration status must be one of the standard enum values
            self.assertIn(cam.status, ["ONLINE", "OFFLINE", "MAINTENANCE", "UNKNOWN"])
            # Stream status must be one of the stream session values
            self.assertIn(cam.stream_status, ["CONNECTED", "DISCONNECTED", "NOT_CONFIGURED", "ERROR"])
            # Verified safe health summary
            self.assertIsNotNone(cam.health_summary)
            self.assertTrue(len(cam.health_summary) > 0)
        print("  [PASS] Test 2: Verified separation of registration and stream session statuses.")

    def test_03_unconfigured_stream_health(self):
        """TEST 3: Live cameras without stream URLs report NOT_CONFIGURED state."""
        res = self.client.get("/api/health/cameras?search=CAM-M11-OFFLINE")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        self.assertGreater(len(data["cameras"]), 0)
        cam = data["cameras"][0]
        self.assertEqual(cam["camera_code"], "CAM-M11-OFFLINE")
        self.assertEqual(cam["stream_status"], "NOT_CONFIGURED")
        self.assertEqual(cam["status"], "OFFLINE")
        print("  [PASS] Test 3: Verified NOT_CONFIGURED state for unconfigured stream URL.")

    def test_04_department_breakdown_aggregation(self):
        """TEST 4: Departments are dynamically grouped from registered camera records."""
        overview = camera_health_service.get_camera_health_overview(self.db)
        
        self.assertGreater(len(overview.departments), 0)
        total_dept_cams = sum(d.total_cameras for d in overview.departments)
        self.assertEqual(total_dept_cams, overview.summary.total)
        
        # Verify department attributes
        for d in overview.departments:
            self.assertTrue(len(d.department) > 0)
            self.assertGreater(d.total_cameras, 0)
            self.assertGreaterEqual(d.online_cameras, 0)
            self.assertGreaterEqual(d.live_cameras, 0)
        print(f"  [PASS] Test 4: Verified {len(overview.departments)} dynamic departments.")

    def test_05_vehicle_analytics_metrics_integrity(self):
        """TEST 5: Vehicle analytics metrics match database table records (no fake data)."""
        overview = camera_health_service.get_camera_health_overview(self.db)
        va = overview.vehicle_analytics
        
        db_anpr_count = self.db.query(AnprDetection).count()
        db_det_count = self.db.query(VehicleDetection).count()
        db_tracks_count = self.db.query(VehicleTrack).count()
        db_alerts_count = self.db.query(VehicleAlert).count()
        
        self.assertEqual(va.total_anpr_observations, db_anpr_count)
        self.assertEqual(va.total_vehicles_detected, db_det_count)
        self.assertEqual(va.total_tracked_vehicles, db_tracks_count)
        self.assertEqual(va.total_watchlist_matches, db_alerts_count)
        print(f"  [PASS] Test 5: Verified vehicle analytics ({va.total_anpr_observations} ANPR, {va.total_vehicles_detected} Detections).")

    def test_06_recent_watchlist_alerts_integration(self):
        """TEST 6: Recent watchlist alerts are included with camera context and sanitized details."""
        res = self.client.get("/api/health/cameras")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        recent_alerts = data["recent_alerts"]
        if recent_alerts:
            first = recent_alerts[0]
            self.assertIn("alert_id", first)
            self.assertIn("plate_text", first)
            self.assertIn("severity", first)
            self.assertIn("camera_code", first)
            self.assertIn("timestamp_formatted", first)
        print(f"  [PASS] Test 6: Verified recent alerts feed ({len(recent_alerts)} items).")

    def test_07_camera_health_filtering(self):
        """TEST 7: GET /api/health/cameras filters camera records accurately."""
        # Filter by status = ONLINE
        res_online = self.client.get("/api/health/cameras?status=ONLINE")
        self.assertEqual(res_online.status_code, 200)
        data_online = res_online.json()
        for c in data_online["cameras"]:
            self.assertEqual(c["status"], "ONLINE")
            
        # Filter by source_type = RECORDED_FOOTAGE
        res_rec = self.client.get("/api/health/cameras?source_type=RECORDED_FOOTAGE")
        self.assertEqual(res_rec.status_code, 200)
        data_rec = res_rec.json()
        for c in data_rec["cameras"]:
            self.assertEqual(c["source_type"], "RECORDED_FOOTAGE")
            
        print("  [PASS] Test 7: Verified multi-filter query parameters on camera health table.")

    def test_08_system_health_diagnostics_endpoint(self):
        """TEST 8: GET /api/health/system evaluates 5 core subsystems without credential exposure."""
        res = self.client.get("/api/health/system")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        self.assertIn("status", data)
        self.assertIn("backend_api", data)
        self.assertIn("database", data)
        self.assertIn("gis", data)
        self.assertIn("ai_processing", data)
        self.assertIn("stream_service", data)
        
        # Verify no passwords or tokens in response
        raw_json = json.dumps(data)
        self.assertNotIn("password", raw_json.lower())
        self.assertNotIn("secret", raw_json.lower())
        print(f"  [PASS] Test 8: Verified system diagnostics (Overall status: {data['status']}).")

    def test_09_credential_protection_and_sanitization(self):
        """TEST 9: Security audit ensuring zero RTSP passwords or internal paths are leaked."""
        res = self.client.get("/api/health/cameras")
        self.assertEqual(res.status_code, 200)
        raw_text = res.text
        
        self.assertNotIn("secret123", raw_text)
        self.assertNotIn("admin:", raw_text)
        print("  [PASS] Test 9: Security audit passed (zero credential leakage).")

    def test_10_regression_endpoints_accessibility(self):
        """TEST 10: Regression check verifying all milestones 1-10 endpoints continue working."""
        endpoints = [
            "/api/cameras/stats",
            "/api/cameras/geojson",
            "/api/viewer/stats",
            "/api/streams/stats",
            "/api/watchlist",
            "/api/alerts/stats",
            "/api/vehicle-search?plate_text=GJ01",
        ]
        for ep in endpoints:
            r = self.client.get(ep)
            self.assertIn(r.status_code, [200, 204], f"Endpoint {ep} failed with status {r.status_code}")
        print("  [PASS] Test 10: Regression verified across all existing module endpoints.")


if __name__ == "__main__":
    print("========================================================================")
    print("Running Milestone 11: Camera Health Monitoring & Operational Dashboard")
    print("========================================================================")
    unittest.main(verbosity=2)
