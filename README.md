# Gujarat CCTV Intelligence Platform 🚔

[![Gujarat Police Innovation Hackathon 2026](https://img.shields.io/badge/Gujarat%20Police-Hackathon%202026-blue.svg)](https://gujaratpolice.gov.in)
[![Milestone](https://img.shields.io/badge/Milestone-1%20Project%20Foundation-emerald.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL%2BPostGIS-Spatial-336791.svg)](https://postgis.net)

Proof of Concept developed for the **Gujarat Police Innovation Hackathon 2026**.

- **Selected Solution**: Model 2 – Unified Viewing and Selective Analytics
- **Mandatory Foundation**: Model 1 – CCTV Registry and GIS Foundation

---

## 1. Project Purpose 🎯

The **Gujarat CCTV Intelligence Platform** is a scalable, modular surveillance intelligence solution tailored for Gujarat Police operations. 

In real-world police scenarios, thousands of CCTV cameras across traffic intersections, toll plazas, crime hotspots, and public venues stream continuous video feeds. Operating full AI analytics on all feeds simultaneously is computationally prohibitive.

This platform solves that problem in two key phases:
1. **Model 1 (Registry & GIS Foundation)**: Centralizes all CCTV cameras across jurisdictions with spatial coordinates, coverage zones, stream metadata, and camera status.
2. **Model 2 (Unified Viewing & Selective Analytics)**: Allows police operators in command centers to view unified feeds and selectively activate targeted AI analytics (such as vehicle tracking, ANPR, and object detection) on high-priority cameras on-demand.

> [!NOTE]
> **Milestone 1 — Project Foundation** establishes the clean multi-tier architecture, environment configuration, database connectivity layer, FastAPI backend with health endpoints, and a React + Vite dashboard placeholder.

---

## 2. Technology Stack 💻

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons | Police Command Center UI Dashboard |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 | High-performance Asynchronous REST API |
| **Database** | PostgreSQL + PostGIS, SQLAlchemy 2.0, GeoAlchemy2 | Geospatial Data & Camera Registry Storage |
| **Configuration** | Pydantic Settings, python-dotenv | Secure environment variable handling |

---

## 3. Project Structure 📁

```text
gujarat-cctv-platform/
├── frontend/                     # React + Vite Command Center Dashboard
│   ├── src/
│   │   ├── components/           # UI Components
│   │   ├── App.jsx               # Main Dashboard with Live Status
│   │   ├── main.jsx              # React Entrypoint
│   │   └── index.css             # Tailwind Styles
│   ├── index.html                # HTML Document
│   ├── vite.config.js            # Vite Configuration & API Proxy
│   ├── tailwind.config.js        # Tailwind Theme Configuration
│   └── package.json              # Frontend Dependencies
│
├── backend/                      # Python FastAPI REST API
│   ├── app/
│   │   ├── main.py               # FastAPI App Initialization & CORS
│   │   ├── api/                  # API Routers & Endpoints
│   │   │   └── v1/
│   │   │       ├── router.py     # Endpoint Aggregator
│   │   │       └── endpoints/
│   │   │           └── health.py # Health Check Route (/api/health)
│   │   ├── core/
│   │   │   └── config.py         # Pydantic App Settings (.env loader)
│   │   ├── database/
│   │   │   ├── base.py           # SQLAlchemy Declarative Base
│   │   │   └── session.py        # Database Engine & Session Generator
│   │   ├── models/               # SQLAlchemy ORM Models (Milestone 2+)
│   │   ├── schemas/              # Pydantic Schemas & DTOs
│   │   │   └── health.py         # Health Check Schemas
│   │   └── services/             # Business Logic & Services (Milestone 2+)
│   ├── run.py                    # Backend Launcher Script
│   └── requirements.txt          # Python Dependencies
│
├── database/                     # Database Migrations & GIS Scripts
│   ├── init-scripts/
│   │   └── 01_init_postgis.sql   # PostGIS Extension Init Script
│   └── README.md
│
├── ai/                           # AI / Analytics Pipelines (Milestone 4+)
├── streams/                      # RTSP / Video Stream Handling (Milestone 3+)
├── sample-data/                  # Mock Video Feeds & GIS Shapefiles
├── storage/                      # Local Media & Snapshots (Git Ignored)
├── docs/                         # Project Architecture & Notes
├── .gitignore                    # Git Ignore Rules
├── .env.example                  # Environment Variables Template
└── README.md                     # Project Guide & Documentation
```

---

## 4. Setup & Running Instructions (Windows) 🚀

Follow these beginner-friendly step-by-step instructions in PowerShell or Windows Command Prompt.

### Step A: Configure Environment Variables

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd "E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform"
   ```

2. Copy the `.env.example` file to create your local `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

---

### Step B: How to Start PostgreSQL + PostGIS

#### Option 1: Using Installed PostgreSQL on Windows
1. If PostgreSQL is installed, start the PostgreSQL service:
   ```powershell
   Start-Service postgresql*
   ```
2. Open pgAdmin or `psql` and create the platform database:
   ```sql
   CREATE DATABASE gujarat_cctv_db;
   \c gujarat_cctv_db
   CREATE EXTENSION postgis;
   ```

#### Option 2: Using Docker (Recommended for Portability)
If you have Docker installed, you can start PostgreSQL with PostGIS in one command:
```powershell
docker run --name gujarat-cctv-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=gujarat_cctv_db -p 5432:5432 -d postgis/postgis:16-3.4
```

> **Note**: The backend will run and serve `/api/health` even if PostgreSQL is not started yet. The database connection is handled gracefully with diagnostics.

---

### Step C: How to Start FastAPI (Backend)

1. Open a new PowerShell window and navigate to the `backend` folder:
   ```powershell
   cd "E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform\backend"
   ```

2. Activate the Python virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled in PowerShell, you can run directly using `.\.venv\Scripts\python.exe run.py`)*

3. Start the FastAPI development server:
   ```powershell
   python run.py
   ```
   Or using Uvicorn directly:
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. You will see:
   ```text
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   INFO:     Application startup complete.
   ```

---

### Step D: How to Start React (Frontend)

1. Open another PowerShell window and navigate to the `frontend` folder:
   ```powershell
   cd "E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform\frontend"
   ```

2. Start the Vite development server:
   ```powershell
   cmd /c npm run dev
   ```

3. You will see:
   ```text
     VITE v5.1.6  ready in 250 ms

     ➜  Local:   http://localhost:5173/
     ➜  Network: use --host to expose
   ```

4. Open `http://localhost:5173` in your browser.

---

## 5. How to Test the Health API 🧪

### Test via Web Browser
- Open: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Interactive Swagger UI Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Test via PowerShell
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" | ConvertTo-Json
```

### Expected Response:
```json
{
  "status": "ok",
  "service": "Gujarat CCTV Intelligence Platform",
  "version": "1.0.0",
  "database": null
}
```

---

## 6. Verification Checklist ✅

- [x] Directory structure created
- [x] `.gitignore` and `.env.example` created
- [x] Backend FastAPI application created with `/api/health`
- [x] Database configuration with PostgreSQL + PostGIS support
- [x] React + Vite frontend dashboard showing **"Gujarat CCTV Intelligence Platform"** and **"System Status: Connected"**
- [x] Real-time health polling between frontend and backend verified
- [x] Detailed beginner-friendly documentation created

---

## 7. Next Steps (Upcoming Milestones) 🔮

- **Milestone 2**: Model 1 — CCTV Registry & GIS Foundation (Camera CRUD, PostGIS spatial models, GeoJSON map visualization).
- **Milestone 3**: Model 2 — Unified Multi-Camera Stream Viewing (HLS/WebRTC streaming grid).
- **Milestone 4**: Selective AI Analytics (On-demand YOLO detection, ANPR, vehicle tracking).
- **Milestone 5**: Command Center Alerting & Incident Reports.
