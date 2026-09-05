import os
import cv2
import time
import numpy as np
from typing import Generator, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

# Section 3 Rule: DO - Force RTSP over TCP
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

def connect_camera(rtsp_url: str, retry_count: int = 0) -> Optional[cv2.VideoCapture]:
    """
    Establishes an RTSP camera connection over TCP using OpenCV FFMPEG.
    Includes exponential backoff retry (2s, 4s, 8s, 16s, 30s max cap).
    """
    mode = os.getenv("CCTV_MODE", "mock").lower()
    mock_video_path = os.getenv("CCTV_MOCK_VIDEO_PATH", "data/sample.mp4")

    # Mock mode local sample video fallback
    if mode == "mock" or rtsp_url.startswith("synthetic://") or "<host>" in rtsp_url:
        if os.path.exists(mock_video_path):
            print(f"[CCTVStream] Opening local sample video: {mock_video_path}")
            cap = cv2.VideoCapture(mock_video_path)
            if cap.isOpened():
                return cap
        print("[CCTVStream] Operating in synthetic frame generator mode.")
        return None

    print(f"[CCTVStream] Connecting to RTSP over TCP: {rtsp_url}")
    try:
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                print(f"[CCTVStream] Live RTSP stream connected: {rtsp_url}")
                return cap
    except Exception as e:
        print(f"[CCTVStream] Connection warning: {e}")

    # Exponential Backoff Retry (~2s -> 30s cap)
    backoff_schedule = [2.0, 4.0, 8.0, 16.0, 30.0]
    sleep_time = backoff_schedule[min(retry_count, len(backoff_schedule) - 1)]
    print(f"[CCTVStream] Reconnecting in {sleep_time:.1f}s (Attempt #{retry_count + 1})...")
    time.sleep(sleep_time)
    return connect_camera(rtsp_url, retry_count + 1)


def read_camera(cap: Optional[cv2.VideoCapture], camera_id: str = "1") -> Generator[Tuple[np.ndarray, float], None, None]:
    """
    Yields (frame, pts_ms) continuously.
    Driven STRICTLY by Presentation Timestamps (CAP_PROP_POS_MSEC).
    """
    mode = os.getenv("CCTV_MODE", "mock").lower()
    mock_video_path = os.getenv("CCTV_MOCK_VIDEO_PATH", "data/sample.mp4")

    if cap is not None and cap.isOpened():
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                if mode == "mock" and os.path.exists(mock_video_path):
                    # Loop local sample video cleanly
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                print(f"[CCTVStream] Stream read finished or interrupted for Cam #{camera_id}.")
                break

            # Monotonic Presentation Timestamp (PTS)
            pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            if pts_ms <= 0:
                pts_ms = time.time() * 1000.0

            yield frame, pts_ms

        cap.release()

    else:
        # Synthetic Frame Generator Yield
        while True:
            t = time.time()
            pts_ms = t * 1000.0
            frame = generate_synthetic_frame(camera_id, pts_ms)
            yield frame, pts_ms
            time.sleep(0.04)


def generate_synthetic_frame(camera_id: str, pts_ms: float) -> np.ndarray:
    width, height = 640, 360
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = (20, 25, 35)

    cv2.putText(frame, f"CAM #{camera_id} | LIVE SURVEILLANCE", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, f"PTS: {int(pts_ms)} ms", (width - 170, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 240, 255), 1)
    return frame