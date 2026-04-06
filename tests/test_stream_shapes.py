import unittest
import uuid

import numpy as np

from app.utils.drawing import draw_face_boxes


class DrawFaceBoxesTests(unittest.TestCase):
    def test_recognized_face_uses_user_id_for_label_lookup(self):
        frame = np.zeros((40, 40, 3), dtype=np.uint8)
        user_id = uuid.uuid4()
        faces = [
            {
                "user_id": user_id,
                "confidence": 0.91,
                "bbox": {"x": 4, "y": 4, "width": 16, "height": 16},
            }
        ]

        annotated = draw_face_boxes(frame, faces, {user_id: "Alice Example"})

        self.assertEqual(annotated.shape, frame.shape)
        self.assertGreater(int(annotated.sum()), 0)


if __name__ == "__main__":
    unittest.main()
