# Gujarat CCTV Intelligence Platform 🚔

[![Gujarat Police Innovation Hackathon 2026](https://img.shields.io/badge/Gujarat%20Police-Hackathon%202026-blue.svg)](https://gujaratpolice.gov.in)
[![Milestone 6 Active](https://img.shields.io/badge/Milestone-6%20ANPR%20%2B%20OCR-emerald.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL%2BPostGIS-Spatial-336791.svg)](https://postgis.net)
[![YOLOv8 + ByteTrack](https://img.shields.io/badge/AI-YOLOv8%20%2B%20ByteTrack-FF6F00.svg)](https://ultralytics.com)
[![EasyOCR](https://img.shields.io/badge/OCR-EasyOCR%20(Indian%20Syntax)-purple.svg)](https://github.com/JaidedAI/EasyOCR)

Proof of Concept developed for the **Gujarat Police Innovation Hackathon 2026**.

- **Selected Solution**: Model 2 – Unified Viewing and Selective Analytics
- **Mandatory Foundation**: Model 1 – CCTV Registry and GIS Foundation

---

## 1. Project Overview 🎯

The **Gujarat CCTV Intelligence Platform** is a centralized surveillance intelligence application designed for Gujarat Police command and control centers. 

Thousands of CCTV cameras across traffic intersections, toll plazas, crime hotspots, and public venues stream continuous video feeds. Operating full AI analytics on all feeds simultaneously is computationally prohibitive.

This platform solves that challenge in two core models:
1. **Model 1 (CCTV Registry & GIS Foundation)**: Centralizes all CCTV cameras across jurisdictions with spatial coordinates (PostGIS SRID 4326), coverage zones, stream metadata, and camera status on an interactive Leaflet GIS map.
2. **Model 2 (Unified Viewing & Selective Analytics)**: Allows police operators to view unified feeds and selectively activate targeted AI analytics (YOLOv8 Vehicle Detection, ByteTrack Multi-Object Tracking, and Automatic Number Plate Recognition with EasyOCR) on-demand.

---

## 2. Implemented Features (Milestones 1–6) 🚀

- **Milestone 1 — Project Foundation**: FastAPI backend, React 18 frontend with police theme, health checks, and diagnostics.
- **Milestone 2 — CCTV Registry & Recorded CCTV Footage**: Camera CRUD, PostgreSQL/PostGIS registry with persistent SQLite fallback, video upload, and HTTP 206 partial content streaming.
- **Milestone 3 — GIS Camera Map**: Interactive Leaflet map with custom status markers, location popups, and GeoJSON export (`/api/cameras/geojson`).
- **Milestone 4 — YOLOv8 Vehicle Detection**: Real-time bounding box detection for cars, motorcycles, buses, and trucks across video frames.
- **Milestone 5 — Multi-Object Vehicle Tracking**: ByteTrack temporal tracking across frames, Track IDs, centroid motion trails, representative vehicle crops, and click-to-seek video seeking.
- **Milestone 6 — ANPR & OCR Intelligence**: Automatic Number Plate Recognition using EasyOCR, Indian license plate syntax validation (`GJ01AB1234`, `22BH1234AA`), multi-frame deduplication, and cross-camera plate search.
- **Milestone 7 — Watchlist + Automatic Alerts**: Authorized watchlist database matching, configurable severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), temporal deduplication, and real-time surveillance alerts.
- **Milestone 8 — Vehicle Search & Observed Camera Detection Sequence**: Vehicle number search, chronological multi-camera timeline traversal, traversal duration & route sequence cards, and GIS map popup integration.
- **Milestone 9 — Unified Multi-Camera CCTV Viewer**: Dynamic grid layouts (1x1, 2x1, 2x2, 3x2, 3x3), camera sidebar with real-time filters, synchronized seek bars, and cross-module deep linking.
- **Milestone 10 — Authorized RTSP/VMS Integration & Stream Adapter Layer**: Modular backend stream adapter architecture (`StreamManager`, `RTSPAdapter`, `RecordedFootageAdapter`, `VMSAdapter`, `ONVIFAdapter`, `SDKAdapter`), live HTTP/MJPEG browser media relay, RTSP credential protection, and connect/disconnect stream lifecycle.

---

## 3. Technology Stack 💻

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Leaflet, Lucide Icons | Police Command Center UI Dashboard & Multi-Camera Viewer |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 | High-performance Asynchronous REST API |
| **Stream Adapter Layer** | `StreamManager`, OpenCV, MJPEG Relay, HLS Adapter | Authorized RTSP, Recorded Footage & VMS Streaming |
| **Database** | PostgreSQL + PostGIS, GeoAlchemy2, SQLAlchemy 2.0 (with SQLite fallback) | Spatial GIS & CCTV Registry Storage |
| **Object Detection & Tracking** | YOLOv8 (Nano), ByteTrack, PyTorch, OpenCV | Vehicle Localization, Trajectories & Crops |
| **ANPR & OCR** | EasyOCR, CLAHE Contrast Enhancement, Otsu Binarization | Number Plate Localization & Character Extraction |
| **Configuration** | Pydantic Settings, python-dotenv | Secure environment variable handling |

---

## 4. Authorized Live Stream Integration (Model 2 Architecture) 📡

```text
Existing Departmental CCTV / VMS / Recorded Sources
                      ↓
           [Stream Adapter Layer]
     ┌───────────────┬───────────────┬──────────────┐
     │ RTSPAdapter   │ RecordedAdapter│ VMSAdapter   │ (ONVIF/SDK Placeholders)
     └───────┬───────┴───────┬───────┴──────┬───────┘
             └───────────────┼──────────────┘
                             ↓
                      [StreamManager]
              (Session lifecycle, health check,
               resource cleanup & deduplication)
                             ↓
              [Media Relay / Stream Engine]
          (HTTP/MJPEG Relay, HLS Adapter Status)
                             ↓
            [Unified Multi-Camera CCTV Viewer]
```

### Model 2 Integration Principles:
1. **Departmental VMS Independence**: Legacy departmental video storage and VMS systems remain intact and autonomous. The platform acts as a secure, unified integration layer without requiring central video migration.
2. **Authorized Sources Only**: The platform connects strictly to cameras registered in the database. **Zero unauthorized camera discovery, zero IP/port scanning, and zero credential brute-forcing.**
3. **Strict Credential Protection**: RTSP credentials (`username:password`) are stripped from API responses, sanitized in logs (`rtsp://****:****@host:554/stream`), and stored safely server-side.
4. **Browser RTSP Limitation Handled**: Modern browsers cannot natively play raw `rtsp://` via HTML5 video elements. The backend media relay transcodes authorized streams into browser-compatible HTTP/MJPEG streams (`/api/streams/{camera_id}/live`) and HLS relays.
5. **Reliable Recorded Fallback**: Recorded MP4 footage remains the 100% reliable fallback demo when external live streams are offline.
6. **Future VMS & ONVIF Extensibility**: Modular adapter placeholders (`VMSAdapter`, `ONVIFAdapter`, `SDKAdapter`) allow seamless future integration with vendor APIs (Milestone, Genetec, Hanwha) without rewriting core platform code.

---

## 5. Quick Setup Summary ⚡

For the complete, beginner-friendly setup guide, see **[`RUN_PROJECT.txt`](RUN_PROJECT.txt)**.

### Prerequisites:
- Python 3.10 to 3.12 (64-bit)
- Node.js v18+ / v20+ LTS
- PostgreSQL 14+ with PostGIS (optional, automatic SQLite fallback active)

### 1. Backend Setup:
```powershell
# Create & activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment file
copy .env.example .env

# Run FastAPI server
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup:
```powershell
# Open a second terminal
cd frontend
npm install
npm run dev
```

### 3. Access Dashboards:
- **Frontend Dashboard**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend API & Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 6. Operational Command Dashboard & Health Monitoring 📊

Milestone 11 establishes a real-time, dynamic **Operational Command Dashboard** designed for police command centers:

### Core Capabilities:
- **Dynamic Infrastructure Telemetry**: Real-time KPI summary cards (Total Cameras, Online, Offline, Maintenance/Unknown, Live Sources, Recorded Sources, Active Alerts, Vehicle Observations) computed dynamically from database records (zero hardcoded/fake numbers).
- **Fleet Distribution & Progress Gauges**: Visual health breakdown (`Online █████████`, `Offline ███`, `Maintenance ██`, `Unknown █`) with interactive click-to-filter capabilities.
- **Dynamic Department Breakdown**: Aggregates camera counts, live feeds, and active alert badges across all registered police departments (Traffic Police, City Surveillance, Highway Patrol, Industrial Security, etc.).
- **Camera Registration vs. Stream Session Separation**: Preserves permanent camera registration status (`ONLINE`, `OFFLINE`, `MAINTENANCE`, `UNKNOWN`) while reporting transient live stream session statuses (`CONNECTED`, `DISCONNECTED`, `NOT_CONFIGURED`, `ERROR`) independently.
- **Recent Watchlist Alerts Feed**: Live stream of high/critical alerts with severity badges, vehicle license plates, camera locations, and direct navigation.
- **Genuine Vehicle Analytics**: Database-backed counters for ANPR plate observations, YOLOv8 detections, ByteTrack trajectories, and watchlist matches.
- **System Health Diagnostics (`/api/health/system`)**: Automated verification of Backend API, Relational Database, GIS Map, AI Engine, and Live Stream Relay without credential leakage.
- **Configurable Auto-Refresh & Timestamps**: Configurable periodic polling (15s, 30s, 60s, OFF) with "Last updated X seconds ago" indicators.

---

## 7. Security & Operational Guidelines 🛡️

> [!IMPORTANT]
> **Only authorized CCTV sources may be configured and connected.**

- **DO NOT commit `.env` files, passwords, or tokens to GitHub.**
- **DO NOT commit live police feed credentials, API keys, or private streams.**
- **DO NOT scan the internet, IP ranges, or perform port scanning for CCTV cameras.**
- **DO NOT guess RTSP URLs or attempt authentication bypass.**
- Use only locally authorized sample footage or officially provided hackathon feeds.
- Large video clips (`*.mp4`, `*.avi`, `*.mov`) and model weights are excluded from Git via `.gitignore`.

---

## 8. Detailed Team Documentation 📖

Please refer to **[`RUN_PROJECT.txt`](RUN_PROJECT.txt)** for complete step-by-step installation instructions, PostgreSQL setup, PostGIS configuration, Git branch workflow, and common troubleshooting tips.

