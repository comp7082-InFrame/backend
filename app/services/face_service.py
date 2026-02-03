import cv2
import face_recognition
import numpy as np
from typing import List, Dict, Tuple, Optional
from app.config import get_settings

settings = get_settings()


class FaceService:
    """Service for face detection and recognition."""

    def __init__(self, known_encodings: Dict[int, np.ndarray] = None):
        """
        Initialize face service.

        Args:
            known_encodings: Dict mapping person_id to face encoding
        """
        self.known_encodings = known_encodings or {}
        self.tolerance = settings.FACE_RECOGNITION_TOLERANCE
        self.model = settings.FACE_RECOGNITION_MODEL

    def update_known_encodings(self, known_encodings: Dict[int, np.ndarray]):
        """Update the known encodings dictionary."""
        self.known_encodings = known_encodings

    def add_encoding(self, person_id: int, encoding: np.ndarray):
        """Add a single encoding to known faces."""
        self.known_encodings[person_id] = encoding

    def remove_encoding(self, person_id: int):
        """Remove an encoding from known faces."""
        if person_id in self.known_encodings:
            del self.known_encodings[person_id]

    def extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract face encoding from an image.

        Args:
            image: BGR image (OpenCV format)

        Returns:
            Face encoding array or None if no face found
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image, model=self.model)

        if not face_locations:
            return None

        # Get encoding for the first (or only) face
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        if not encodings:
            return None

        return encodings[0]

    def process_frame(self, frame: np.ndarray) -> List[dict]:
        """
        Process a single frame and return detected faces with identities.

        Args:
            frame: BGR frame from webcam

        Returns:
            List of face detection results with bounding boxes and identities
        """
        # Resize for faster processing (1/4 size)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame, model=self.model)

        if not face_locations:
            return []

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        results = []
        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            # Scale back coordinates to original size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Match against known faces
            person_id, confidence = self._match_face(encoding)

            results.append({
                "person_id": person_id,
                "confidence": confidence,
                "bbox": {
                    "x": left,
                    "y": top,
                    "width": right - left,
                    "height": bottom - top
                }
            })

        return results

    def _match_face(self, encoding: np.ndarray) -> Tuple[Optional[int], float]:
        """
        Match encoding against known faces.

        Args:
            encoding: Face encoding to match

        Returns:
            Tuple of (person_id or None, confidence score)
        """
        if not self.known_encodings:
            return None, 0.0

        known_ids = list(self.known_encodings.keys())
        known_encs = list(self.known_encodings.values())

        # Calculate distances to all known faces
        distances = face_recognition.face_distance(known_encs, encoding)
        best_idx = np.argmin(distances)
        best_distance = distances[best_idx]

        if best_distance <= self.tolerance:
            confidence = 1.0 - best_distance
            return known_ids[best_idx], round(confidence, 3)

        return None, 0.0


def draw_face_boxes(frame: np.ndarray, faces: List[dict], names: Dict[int, str] = None) -> np.ndarray:
    """
    Draw bounding boxes and labels on frame.

    Args:
        frame: BGR frame
        faces: List of face detection results
        names: Dict mapping person_id to name

    Returns:
        Annotated frame
    """
    names = names or {}
    annotated = frame.copy()

    for face in faces:
        bbox = face["bbox"]
        x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
        person_id = face.get("person_id")
        confidence = face.get("confidence", 0)

        # Choose color based on recognition status
        if person_id:
            color = (0, 255, 0)  # Green for recognized
            name = names.get(person_id, f"ID: {person_id}")
            label = f"{name} ({confidence:.0%})"
        else:
            color = (0, 0, 255)  # Red for unknown
            label = "Unknown"

        # Draw rectangle
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

        # Draw label background
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(annotated, (x, y - 20), (x + label_size[0], y), color, -1)

        # Draw label text
        cv2.putText(annotated, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return annotated
