# Gujarat Police Hackathon 2026 - Modular AI-CCTV System

A modular, high-performance Command & Control Center Surveillance Portal designed for the Gujarat Police Hackathon 2026.

---

## 🏗️ Project Architecture

```text
AI-CCTV-Project/
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── backend/
│   ├── main.py             <-- Application Entry Point
│   ├── cctv/
│   │   ├── camera_catalog.py <-- Ingest Catalogue Service (/api/ingest)
│   │   ├── stream.py         <-- OpenCV RTSP over TCP Reader & Reconnect
│   │   ├── tracker.py        <-- PTS Monotonic Object Tracker
│   │   └── test_camera.py    <-- Standalone RTSP Stream Test Script
│   │
│   ├── api/
│   │   └── cameras.py        <-- REST Endpoints (/api/cameras, /api/events)
│   │
│   └── ai/
│       └── detector.py       <-- AI Object Detection Model Interface
│
├── models/                   <-- Weights (ONNX, YOLO)
│
└── README.md
```

---

## 🔄 Execution & Data Flow

```text
                    BACKEND
                       │
              GET /api/ingest
                       │
                Camera Catalogue
                       │
                 Select Camera (POST /api/cameras/{id}/start)
                       │
                    RTSP (TCP Mode)
                       │
                  OpenCV VideoCapture
                       │
             Video Frame + PTS Timestamp
                       │
                AI Detector (ai/detector.py)
                       │
             Tracker (cctv/tracker.py)
                       │
                Detection Events
                       │
             SQLite Database (database.py)
                       │
                  FRONTEND UI
```

---

## 🚀 Running the Project

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Launch Backend
```bash
python main.py
# or: python app.py
```
*(Runs on `http://localhost:8000`)*

### 3. Open Frontend Dashboard
Open `http://localhost:8000` in your web browser.

---

## 🧪 Testing Standalone RTSP Capture
Run `test_camera.py` to test raw RTSP capture over TCP:
```bash
python cctv/test_camera.py
```
