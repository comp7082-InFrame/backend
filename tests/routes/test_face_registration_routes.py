import asyncio
import os
import tempfile
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.api.routes.face_registration import register_face, remove_face, update_face


class FakeQuery:
    def __init__(self, db):
        self.db = db

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.db.user


class FakeDB:
    def __init__(self, user=None):
        self.user = user
        self.committed = False
        self.refreshed = None

    def query(self, model):
        return FakeQuery(self)

    def commit(self):
        self.committed = True

    def refresh(self, user):
        self.refreshed = user


class FakeUser:
    def __init__(self):
        self.id = uuid.uuid4()
        self.first_name = "April"
        self.last_name = "ONeil"
        self.photo_path = None
        self.photo_encoding = None


class FaceRegistrationRouteTests(unittest.TestCase):
    def test_register_face_updates_user_and_runtime_services(self):
        user = FakeUser()
        db = FakeDB(user=user)
        prepared_photo = type(
            "Prepared",
            (),
            {"photo_path": "uploads/april.jpg", "encoding": "embedding", "encoding_bytes": b"encoding-bytes"},
        )()

        with patch("app.api.routes.face_registration.prepare_user_photo", new=AsyncMock(return_value=prepared_photo)) as prepare_mock:
            with patch("app.api.routes.face_registration.add_user_to_services") as add_user_mock:
                result = asyncio.run(register_face(user_id=user.id, photo=object(), db=db))

        self.assertIs(result, user)
        self.assertEqual(user.photo_path, "uploads/april.jpg")
        self.assertEqual(user.photo_encoding, b"encoding-bytes")
        prepare_mock.assert_awaited_once()
        add_user_mock.assert_called_once_with(user.id, "April ONeil", "embedding")
        self.assertTrue(db.committed)
        self.assertIs(db.refreshed, user)

    def test_register_face_raises_404_when_user_missing(self):
        db = FakeDB(user=None)

        with self.assertRaises(HTTPException) as exc_info:
            asyncio.run(register_face(user_id=uuid.uuid4(), photo=object(), db=db))

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "User not found")

    def test_update_face_updates_existing_photo(self):
        user = FakeUser()
        db = FakeDB(user=user)
        prepared_photo = type(
            "Prepared",
            (),
            {"photo_path": "uploads/april-new.jpg", "encoding": "embedding", "encoding_bytes": b"encoding-bytes"},
        )()

        with patch("app.api.routes.face_registration.prepare_user_photo", new=AsyncMock(return_value=prepared_photo)):
            with patch("app.api.routes.face_registration.add_user_to_services") as add_user_mock:
                result = asyncio.run(update_face(user_id=user.id, photo=object(), db=db))

        self.assertIs(result, user)
        self.assertEqual(user.photo_path, "uploads/april-new.jpg")
        add_user_mock.assert_called_once_with(user.id, "April ONeil", "embedding")
        self.assertTrue(db.committed)

    def test_remove_face_clears_db_fields_and_runtime_services(self):
        user = FakeUser()

        with tempfile.TemporaryDirectory() as temp_dir:
            user.photo_path = os.path.join(temp_dir, "face.jpg")
            with open(user.photo_path, "wb") as handle:
                handle.write(b"old")

            db = FakeDB(user=user)

            with patch("app.api.routes.face_registration.remove_user_from_services") as remove_user_mock:
                result = asyncio.run(remove_face(user_id=user.id, db=db))

        self.assertEqual(result, {"message": "Face registration removed successfully"})
        self.assertIsNone(user.photo_path)
        self.assertIsNone(user.photo_encoding)
        self.assertTrue(db.committed)
        remove_user_mock.assert_called_once_with(user.id)
