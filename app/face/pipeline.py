from typing import List, Optional

import numpy as np

from .detectors.base import FaceDetector
from .embedders.base import FaceEmbedder
from .preprocessing.alignment import align_face


class FaceRecognitionPipeline:
    def __init__(self, detector: FaceDetector, embedder: FaceEmbedder):
        self.detector = detector
        self.embedder = embedder

    def process_frame(self, frame: np.ndarray) -> List[dict]:
        """
        Detect all faces in a frame, embed each, and return a list of dicts.

        Returns:
            [{"bbox": {...}, "embedding": ndarray(512,), "det_score": float}, ...]
        """
        detected = self.detector.detect(frame)
        if not detected:
            return []

        aligned = [align_face(frame, d.landmarks_5pt) for d in detected]
        embeddings = self.embedder.embed_batch(aligned)

        return [
            {
                "bbox": d.bbox,
                "embedding": emb,
                "det_score": d.score,
            }
            for d, emb in zip(detected, embeddings)
        ]

    def extract_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect the highest-confidence face in image and return its 512-dim embedding.

        Returns:
            numpy array (512,) float32, or None if no face detected.
        """
        detected = self.detector.detect(image)
        if not detected:
            return None

        best = max(detected, key=lambda d: d.score)
        aligned = align_face(image, best.landmarks_5pt)
        return self.embedder.embed(aligned)
