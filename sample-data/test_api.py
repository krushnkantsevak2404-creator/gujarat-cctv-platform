import urllib.request
import urllib.parse
import json
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
video_path = Path(r"E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform\sample-data\videos\sample_cctv_clip.mp4")

# Multipart form-data upload using python
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = []
body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="file"; filename="sample_cctv_clip.mp4"')
body.append(b"Content-Type: video/mp4")
body.append(b"")
with open(video_path, "rb") as f:
    body.append(f.read())
body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="description"')
body.append(b"")
body.append(b"Sample traffic video clip for Iskcon junction")
body.append(f"--{boundary}--".encode())
body.append(b"")

payload = b"\r\n".join(body)

req = urllib.request.Request(
    f"{BASE_URL}/api/cameras/1/footage",
    data=payload,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(f"UPLOAD SUCCESS: ID={data['id']}, Stream URL={data['stream_url']}, Size={data['file_size']} bytes")
        footage_id = data["id"]
        
        # Test Stream GET
        stream_url = f"{BASE_URL}{data['stream_url']}"
        stream_req = urllib.request.Request(stream_url, headers={"Range": "bytes=0-50"})
        with urllib.request.urlopen(stream_req) as s_resp:
            print(f"STREAM SUCCESS: Status={s_resp.status}, Content-Range={s_resp.headers.get('Content-Range')}")
            
        # Test Footage List
        with urllib.request.urlopen(f"{BASE_URL}/api/cameras/1/footage") as l_resp:
            flist = json.loads(l_resp.read().decode())
            print(f"LIST SUCCESS: Total clips for Camera 1 = {len(flist)}")
except Exception as e:
    print(f"ERROR: {e}")
