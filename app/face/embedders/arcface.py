from typing import List

import numpy as np

from .base import FaceEmbedder


class ArcFaceEmbedder(FaceEmbedder):
    def __init__(self, model_pack: str = "buffalo_l"):
        from insightface.app import FaceAnalysis

        app = FaceAnalysis(name=model_pack, allowed_modules=["detection", "recognition"])
        app.prepare(ctx_id=-1)
        self._rec = app.models["recognition"]

    def embed(self, aligned_face: np.ndarray) -> np.ndarray:
        vecs = self._rec.get_feat([aligned_face])  # (1, 512) float32
        vec = vecs[0].astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_batch(self, aligned_faces: List[np.ndarray]) -> List[np.ndarray]:
        if not aligned_faces:
            return []
        vecs = self._rec.get_feat(aligned_faces)  # (N, 512) float32
        results = []
        for vec in vecs:
            vec = vec.astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec)
        return results
