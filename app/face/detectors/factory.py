from .base import FaceDetector


def create_detector(name: str, settings) -> FaceDetector:
    """
    Instantiate a FaceDetector by name.

    Args:
        name: "retinaface" or "yunet"
        settings: app Settings object

    Returns:
        FaceDetector instance
    """
    name = name.lower()
    if name == "retinaface":
        from .retinaface import RetinaFaceDetector
        return RetinaFaceDetector(model_pack=settings.ARCFACE_MODEL_PACK)
    elif name == "yunet":
        from .yunet import YuNetDetector
        return YuNetDetector(model_path=settings.YUNET_MODEL_PATH)
    else:
        raise ValueError(
            f"Unknown detector backend: '{name}'. "
            "Valid options are 'retinaface' and 'yunet'."
        )
