"""
Video Processing & Storage Service
Handles safe file storage, metadata extraction, validation, and HTTP 206 video streaming.
"""

import os
import uuid
import re
import struct
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Generator
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")


def sanitize_filename(filename: str) -> str:
    """Removes unsafe characters and returns base name."""
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(filename).name)
    return clean[:100] if clean else "footage"


def generate_safe_filename(original_filename: str) -> str:
    """Generates unique UUID-based safe storage filename."""
    ext = Path(original_filename).suffix.lower().lstrip(".")
    if not ext or ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        ext = "mp4"
    return f"{uuid.uuid4().hex}.{ext}"


def get_camera_storage_dir(camera_id: int) -> Path:
    """Gets and ensures storage directory for a specific camera."""
    cam_dir = settings.footage_storage_path / f"camera_{camera_id}"
    
    # Path traversal security check
    try:
        resolved_cam_dir = cam_dir.resolve()
        resolved_storage = settings.footage_storage_path.resolve()
        if not str(resolved_cam_dir).startswith(str(resolved_storage)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Error: Invalid storage path traversal detected",
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path resolution error: {e}",
        )

    cam_dir.mkdir(parents=True, exist_ok=True)
    return cam_dir


def extract_video_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extracts video metadata (dimensions, fps, duration, frame count).
    Attempts OpenCV if available, else falls back to binary MP4 parsing / defaults.
    """
    metadata: Dict[str, Any] = {
        "width": None,
        "height": None,
        "fps": None,
        "frame_count": None,
        "duration_seconds": None,
    }

    # Method 1: Try OpenCV if installed
    try:
        import cv2
        cap = cv2.VideoCapture(str(file_path))
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            duration = None
            if fps > 0 and frame_count > 0:
                duration = round(frame_count / fps, 2)
            
            cap.release()

            if width > 0 and height > 0:
                metadata["width"] = width
                metadata["height"] = height
                metadata["fps"] = round(fps, 2) if fps > 0 else None
                metadata["frame_count"] = frame_count if frame_count > 0 else None
                metadata["duration_seconds"] = duration
                return metadata
    except Exception as e:
        logger.debug(f"OpenCV metadata extraction skipped/failed: {e}")

    # Method 2: Pure Python MP4 header parser for duration / dimensions
    try:
        metadata.update(_parse_mp4_header(file_path))
    except Exception as e:
        logger.debug(f"Pure python MP4 parser failed: {e}")

    return metadata


def _parse_mp4_header(file_path: Path) -> Dict[str, Any]:
    """Lightweight pure-python parser for MP4 'mvhd' atom duration & dimensions."""
    res: Dict[str, Any] = {}
    with open(file_path, "rb") as f:
        data = f.read(1024 * 64)  # Read initial header chunk
        # Look for mvhd atom
        mvhd_idx = data.find(b"mvhd")
        if mvhd_idx != -1 and len(data) >= mvhd_idx + 24:
            version = data[mvhd_idx + 4]
            if version == 0:
                timescale = struct.unpack(">I", data[mvhd_idx + 16 : mvhd_idx + 20])[0]
                duration = struct.unpack(">I", data[mvhd_idx + 20 : mvhd_idx + 24])[0]
                if timescale > 0:
                    res["duration_seconds"] = round(duration / timescale, 2)
    return res


def create_range_streaming_response(
    file_path: Path, range_header: Optional[str], mime_type: str = "video/mp4"
) -> StreamingResponse:
    """
    Constructs an HTTP 206 Partial Content or HTTP 200 StreamingResponse
    to enable fast video seeking and streaming in HTML5 video players.
    """
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Footage video file not found on disk",
        )

    file_size = file_path.stat().st_size
    start = 0
    end = file_size - 1

    if range_header:
        # Example range header: bytes=0-1048575
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start_str, end_str = range_match.groups()
            start = int(start_str)
            if end_str:
                end = int(end_str)
            else:
                # Default chunk size of 2MB
                chunk_size = 2 * 1024 * 1024
                end = min(start + chunk_size - 1, file_size - 1)

    if start >= file_size or start > end:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            headers={"Content-Range": f"bytes */{file_size}"},
            detail="Requested range outside file boundaries",
        )

    content_length = end - start + 1

    def iterfile() -> Generator[bytes, None, None]:
        with open(file_path, "rb") as video:
            video.seek(start)
            bytes_left = content_length
            while bytes_left > 0:
                chunk = video.read(min(bytes_left, 64 * 1024))
                if not chunk:
                    break
                bytes_left -= len(chunk)
                yield chunk

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": mime_type or "video/mp4",
    }

    return StreamingResponse(
        iterfile(),
        status_code=status.HTTP_206_PARTIAL_CONTENT if range_header else status.HTTP_200_OK,
        headers=headers,
    )
