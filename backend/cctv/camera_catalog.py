import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

CCTV_MODE = os.getenv("CCTV_MODE", "mock").lower()
CCTV_GATEWAY_HOST = os.getenv("CCTV_GATEWAY_HOST", "localhost:8000")

cached_catalogue: List[Dict[str, Any]] = []

def fetch_catalogue(target_host: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Queries GET http://<host>/api/ingest as required by Section 1 Hackathon Spec.
    Returns list of camera metadata dictionary objects.
    """
    global cached_catalogue
    host = target_host or os.getenv("CCTV_GATEWAY_HOST", "localhost:8000")
    url = f"http://{host}/api/ingest" if not host.startswith("http") else f"{host}/api/ingest"

    if os.getenv("CCTV_MODE", "mock").lower() == "hackathon":
        print(f"[CameraCatalog] Querying Hackathon Gateway: {url}")
        try:
            resp = requests.get(url, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                cached_catalogue = data.get("cameras", [])
                return cached_catalogue
        except Exception as e:
            print(f"[CameraCatalog] Ingest query error ({url}): {e}")

    # Mock / Fallback Catalogue Mode
    clean_host = host.split(':')[0].replace("http://", "")
    cached_catalogue = [
        {
            "id": "1",
            "location": "Gandhinagar HQ Gate 1",
            "codec": "h264",
            "resolution": "1920x1080",
            "fps": 25,
            "live_status": True,
            "stream_urls": {
                "rtsp": f"rtsp://{clean_host}:8554/stream/1",
                "whep": f"http://{clean_host}:8889/stream/1/whep",
                "hls": f"http://{clean_host}/live/stream/1/index.m3u8"
            }
        },
        {
            "id": "2",
            "location": "Ahmedabad SG Highway Junction",
            "codec": "h265",
            "resolution": "1920x1080",
            "fps": 30,
            "live_status": True,
            "stream_urls": {
                "rtsp": f"rtsp://{clean_host}:8554/stream/2",
                "whep": f"http://{clean_host}:8889/stream/2/whep",
                "hls": f"http://{clean_host}/live/stream/2/index.m3u8"
            }
        },
        {
            "id": "3",
            "location": "Surat Ring Road Toll",
            "codec": "h264",
            "resolution": "1280x720",
            "fps": 25,
            "live_status": True,
            "stream_urls": {
                "rtsp": f"rtsp://{clean_host}:8554/stream/3",
                "whep": f"http://{clean_host}:8889/stream/3/whep",
                "hls": f"http://{clean_host}/live/stream/3/index.m3u8"
            }
        }
    ]
    return cached_catalogue

def get_camera_metadata(camera_id: str) -> Optional[Dict[str, Any]]:
    catalogue = fetch_catalogue()
    for cam in catalogue:
        if str(cam.get("id")) == str(camera_id):
            return cam
    return None
