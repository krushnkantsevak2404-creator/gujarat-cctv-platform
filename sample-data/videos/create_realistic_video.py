"""
Generate a realistic CCTV test video clip using official Ultralytics image assets.
Creates sample-data/videos/gujarat_traffic_demo.mp4 with real vehicles (Bus, Cars).
"""

import cv2
import numpy as np
from pathlib import Path
import ultralytics

asset_bus = Path(ultralytics.__file__).parent / "assets" / "bus.jpg"
img = cv2.imread(str(asset_bus))
h, w, _ = img.shape

output_dir = Path(r"E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform\sample-data\videos")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "gujarat_traffic_demo.mp4"

fps = 25
duration_sec = 4  # 4 seconds = 100 frames
total_frames = fps * duration_sec

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

for f in range(total_frames):
    frame = img.copy()
    
    # Add dynamic CCTV overlay
    sec = f / fps
    cctv_text = f"GJ-POLICE-CAM-001 | SG HIGHWAY | 2026-09-04 15:45:{sec:04.1f}"
    cv2.rectangle(frame, (10, 10), (600, 45), (10, 20, 35), -1)
    cv2.putText(frame, cctv_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 1, cv2.LINE_AA)
    
    writer.write(frame)

writer.release()
print(f"Realistic CCTV test video generated at {output_path} ({total_frames} frames, {output_path.stat().st_size} bytes)")
