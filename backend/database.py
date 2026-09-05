import os
import time
import sqlite3

DB_PATH = os.getenv("DATABASE_PATH", "cctv_events.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cctv_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            pts_ms REAL NOT NULL,
            delta_pts_ms REAL DEFAULT 0.0,
            object_type TEXT NOT NULL,
            tracking_id INTEGER,
            confidence REAL DEFAULT 0.0,
            location TEXT DEFAULT 'Gujarat Sector',
            event_type TEXT DEFAULT 'DETECTION',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize DB table on module import
init_db()

def log_cctv_event(camera_id: str, pts_ms: float, delta_pts_ms: float, object_type: str, 
                   tracking_id: int, confidence: float, location: str, event_type: str = "DETECTION"):
    """Safely logs an AI detection event to SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO cctv_events 
            (camera_id, pts_ms, delta_pts_ms, object_type, tracking_id, confidence, location, event_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(camera_id), float(pts_ms), float(delta_pts_ms), object_type, int(tracking_id), float(confidence), location, event_type, now_str))
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        return event_id
    except Exception as e:
        print(f"[DatabaseError] Failed to log CCTV event: {e}")
        return None

def get_recent_events(limit: int = 50):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cctv_events ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        events = [dict(row) for row in rows]
        conn.close()
        return events
    except Exception as e:
        print(f"[DatabaseError] Failed to read CCTV events: {e}")
        return []
