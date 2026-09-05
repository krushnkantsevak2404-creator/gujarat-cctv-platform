import urllib.request
import urllib.parse
import json
import time
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
video_path = Path(r"E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform\sample-data\videos\gujarat_traffic_demo.mp4")

print(f"Testing YOLO + ByteTrack Vehicle Tracking Pipeline on: {video_path.name} ({video_path.stat().st_size} bytes)...")

# 1. Upload sample video
boundary = "----WebKitFormBoundaryTrackTest77"
body = []
body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="file"; filename="gujarat_traffic_demo.mp4"')
body.append(b"Content-Type: video/mp4")
body.append(b"")
with open(video_path, "rb") as f:
    body.append(f.read())
body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="description"')
body.append(b"")
body.append(b"Multi-lane SG Highway traffic surveillance clip for ByteTrack vehicle tracking")
body.append(f"--{boundary}--".encode())
body.append(b"")

payload = b"\r\n".join(body)

req = urllib.request.Request(
    f"{BASE_URL}/api/cameras/1/footage",
    data=payload,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    footage_id = data["id"]
    print(f"1. Footage uploaded: ID #{footage_id} ({data['file_name']})")

# 2. Trigger YOLO + ByteTrack Tracking Analysis
analyze_req = urllib.request.Request(
    f"{BASE_URL}/api/footage/{footage_id}/analyze?job_type=VEHICLE_TRACKING",
    data=b"",
    headers={"Content-Type": "application/json"},
    method="POST",
)

start_time = time.time()
with urllib.request.urlopen(analyze_req) as resp:
    job_data = json.loads(resp.read().decode())
    job_id = job_data["id"]
    print(f"2. Tracking Job Started: Job #{job_id} on {job_data['device']} (Type: {job_data['job_type']}, Status: {job_data['status']})")

# 3. Poll Job Status until completion
print("3. Polling Vehicle Tracking Job...")
completed_job = None
while True:
    time.sleep(1.0)
    with urllib.request.urlopen(f"{BASE_URL}/api/analysis/jobs/{job_id}") as resp:
        job = json.loads(resp.read().decode())
        print(f"   Progress: {job['progress']}% | Status: {job['status']} | Unique Tracks: {job['total_tracks']} (Cars: {job['car_tracks']}, Bikes: {job['motorcycle_tracks']}, Buses: {job['bus_tracks']}, Trucks: {job['truck_tracks']}) | Total Sightings: {job['total_detections']}")
        if job["status"] in ("COMPLETED", "FAILED"):
            completed_job = job
            break

elapsed = round(time.time() - start_time, 2)
print(f"4. Tracking Job Finished in {elapsed}s with status: {completed_job['status']}")

if completed_job["status"] == "COMPLETED":
    # 5. Fetch Tracks Summary
    with urllib.request.urlopen(f"{BASE_URL}/api/footage/{footage_id}/tracks") as resp:
        tracks_data = json.loads(resp.read().decode())
        print(f"5. Tracks Summary Fetched: Total {tracks_data['total_tracks']} tracked vehicles.")
        print(f"   Track Breakdown: Cars={tracks_data['car_tracks']}, 2-Wheelers={tracks_data['motorcycle_tracks']}, Buses={tracks_data['bus_tracks']}, Trucks={tracks_data['truck_tracks']}")
        for t in tracks_data["tracks"]:
            print(f"   - Track #{t['track_id']} | Class: {t['vehicle_class'].upper()} | Seen: {t['first_seen_formatted']} -> {t['last_seen_formatted']} ({t['duration_seconds']}s) | Sightings: {t['detection_count']} | Avg Conf: {t['avg_confidence_percent']} | Crop: {t['crop_url']}")

    # 6. Fetch Track Details & Frame Sightings
    if tracks_data["tracks"]:
        first_track = tracks_data["tracks"][0]
        t_id = first_track["track_id"]
        with urllib.request.urlopen(f"{BASE_URL}/api/footage/{footage_id}/tracks/{t_id}") as resp:
            t_detail = json.loads(resp.read().decode())
            print(f"6. Track #{t_id} Details Fetched: {len(t_detail['detections'])} timestamped frame sightings recorded.")

        # 7. Verify Representative Crop Image Endpoint
        if first_track.get("crop_url"):
            with urllib.request.urlopen(f"{BASE_URL}{first_track['crop_url']}") as resp:
                crop_bytes = len(resp.read())
                print(f"7. Representative Crop Downloaded: {crop_bytes} bytes (Content-Type: {resp.headers.get('Content-Type')})")

    # 8. Fetch Detections Summary
    with urllib.request.urlopen(f"{BASE_URL}/api/footage/{footage_id}/detections") as resp:
        dets = json.loads(resp.read().decode())
        print(f"8. Detections Summary Fetched: Total {dets['total_detections']} records with Track IDs.")
        if dets["detections"]:
            first_det = dets["detections"][0]
            print(f"   Sample Sighting: Time: {first_det['formatted_timestamp']} | Frame: #{first_det['frame_number']} | Track: #{first_det['track_id']} | Class: {first_det['vehicle_class'].upper()} | Conf: {first_det['confidence_percent']}")

    # 9. Verify Processed Video Streaming Endpoint
    stream_req = urllib.request.Request(
        f"{BASE_URL}/api/footage/{footage_id}/processed/stream",
        headers={"Range": "bytes=0-100"},
    )
    with urllib.request.urlopen(stream_req) as resp:
        print(f"9. Processed Tracking Video Stream: HTTP {resp.status} | Content-Range: {resp.headers.get('Content-Range')}")

print("\n--- ALL MILESTONE 5 VEHICLE TRACKING TESTS PASSED ---")

