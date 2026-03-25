from .pipeline import FaceRecognitionPipeline
from .detectors.factory import create_detector
from .embedders.arcface import ArcFaceEmbedder


def create_pipeline(settings) -> FaceRecognitionPipeline:
    """
    Build a FaceRecognitionPipeline from app settings.

    settings must expose:
      - DETECTOR_BACKEND: str
      - ARCFACE_MODEL_PACK: str
      - YUNET_MODEL_PATH: str  (only needed when DETECTOR_BACKEND == "yunet")
    """
    detector = create_detector(settings.DETECTOR_BACKEND, settings)
    embedder = ArcFaceEmbedder(model_pack=settings.ARCFACE_MODEL_PACK)
    return FaceRecognitionPipeline(detector=detector, embedder=embedder)


__all__ = ["FaceRecognitionPipeline", "create_pipeline"]
