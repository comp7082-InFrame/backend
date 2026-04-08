import asyncio
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.api.routes.users import get_user_by_id, get_users, update_user


class FakeQuery:
    def __init__(self, db):
        self.db = db
        self.filter_calls = []

    def filter(self, *args, **kwargs):
        self.filter_calls.append((args, kwargs))
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.db.single_user

    def all(self):
        return list(self.db.users)


class FakeDB:
    def __init__(self, single_user=None, users=None):
        self.single_user = single_user
        self.users = users or []
        self.committed = False
        self.refreshed = None
        self.last_query = None

    def query(self, model):
        self.last_query = FakeQuery(self)
        return self.last_query

    def commit(self):
        self.committed = True

    def refresh(self, user):
        self.refreshed = user


class FakeUser:
    def __init__(self, user_id=None):
        self.id = user_id or uuid.uuid4()
        self.first_name = "Leonardo"
        self.last_name = "Hamato"
        self.email = "leo@example.com"
        self.role = ["student"]
        self.photo_path = None
        self.photo_encoding = None
        self.student_number = None
        self.major = None
        self.employee_number = None
        self.department = None
        self.title = None
        self.active = True


class UserRouteTests(unittest.TestCase):
    def test_get_users_returns_active_users(self):
        users = [FakeUser(), FakeUser()]
        db = FakeDB(users=users)

        result = get_users(db=db)

        self.assertEqual(result, users)
        self.assertEqual(len(db.last_query.filter_calls), 1)

    def test_get_users_applies_role_filter(self):
        users = [FakeUser()]
        db = FakeDB(users=users)

        result = get_users(role="teacher", db=db)

        self.assertEqual(result, users)
        self.assertEqual(len(db.last_query.filter_calls), 2)

    def test_get_user_by_id_returns_user(self):
        user = FakeUser()
        db = FakeDB(single_user=user)

        result = get_user_by_id(user.id, db=db)

        self.assertIs(result, user)

    def test_get_user_by_id_raises_404_when_missing(self):
        db = FakeDB(single_user=None)

        with self.assertRaises(HTTPException) as exc_info:
            get_user_by_id(uuid.uuid4(), db=db)

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "User not found")

    def test_update_user_updates_fields_and_commits(self):
        user = FakeUser()
        db = FakeDB(single_user=user)

        result = asyncio.run(
            update_user(
                user_uuid=str(user.id),
                first_name="Michelangelo",
                last_name=None,
                email="mikey@example.com",
                role='["teacher"]',
                student_number=None,
                major=None,
                employee_number=None,
                department=None,
                title=None,
                active=False,
                photo=None,
                db=db,
            )
        )

        self.assertIs(result, user)
        self.assertEqual(user.first_name, "Michelangelo")
        self.assertEqual(user.email, "mikey@example.com")
        self.assertEqual(user.role, ["teacher"])
        self.assertFalse(user.active)
        self.assertTrue(db.committed)
        self.assertIs(db.refreshed, user)

    def test_update_user_processes_photo_with_shared_helper(self):
        user = FakeUser()
        db = FakeDB(single_user=user)
        prepared_photo = AsyncPreparedPhoto(
            photo_path="uploads/raph.jpg",
            encoding=b"embedding-array",
            encoding_bytes=b"embedding-bytes",
        )

        with patch("app.api.routes.users.prepare_user_photo", new=AsyncMock(return_value=prepared_photo)) as prepare_mock:
            with patch("app.api.routes.users.add_user_to_services") as add_user_mock:
                result = asyncio.run(
                    update_user(
                        user_uuid=str(user.id),
                        first_name=None,
                        last_name=None,
                        email=None,
                        role=None,
                        student_number=None,
                        major=None,
                        employee_number=None,
                        department=None,
                        title=None,
                        active=None,
                        photo=object(),
                        db=db,
                    )
                )

        self.assertIs(result, user)
        self.assertEqual(user.photo_path, "uploads/raph.jpg")
        self.assertEqual(user.photo_encoding, b"embedding-bytes")
        prepare_mock.assert_awaited_once()
        add_user_mock.assert_called_once_with(
            user.id,
            "Leonardo Hamato",
            b"embedding-array",
        )
        self.assertTrue(db.committed)
        self.assertIs(db.refreshed, user)

    def test_update_user_falls_back_to_single_role_string_when_json_is_invalid(self):
        user = FakeUser()
        db = FakeDB(single_user=user)

        asyncio.run(
            update_user(
                user_uuid=str(user.id),
                role="teacher",
                photo=None,
                db=db,
            )
        )

        self.assertEqual(user.role, ["teacher"])

    def test_update_user_raises_404_when_missing(self):
        db = FakeDB(single_user=None)

        with self.assertRaises(HTTPException) as exc_info:
            asyncio.run(
                update_user(
                    user_uuid=str(uuid.uuid4()),
                    photo=None,
                    db=db,
                )
            )

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "User not found")


class AsyncPreparedPhoto:
    def __init__(self, photo_path, encoding, encoding_bytes):
        self.photo_path = photo_path
        self.encoding = encoding
        self.encoding_bytes = encoding_bytes
