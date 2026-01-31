import cv2
import asyncio
import numpy as np
from typing import AsyncGenerator, Optional
from app.config import get_settings

settings = get_settings()


class CameraService:
    """Service for webcam capture and frame encoding."""

    def __init__(self, camera_id: int = 0):
        """
        Initialize camera service.

        Args:
            camera_id: Camera device ID (0 for default webcam)
        """
        self.camera_id = camera_id
        self.target_fps = settings.PROCESSING_FPS
        self.frame_interval = 1.0 / self.target_fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False

    def start(self) -> bool:
        """
        Initialize camera capture.

        Returns:
            True if camera started successfully
        """
        self.cap = cv2.VideoCapture(self.camera_id)

        if not self.cap.isOpened():
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
        self.is_running = True
        return True

    def stop(self):
        """Release camera."""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from camera.

        Returns:
            Frame as numpy array or None if failed
        """
        if not self.cap or not self.is_running:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    async def get_frames(self) -> AsyncGenerator[np.ndarray, None]:
        """
        Async generator yielding frames at target FPS.

        Yields:
            Frames as numpy arrays
        """
        while self.is_running:
            frame = self.read_frame()
            if frame is None:
                break
            yield frame
            await asyncio.sleep(self.frame_interval)

    @staticmethod
    def encode_frame(frame: np.ndarray, quality: int = None) -> bytes:
        """
        Encode frame as JPEG.

        Args:
            frame: BGR frame
            quality: JPEG quality (0-100)

        Returns:
            JPEG bytes
        """
        if quality is None:
            quality = settings.JPEG_QUALITY
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buffer.tobytes()
