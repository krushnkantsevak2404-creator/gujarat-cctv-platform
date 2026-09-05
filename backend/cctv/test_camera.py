from cctv.stream import connect_camera, read_camera

RTSP_URL = "rtsp://AUTHORIZED-HOST:8554/stream/123"

cap = connect_camera(RTSP_URL)

if cap:
    for frame, pts_ms in read_camera(cap):
        print("Frame received:", frame.shape)
        print("PTS:", pts_ms)