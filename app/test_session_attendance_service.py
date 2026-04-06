import unittest
import uuid
import importlib.util
from types import SimpleNamespace


class SessionAttendanceServiceTests(unittest.TestCase):
    def test_select_single_active_class_returns_single_unique_match(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.services.session_attendance_service import select_single_active_class

        class_id = uuid.uuid4()

        selected = select_single_active_class([class_id, class_id])

        self.assertEqual(selected, class_id)

    def test_select_single_active_class_returns_none_for_zero_or_multiple(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.services.session_attendance_service import select_single_active_class

        self.assertIsNone(select_single_active_class([]))
        self.assertIsNone(select_single_active_class([uuid.uuid4(), uuid.uuid4()]))

    def test_mark_absent_students_for_session_adds_only_missing_active_students(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.models.attendance_record import AttendanceRecord
        from app.models.attendance_session import AttendanceSession
        from app.models.classes import Classes
        from app.models.student_course import StudentCourse
        from app.services.session_attendance_service import mark_absent_students_for_session

        session_id = uuid.uuid4()
        class_id = uuid.uuid4()
        course_id = uuid.uuid4()
        existing_student_id = uuid.uuid4()
        missing_student_id = uuid.uuid4()

        db = FakeSessionAttendanceDB(
            session=SimpleNamespace(id=session_id, class_id=class_id),
            class_row=SimpleNamespace(id=class_id, course_id=course_id),
            enrolled_student_ids=[existing_student_id, missing_student_id],
            existing_record_student_ids=[existing_student_id],
        )

        created = mark_absent_students_for_session(db, db.session)

        self.assertEqual(created, 1)
        self.assertEqual(len(db.added_records), 1)

        absent_record = db.added_records[0]
        self.assertIsInstance(absent_record, AttendanceRecord)
        self.assertEqual(absent_record.session_id, session_id)
        self.assertEqual(absent_record.student_id, missing_student_id)
        self.assertEqual(absent_record.status, "absent")
        self.assertFalse(absent_record.face_recognized)

    def test_mark_absent_students_for_session_returns_zero_when_class_missing(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.services.session_attendance_service import mark_absent_students_for_session

        db = FakeSessionAttendanceDB(
            session=SimpleNamespace(id=uuid.uuid4(), class_id=uuid.uuid4()),
            class_row=None,
            enrolled_student_ids=[],
            existing_record_student_ids=[],
        )

        created = mark_absent_students_for_session(db, db.session)

        self.assertEqual(created, 0)
        self.assertEqual(db.added_records, [])

    def test_end_session_marks_absent_students_and_commits(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.routes.sessions import EndSessionRequest, end_session

        session_id = uuid.uuid4()
        class_id = uuid.uuid4()
        course_id = uuid.uuid4()
        existing_student_id = uuid.uuid4()
        missing_student_id = uuid.uuid4()

        db = FakeSessionAttendanceDB(
            session=SimpleNamespace(id=session_id, class_id=class_id),
            class_row=SimpleNamespace(id=class_id, course_id=course_id),
            enrolled_student_ids=[existing_student_id, missing_student_id],
            existing_record_student_ids=[existing_student_id],
        )

        response = end_session(EndSessionRequest(session_id=session_id), db=db)

        self.assertEqual(
            response,
            {"status": "success", "message": "Session ended and absent students marked"},
        )
        self.assertTrue(db.committed)
        self.assertEqual(len(db.added_records), 1)
        self.assertEqual(db.added_records[0].student_id, missing_student_id)

    def test_end_session_raises_404_when_session_missing(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from fastapi import HTTPException

        from app.api.routes.sessions import EndSessionRequest, end_session

        db = FakeSessionAttendanceDB(
            session=None,
            class_row=None,
            enrolled_student_ids=[],
            existing_record_student_ids=[],
        )

        with self.assertRaises(HTTPException) as exc_info:
            end_session(EndSessionRequest(session_id=uuid.uuid4()), db=db)

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "Session not found")
        self.assertFalse(db.committed)


class FakeSessionAttendanceQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        if self.rows is None:
            return None
        if isinstance(self.rows, list):
            return self.rows[0] if self.rows else None
        return self.rows

    def all(self):
        if self.rows is None:
            return []
        if isinstance(self.rows, list):
            return list(self.rows)
        return [self.rows]


class FakeSessionAttendanceDB:
    def __init__(self, session, class_row, enrolled_student_ids, existing_record_student_ids):
        self.session = session
        self.class_row = class_row
        self.enrolled_student_ids = list(enrolled_student_ids)
        self.existing_record_student_ids = list(existing_record_student_ids)
        self.added_records = []
        self.committed = False

    def query(self, entity):
        entity_name = getattr(entity, "__name__", None)
        entity_class_name = getattr(getattr(entity, "class_", None), "__name__", None)
        entity_key = getattr(entity, "key", None)

        if entity_name == "AttendanceSession":
            return FakeSessionAttendanceQuery(self.session)

        if entity_name == "Classes":
            return FakeSessionAttendanceQuery(self.class_row)

        if entity_class_name == "StudentCourse" and entity_key == "student_id":
            rows = [SimpleNamespace(student_id=student_id) for student_id in self.enrolled_student_ids]
            return FakeSessionAttendanceQuery(rows)

        if entity_class_name == "AttendanceRecord" and entity_key == "student_id":
            rows = [SimpleNamespace(student_id=student_id) for student_id in self.existing_record_student_ids]
            return FakeSessionAttendanceQuery(rows)

        raise AssertionError(f"Unexpected query target: {entity!r}")

    def add(self, record):
        self.added_records.append(record)

    def commit(self):
        self.committed = True


if __name__ == "__main__":
    unittest.main()
