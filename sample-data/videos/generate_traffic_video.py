"""
Generate a high-quality sample CCTV traffic surveillance video for testing YOLO vehicle detection.
Creates sample-data/videos/sample_traffic_video.mp4 with moving vehicles.
"""

import cv2
import numpy as np
from pathlib import Path

output_dir = Path(r"E:\Kishan All File's\MCA Works\Gujrat Police Hackthon Project's\Hackthon Project File's\gujarat-cctv-platform\sample-data\videos")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "sample_traffic_video.mp4"

width, height = 1280, 720
fps = 30
duration_sec = 6  # 6 seconds = 180 frames
total_frames = fps * duration_sec

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

# Simulate traffic scene
for f in range(total_frames):
    # Road background
    frame = np.full((height, width, 3), (40, 45, 50), dtype=np.uint8)

    # Road lanes
    cv2.rectangle(frame, (100, 150), (1180, 650), (60, 65, 70), -1)
    # Road divider
    for x in range(120, 1160, 80):
        cv2.rectangle(frame, (x, 395), (x + 40, 405), (220, 220, 220), -1)

    # Road curbs & grass
    cv2.rectangle(frame, (0, 0), (1280, 150), (35, 70, 45), -1)
    cv2.rectangle(frame, (0, 650), (1280, 720), (35, 70, 45), -1)

    # Vehicle 1: Moving Car (Lane 1, West to East)
    car1_x = int(100 + (f * 6) % 1000)
    car1_y = 260
    # Car body
    cv2.rectangle(frame, (car1_x, car1_y), (car1_x + 130, car1_y + 60), (200, 50, 50), -1)
    cv2.rectangle(frame, (car1_x + 25, car1_y - 25), (car1_x + 105, car1_y), (180, 40, 40), -1)
    # Windows
    cv2.rectangle(frame, (car1_x + 30, car1_y - 20), (car1_x + 60, car1_y - 2), (220, 240, 255), -1)
    cv2.rectangle(frame, (car1_x + 65, car1_y - 20), (car1_x + 100, car1_y - 2), (220, 240, 255), -1)
    # Wheels
    cv2.circle(frame, (car1_x + 30, car1_y + 60), 14, (20, 20, 20), -1)
    cv2.circle(frame, (car1_x + 100, car1_y + 60), 14, (20, 20, 20), -1)

    # Vehicle 2: Moving Truck (Lane 1, West to East)
    truck_x = int(500 + (f * 4) % 1000)
    truck_y = 230
    # Cargo container
    cv2.rectangle(frame, (truck_x, truck_y), (truck_x + 180, truck_y + 90), (50, 120, 200), -1)
    # Cab
    cv2.rectangle(frame, (truck_x + 180, truck_y + 20), (truck_x + 230, truck_y + 90), (40, 100, 180), -1)
    # Cab window
    cv2.rectangle(frame, (truck_x + 190, truck_y + 25), (truck_x + 225, truck_y + 55), (220, 240, 255), -1)
    # Wheels
    cv2.circle(frame, (truck_x + 40, truck_y + 90), 16, (20, 20, 20), -1)
    cv2.circle(frame, (truck_x + 140, truck_y + 90), 16, (20, 20, 20), -1)
    cv2.circle(frame, (truck_x + 205, truck_y + 90), 16, (20, 20, 20), -1)

    # Vehicle 3: Moving Motorcycle (Lane 2, East to West)
    bike_x = int(1100 - (f * 7) % 1000)
    bike_y = 480
    cv2.rectangle(frame, (bike_x, bike_y), (bike_x + 60, bike_y + 30), (30, 180, 220), -1)
    cv2.circle(frame, (bike_x + 10, bike_y + 30), 10, (20, 20, 20), -1)
    cv2.circle(frame, (bike_x + 50, bike_y + 30), 10, (20, 20, 20), -1)
    cv2.circle(frame, (bike_x + 30, bike_y - 15), 10, (240, 200, 160), -1) # Rider head

    # Vehicle 4: Moving Bus (Lane 2, East to West)
    bus_x = int(800 - (f * 5) % 1000)
    bus_y = 450
    cv2.rectangle(frame, (bus_x, bus_y), (bus_x + 220, bus_y + 80), (180, 60, 160), -1)
    for wx in range(bus_x + 20, bus_x + 200, 35):
        cv2.rectangle(frame, (wx, bus_y + 10), (wx + 25, bus_y + 35), (220, 240, 255), -1)
    cv2.circle(frame, (bus_x + 40, bus_y + 80), 15, (20, 20, 20), -1)
    cv2.circle(frame, (bus_x + 180, bus_y + 80), 15, (20, 20, 20), -1)

    # CCTV timestamp overlay
    sec = f / fps
    cctv_text = f"CAM-001 [LIVE RECORDING] 2026-09-04 15:30:{sec:04.1f}"
    cv2.putText(frame, cctv_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    writer.write(frame)

writer.release()
print(f"Traffic surveillance video generated successfully at {output_path} (Frames: {total_frames}, Size: {output_path.stat().st_size} bytes)")
