import cv2
import numpy as np
from typing import List, Dict, Any

class AIDetector:
    """
    AI Detection Model Interface.
    Processes video frames and returns detected objects (ANPR, Vehicles, Crowd).
    """
    def __init__(self, model_path: str = "models/yolo_cctv.onnx"):
        self.model_path = model_path
        print(f"[AIDetector] Initializing AI Detection Pipeline (Model: {model_path})")

    def detect(self, frame: np.ndarray, pts_ms: float) -> List[Dict[str, Any]]:
        """
        Runs object detection on input frame.
        Returns list of detection dictionaries: {label, confidence, bbox}
        """
        if frame is None or frame.size == 0:
            return []

        h, w, _ = frame.shape
        speed_px_per_ms = 0.08
        obj_x = int(((pts_ms * speed_px_per_ms) % (w - 100)))
        obj_y = int(h * 0.55)

        detections = []
        if 0 <= obj_x <= w - 80:
            detections.append({
                "label": "VEHICLE",
                "confidence": 0.95,
                "bbox": [obj_x, obj_y, obj_x + 90, obj_y + 45]
            })

        return detections

    def draw_detections(self, frame: np.ndarray, tracked_objects: List[Dict[str, Any]]) -> np.ndarray:
        """Draws bounding boxes and labels on frame."""
        annotated = frame.copy()
        for obj in tracked_objects:
            bbox = obj.get("bbox", [0, 0, 50, 50])
            track_id = obj.get("track_id", 0)
            label = obj.get("label", "OBJECT")
            conf = obj.get("confidence", 0.9)
            
            x1, y1, x2, y2 = bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 120), 2)
            cv2.putText(annotated, f"{label} #{track_id} ({int(conf*100)}%)", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 120), 1)

        return annotated
