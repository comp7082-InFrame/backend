import asyncio
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile

from app.services.user_photo_service import prepare_user_photo, settings


class FakeFaceService:
    def __init__(self, encoding):
        self.encoding = encoding

    def extract_face_encoding(self, image):
        return self.encoding


class UserPhotoServiceTests(unittest.TestCase):
    def test_prepare_user_photo_saves_photo_and_removes_previous_file(self):
        image = np.full((8, 8, 3), 255, dtype=np.uint8)
        success, encoded = cv2.imencode(".jpg", image)
        self.assertTrue(success)

        upload = UploadFile(filename="raph.jpg", file=BytesIO(encoded.tobytes()))
        expected_encoding = np.ones(512, dtype=np.float32)

        with tempfile.TemporaryDirectory() as temp_dir:
            old_photo_path = os.path.join(temp_dir, "old-photo.jpg")
            with open(old_photo_path, "wb") as file_handle:
                file_handle.write(b"old")

            with patch("app.services.user_photo_service.get_face_service", return_value=FakeFaceService(expected_encoding)):
                with patch.object(settings, "UPLOAD_DIR", temp_dir):
                    prepared_photo = asyncio.run(
                        prepare_user_photo(upload, existing_photo_path=old_photo_path)
                    )

            self.assertTrue(os.path.exists(prepared_photo.photo_path))
            self.assertFalse(os.path.exists(old_photo_path))

        self.assertTrue(prepared_photo.photo_path.endswith(".jpg"))
        self.assertEqual(prepared_photo.encoding.tolist(), expected_encoding.tolist())
        self.assertEqual(prepared_photo.encoding_bytes, expected_encoding.tobytes())

    def test_prepare_user_photo_raises_400_for_invalid_image(self):
        upload = UploadFile(filename="donnie.txt", file=BytesIO(b"not-an-image"))

        with self.assertRaises(HTTPException) as exc_info:
            asyncio.run(prepare_user_photo(upload))

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertEqual(exc_info.exception.detail, "Invalid image file")

    def test_prepare_user_photo_raises_503_when_face_service_missing(self):
        image = np.full((4, 4, 3), 255, dtype=np.uint8)
        success, encoded = cv2.imencode(".jpg", image)
        self.assertTrue(success)
        upload = UploadFile(filename="leo.jpg", file=BytesIO(encoded.tobytes()))

        with patch("app.services.user_photo_service.get_face_service", return_value=None):
            with self.assertRaises(HTTPException) as exc_info:
                asyncio.run(prepare_user_photo(upload))

        self.assertEqual(exc_info.exception.status_code, 503)
        self.assertEqual(exc_info.exception.detail, "Face recognition service is not initialized")

    def test_prepare_user_photo_raises_400_when_no_face_detected(self):
        image = np.full((4, 4, 3), 255, dtype=np.uint8)
        success, encoded = cv2.imencode(".jpg", image)
        self.assertTrue(success)
        upload = UploadFile(filename="mikey.jpg", file=BytesIO(encoded.tobytes()))

        with patch("app.services.user_photo_service.get_face_service", return_value=FakeFaceService(None)):
            with self.assertRaises(HTTPException) as exc_info:
                asyncio.run(prepare_user_photo(upload))

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertEqual(exc_info.exception.detail, "No face detected in image")


if __name__ == "__main__":
    unittest.main()
