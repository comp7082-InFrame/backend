from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/attendance"

    # Face recognition
    DETECTOR_BACKEND: str = "retinaface"  # "retinaface" or "yunet"
    YUNET_MODEL_PATH: str = "models/face_detection_yunet_2023mar.onnx"
    ARCFACE_MODEL_PACK: str = "buffalo_l"
    SIMILARITY_THRESHOLD: float = 0.35

    # Entry/Exit tracking
    ENTRY_FRAME_THRESHOLD: int = 5   # Frames to confirm entry (~0.5s at 10 FPS)
    EXIT_FRAME_THRESHOLD: int = 10   # Frames to confirm exit (~1.0s at 10 FPS)
    LIVE_PRESENCE_TTL_SECONDS: float = 2.0

    # Video processing
    PROCESSING_FPS: int = 10
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    JPEG_QUALITY: int = 70

    # Storage
    UPLOAD_DIR: str = "uploads"

    model_config = ConfigDict(env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
