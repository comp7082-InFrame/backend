import cv2
import numpy as np
from typing import List, Dict


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

        if person_id:
            color = (0, 255, 0)  # Green for recognized
            name = names.get(person_id, f"ID: {person_id}")
            label = f"{name} ({confidence:.0%})"
        else:
            color = (0, 0, 255)  # Red for unknown
            label = "Unknown"

        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(annotated, (x, y - 20), (x + label_size[0], y), color, -1)

        cv2.putText(annotated, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return annotated
