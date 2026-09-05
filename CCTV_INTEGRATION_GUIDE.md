# Gujarat Police Hackathon 2026 - CCTV Live Integration Guide

This guide documents the integration of the **Gujarat Police Hackathon 2026 CCTV Live-Stream Architecture** into our solution.

---

## 1. How the CCTV Integration Works

The system architecture connects live CCTV camera streams from the hackathon gateway into our Python AI tracking pipeline and Web Command Center UI:

```text
Hackathon Gateway (/api/ingest)
       ↓
  CCTV Service (FastAPI)
       ↓
OpenCV VideoCapture (RTSP over TCP)
       ↓
Presentation Timestamps (PTS Monotonic)
       ↓
AI Detection & Tracking Pipeline
       ↓
SQLite Events Database (Event Metadata Only)
       ↓
Web Command Dashboard UI (WHEP / HLS / MJPEG)
```

- **Load Management**: Streams are opened only when explicitly requested (`POST /api/cameras/{id}/start`) and released when stopped (`POST /api/cameras/{id}/stop`).
- **No Full Video Downloads**: The system consumes live streams directly over memory buffers without downloading MP4 video files to disk.

---

## 2. How `/api/ingest` is Used

The backend `CCTVStreamService` calls `GET http://<host>/api/ingest` at startup and on demand to fetch the active camera catalogue:

- It reads camera metadata: `id`, `location`, `codec`, `resolution`, `fps`, `live_status`, and stream URLs (`rtsp`, `whep`, `hls`).
- It does **NOT** hard-code camera IP addresses or credentials.
- Camera IDs and available streams are dynamic; the backend validates the payload and exposes `GET /api/cameras` to the frontend.

---

## 3. How to Configure the Official Gateway Host

To set or change the official hackathon gateway host, update the `.env` file in the `backend/` directory:

```env
CCTV_GATEWAY_HOST=cctv-gateway.gujarat.gov.in:8000
```
Or set the environment variable in your terminal:
```bash
export CCTV_GATEWAY_HOST=192.168.1.100:8000
```

---

## 4. How to Run Mock / Local Video Mode

For offline testing without live hardware or gateway credentials, set `CCTV_MODE=mock` in `backend/.env`:

```env
CCTV_MODE=mock
CCTV_MOCK_VIDEO_PATH=data/sample.mp4
```

In Mock Mode:
- If `data/sample.mp4` exists, OpenCV reads and loops the local sample video.
- If `data/sample.mp4` does not exist, a high-definition synthetic camera HUD generator renders frames automatically.

---

## 5. How to Switch to Hackathon Mode

To switch to the live hackathon CCTV network:

1. Edit `backend/.env`:
   ```env
   CCTV_MODE=hackathon
   CCTV_GATEWAY_HOST=<official-gateway-host>
   ```
2. Restart the backend server. The service will immediately query `/api/ingest` on the official host and stream live RTSP feeds over TCP.

---

## 6. How RTSP over TCP is Configured

OpenCV FFMPEG capture options are configured at system initialization in `backend/cctv_manager.py`:

```python
import os
import cv2

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
```
This forces RTSP over TCP, eliminating UDP packet drop and frame corruption across NATs and firewalls.

---

## 7. How PTS Timestamps are Used

All timing, movement, and velocity calculations are driven **strictly by Presentation Timestamps (PTS)**:

```python
pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
delta_pts_ms = pts_ms - previous_pts_ms
```

- **Wall-clock time (`time.time()`) and `CAP_PROP_FPS` are ignored** for speed/dwell calculations.
- Using PTS ensures accurate tracking even during initial GoP replay bursts or variable frame rate gaps.

---

## 8. How Reconnect / Backoff Works

When a stream drops or encounters network interruption:

1. The capture thread catches the failure (`if not ok:`).
2. It releases the OpenCV `VideoCapture` cleanly.
3. It applies exponential backoff: **2 s → 4 s → 8 s → 16 s → 30 s max cap**.
4. It logs the connection failure clearly without crashing the backend or looping tightly.

---

## 9. How Mixed H.264 / H.265 Streams are Handled

- Per-camera properties (`codec`, `resolution`) are parsed dynamically from `/api/ingest`.
- Mid-stream join decode warnings (`Error constructing frame RPS`, `Could not find ref with POC`) are caught and logged as non-fatal, allowing the stream to recover as soon as the first IDR keyframe arrives.
- The AI inference pipeline resizes frames dynamically without hardcoding input matrix shapes.

---

## 10. How WebRTC / HLS Preview Works

The catalogue payload provides three protocol URLs per camera:
- **RTSP**: `rtsp://<host>:8554/stream/<id>` (Used by backend for OpenCV AI inference).
- **WebRTC (WHEP)**: `http://<host>:8889/stream/<id>/whep` (For ultra-low latency browser playback).
- **HLS**: `http://<host>/live/stream/<id>/index.m3u8` (For standard dashboard & mobile network playback).

The frontend UI displays protocol badges and links for each camera.

---

## 11. How to Run the Backend

```bash
cd C:\Users\ABCD\.gemini\antigravity-ide\scratch\gujarat-police-cctv\backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run FastAPI Server
python app.py
```
The server will start on `http://localhost:8000`.

---

## 12. How to Run the Frontend

Open `http://localhost:8000` in your web browser, or open [frontend/index.html](file:///C:/Users/ABCD/.gemini/antigravity-ide/scratch/gujarat-police-cctv/frontend/index.html) directly.

---

## 13. How to Test the System

### Test 1: Verify Mock Mode & API Catalogue
1. Start the server (`python backend/app.py`).
2. Open `http://localhost:8000/api/ingest` in your browser.
3. Verify that the JSON response returns cameras, `cctv_mode: "mock"`, and stream URLs.

### Test 2: Test Load Management (Start / Stop Stream)
1. Open the Web Dashboard at `http://localhost:8000`.
2. Select Camera #1 from the dropdown and click **START STREAM**.
3. Verify that live video frames appear with PTS timestamps updating (`PTS: <ms> | Δ: <ms>`).
4. Click **STOP STREAM**. Verify that capture stops and OpenCV resources are released.

### Test 3: Check Event Persistence Database
1. Query `http://localhost:8000/api/events`.
2. Verify that detection events logged during stream processing are stored with `camera_id`, `pts_ms`, `delta_pts_ms`, and `object_type`.
