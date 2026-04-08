import unittest
import uuid
from unittest.mock import patch

import numpy as np

from app.services.face_service import FaceService


class FakePipeline:
    def __init__(self, frame_results=None, embedding=None):
        self.frame_results = list(frame_results or [])
        self.embedding = embedding

    def process_frame(self, frame):
        return list(self.frame_results)

    def extract_embedding(self, image):
        return self.embedding


class FaceServiceTests(unittest.TestCase):
    def test_process_frame_matches_known_face_above_threshold(self):
        user_id = uuid.uuid4()
        known_encoding = np.array([1.0, 0.0], dtype=np.float32)
        detected_encoding = np.array([0.9, 0.1], dtype=np.float32)
        pipeline = FakePipeline(
            frame_results=[
                {
                    "embedding": detected_encoding,
                    "bbox": {"x": 1, "y": 2, "width": 3, "height": 4},
                }
            ]
        )

        with patch("app.services.face_service.create_pipeline", return_value=pipeline):
            service = FaceService({user_id: known_encoding})
            service.threshold = 0.5
            results = service.process_frame(np.zeros((4, 4, 3), dtype=np.uint8))

        self.assertEqual(results[0]["user_id"], user_id)
        self.assertEqual(results[0]["confidence"], 0.9)
        self.assertEqual(results[0]["bbox"]["width"], 3)

    def test_process_frame_returns_unknown_when_below_threshold(self):
        user_id = uuid.uuid4()
        pipeline = FakePipeline(
            frame_results=[
                {
                    "embedding": np.array([0.3, 0.0], dtype=np.float32),
                    "bbox": {"x": 0, "y": 0, "width": 1, "height": 1},
                }
            ]
        )

        with patch("app.services.face_service.create_pipeline", return_value=pipeline):
            service = FaceService({user_id: np.array([1.0, 0.0], dtype=np.float32)})
            service.threshold = 0.5
            results = service.process_frame(np.zeros((4, 4, 3), dtype=np.uint8))

        self.assertIsNone(results[0]["user_id"])
        self.assertEqual(results[0]["confidence"], 0.0)

    def test_add_and_remove_encoding_rebuild_the_known_matrix(self):
        first_user = uuid.uuid4()
        second_user = uuid.uuid4()

        with patch("app.services.face_service.create_pipeline", return_value=FakePipeline()):
            service = FaceService({first_user: np.array([1.0, 0.0], dtype=np.float32)})
            service.add_encoding(second_user, np.array([0.0, 1.0], dtype=np.float32))
            self.assertEqual(set(service.known_encodings), {first_user, second_user})
            self.assertEqual(service._known_matrix.shape, (2, 2))

            service.remove_encoding(first_user)

        self.assertEqual(set(service.known_encodings), {second_user})
        self.assertEqual(service._known_matrix.shape, (1, 2))

    def test_extract_face_encoding_delegates_to_pipeline(self):
        expected = np.array([0.5, 0.5], dtype=np.float32)
        pipeline = FakePipeline(embedding=expected)

        with patch("app.services.face_service.create_pipeline", return_value=pipeline):
            service = FaceService()
            result = service.extract_face_encoding(np.zeros((2, 2, 3), dtype=np.uint8))

        self.assertTrue(np.array_equal(result, expected))
