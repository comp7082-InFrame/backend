import unittest
import uuid
import importlib.util

from app.api.routes.courses import get_courses


class FakeCourseQuery:
    def __init__(self, rows):
        self.rows = rows
        self.join_calls = []
        self.distinct_called = False

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        self.join_calls.append((args, kwargs))
        return self

    def distinct(self):
        self.distinct_called = True
        return self

    def all(self):
        return list(self.rows)


class FakeCourseDB:
    def __init__(self, rows):
        self.rows = rows
        self.last_query = None

    def query(self, model):
        self.last_query = FakeCourseQuery(self.rows)
        return self.last_query


class CourseRouteTests(unittest.TestCase):
    def test_get_courses_without_teacher_filter_avoids_teacher_join(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        course = type("CourseRow", (), {"id": uuid.uuid4(), "term_id": uuid.uuid4(), "name": "Math", "description": None, "active": True})()
        db = FakeCourseDB([course])

        result = get_courses(term_id=course.term_id, teacher_id=None, db=db)

        self.assertEqual(result, [course])
        self.assertEqual(db.last_query.join_calls, [])
        self.assertFalse(db.last_query.distinct_called)

    def test_get_courses_with_teacher_filter_uses_distinct(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        course = type("CourseRow", (), {"id": uuid.uuid4(), "term_id": uuid.uuid4(), "name": "Science", "description": None, "active": True})()
        db = FakeCourseDB([course])

        result = get_courses(term_id=course.term_id, teacher_id=uuid.uuid4(), db=db)

        self.assertEqual(result, [course])
        self.assertEqual(len(db.last_query.join_calls), 1)
        self.assertTrue(db.last_query.distinct_called)


if __name__ == "__main__":
    unittest.main()
