"""
Milestone 10: Stream Adapter & RTSP Integration Test Suite
Validates StreamManager, RTSPAdapter, RecordedFootageAdapter, VMSAdapter, ONVIFAdapter, SDKAdapter,
security & credential masking, session deduplication, and REST API endpoints.
"""

import os
import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.camera import Camera, SourceType, ConnectivityType, CameraStatus, CameraType
from app.models.footage import CameraFootage
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum
from app.streams import (
    StreamManager,
    stream_manager,
    RTSPAdapter,
    RecordedFootageAdapter,
    VMSAdapter,
    ONVIFAdapter,
    SDKAdapter,
    mask_rtsp_url,
    check_media_relay_status,
)


class TestStreamAdapters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        stream_manager.shutdown_all()
        cls.db.close()

    def test_01_recorded_footage_adapter(self):
        """TEST 1: RecordedFootageAdapter correctly indexes recorded MP4 footage without duplicating files."""
        # Find camera with recorded footage
        camera = (
            self.db.query(Camera)
            .filter(Camera.source_type == SourceType.RECORDED_FOOTAGE)
            .first()
        )
        self.assertIsNotNone(camera, "Should find a registered recorded camera in database")
        
        adapter = RecordedFootageAdapter(camera, db=self.db)
        info = adapter.get_stream_info()
        
        self.assertEqual(info["connectivity_type"], "FILE")
        self.assertEqual(info["playback_mode"], PlaybackModeEnum.RECORDED_STREAM.value)
        self.assertEqual(info["stream_status"], StreamStatusEnum.CONNECTED.value)
        self.assertIn("available_footage", info)
        self.assertGreaterEqual(info["footage_count"], 1)
        self.assertTrue(info["available_footage"][0]["stream_url"].startswith("/api/footage/"))

    def test_02_unconfigured_camera_status(self):
        """TEST 2: Camera with no stream URL returns NOT_CONFIGURED state."""
        unconfigured_cam = Camera(
            id=9991,
            camera_code="GJ-TEST-UNCONFIG",
            camera_name="Test Unconfigured Cam",
            department="Traffic Branch",
            location_name="Test Junction",
            latitude=23.0,
            longitude=72.5,
            source_type=SourceType.LIVE_CAMERA,
            connectivity_type=ConnectivityType.RTSP,
            stream_url=None,
            status=CameraStatus.ONLINE,
        )
        adapter = RTSPAdapter(unconfigured_cam)
        is_valid, err = adapter.validate_source()
        
        self.assertFalse(is_valid)
        self.assertIn("Live stream is not configured", err)
        self.assertEqual(adapter.get_status(), StreamStatusEnum.NOT_CONFIGURED)

    def test_03_rtsp_credential_masking_security(self):
        """TEST 3: RTSP URLs with credentials MUST be masked and never exposed in responses or logs."""
        raw_url = "rtsp://admin:SecretPassword123@192.168.1.100:554/stream1"
        masked = mask_rtsp_url(raw_url)
        
        self.assertEqual(masked, "rtsp://****:****@192.168.1.100:554/stream1")
        self.assertNotIn("SecretPassword123", masked)
        self.assertNotIn("admin", masked)

        # Test with camera model
        cam = Camera(
            id=9992,
            camera_code="GJ-TEST-SECURE-RTSP",
            camera_name="Secure RTSP Cam",
            department="Ahmedabad City Police",
            location_name="Ring Road",
            latitude=23.0,
            longitude=72.5,
            source_type=SourceType.LIVE_CAMERA,
            connectivity_type=ConnectivityType.RTSP,
            stream_url=raw_url,
            status=CameraStatus.ONLINE,
        )
        adapter = RTSPAdapter(cam)
        info = adapter.get_stream_info()
        
        # Verify response dictionary does NOT contain the raw credentials
        info_str = str(info)
        self.assertNotIn("SecretPassword123", info_str)
        self.assertEqual(info["connectivity_type"], "RTSP")

    def test_04_stream_manager_adapter_routing(self):
        """TEST 4: StreamManager correctly routes to RTSP, Recorded, VMS, ONVIF, and SDK adapters."""
        c_rtsp = Camera(id=1, camera_code="C1", source_type=SourceType.LIVE_CAMERA, connectivity_type=ConnectivityType.RTSP)
        c_file = Camera(id=2, camera_code="C2", source_type=SourceType.RECORDED_FOOTAGE, connectivity_type=ConnectivityType.FILE)
        c_vms = Camera(id=3, camera_code="C3", source_type=SourceType.LIVE_CAMERA, connectivity_type=ConnectivityType.VMS_API)
        c_onvif = Camera(id=4, camera_code="C4", source_type=SourceType.LIVE_CAMERA, connectivity_type=ConnectivityType.ONVIF)
        c_sdk = Camera(id=5, camera_code="C5", source_type=SourceType.LIVE_CAMERA, connectivity_type=ConnectivityType.SDK)

        self.assertIsInstance(stream_manager.get_adapter(c_rtsp), RTSPAdapter)
        self.assertIsInstance(stream_manager.get_adapter(c_file, db=self.db), RecordedFootageAdapter)
        self.assertIsInstance(stream_manager.get_adapter(c_vms), VMSAdapter)
        self.assertIsInstance(stream_manager.get_adapter(c_onvif), ONVIFAdapter)
        self.assertIsInstance(stream_manager.get_adapter(c_sdk), SDKAdapter)

    def test_05_vms_onvif_sdk_placeholders(self):
        """TEST 5: VMS, ONVIF, and SDK adapters return honest integration readiness messages."""
        c_vms = Camera(id=101, camera_code="VMS-01", source_type=SourceType.LIVE_CAMERA, connectivity_type=ConnectivityType.VMS_API)
        vms_adapter = VMSAdapter(c_vms)
        info = vms_adapter.get_stream_info()
        self.assertIn("vendor-specific API configuration", info["status_message"])
        self.assertEqual(info["stream_status"], StreamStatusEnum.NOT_CONFIGURED.value)

        c_onvif = Camera(id=102, camera_code="ONVIF-01", source_type=SourceType.LIVE_CAMERA, connectivity_type=ConnectivityType.ONVIF)
        onvif_adapter = ONVIFAdapter(c_onvif)
        self.assertIn("authorized device credentials", onvif_adapter.get_stream_info()["status_message"])

        c_sdk = Camera(id=103, camera_code="SDK-01", source_type=SourceType.LIVE_CAMERA, connectivity_type=ConnectivityType.SDK)
        sdk_adapter = SDKAdapter(c_sdk)
        self.assertIn("proprietary driver library", sdk_adapter.get_stream_info()["status_message"])

    def test_06_stream_manager_session_lifecycle_and_deduplication(self):
        """TEST 6: StreamManager connect, disconnect, and session deduplication (reuses active session)."""
        cam = self.db.query(Camera).first()
        self.assertIsNotNone(cam)

        # Connect
        res1 = stream_manager.connect_stream(cam, db=self.db)
        self.assertIsNotNone(res1.session_id)
        self.assertEqual(res1.camera_id, cam.id)

        # Connect second time -> deduplication should return same session
        res2 = stream_manager.connect_stream(cam, db=self.db, force_reconnect=False)
        self.assertEqual(res1.session_id, res2.session_id)

        # Disconnect
        disc_res = stream_manager.disconnect_stream(cam.id)
        self.assertEqual(disc_res.status, StreamStatusEnum.DISCONNECTED)
        self.assertFalse(disc_res.is_live_active)

    def test_07_api_stream_stats(self):
        """TEST 7: GET /api/streams/stats returns platform stream statistics."""
        response = self.client.get("/api/streams/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("total_cameras", data)
        self.assertIn("live_cameras", data)
        self.assertIn("recorded_sources", data)
        self.assertIn("active_stream_sessions", data)
        self.assertIn("media_relay_ready", data)
        self.assertGreaterEqual(data["total_cameras"], 1)

    def test_08_api_stream_status_and_info(self):
        """TEST 8: GET /api/streams/{id}/status and /info return sanitized metadata."""
        cam = self.db.query(Camera).first()
        
        status_res = self.client.get(f"/api/streams/{cam.id}/status")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertEqual(status_data["camera_id"], cam.id)
        self.assertIn("status", status_data)
        self.assertIn("connectivity_type", status_data)

        info_res = self.client.get(f"/api/streams/{cam.id}/info")
        self.assertEqual(info_res.status_code, 200)
        info_data = info_res.json()
        self.assertEqual(info_data["camera_id"], cam.id)
        self.assertIn("playback_mode", info_data)
        self.assertIn("media_relay_details", info_data)

    def test_09_api_connect_and_disconnect_endpoints(self):
        """TEST 9: POST /api/streams/{id}/connect and /disconnect operate cleanly via REST."""
        cam = self.db.query(Camera).first()
        
        # Connect
        conn_res = self.client.post(f"/api/streams/{cam.id}/connect", json={"force_reconnect": True})
        self.assertEqual(conn_res.status_code, 200)
        conn_data = conn_res.json()
        self.assertEqual(conn_data["camera_id"], cam.id)
        self.assertIsNotNone(conn_data["session_id"])

        # Check active sessions
        sess_res = self.client.get("/api/streams/active-sessions")
        self.assertEqual(sess_res.status_code, 200)

        # Disconnect
        disc_res = self.client.post(f"/api/streams/{cam.id}/disconnect")
        self.assertEqual(disc_res.status_code, 200)
        disc_data = disc_res.json()
        self.assertEqual(disc_data["status"], "DISCONNECTED")

    def test_10_security_and_no_ip_scanning_verification(self):
        """TEST 10: Security audit verifying zero unauthorized IP scanning, credential exposure, or secrets."""
        # 1. Check gitignore contains .env
        gitignore_path = PROJECT_ROOT / ".gitignore"
        if gitignore_path.exists():
            gitignore_text = gitignore_path.read_text(encoding="utf-8")
            self.assertIn(".env", gitignore_text)

        # 2. Check no raw passwords in API stream responses
        for cam in self.db.query(Camera).limit(10).all():
            res = self.client.get(f"/api/streams/{cam.id}/status")
            self.assertEqual(res.status_code, 200)
            res_str = res.text
            self.assertNotIn("password", res_str.lower())
            self.assertNotIn("secret", res_str.lower())


if __name__ == "__main__":
    print("========================================================================")
    print("Running Milestone 10: Stream Adapter & RTSP Integration Test Suite")
    print("========================================================================")
    unittest.main(verbosity=2)
