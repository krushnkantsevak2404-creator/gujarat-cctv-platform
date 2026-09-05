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
- **Milestone 6 — ANPR & OCR Intelligence**: Automatic Number Plate Recognition using EasyOCR, Indian license plate syntax validation (`GJ01AB1234`, `22BH1234AA`), multi-frame deduplication, high-contrast Indian plate badges, and cross-camera global plate search.

---

## 3. Technology Stack 💻

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Leaflet, Lucide Icons | Police Command Center UI Dashboard |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 | High-performance Asynchronous REST API |
| **Database** | PostgreSQL + PostGIS, GeoAlchemy2, SQLAlchemy 2.0 (with SQLite fallback) | Spatial GIS & CCTV Registry Storage |
| **Object Detection & Tracking** | YOLOv8 (Nano), ByteTrack, PyTorch, OpenCV | Vehicle Localization, Trajectories & Crops |
| **ANPR & OCR** | EasyOCR, CLAHE Contrast Enhancement, Otsu Binarization | Number Plate Localization & Character Extraction |
| **Configuration** | Pydantic Settings, python-dotenv | Secure environment variable handling |

---

## 4. Architecture Pipeline 🏛️

```
                      ┌─────────────────────────────────────────┐
                      │    Uploaded Recorded CCTV Footage       │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │   YOLOv8 Detection + ByteTrack Tracking  │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │    Plate Region Candidate Localization   │
                      │   (Contour, AR, Morphological Filtering)│
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │      Adaptive Image Preprocessing       │
                      │     (CLAHE + Bilateral + Otsu Thresh)   │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │       EasyOCR Character Extraction       │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │ Indian Plate Normalization & Formatting │
                      │  (Positional Syntax & Regex Validation) │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │    Multi-Frame Track Deduplication       │
                      │     (Best Confidence Reading Saved)     │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │   PostgreSQL / SQLite Database Records  │
                      │       + Saved Crop JPEGs on Disk        │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │   FastAPI REST APIs & React Dashboard   │
                      │    (Global Search, Dossier, Player Seek)│
                      └─────────────────────────────────────────┘
```

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

## 6. Security & Operational Guidelines 🛡️

- **DO NOT commit `.env` files, passwords, or tokens to GitHub.**
- **DO NOT commit live police feed credentials, API keys, or private streams.**
- **DO NOT connect to unauthorized public CCTV cameras or IP scanners.**
- Use only locally authorized sample footage or officially provided hackathon feeds.
- Large video clips (`*.mp4`, `*.avi`, `*.mov`) are excluded from Git via `.gitignore`.

---

## 7. Current Project Limitations ⚠️

### Implemented:
- CCTV Camera Registry (CRUD, GPS, metadata, status)
- PostGIS + Leaflet GIS Interactive Map
- Recorded Footage Upload, Storage & HTTP 206 Streaming
- YOLOv8 Vehicle Detection (Car, Motorcycle, Bus, Truck)
- ByteTrack Multi-Object Tracking & Motion Trails
- ANPR & OCR (EasyOCR, Indian Plate syntax validation, deduplication)
- Central Cross-Camera License Plate Search
- Synchronized Video Seeking from Plate & Track Sightings

### Not Yet Implemented (Future Milestones):
- Watchlist management & automated alerting
- Multi-camera cross-junction journey reconstruction
- Facial recognition or biometric analytics
- Live RTSP/ONVIF streaming ingestion (future milestone)

---

## 8. Detailed Team Documentation 📖

Please refer to **[`RUN_PROJECT.txt`](RUN_PROJECT.txt)** for complete step-by-step installation instructions, PostgreSQL setup, PostGIS configuration, Git branch workflow, and common troubleshooting tips.
