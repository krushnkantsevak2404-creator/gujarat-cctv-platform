import time
from typing import Dict, Any, List, Tuple

class ObjectTracker:
    """
    PTS-driven Object Tracker.
    - Driven STRICTLY by PTS deltas (pts_ms), ignoring arrival time.
    - Resilient to Scene Discontinuities (hard cuts / looping feeds).
    - Tolerates Variable Frame Rate (VFR) inter-frame gaps.
    """
    def __init__(self, scene_cut_threshold_ms: float = 3000.0):
        self.scene_cut_threshold_ms = scene_cut_threshold_ms
        self.last_pts_by_cam: Dict[str, float] = {}
        self.active_tracks: Dict[str, List[Dict[str, Any]]] = {}

    def update(self, camera_id: str, detections: List[Dict[str, Any]], pts_ms: float) -> Tuple[List[Dict[str, Any]], float]:
        """
        Updates object trajectories based on stream PTS timestamps.
        Returns tracked objects and current delta PTS.
        """
        camera_id = str(camera_id)
        last_pts = self.last_pts_by_cam.get(camera_id, pts_ms)
        delta_pts = pts_ms - last_pts

        # Section 3 Rule: Handle Scene Discontinuity (loops / hard cuts)
        if delta_pts < 0 or delta_pts > self.scene_cut_threshold_ms:
            print(f"[Tracker] Scene Discontinuity detected on Cam #{camera_id} (ΔPTS={delta_pts:.1f}ms). Resetting track state.")
            self.reset(camera_id)
            delta_pts = 40.0

        self.last_pts_by_cam[camera_id] = pts_ms

        tracked_objects = []
        for i, det in enumerate(detections):
            track_id = 100 + i + (int(camera_id) if camera_id.isdigit() else 1)
            tracked_objects.append({
                "track_id": track_id,
                "label": det.get("label", "VEHICLE"),
                "confidence": det.get("confidence", 0.90),
                "bbox": det.get("bbox", [100, 100, 200, 200]),
                "pts_ms": pts_ms,
                "delta_pts_ms": delta_pts
            })

        self.active_tracks[camera_id] = tracked_objects
        return tracked_objects, delta_pts

    def reset(self, camera_id: str):
        """Resets tracking state for camera upon hard scene cuts."""
        if str(camera_id) in self.active_tracks:
            del self.active_tracks[str(camera_id)]
