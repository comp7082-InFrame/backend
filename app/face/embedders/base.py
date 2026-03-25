from abc import ABC, abstractmethod
from typing import List

import numpy as np


class FaceEmbedder(ABC):
    @abstractmethod
    def embed(self, aligned_face: np.ndarray) -> np.ndarray:
        """Return a normalised 512-dim float32 embedding for a single 112x112 BGR face."""

    def embed_batch(self, aligned_faces: List[np.ndarray]) -> List[np.ndarray]:
        """Embed a list of faces. Default: loop over embed(). Override for batching."""
        return [self.embed(f) for f in aligned_faces]
