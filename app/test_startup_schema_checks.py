import asyncio
import unittest
from unittest.mock import patch

from app.main import REQUIRED_TABLES, REQUIRED_VIEWS, lifespan, verify_schema_objects


class FakeInspector:
    def __init__(self, table_names, view_names):
        self.table_names = table_names
        self.view_names = view_names

    def get_table_names(self):
        return list(self.table_names)

    def get_view_names(self):
        return list(self.view_names)


class StartupSchemaCheckTests(unittest.TestCase):
    def test_verify_schema_objects_accepts_complete_schema(self):
        inspector = FakeInspector(
            table_names=REQUIRED_TABLES | {"unused_table"},
            view_names=REQUIRED_VIEWS | {"unused_view"},
        )

        with patch("app.main.inspect", return_value=inspector):
            verify_schema_objects(object())

    def test_verify_schema_objects_raises_for_missing_objects(self):
        inspector = FakeInspector(
            table_names=REQUIRED_TABLES - {"users"},
            view_names=REQUIRED_VIEWS - {"class_users"},
        )

        with patch("app.main.inspect", return_value=inspector):
            with self.assertRaises(RuntimeError) as exc_info:
                verify_schema_objects(object())

        message = str(exc_info.exception)
        self.assertIn("users", message)
        self.assertIn("class_users", message)
        self.assertIn("Run the Supabase migrations", message)

    def test_lifespan_initializes_global_roster_once(self):
        fake_db = FakeStartupDB()
        fake_app = object()

        async def run_lifespan():
            async with lifespan(fake_app):
                return None

        with patch("app.main.verify_schema_objects") as verify_mock:
            with patch("app.main.os.makedirs") as makedirs_mock:
                with patch("app.main.SessionLocal", return_value=fake_db):
                    with patch("app.main.init_services") as init_services_mock:
                        asyncio.run(run_lifespan())

        verify_mock.assert_called_once()
        makedirs_mock.assert_called_once()
        init_services_mock.assert_called_once_with(fake_db)
        self.assertTrue(fake_db.closed)


class FakeStartupDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


if __name__ == "__main__":
    unittest.main()
