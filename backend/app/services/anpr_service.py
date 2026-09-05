"""
Automatic Number Plate Recognition (ANPR) & OCR Engine Service
Integrates YOLO vehicle detection, ByteTrack tracking, plate region localization,
adaptive image preprocessing, EasyOCR recognition, Indian plate syntax normalization,
and multi-frame track deduplication.
"""

import os
import re
import time
import shutil
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import cv2
import numpy as np
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
from app.models.anpr import (
    AnprDetection,
    AnprStatus,
    PlateFormatStatus,
)
from app.services.yolo_service import (
    get_processing_device,
    load_yolo_model,
    format_timestamp,
)

logger = logging.getLogger("uvicorn.error")

# Cached EasyOCR Reader instance
_ocr_reader = None
_ocr_lock = threading.Lock()

# Common Indian State Codes
INDIAN_STATE_CODES = {
    "GJ", "MH", "DL", "KA", "TN", "UP", "HR", "RJ", "MP", "AP", 
    "TS", "KL", "WB", "PB", "BR", "OD", "AS", "JK", "UK", "HP",
    "CG", "GA", "TR", "ML", "MN", "NL", "MZ", "AR", "SK", "PY",
    "CH", "AN", "DN", "DD", "LD", "LA"
}

# Standard Indian Plate Regex Patterns
REGEX_STANDARD_PLATE = re.compile(r"^([A-Z]{2})([0-9]{1,2})([A-Z]{1,3})([0-9]{4})$")
REGEX_BHARAT_SERIES = re.compile(r"^([0-9]{2})BH([0-9]{4})([A-Z]{1,2})$")
REGEX_OLD_STANDARD = re.compile(r"^([A-Z]{2})([0-9]{1,2})([0-9]{4})$")
REGEX_GENERIC_ALPHANUM = re.compile(r"^[A-Z0-9]{6,12}$")


def load_ocr_reader():
    """Initializes and caches EasyOCR reader instance."""
    global _ocr_reader
    with _ocr_lock:
        if _ocr_reader is None:
            try:
                import easyocr
                import torch
                use_gpu = torch.cuda.is_available()
                logger.info(f"Initializing EasyOCR Reader (GPU={use_gpu})...")
                _ocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
                logger.info("EasyOCR Reader initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                raise e
    return _ocr_reader


def clean_raw_plate_text(raw_text: str) -> str:
    """Strips punctuation, spaces, and special symbols; converts to uppercase."""
    if not raw_text:
        return ""
    # Remove everything except alphanumeric chars
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw_text).upper()
    return cleaned


def normalize_indian_plate(raw_text: str) -> Tuple[str, PlateFormatStatus]:
    """
    Applies domain-specific character substitution rules for Indian number plates
    and validates format syntax.
    """
    cleaned = clean_raw_plate_text(raw_text)
    if not cleaned or len(cleaned) < 5:
        return cleaned, PlateFormatStatus.UNCERTAIN

    # Check direct match with standard format
    if REGEX_STANDARD_PLATE.match(cleaned) or REGEX_BHARAT_SERIES.match(cleaned) or REGEX_OLD_STANDARD.match(cleaned):
        return cleaned, PlateFormatStatus.VALID_FORMAT

    # Character confusion mappings
    digit_to_char = {'0': 'O', '1': 'I', '8': 'B', '5': 'S', '2': 'Z', '6': 'G'}
    char_to_digit = {'O': '0', 'D': '0', 'Q': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8', 'A': '4', 'G': '6', 'T': '7'}

    chars = list(cleaned)
    n = len(chars)

    # Attempt standard plate normalization if length is 9, 10, or 11
    if 8 <= n <= 11:
        # First 2 must be State Code (Letters)
        for i in (0, 1):
            if chars[i] in digit_to_char:
                chars[i] = digit_to_char[chars[i]]

        # Next 1 or 2 must be RTO Code (Digits)
        if chars[2] in char_to_digit:
            chars[2] = char_to_digit[chars[2]]
        
        # Last 4 characters are serial digits
        for i in range(n - 4, n):
            if chars[i] in char_to_digit:
                chars[i] = char_to_digit[chars[i]]

        candidate = "".join(chars)
        state_prefix = candidate[:2]

        if (REGEX_STANDARD_PLATE.match(candidate) or REGEX_OLD_STANDARD.match(candidate)) and state_prefix in INDIAN_STATE_CODES:
            return candidate, PlateFormatStatus.VALID_FORMAT

    # Attempt Bharat series normalization (e.g. 22BH1234AA)
    if n == 10 and "".join(chars[2:4]) in ("BH", "8H", "B#"):
        chars[2] = 'B'
        chars[3] = 'H'
        for i in (0, 1):
            if chars[i] in char_to_digit:
                chars[i] = char_to_digit[chars[i]]
        for i in range(4, 8):
            if chars[i] in char_to_digit:
                chars[i] = char_to_digit[chars[i]]
        for i in (8, 9):
            if chars[i] in digit_to_char:
                chars[i] = digit_to_char[chars[i]]
        candidate = "".join(chars)
        if REGEX_BHARAT_SERIES.match(candidate):
            return candidate, PlateFormatStatus.VALID_FORMAT

    # Check if generic alphanumeric pattern
    candidate = "".join(chars)
    if REGEX_GENERIC_ALPHANUM.match(candidate):
        return candidate, PlateFormatStatus.POSSIBLE_FORMAT

    return candidate, PlateFormatStatus.UNCERTAIN


def localize_plate_candidate(vehicle_crop: np.ndarray) -> Tuple[Optional[np.ndarray], Tuple[int, int, int, int], float]:
    """
    Extracts license plate candidate from a vehicle crop image using edge/contour analysis
    with morphological filtering and aspect ratio constraints.
    
    Returns:
        (plate_crop, (rel_x1, rel_y1, rel_x2, rel_y2), localization_confidence)
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return None, (0, 0, 0, 0), 0.0

    vh, vw = vehicle_crop.shape[:2]
    if vh < 20 or vw < 40:
        return None, (0, 0, 0, 0), 0.0

    # License plates are predominantly located in the lower 55% of the vehicle
    lower_y_start = int(vh * 0.40)
    lower_crop = vehicle_crop[lower_y_start:vh, 0:vw]
    lh, lw = lower_crop.shape[:2]

    if lh < 10 or lw < 20:
        return None, (0, 0, 0, 0), 0.0

    gray = cv2.cvtColor(lower_crop, cv2.COLOR_BGR2GRAY)
    
    # Bilateral blur preserves plate edges while smoothing surface noise
    blurred = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Edge detection
    edges = cv2.Canny(blurred, 50, 200)
    
    # Morphological closing with horizontal rectangular structuring element
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_candidate = None
    best_bbox = None
    best_score = 0.0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if h == 0 or w == 0:
            continue
        
        aspect_ratio = float(w) / float(h)
        area = w * h
        relative_area = area / float(lh * lw)

        # Standard Indian plates aspect ratio typically ranges between 2.0 and 5.5
        if 1.8 <= aspect_ratio <= 5.8 and 0.01 <= relative_area <= 0.45 and w >= 35 and h >= 12:
            # Score candidate based on rectangularity, central positioning, and aspect ratio
            rect_score = 1.0 - abs(aspect_ratio - 3.8) / 3.8
            pos_score = 1.0 - abs((x + w / 2) - (lw / 2)) / (lw / 2)
            score = 0.6 * rect_score + 0.4 * pos_score

            if score > best_score:
                best_score = score
                best_bbox = (x, y + lower_y_start, x + w, y + lower_y_start + h)

    if best_bbox is not None and best_score > 0.35:
        bx1, by1, bx2, by2 = best_bbox
        # Add slight padding
        pad_x = int((bx2 - bx1) * 0.05)
        pad_y = int((by2 - by1) * 0.10)
        px1 = max(0, bx1 - pad_x)
        py1 = max(0, by1 - pad_y)
        px2 = min(vw, bx2 + pad_x)
        py2 = min(vh, by2 + pad_y)

        plate_crop = vehicle_crop[py1:py2, px1:px2]
        return plate_crop, (px1, py1, px2, py2), float(min(1.0, best_score + 0.2))

    # Fallback: Central lower region heuristic
    fx1 = int(vw * 0.20)
    fy1 = int(vh * 0.58)
    fx2 = int(vw * 0.80)
    fy2 = int(vh * 0.94)
    fallback_crop = vehicle_crop[fy1:fy2, fx1:fx2]
    return fallback_crop, (fx1, fy1, fx2, fy2), 0.40


def preprocess_plate_for_ocr(plate_crop: np.ndarray) -> List[np.ndarray]:
    """
    Applies adaptive contrast enhancement, bilateral denoising, and Otsu thresholding
    to prepare license plate crops for OCR.
    """
    if plate_crop is None or plate_crop.size == 0:
        return []

    ph, pw = plate_crop.shape[:2]
    
    # Scale up if plate is small to improve character recognition
    target_width = max(pw, 200)
    scale = target_width / pw
    target_height = int(ph * scale)
    resized = cv2.resize(plate_crop, (target_width, target_height), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # Bilateral smoothing
    denoised = cv2.bilateralFilter(enhanced_gray, 9, 50, 50)

    # Otsu thresholding
    _, otsu_thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Return multiple representation variants (enhanced grayscale and binarized)
    return [resized, denoised, otsu_thresh]


def perform_anpr_ocr(plate_crop: np.ndarray, reader) -> Tuple[Optional[str], Optional[str], float, AnprStatus, PlateFormatStatus]:
    """
    Runs EasyOCR with uppercase alphanumeric allowlist on preprocessed plate candidates.
    
    Returns:
        (raw_text, normalized_text, ocr_confidence, anpr_status, format_status)
    """
    if plate_crop is None or plate_crop.size == 0 or reader is None:
        return None, None, 0.0, AnprStatus.OCR_UNREADABLE, PlateFormatStatus.UNCERTAIN

    variants = preprocess_plate_for_ocr(plate_crop)
    if not variants:
        return None, None, 0.0, AnprStatus.OCR_UNREADABLE, PlateFormatStatus.UNCERTAIN

    best_raw = ""
    best_norm = ""
    best_conf = 0.0
    best_format = PlateFormatStatus.UNCERTAIN

    allowlist = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for img_variant in variants:
        try:
            results = reader.readtext(
                img_variant,
                allowlist=allowlist,
                detail=1,
                paragraph=False,
                batch_size=1,
            )
            
            if not results:
                continue

            # Accumulate text snippets ordered horizontally
            snippets = []
            confidences = []
            for item in results:
                bbox, text, conf = item
                text_clean = text.strip().replace(" ", "").upper()
                if text_clean:
                    snippets.append(text_clean)
                    confidences.append(float(conf))

            if snippets:
                combined_raw = "".join(snippets)
                avg_conf = float(np.mean(confidences))
                norm_text, fmt_status = normalize_indian_plate(combined_raw)

                # Prioritize valid format or higher confidence
                score = avg_conf
                if fmt_status == PlateFormatStatus.VALID_FORMAT:
                    score += 0.50
                elif fmt_status == PlateFormatStatus.POSSIBLE_FORMAT:
                    score += 0.20

                if score > best_conf:
                    best_conf = avg_conf
                    best_raw = combined_raw
                    best_norm = norm_text
                    best_format = fmt_status

        except Exception as e:
            logger.debug(f"OCR variant exception: {e}")
            continue

    if not best_raw:
        return None, None, 0.0, AnprStatus.PLATE_DETECTED, PlateFormatStatus.UNCERTAIN

    # Determine status
    if best_conf >= 0.55 and best_format in (PlateFormatStatus.VALID_FORMAT, PlateFormatStatus.POSSIBLE_FORMAT):
        status = AnprStatus.OCR_SUCCESS
    elif best_conf >= 0.30 or len(best_norm) >= 6:
        status = AnprStatus.OCR_LOW_CONFIDENCE
    elif len(best_norm) < 4:
        status = AnprStatus.OCR_UNREADABLE
    else:
        status = AnprStatus.OCR_LOW_CONFIDENCE

    return best_raw, best_norm, float(best_conf), status, best_format


def run_anpr_pipeline(footage_id: int, job_id: int):
    """
    Executes the complete ANPR & OCR pipeline for a recorded CCTV footage:
    1. Loads video & YOLO tracker.
    2. Processes frames at specified interval.
    3. Detects vehicle bounding boxes & tracks.
    4. Localizes plate candidate regions.
    5. Runs EasyOCR on plate crops.
    6. Normalizes plate text and formats.
    7. Deduplicates across track occurrences and saves best plate crops.
    8. Records AnprDetection records in database.
    """
    db: Session = SessionLocal()
    start_time = time.time()
    logger.info(f"Starting ANPR & OCR processing for footage_id={footage_id}, job_id={job_id}")

    try:
        footage = db.query(CameraFootage).filter(CameraFootage.id == footage_id).first()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

        if not footage or not job:
            logger.error(f"Footage {footage_id} or Job {job_id} not found.")
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        job.device = get_processing_device()
        db.commit()

        # Locate source video file
        video_path = settings.footage_storage_path / f"camera_{footage.camera_id}" / footage.file_name
        if not video_path.exists():
            video_path = Path(settings.STORAGE_DIR) / footage.file_path
        if not video_path.exists():
            video_path = Path(footage.file_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Footage video file not found at: {video_path}")

        # Ensure plate crop directory exists: storage/plate_crops/footage_<id>
        footage_crops_dir = settings.plate_crops_storage_path / f"footage_{footage_id}"
        footage_crops_dir.mkdir(parents=True, exist_ok=True)

        # Clear existing ANPR records for this footage to allow clean rerun
        db.query(AnprDetection).filter(AnprDetection.footage_id == footage_id).delete()
        db.commit()

        # Load models
        yolo_model = load_yolo_model()
        ocr_reader = load_ocr_reader()

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 25.0
        frame_interval = max(1, settings.ANPR_FRAME_INTERVAL)

        job.total_frames = total_frames
        db.commit()

        frame_idx = 0
        processed_count = 0
        raw_detections: List[Dict[str, Any]] = []

        logger.info(f"Processing {total_frames} frames (interval={frame_interval}) for ANPR...")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if (frame_idx - 1) % frame_interval != 0:
                continue

            processed_count += 1
            timestamp_sec = float((frame_idx - 1) / fps)

            # YOLO Track on frame
            results = yolo_model.track(
                source=frame,
                persist=True,
                tracker=settings.TRACKER_TYPE,
                conf=settings.YOLO_CONFIDENCE_THRESHOLD,
                classes=[2, 3, 5, 7],  # car, motorcycle, bus, truck in COCO
                verbose=False,
            )

            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    for i, box in enumerate(boxes):
                        cls_id = int(box.cls[0])
                        cls_name = yolo_model.names.get(cls_id, "car")
                        v_conf = float(box.conf[0])
                        track_id = int(box.id[0]) if box.id is not None else None

                        vx1, vy1, vx2, vy2 = map(int, box.xyxy[0].tolist())
                        vx1, vy1 = max(0, vx1), max(0, vy1)
                        vx2, vy2 = min(frame.shape[1], vx2), min(frame.shape[0], vy2)

                        if (vx2 - vx1) < 40 or (vy2 - vy1) < 30:
                            continue

                        vehicle_crop = frame[vy1:vy2, vx1:vx2]

                        # Localize plate candidate
                        plate_crop, (rel_x1, rel_y1, rel_x2, rel_y2), loc_conf = localize_plate_candidate(vehicle_crop)

                        if plate_crop is None or plate_crop.size == 0:
                            continue

                        # Convert relative coordinates to frame space
                        px1 = float(vx1 + rel_x1)
                        py1 = float(vy1 + rel_y1)
                        px2 = float(vx1 + rel_x2)
                        py2 = float(vy1 + rel_y2)

                        # Run OCR on plate crop
                        raw_text, norm_text, ocr_conf, anpr_status, fmt_status = perform_anpr_ocr(
                            plate_crop, ocr_reader
                        )

                        combined_conf = float(0.4 * loc_conf + 0.6 * ocr_conf)

                        raw_detections.append({
                            "footage_id": footage_id,
                            "track_id": track_id,
                            "frame_number": frame_idx,
                            "timestamp_seconds": timestamp_sec,
                            "vehicle_class": cls_name,
                            "plate_number_raw": raw_text,
                            "plate_number_normalized": norm_text,
                            "confidence": round(combined_conf, 4),
                            "ocr_confidence": round(ocr_conf, 4) if ocr_conf > 0 else None,
                            "detection_confidence": round(loc_conf, 4),
                            "status": anpr_status,
                            "format_status": fmt_status,
                            "x1": round(px1, 1),
                            "y1": round(py1, 1),
                            "x2": round(px2, 1),
                            "y2": round(py2, 1),
                            "vehicle_x1": round(float(vx1), 1),
                            "vehicle_y1": round(float(vy1), 1),
                            "vehicle_x2": round(float(vx2), 1),
                            "vehicle_y2": round(float(vy2), 1),
                            "plate_crop_img": plate_crop.copy(),
                        })

            # Update progress periodically
            if processed_count % 10 == 0 or frame_idx >= total_frames:
                progress = min(95, int((frame_idx / total_frames) * 95))
                job.progress = progress
                job.processed_frames = frame_idx
                db.commit()

        cap.release()

        # Step 8: Deduplicate and consolidate ANPR sightings per track / vehicle
        logger.info(f"Consolidating {len(raw_detections)} raw ANPR detections...")
        consolidated_groups: Dict[Any, List[Dict[str, Any]]] = {}

        for det in raw_detections:
            # Group key: track_id if available, otherwise cluster by time & normalized plate
            key = det["track_id"] if det["track_id"] is not None else f"time_{int(det['timestamp_seconds'] // 3)}_{det['plate_number_normalized'] or 'unrecognized'}"
            if key not in consolidated_groups:
                consolidated_groups[key] = []
            consolidated_groups[key].append(det)

        total_plates_detected = len(raw_detections)
        successful_ocr_count = 0
        valid_format_count = 0
        saved_anpr_records: List[AnprDetection] = []

        for key, group in consolidated_groups.items():
            # Select best candidate in group:
            # Rank 1: VALID_FORMAT with highest confidence
            # Rank 2: POSSIBLE_FORMAT with highest confidence
            # Rank 3: Highest OCR confidence
            def ranking_key(d):
                fmt_rank = 3 if d["format_status"] == PlateFormatStatus.VALID_FORMAT else (2 if d["format_status"] == PlateFormatStatus.POSSIBLE_FORMAT else 1)
                return (fmt_rank, d["ocr_confidence"] or 0.0, d["confidence"])

            best_det = max(group, key=ranking_key)
            sighting_count = len(group)

            for det in group:
                is_best = (det == best_det)
                
                # Save crop image for the best representative detection
                crop_path_rel = None
                if is_best and det["plate_crop_img"] is not None:
                    crop_filename = f"anpr_{footage_id}_track_{det['track_id'] or 'veh'}_{det['frame_number']}.jpg"
                    crop_file_path = footage_crops_dir / crop_filename
                    try:
                        cv2.imwrite(str(crop_file_path), det["plate_crop_img"])
                        crop_path_rel = str(Path(settings.PLATE_CROPS_DIR_NAME) / f"footage_{footage_id}" / crop_filename)
                    except Exception as e:
                        logger.error(f"Failed to save plate crop: {e}")

                record = AnprDetection(
                    footage_id=det["footage_id"],
                    track_id=det["track_id"],
                    frame_number=det["frame_number"],
                    timestamp_seconds=det["timestamp_seconds"],
                    vehicle_class=det["vehicle_class"],
                    plate_number_raw=det["plate_number_raw"],
                    plate_number_normalized=det["plate_number_normalized"],
                    confidence=det["confidence"],
                    ocr_confidence=det["ocr_confidence"],
                    detection_confidence=det["detection_confidence"],
                    status=det["status"],
                    format_status=det["format_status"],
                    x1=det["x1"],
                    y1=det["y1"],
                    x2=det["x2"],
                    y2=det["y2"],
                    vehicle_x1=det["vehicle_x1"],
                    vehicle_y1=det["vehicle_y1"],
                    vehicle_x2=det["vehicle_x2"],
                    vehicle_y2=det["vehicle_y2"],
                    plate_crop_path=crop_path_rel,
                    is_consolidated=is_best,
                    sighting_count=sighting_count if is_best else 1,
                )
                db.add(record)
                saved_anpr_records.append(record)

                if is_best:
                    if det["status"] == AnprStatus.OCR_SUCCESS:
                        successful_ocr_count += 1
                    if det["format_status"] == PlateFormatStatus.VALID_FORMAT:
                        valid_format_count += 1

        db.commit()

        # Update job summary counters
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.processed_frames = total_frames
        job.total_plates_detected = total_plates_detected
        job.successful_ocr_count = successful_ocr_count
        job.valid_format_count = valid_format_count
        job.unique_plates_count = len(consolidated_groups)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        elapsed = time.time() - start_time
        logger.info(
            f"ANPR & OCR completed for footage {footage_id} in {elapsed:.2f}s. "
            f"Total Plates: {total_plates_detected}, Unique: {len(consolidated_groups)}, "
            f"Valid Format: {valid_format_count}, Success OCR: {successful_ocr_count}."
        )

    except Exception as e:
        logger.error(f"ANPR pipeline failed for footage {footage_id}: {e}", exc_info=True)
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
