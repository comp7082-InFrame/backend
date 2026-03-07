from typing import List

import cv2
import numpy as np

from .base import DetectedFace, FaceDetector


class YuNetDetector(FaceDetector):
    def __init__(self, model_path: str, score_threshold: float = 0.6):
        self._model_path = model_path
        self._score_threshold = score_threshold
        self._det = None
        self._input_size = (0, 0)

    def _ensure_detector(self, w: int, h: int):
        if self._det is None:
            self._det = cv2.FaceDetectorYN.create(
                self._model_path, "", (w, h), score_threshold=self._score_threshold
            )
            self._input_size = (w, h)
        elif self._input_size != (w, h):
            self._det.setInputSize((w, h))
            self._input_size = (w, h)

    def detect(self, image: np.ndarray) -> List[DetectedFace]:
        h, w = image.shape[:2]
        self._ensure_detector(w, h)
        _, raw = self._det.detect(image)
        if raw is None:
            return []

        results = []
        for row in raw:
            x, y, bw, bh = int(row[0]), int(row[1]), int(row[2]), int(row[3])
            landmarks_5pt = np.array([
                [row[4],  row[5]],   # right eye
                [row[6],  row[7]],   # left eye
                [row[8],  row[9]],   # nose tip
                [row[10], row[11]],  # right mouth corner
                [row[12], row[13]],  # left mouth corner
            ], dtype=np.float32)
            score = float(row[14])
            results.append(DetectedFace(
                bbox={"x": x, "y": y, "width": bw, "height": bh},
                landmarks_5pt=landmarks_5pt,
                score=score,
            ))
        return results
