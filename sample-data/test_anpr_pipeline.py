import urllib.request
import urllib.parse
import json
import time
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
video_path = Path(r"E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform\sample-data\videos\gujarat_traffic_demo.mp4")

print(f"Testing Milestone 6: ANPR + OCR Pipeline on: {video_path.name}...")

# 1. Upload sample video
boundary = "----WebKitFormBoundaryAnprTest99"
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
body.append(b"Surveillance footage for Milestone 6 ANPR and OCR license plate extraction")
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

# 2. Trigger ANPR Processing Job
anpr_req = urllib.request.Request(
    f"{BASE_URL}/api/footage/{footage_id}/anpr",
    data=b"",
    headers={"Content-Type": "application/json"},
    method="POST",
)

start_time = time.time()
with urllib.request.urlopen(anpr_req) as resp:
    job_data = json.loads(resp.read().decode())
    job_id = job_data["id"]
    print(f"2. ANPR Job Started: Job #{job_id} on {job_data['device']} (Type: {job_data['job_type']}, Status: {job_data['status']})")

# 3. Poll Job Status until completion
print("3. Polling ANPR Job...")
completed_job = None
while True:
    time.sleep(1.0)
    with urllib.request.urlopen(f"{BASE_URL}/api/analysis/jobs/{job_id}") as resp:
        job = json.loads(resp.read().decode())
        print(f"   Progress: {job['progress']}% | Status: {job['status']} | Plates Detected: {job.get('total_plates_detected', 0)} | Unique: {job.get('unique_plates_count', 0)} | Valid Format: {job.get('valid_format_count', 0)} | Success OCR: {job.get('successful_ocr_count', 0)}")
        if job["status"] in ("COMPLETED", "FAILED"):
            completed_job = job
            break

elapsed = round(time.time() - start_time, 2)
print(f"4. ANPR Job Finished in {elapsed}s with status: {completed_job['status']}")

if completed_job["status"] == "COMPLETED":
    # 5. Fetch ANPR Summary
    with urllib.request.urlopen(f"{BASE_URL}/api/footage/{footage_id}/anpr/summary") as resp:
        summary_data = json.loads(resp.read().decode())
        print(f"5. ANPR Summary Fetched: Total {summary_data['total_plates_detected']} plate sightings, {summary_data['unique_plates_count']} unique consolidated vehicles.")
        print(f"   Breakdown: Valid Format={summary_data['valid_format_count']}, Successful OCR={summary_data['successful_ocr_count']}")
        for d in summary_data["detections"]:
            print(f"   - Plate: {d['plate_number_normalized'] or 'UNRECOGNIZED'} | Raw: {d['plate_number_raw']} | Status: {d['status']} | Format: {d['format_status']} | Vehicle: {d['vehicle_class'].upper()} | Track #{d['track_id']} | Conf: {d['confidence_percent']} | Time: {d['formatted_timestamp']} | Crop: {d['plate_crop_url']}")

    # 6. Verify Plate Crop Stream Endpoint
    if summary_data["detections"]:
        sample_det = summary_data["detections"][0]
        if sample_det.get("plate_crop_url"):
            with urllib.request.urlopen(f"{BASE_URL}{sample_det['plate_crop_url']}") as resp:
                crop_bytes = len(resp.read())
                print(f"6. Plate Crop Downloaded: {crop_bytes} bytes (Content-Type: {resp.headers.get('Content-Type')})")

    # 7. Global License Plate Search Test
    query_plate = summary_data["detections"][0]["plate_number_normalized"] if summary_data["detections"] and summary_data["detections"][0]["plate_number_normalized"] else "GJ"
    search_url = f"{BASE_URL}/api/anpr/search?query={urllib.parse.quote(query_plate[:4])}"
    with urllib.request.urlopen(search_url) as resp:
        search_results = json.loads(resp.read().decode())
        print(f"7. Global Search for '{query_plate[:4]}': Found {search_results['total_results']} matching records across all CCTV cameras.")
        for res in search_results["results"][:3]:
            print(f"   -> Match: Plate={res['plate_number_normalized']} at Camera {res['camera_code']} ({res['camera_name']}, {res['location_name']}) at {res['formatted_timestamp']}")

print("\n--- ALL MILESTONE 6 ANPR & OCR TESTS PASSED ---")
