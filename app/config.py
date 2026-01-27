from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/attendance"

    # Face recognition
    FACE_RECOGNITION_TOLERANCE: float = 0.6
    FACE_RECOGNITION_MODEL: str = "hog"  # "hog" for CPU, "cnn" for GPU

    # Entry/Exit tracking
    ENTRY_FRAME_THRESHOLD: int = 5   # Frames to confirm entry (~0.5s at 10 FPS)
    EXIT_FRAME_THRESHOLD: int = 10   # Frames to confirm exit (~1.0s at 10 FPS)

    # Video processing
    PROCESSING_FPS: int = 10
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    JPEG_QUALITY: int = 70

    # Storage
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
