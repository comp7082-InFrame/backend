from typing import List

import numpy as np

from .base import DetectedFace, FaceDetector


class RetinaFaceDetector(FaceDetector):
    def __init__(self, model_pack: str = "buffalo_l", det_size: tuple = (640, 640)):
        from insightface.app import FaceAnalysis

        self._app = FaceAnalysis(name=model_pack, allowed_modules=["detection"])
        self._app.prepare(ctx_id=-1, det_size=det_size)

    def detect(self, image: np.ndarray) -> List[DetectedFace]:
        faces = self._app.get(image)
        results = []
        for f in faces:
            x1, y1, x2, y2 = [int(v) for v in f.bbox]
            results.append(DetectedFace(
                bbox={"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1},
                landmarks_5pt=f.kps.astype(np.float32),
                score=float(f.det_score),
            ))
        return results
