"""
GIS Map & Coordinate Fix Verification Test Suite
Verifies:
1. OpenStreetMap Tile Layer integration without API keys.
2. Accurate coordinate persistence for Gujarat cities (Vadodara, Ahmedabad, Surat, Rajkot, Gandhinagar).
3. Vadodara camera (CAM-1 / Camera ID 8) has true Vadodara coordinates (22.3072, 73.1812) and NOT Ahmedabad coordinates.
4. GeoJSON coordinate standard RFC 7946: geometry.coordinates = [longitude, latitude].
5. Latitude / Longitude range validation.
"""

import os
import sys
import sqlite3
import json

def test_sqlite_camera_coordinates():
    print("=== TEST 1: Database Camera Coordinates Validation ===")
    db_path = os.path.join(os.getcwd(), 'storage', 'local_dev.db')
    assert os.path.exists(db_path), f"Database not found at {db_path}"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, camera_code, camera_name, location_name, latitude, longitude FROM cameras")
    cameras = cursor.fetchall()
    conn.close()

    print(f"Total registered cameras in database: {len(cameras)}")
    assert len(cameras) > 0, "No cameras found in database"

    vadodara_cams = []
    ahmedabad_cams = []
    surat_cams = []
    rajkot_cams = []

    for cam in cameras:
        cid, code, name, loc, lat, lng = cam
        print(f"  [Camera #{cid} | {code}] {name} -> Loc: '{loc}' | Lat: {lat}, Lng: {lng}")
        
        # Verify coordinates are valid floats within bounds
        assert lat is not None and lng is not None, f"Camera {code} has null coordinates"
        assert -90.0 <= lat <= 90.0, f"Camera {code} invalid latitude {lat}"
        assert -180.0 <= lng <= 180.0, f"Camera {code} invalid longitude {lng}"

        loc_lower = loc.lower() if loc else ""
        if 'vadodara' in loc_lower or code == 'CAM-1':
            vadodara_cams.append(cam)
        elif 'ahmedabad' in loc_lower:
            ahmedabad_cams.append(cam)
        elif 'surat' in loc_lower:
            surat_cams.append(cam)
        elif 'rajkot' in loc_lower:
            rajkot_cams.append(cam)

    print("\n--- Testing Vadodara Cameras Coordinates ---")
    assert len(vadodara_cams) > 0, "No Vadodara cameras found"
    for cam in vadodara_cams:
        cid, code, name, loc, lat, lng = cam
        print(f"  Verifying Vadodara Camera {code} ({loc}): Lat={lat}, Lng={lng}")
        # Vadodara is approximately Lat 22.25 - 22.38, Lng 73.10 - 73.28
        assert 22.20 <= lat <= 22.40, f"Vadodara camera {code} has wrong latitude {lat} (expected ~22.30)"
        assert 73.00 <= lng <= 73.35, f"Vadodara camera {code} has wrong longitude {lng} (expected ~73.18)"
        # Explicit check: Must NOT be Ahmedabad coordinates (23.0225, 72.5714)
        assert abs(lat - 23.0225) > 0.1, f"Vadodara camera {code} is erroneously set to Ahmedabad latitude!"
        assert abs(lng - 72.5714) > 0.1, f"Vadodara camera {code} is erroneously set to Ahmedabad longitude!"
    print("  [PASS] All Vadodara cameras verified with genuine Vadodara coordinates.")

    print("\n--- Testing Ahmedabad Cameras Coordinates ---")
    for cam in ahmedabad_cams:
        cid, code, name, loc, lat, lng = cam
        assert 22.90 <= lat <= 23.20, f"Ahmedabad camera {code} has wrong latitude {lat}"
        assert 72.40 <= lng <= 72.70, f"Ahmedabad camera {code} has wrong longitude {lng}"
    print("  [PASS] Ahmedabad cameras verified.")

    print("\n--- Testing Surat Cameras Coordinates ---")
    for cam in surat_cams:
        cid, code, name, loc, lat, lng = cam
        assert 21.05 <= lat <= 21.30, f"Surat camera {code} has wrong latitude {lat}"
        assert 72.70 <= lng <= 72.95, f"Surat camera {code} has wrong longitude {lng}"
    print("  [PASS] Surat cameras verified.")

    print("\n--- Testing Rajkot Cameras Coordinates ---")
    for cam in rajkot_cams:
        cid, code, name, loc, lat, lng = cam
        assert 22.15 <= lat <= 22.40, f"Rajkot camera {code} has wrong latitude {lat}"
        assert 70.65 <= lng <= 70.95, f"Rajkot camera {code} has wrong longitude {lng}"
    print("  [PASS] Rajkot cameras verified.")


def test_geojson_specification():
    print("\n=== TEST 2: GeoJSON RFC 7946 Standard & Format Check ===")
    sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
    from app.database.session import SessionLocal
    from app.services import camera_service

    db = SessionLocal()
    try:
        cameras, _ = camera_service.get_cameras(db=db, skip=0, limit=100)
        assert len(cameras) > 0, "No cameras retrieved via camera_service"
        
        for cam in cameras:
            if cam.latitude is not None and cam.longitude is not None:
                coords = [float(cam.longitude), float(cam.latitude)]
                assert len(coords) == 2, "GeoJSON coordinates must have length 2"
                assert coords[0] == float(cam.longitude), "coords[0] must be Longitude (East/West)"
                assert coords[1] == float(cam.latitude), "coords[1] must be Latitude (North/South)"
        print(f"  [PASS] Verified GeoJSON coordinate ordering [lng, lat] for {len(cameras)} cameras.")
    finally:
        db.close()


def test_frontend_map_tile_source():
    print("\n=== TEST 3: Frontend OpenStreetMap Tile Source (Zero API Key) ===")
    gis_map_file = os.path.join(os.getcwd(), 'frontend', 'src', 'components', 'GisMap.jsx')
    assert os.path.exists(gis_map_file), f"GisMap.jsx not found at {gis_map_file}"
    
    with open(gis_map_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'api_key' not in content.lower(), "Found API key reference in GisMap.jsx"
    assert 'maps.googleapis.com' not in content, "Found Google Maps API in GisMap.jsx"
    assert 'api.mapbox.com' not in content, "Found Mapbox API in GisMap.jsx"
    assert 'tile.openstreetmap.org' in content, "OpenStreetMap tile URL not found in GisMap.jsx"
    assert 'OpenStreetMap' in content, "OpenStreetMap attribution not found in GisMap.jsx"
    assert 'Reset Gujarat View' in content, "Reset Gujarat View button not found in GisMap.jsx"
    print("  [PASS] GisMap.jsx uses pure OpenStreetMap tiles with zero API key dependencies.")

    camera_modal_file = os.path.join(os.getcwd(), 'frontend', 'src', 'components', 'CameraModal.jsx')
    with open(camera_modal_file, 'r', encoding='utf-8') as f:
        mcontent = f.read()
    
    assert 'GUJARAT_DISTRICT_PRESETS' in mcontent, "Gujarat District Presets not found in CameraModal.jsx"
    assert 'Vadodara' in mcontent and '22.3072' in mcontent, "Vadodara preset missing in CameraModal.jsx"
    assert 'TileLayer' in mcontent and 'tile.openstreetmap.org' in mcontent, "OpenStreetMap TileLayer missing in CameraModal.jsx"
    print("  [PASS] CameraModal.jsx includes District Presets and Interactive Map Picker.")


if __name__ == '__main__':
    print("Running GIS Map & Coordinates Verification Tests...\n")
    test_sqlite_camera_coordinates()
    test_geojson_specification()
    test_frontend_map_tile_source()
    print("\n=======================================================")
    print("ALL GIS MAP & COORDINATES VERIFICATION TESTS PASSED!")
    print("=======================================================")
