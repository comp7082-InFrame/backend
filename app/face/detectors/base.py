from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class DetectedFace:
    bbox: dict          # {"x": int, "y": int, "width": int, "height": int}
    landmarks_5pt: np.ndarray  # (5, 2) float32: [re, le, nose, rm, lm]
    score: float


class FaceDetector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[DetectedFace]:
        """Detect faces in a BGR image. Returns list of DetectedFace."""
