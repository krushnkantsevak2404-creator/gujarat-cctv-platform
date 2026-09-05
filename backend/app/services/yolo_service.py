"""
YOLO Vehicle Detection & Multi-Object Tracking Service
Handles ByteTrack vehicle tracking across consecutive video frames,
representative vehicle crop saving, track summary persistence, and annotated video generation.
"""

import os
import time
import shutil
import threading
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.footage import CameraFootage, FootageStatus
from app.models.detection import (
    VehicleDetection,
    VehicleTrack,
    ProcessingJob,
    JobStatus,
    JobType,
)

logger = logging.getLogger("uvicorn.error")

# Cached YOLO model instance
_yolo_model = None
_model_lock = threading.Lock()


def get_processing_device() -> str:
    """Detects available hardware device (GPU or CPU)."""
    try:
        import torch
        if torch.cuda.is_available():
            return f"GPU: {torch.cuda.get_device_name(0)}"
    except Exception:
        pass
    return "CPU"


def load_yolo_model():
    """Loads or initializes pretrained Ultralytics YOLO model."""
    global _yolo_model
    with _model_lock:
        if _yolo_model is None:
            try:
                from ultralytics import YOLO
                model_path = settings.models_storage_path / settings.YOLO_MODEL_NAME
                if not model_path.exists():
                    logger.info(f"Downloading/Loading YOLO model: {settings.YOLO_MODEL_NAME}")
                    _yolo_model = YOLO(settings.YOLO_MODEL_NAME)
                    try:
                        _yolo_model.save(str(model_path))
                    except Exception:
                        pass
                else:
                    _yolo_model = YOLO(str(model_path))
                logger.info(f"YOLO model loaded successfully on {get_processing_device()}.")
            except Exception as e:
                logger.error(f"Failed to load Ultralytics YOLO model: {e}")
                raise e
    return _yolo_model


def format_timestamp(seconds: float) -> str:
    """Formats float seconds to mm:ss.s format (e.g. 01:23.4)."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:04.1f}"


# Color palette for distinct Track IDs & Vehicle Classes (BGR)
TRACK_PALETTE = [
    (0, 215, 255),    # Gold / Yellow
    (255, 191, 0),    # Deep Sky Blue
    (0, 255, 128),    # Emerald / Spring Green
    (255, 0, 128),    # Purple / Magenta
    (0, 140, 255),    # Dark Orange
    (255, 255, 0),    # Cyan
    (203, 192, 255),  # Pink Lavender
    (50, 205, 50),    # Lime Green
    (230, 216, 173),  # Light Blue
    (180, 105, 255),  # Hot Pink
]

CLASS_COLORS = {
    "car": (0, 215, 255),        # Yellow/Gold
    "motorcycle": (255, 191, 0), # Cyan/Blue
    "bus": (255, 0, 128),        # Magenta
    "truck": (0, 140, 255),      # Orange
}


def get_track_color(track_id: Optional[int], cls_name: str) -> Tuple[int, int, int]:
    """Returns color based on track ID or fallback vehicle class."""
    if track_id is not None and track_id > 0:
        return TRACK_PALETTE[(track_id - 1) % len(TRACK_PALETTE)]
    return CLASS_COLORS.get(cls_name, (0, 255, 0))


def process_video_background(footage_id: int, job_id: int):
    """
    Background worker thread function that runs YOLO detection + ByteTrack tracking,
    saves representative vehicle crops, stores track summaries, and creates annotated output video.
    """
    db: Session = SessionLocal()
    job: Optional[ProcessingJob] = None
    footage: Optional[CameraFootage] = None

    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()

        if not job or not footage:
            logger.error(f"Job #{job_id} or Footage #{footage_id} not found.")
            return

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        job.device = get_processing_device()
        footage.status = FootageStatus.PROCESSING
        db.commit()

        # Locate source video file
        source_path = settings.footage_storage_path / f"camera_{footage.camera_id}" / footage.file_name
        if not source_path.exists():
            source_path = Path(settings.STORAGE_DIR) / footage.file_path

        if not source_path.exists():
            raise FileNotFoundError(f"Source video file not found at {source_path}")

        # Target processed video directory & output paths
        processed_dir = settings.processed_storage_path / f"footage_{footage.id}"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        tracks_dir = processed_dir / "tracks"
        if tracks_dir.exists():
            shutil.rmtree(str(tracks_dir), ignore_errors=True)
        tracks_dir.mkdir(parents=True, exist_ok=True)

        output_video_path = processed_dir / "vehicle_tracking.mp4"
        legacy_video_path = processed_dir / "vehicle_detection.mp4"

        # Load YOLO model
        model = load_yolo_model()

        # Open video with OpenCV
        import cv2
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file {source_path} with OpenCV.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            fps = 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            width, height = 1280, 720

        job.total_frames = total_frames if total_frames > 0 else None
        db.commit()

        # Initialize VideoWriter with H264 / mp4v codec
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

        frame_idx = 0
        total_detections = 0
        cars_count = 0
        motorcycles_count = 0
        buses_count = 0
        trucks_count = 0

        # Track tracking structures
        track_summaries: Dict[int, Dict[str, Any]] = {}
        track_trajectories: Dict[int, deque] = {}  # track_id -> deque of (cx, cy)
        detections_to_insert: List[VehicleDetection] = []
        last_drawn_objects: List[Dict[str, Any]] = []

        is_tracking = (job.job_type == JobType.VEHICLE_TRACKING)
        logger.info(
            f"Starting {'YOLO + ByteTrack Vehicle Tracking' if is_tracking else 'YOLO Vehicle Detection'} "
            f"for footage #{footage_id} ({total_frames} frames)..."
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            timestamp_sec = round((frame_idx - 1) / fps, 2)

            # Frame inference condition
            should_infer = (frame_idx % settings.DETECTION_FRAME_INTERVAL == 0 or frame_idx == 1)

            if should_infer:
                last_drawn_objects = []

                if is_tracking:
                    # Run ByteTrack multi-object tracking
                    results = model.track(
                        source=frame,
                        persist=True,
                        tracker=settings.TRACKER_TYPE,
                        conf=settings.YOLO_CONFIDENCE_THRESHOLD,
                        verbose=False,
                        device=0 if "GPU" in job.device else "cpu",
                    )
                else:
                    # Detection only
                    results = model.predict(
                        source=frame,
                        conf=settings.YOLO_CONFIDENCE_THRESHOLD,
                        verbose=False,
                        device=0 if "GPU" in job.device else "cpu",
                    )

                if results and len(results) > 0:
                    r = results[0]
                    boxes = r.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        cls_name = r.names.get(cls_id, "").lower()
                        conf = float(box.conf[0].item())

                        # Filter strictly for target vehicle classes
                        if cls_name in settings.TARGET_VEHICLE_CLASSES and conf >= settings.YOLO_CONFIDENCE_THRESHOLD:
                            xyxy = box.xyxy[0].tolist()
                            x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
                            
                            # Extract Track ID if available
                            track_id: Optional[int] = None
                            if hasattr(box, "id") and box.id is not None:
                                try:
                                    track_id = int(box.id[0].item())
                                except Exception:
                                    track_id = None

                            cx = int((x1 + x2) / 2)
                            cy = int((y1 + y2) / 2)

                            last_drawn_objects.append({
                                "cls_name": cls_name,
                                "conf": conf,
                                "track_id": track_id,
                                "x1": x1,
                                "y1": y1,
                                "x2": x2,
                                "y2": y2,
                                "cx": cx,
                                "cy": cy,
                            })

                            # Increment detection counters
                            total_detections += 1
                            if cls_name == "car":
                                cars_count += 1
                            elif cls_name == "motorcycle":
                                motorcycles_count += 1
                            elif cls_name == "bus":
                                buses_count += 1
                            elif cls_name == "truck":
                                trucks_count += 1

                            # Update Track Summary aggregates if tracked
                            if track_id is not None:
                                if track_id not in track_trajectories:
                                    track_trajectories[track_id] = deque(maxlen=25)
                                track_trajectories[track_id].append((cx, cy))

                                # Calculate bounding box area
                                box_area = (x2 - x1) * (y2 - y1)

                                # Extract safe crop image for best representation
                                crop_img = None
                                ix1, iy1 = max(0, int(x1)), max(0, int(y1))
                                ix2, iy2 = min(width, int(x2)), min(height, int(y2))
                                if (ix2 - ix1) > 20 and (iy2 - iy1) > 20:
                                    crop_img = frame[iy1:iy2, ix1:ix2].copy()

                                if track_id not in track_summaries:
                                    track_summaries[track_id] = {
                                        "track_id": track_id,
                                        "vehicle_class": cls_name,
                                        "first_seen_seconds": timestamp_sec,
                                        "last_seen_seconds": timestamp_sec,
                                        "first_seen_frame": frame_idx,
                                        "last_seen_frame": frame_idx,
                                        "detection_count": 1,
                                        "conf_sum": conf,
                                        "best_crop": crop_img,
                                        "best_conf": conf,
                                        "best_area": box_area,
                                    }
                                else:
                                    t = track_summaries[track_id]
                                    t["last_seen_seconds"] = timestamp_sec
                                    t["last_seen_frame"] = frame_idx
                                    t["detection_count"] += 1
                                    t["conf_sum"] += conf
                                    # Update best representative crop
                                    if crop_img is not None:
                                        if (conf > t["best_conf"] + 0.1) or (box_area > t["best_area"] * 1.25 and conf >= 0.4):
                                            t["best_crop"] = crop_img
                                            t["best_conf"] = conf
                                            t["best_area"] = box_area

                            # Prepare DB detection record
                            det_record = VehicleDetection(
                                footage_id=footage.id,
                                frame_number=frame_idx,
                                timestamp_seconds=timestamp_sec,
                                vehicle_class=cls_name,
                                confidence=round(conf, 4),
                                track_id=track_id,
                                x1=round(x1, 2),
                                y1=round(y1, 2),
                                x2=round(x2, 2),
                                y2=round(y2, 2),
                            )
                            detections_to_insert.append(det_record)

            # Draw Visual Annotations on Output Video Frame
            for obj in last_drawn_objects:
                cls_name = obj["cls_name"]
                conf = obj["conf"]
                track_id = obj["track_id"]
                x1, y1, x2, y2 = obj["x1"], obj["y1"], obj["x2"], obj["y2"]
                ix1, iy1, ix2, iy2 = int(x1), int(y1), int(x2), int(y2)
                color = get_track_color(track_id, cls_name)

                # Draw Centroid Motion Trails (Smooth vehicle path history)
                if track_id is not None and track_id in track_trajectories:
                    pts = list(track_trajectories[track_id])
                    for i in range(1, len(pts)):
                        if pts[i - 1] is None or pts[i] is None:
                            continue
                        alpha = i / len(pts)
                        thickness = max(1, int(2.5 * alpha))
                        cv2.line(frame, pts[i - 1], pts[i], color, thickness, cv2.LINE_AA)

                # Draw Bounding Box with Corner Accents
                cv2.rectangle(frame, (ix1, iy1), (ix2, iy2), color, 2, cv2.LINE_AA)
                
                # Corner accents for tactical look
                line_len = min(15, int((ix2 - ix1) * 0.25), int((iy2 - iy1) * 0.25))
                if line_len > 3:
                    cv2.line(frame, (ix1, iy1), (ix1 + line_len, iy1), (255, 255, 255), 2)
                    cv2.line(frame, (ix1, iy1), (ix1, iy1 + line_len), (255, 255, 255), 2)
                    cv2.line(frame, (ix2, iy1), (ix2 - line_len, iy1), (255, 255, 255), 2)
                    cv2.line(frame, (ix2, iy1), (ix2, iy1 + line_len), (255, 255, 255), 2)
                    cv2.line(frame, (ix1, iy2), (ix1 + line_len, iy2), (255, 255, 255), 2)
                    cv2.line(frame, (ix1, iy2), (ix1, iy2 - line_len), (255, 255, 255), 2)
                    cv2.line(frame, (ix2, iy2), (ix2 - line_len, iy2), (255, 255, 255), 2)
                    cv2.line(frame, (ix2, iy2), (ix2, iy2 - line_len), (255, 255, 255), 2)

                # Draw Text Label Badge
                if track_id is not None:
                    label = f"{cls_name.upper()} | Track #{track_id} | {int(conf * 100)}%"
                else:
                    label = f"{cls_name.upper()} {int(conf * 100)}%"

                (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                label_y = max(iy1 - 6, th + 6)
                
                # Dark badge background
                cv2.rectangle(
                    frame,
                    (ix1, label_y - th - 5),
                    (ix1 + tw + 8, label_y + baseline - 1),
                    (10, 18, 30),
                    -1,
                )
                cv2.rectangle(
                    frame,
                    (ix1, label_y - th - 5),
                    (ix1 + tw + 8, label_y + baseline - 1),
                    color,
                    1,
                )
                cv2.putText(
                    frame,
                    label,
                    (ix1 + 4, label_y - 3),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

            # Write annotated frame to video
            writer.write(frame)

            # Periodic Progress Updates
            if frame_idx % 10 == 0:
                if total_frames and total_frames > 0:
                    prog = min(int((frame_idx / total_frames) * 95), 95)
                    job.progress = prog
                job.processed_frames = frame_idx
                job.total_detections = total_detections
                job.cars_count = cars_count
                job.motorcycles_count = motorcycles_count
                job.buses_count = buses_count
                job.trucks_count = trucks_count

                # Track counters
                job.total_tracks = len(track_summaries)
                job.car_tracks = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "car")
                job.motorcycle_tracks = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "motorcycle")
                job.bus_tracks = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "bus")
                job.truck_tracks = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "truck")
                db.commit()

        cap.release()
        writer.release()

        # Save Representative Vehicle Crops & Prepare Track Summary Records
        vehicle_tracks_to_insert: List[VehicleTrack] = []
        for track_id, tdata in sorted(track_summaries.items(), key=lambda x: x[0]):
            crop_path_rel = None
            if tdata.get("best_crop") is not None:
                crop_file_name = f"track_{track_id}.jpg"
                crop_abs_path = tracks_dir / crop_file_name
                try:
                    cv2.imwrite(str(crop_abs_path), tdata["best_crop"])
                    crop_path_rel = f"processed/footage_{footage_id}/tracks/{crop_file_name}"
                except Exception as e:
                    logger.warning(f"Failed to save crop for track #{track_id}: {e}")

            avg_conf = tdata["conf_sum"] / max(1, tdata["detection_count"])
            vtrack = VehicleTrack(
                footage_id=footage.id,
                track_id=track_id,
                vehicle_class=tdata["vehicle_class"],
                first_seen_seconds=round(tdata["first_seen_seconds"], 2),
                last_seen_seconds=round(tdata["last_seen_seconds"], 2),
                first_seen_frame=tdata["first_seen_frame"],
                last_seen_frame=tdata["last_seen_frame"],
                detection_count=tdata["detection_count"],
                avg_confidence=round(avg_conf, 4),
                best_crop_path=crop_path_rel,
            )
            vehicle_tracks_to_insert.append(vtrack)

        # Flush Detections and Tracks to Database
        if detections_to_insert:
            db.bulk_save_objects(detections_to_insert)
        if vehicle_tracks_to_insert:
            db.bulk_save_objects(vehicle_tracks_to_insert)
        db.commit()

        # Ensure compatibility alias for video streaming
        if output_video_path.exists():
            try:
                shutil.copyfile(str(output_video_path), str(legacy_video_path))
            except Exception:
                pass

        # Finalize Job Status
        total_tracks_count = len(track_summaries)
        car_tracks_count = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "car")
        bike_tracks_count = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "motorcycle")
        bus_tracks_count = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "bus")
        truck_tracks_count = sum(1 for t in track_summaries.values() if t["vehicle_class"] == "truck")

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.processed_frames = frame_idx
        job.total_detections = total_detections
        job.cars_count = cars_count
        job.motorcycles_count = motorcycles_count
        job.buses_count = buses_count
        job.trucks_count = trucks_count
        job.total_tracks = total_tracks_count
        job.car_tracks = car_tracks_count
        job.motorcycle_tracks = bike_tracks_count
        job.bus_tracks = bus_tracks_count
        job.truck_tracks = truck_tracks_count
        job.completed_at = datetime.now(timezone.utc)
        footage.status = FootageStatus.COMPLETED
        db.commit()

        logger.info(
            f"Vehicle Tracking completed for footage #{footage_id}: "
            f"{total_tracks_count} unique tracks ({car_tracks_count} cars, {bike_tracks_count} motorcycles, {bus_tracks_count} buses, {truck_tracks_count} trucks), "
            f"{total_detections} total sightings across {frame_idx} frames."
        )

    except Exception as e:
        logger.error(f"Error during video tracking for footage #{footage_id}: {e}", exc_info=True)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
        if footage:
            footage.status = FootageStatus.FAILED
        db.commit()

    finally:
        db.close()


def trigger_video_analysis(
    db: Session,
    footage_id: int,
    job_type: JobType = JobType.VEHICLE_TRACKING,
) -> ProcessingJob:
    """Creates a ProcessingJob and launches the background analysis & tracking thread."""
    footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
    if not footage:
        raise ValueError(f"Footage #{footage_id} not found")

    # Clear previous detections & tracks for this footage to allow fresh re-run
    db.query(VehicleDetection).filter(VehicleDetection.footage_id == footage_id).delete()
    db.query(VehicleTrack).filter(VehicleTrack.footage_id == footage_id).delete()

    job = ProcessingJob(
        footage_id=footage.id,
        job_type=job_type,
        status=JobStatus.QUEUED,
        progress=0,
        device=get_processing_device(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background thread
    worker = threading.Thread(
        target=process_video_background,
        args=(footage.id, job.id),
        daemon=True,
    )
    worker.start()

    return job
