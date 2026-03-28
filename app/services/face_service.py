import uuid
import numpy as np
from typing import List, Dict, Tuple, Optional

from app.config import get_settings
from app.face import FaceRecognitionPipeline, create_pipeline

settings = get_settings()


class FaceService:
    """Service for face detection and recognition."""

    def __init__(self, known_encodings: Dict[uuid.UUID, np.ndarray] = None):
        self.known_encodings = known_encodings or {}
        self.threshold = settings.SIMILARITY_THRESHOLD
        self._pipeline: FaceRecognitionPipeline = create_pipeline(settings)
        self._known_ids: List[uuid.UUID] = []
        self._known_matrix: Optional[np.ndarray] = None
        self._rebuild_matrix()

    def _rebuild_matrix(self):
        """Rebuild the cached known IDs list and encoding matrix."""
        if self.known_encodings:
            self._known_ids = list(self.known_encodings.keys())
            self._known_matrix = np.stack(list(self.known_encodings.values()))
        else:
            self._known_ids = []
            self._known_matrix = None

    def update_known_encodings(self, known_encodings: Dict[uuid.UUID, np.ndarray]):
        """Update the known encodings dictionary."""
        self.known_encodings = known_encodings
        self._rebuild_matrix()

    def add_encoding(self, user_id: uuid.UUID, encoding: np.ndarray):
        """Add a single encoding to known faces."""
        self.known_encodings[user_id] = encoding
        self._rebuild_matrix()

    def remove_encoding(self, user_id: uuid.UUID):
        """Remove an encoding from known faces."""
        if user_id in self.known_encodings:
            del self.known_encodings[user_id]
            self._rebuild_matrix()

    def extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract a 512-dim ArcFace embedding from an image.

        Args:
            image: BGR image (OpenCV format)

        Returns:
            512-dim float32 ndarray, or None if no face found.
        """
        return self._pipeline.extract_embedding(image)

    def process_frame(self, frame: np.ndarray) -> List[dict]:
        """
        Process a single frame and return detected faces with identities.

        Args:
            frame: BGR frame from webcam

        Returns:
            List of face detection results with bounding boxes and identities.
        """
        face_results = self._pipeline.process_frame(frame)

        results = []
        for face in face_results:
            user_id, confidence = self._match_face(face["embedding"])
            results.append({
                "user_id": user_id,
                "confidence": confidence,
                "bbox": face["bbox"],
            })

        return results

    def _match_face(self, encoding: np.ndarray) -> Tuple[Optional[uuid.UUID], float]:
        """
        Match a 512-dim unit-vector embedding against known faces using cosine similarity.

        Returns:
            Tuple of (user_id or None, confidence score)
        """
        if self._known_matrix is None:
            return None, 0.0

        # Cosine similarity: dot product of unit vectors
        similarities = self._known_matrix @ encoding  # (N,)
        best_idx = int(np.argmax(similarities))
        best_similarity = float(similarities[best_idx])

        if best_similarity >= self.threshold:
            return self._known_ids[best_idx], round(best_similarity, 3)

        return None, 0.0
