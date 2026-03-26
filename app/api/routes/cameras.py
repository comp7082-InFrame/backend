import cv2
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/")
def list_cameras():
    cameras: list[dict[str, int | str]] = []
    for camera_id in range(settings.CAMERA_SCAN_MAX_INDEX):
        cap = cv2.VideoCapture(camera_id)
        try:
            if cap.isOpened():
                cameras.append({"id": camera_id, "name": f"Camera {camera_id}"})
        finally:
            cap.release()
    return cameras
