"""
Recorded CCTV Footage Stream Adapter
Adapts existing recorded MP4 CCTV footage files to the stream adapter interface.
Reuses existing storage files and HTTP 206 Byte-Range streaming without duplicating files.
"""

from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.camera import Camera, CameraStatus
from app.models.footage import CameraFootage
from app.schemas.stream import StreamStatusEnum, PlaybackModeEnum
from app.streams.base import StreamAdapter
from app.streams.models import StreamSession, StreamHealthStatus
from app.services import yolo_service


class RecordedFootageAdapter(StreamAdapter):
    """
    Adapter for registered cameras configured with recorded footage sources.
    Provides metadata, file validation, and HTTP 206 byte-range stream URLs.
    """

    def __init__(self, camera: Camera, db: Optional[Session] = None):
        super().__init__(camera)
        self.db = db

    def _get_footage_records(self) -> List[CameraFootage]:
        """Queries recorded footage files for this camera from database."""
        if not self.db:
            return []
        return (
            self.db.query(CameraFootage)
            .filter(CameraFootage.camera_id == self.camera_id)
            .order_by(desc(CameraFootage.created_at))
            .all()
        )

    def validate_source(self) -> Tuple[bool, Optional[str]]:
        """Validates that recorded footage records exist and files are present on disk."""
        records = self._get_footage_records()
        if not records:
            return False, "No recorded footage files are registered for this camera."
        
        valid_files = 0
        for ft in records:
            if ft.file_path and Path(ft.file_path).exists():
                valid_files += 1
        
        if valid_files == 0:
            return False, "Recorded footage files are missing from storage directory."
        
        return True, None

    def connect(self, session: StreamSession) -> StreamSession:
        """Connects the session to the primary recorded footage file."""
        records = self._get_footage_records()
        if not records:
            session.status = StreamStatusEnum.NOT_CONFIGURED
            session.error_message = "No recorded footage files found for this camera."
            return session

        primary_file = records[0]
        if not primary_file.file_path or not Path(primary_file.file_path).exists():
            session.status = StreamStatusEnum.ERROR
            session.error_message = f"Footage file '{primary_file.file_name}' not found on disk."
            return session

        session.status = StreamStatusEnum.CONNECTED
        session.error_message = None
        session.is_active = True
        return session

    def disconnect(self, session: StreamSession) -> bool:
        """Terminates active recorded playback session."""
        session.status = StreamStatusEnum.DISCONNECTED
        session.is_active = False
        return True

    def get_status(self, session: Optional[StreamSession] = None) -> StreamStatusEnum:
        """Returns recorded footage operational status."""
        if self.camera.status == CameraStatus.OFFLINE:
            return StreamStatusEnum.DISCONNECTED
        records = self._get_footage_records()
        if not records:
            return StreamStatusEnum.NOT_CONFIGURED
        return StreamStatusEnum.CONNECTED

    def get_stream_info(self) -> Dict[str, Any]:
        """Returns recorded footage catalog and HTTP 206 playback URLs."""
        records = self._get_footage_records()
        footage_items = []
        for ft in records:
            dur = ft.duration_seconds or 0.0
            footage_items.append({
                "id": ft.id,
                "file_name": ft.file_name,
                "original_file_name": ft.original_file_name or ft.file_name,
                "duration_seconds": ft.duration_seconds,
                "formatted_duration": yolo_service.format_timestamp(dur) if dur > 0 else "00:00.0",
                "file_size_bytes": ft.file_size or 0,
                "stream_url": f"/api/footage/{ft.id}/stream",
                "created_at": ft.created_at.isoformat() if ft.created_at else None,
            })

        has_footage = len(footage_items) > 0
        return {
            "camera_id": self.camera_id,
            "camera_code": self.camera_code,
            "connectivity_type": "FILE",
            "playback_mode": PlaybackModeEnum.RECORDED_STREAM.value,
            "stream_status": StreamStatusEnum.CONNECTED.value if has_footage else StreamStatusEnum.NOT_CONFIGURED.value,
            "is_configured": has_footage,
            "is_playable_in_browser": has_footage,
            "relay_stream_url": footage_items[0]["stream_url"] if has_footage else None,
            "media_relay_status": "Native HTTP 206 Byte-Range Video Streaming",
            "status_message": f"{len(footage_items)} recorded CCTV file(s) available for playback.",
            "footage_count": len(footage_items),
            "available_footage": footage_items,
        }

    def health_check(self, session: StreamSession) -> StreamHealthStatus:
        """Verifies footage storage access."""
        records = self._get_footage_records()
        if records and records[0].file_path and Path(records[0].file_path).exists():
            return StreamHealthStatus(status=StreamStatusEnum.CONNECTED, latency_ms=1.0)
        return StreamHealthStatus(status=StreamStatusEnum.ERROR, error="Footage storage inaccessible.")
