import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.cameras import router as cameras_router
from cctv_manager import cctv_service

app = FastAPI(
    title="Gujarat Police CCTV Integration Hub",
    description="Official Modular Architecture for Gujarat Police Hackathon 2026 CCTV Live-Stream Architecture",
    version="3.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular API Routes
app.include_router(cameras_router)

def generate_mjpeg_stream(camera_id: str):
    while True:
        stream = cctv_service.get_stream(camera_id)
        if not stream:
            break
        jpeg_bytes = stream.get_jpeg_frame()
        if jpeg_bytes:
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'
            )
        time.sleep(0.033)

@app.get("/api/stream/{camera_id}")
def video_feed(camera_id: str):
    """Live video stream endpoint."""
    stream = cctv_service.get_stream(camera_id)
    if not stream:
        # Auto-start stream on direct video request
        stream = cctv_service.start_camera(camera_id)

    return StreamingResponse(
        generate_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# Static file serving for Frontend UI
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_root():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Gujarat Police CCTV Gateway Client running cleanly."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
