import unittest
import uuid
import importlib.util
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch


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

    def test_create_session_commits_when_payload_is_valid(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.routes.sessions import create_session
        from app.schemas.attendance_session import AttendanceSessionCreate

        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        room_id = uuid.uuid4()
        payload = AttendanceSessionCreate(
            class_id=class_id,
            teacher_id=teacher_id,
            room_id=room_id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db = FakeCreateSessionDB(
            class_row=SimpleNamespace(id=class_id, room_id=room_id),
            teacher=SimpleNamespace(id=teacher_id),
            room=SimpleNamespace(id=room_id),
            teacher_assignment=SimpleNamespace(id=uuid.uuid4(), class_id=class_id, teacher_id=teacher_id),
        )

        with patch("app.api.routes.sessions.init_services") as init_services_mock:
            result = create_session(payload, db=db)

        self.assertTrue(db.committed)
        self.assertIs(db.refreshed, result)
        self.assertEqual(result.class_id, class_id)
        self.assertEqual(result.teacher_id, teacher_id)
        self.assertEqual(result.room_id, room_id)
        init_services_mock.assert_called_once_with(db, class_id=class_id)

    def test_create_session_rejects_invalid_time_range(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from fastapi import HTTPException

        from app.api.routes.sessions import create_session
        from app.schemas.attendance_session import AttendanceSessionCreate

        payload = AttendanceSessionCreate(
            class_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        db = FakeCreateSessionDB(class_row=None, teacher=None, room=None, teacher_assignment=None)

        with self.assertRaises(HTTPException) as exc_info:
            create_session(payload, db=db)

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertEqual(exc_info.exception.detail, "end_time must be after start_time")
        self.assertFalse(db.committed)

    def test_create_session_rejects_missing_class(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from fastapi import HTTPException

        from app.api.routes.sessions import create_session
        from app.schemas.attendance_session import AttendanceSessionCreate

        payload = AttendanceSessionCreate(
            class_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db = FakeCreateSessionDB(class_row=None, teacher=None, room=None, teacher_assignment=None)

        with self.assertRaises(HTTPException) as exc_info:
            create_session(payload, db=db)

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "Class not found")
        self.assertFalse(db.committed)

    def test_create_session_rejects_missing_teacher(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from fastapi import HTTPException

        from app.api.routes.sessions import create_session
        from app.schemas.attendance_session import AttendanceSessionCreate

        class_id = uuid.uuid4()
        room_id = uuid.uuid4()
        payload = AttendanceSessionCreate(
            class_id=class_id,
            teacher_id=uuid.uuid4(),
            room_id=room_id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db = FakeCreateSessionDB(
            class_row=SimpleNamespace(id=class_id, room_id=room_id),
            teacher=None,
            room=SimpleNamespace(id=room_id),
            teacher_assignment=None,
        )

        with self.assertRaises(HTTPException) as exc_info:
            create_session(payload, db=db)

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "Teacher not found")
        self.assertFalse(db.committed)

    def test_create_session_rejects_missing_room(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from fastapi import HTTPException

        from app.api.routes.sessions import create_session
        from app.schemas.attendance_session import AttendanceSessionCreate

        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        room_id = uuid.uuid4()
        payload = AttendanceSessionCreate(
            class_id=class_id,
            teacher_id=teacher_id,
            room_id=room_id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db = FakeCreateSessionDB(
            class_row=SimpleNamespace(id=class_id, room_id=room_id),
            teacher=SimpleNamespace(id=teacher_id),
            room=None,
            teacher_assignment=SimpleNamespace(id=uuid.uuid4(), class_id=class_id, teacher_id=teacher_id),
        )

        with self.assertRaises(HTTPException) as exc_info:
            create_session(payload, db=db)

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "Room not found")
        self.assertFalse(db.committed)

    def test_create_session_rejects_unassigned_teacher(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from fastapi import HTTPException

        from app.api.routes.sessions import create_session
        from app.schemas.attendance_session import AttendanceSessionCreate

        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        room_id = uuid.uuid4()
        payload = AttendanceSessionCreate(
            class_id=class_id,
            teacher_id=teacher_id,
            room_id=room_id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db = FakeCreateSessionDB(
            class_row=SimpleNamespace(id=class_id, room_id=room_id),
            teacher=SimpleNamespace(id=teacher_id),
            room=SimpleNamespace(id=room_id),
            teacher_assignment=None,
        )

        with self.assertRaises(HTTPException) as exc_info:
            create_session(payload, db=db)

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertEqual(exc_info.exception.detail, "Teacher is not assigned to class")
        self.assertFalse(db.committed)

    def test_create_session_rejects_room_that_does_not_match_class(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from fastapi import HTTPException

        from app.api.routes.sessions import create_session
        from app.schemas.attendance_session import AttendanceSessionCreate

        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        class_room_id = uuid.uuid4()
        payload_room_id = uuid.uuid4()
        payload = AttendanceSessionCreate(
            class_id=class_id,
            teacher_id=teacher_id,
            room_id=payload_room_id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db = FakeCreateSessionDB(
            class_row=SimpleNamespace(id=class_id, room_id=class_room_id),
            teacher=SimpleNamespace(id=teacher_id),
            room=SimpleNamespace(id=payload_room_id),
            teacher_assignment=SimpleNamespace(id=uuid.uuid4(), class_id=class_id, teacher_id=teacher_id),
        )

        with self.assertRaises(HTTPException) as exc_info:
            create_session(payload, db=db)

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertEqual(exc_info.exception.detail, "Room does not match class")
        self.assertFalse(db.committed)

    def test_get_sessions_returns_explicit_contract_shape(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.routes.sessions import getSessions

        session = SimpleNamespace(
            id=uuid.uuid4(),
            class_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        term_id = uuid.uuid4()
        db = FakeSessionReadDB(
            session_results=[(session, "History 101", term_id)],
            session_record_context=None,
        )

        result = getSessions(course_id=uuid.uuid4(), db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, session.id)
        self.assertEqual(result[0].course_name, "History 101")
        self.assertEqual(result[0].term_id, term_id)
        self.assertFalse(hasattr(result[0], "_sa_instance_state"))

    def test_get_session_records_returns_explicit_contract_shape(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.routes.sessions import getSessionRecords

        session_id = uuid.uuid4()
        student_id = uuid.uuid4()
        record_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)

        session = SimpleNamespace(id=session_id, class_id=uuid.uuid4())
        class_row = SimpleNamespace(id=session.class_id, course_id=uuid.uuid4())
        record = SimpleNamespace(
            id=record_id,
            student_id=student_id,
            status="present",
            face_recognized=True,
            timestamp=timestamp,
        )
        db = FakeSessionReadDB(
            session_results=None,
            session_record_context=FakeSessionRecordContext(
                session=session,
                class_row=class_row,
                students=[(student_id, "April", "ONeil", "A001")],
                records=[record],
            ),
        )

        result = getSessionRecords(session_id=session_id, db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, str(record_id))
        self.assertEqual(result[0].session_id, session_id)
        self.assertEqual(result[0].student_id, student_id)
        self.assertEqual(result[0].status, "present")
        self.assertTrue(result[0].face_recognized)
        self.assertEqual(result[0].first_name, "April")
        self.assertEqual(result[0].student_number, "A001")

    def test_get_session_records_returns_synthetic_absent_rows(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.routes.sessions import getSessionRecords

        session_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session = SimpleNamespace(id=session_id, class_id=uuid.uuid4())
        class_row = SimpleNamespace(id=session.class_id, course_id=uuid.uuid4())
        db = FakeSessionReadDB(
            session_results=None,
            session_record_context=FakeSessionRecordContext(
                session=session,
                class_row=class_row,
                students=[(student_id, "Casey", "Jones", "C002")],
                records=[],
            ),
        )

        result = getSessionRecords(session_id=session_id, db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, f"{session_id}:{student_id}")
        self.assertEqual(result[0].status, "absent")
        self.assertFalse(result[0].face_recognized)
        self.assertIsNone(result[0].timestamp)


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


class FakeCreateSessionQuery:
    def __init__(self, row):
        self.row = row

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.row


class FakeCreateSessionDB:
    def __init__(self, class_row, teacher, room, teacher_assignment):
        self.class_row = class_row
        self.teacher = teacher
        self.room = room
        self.teacher_assignment = teacher_assignment
        self.added = []
        self.committed = False
        self.refreshed = None

    def query(self, entity):
        entity_name = getattr(entity, "__name__", None)

        if entity_name == "Classes":
            return FakeCreateSessionQuery(self.class_row)
        if entity_name == "User":
            return FakeCreateSessionQuery(self.teacher)
        if entity_name == "Room":
            return FakeCreateSessionQuery(self.room)
        if entity_name == "TeacherScheduledClass":
            return FakeCreateSessionQuery(self.teacher_assignment)

        raise AssertionError(f"Unexpected query target: {entity!r}")

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.committed = True

    def refresh(self, item):
        self.refreshed = item


class FakeSessionReadQuery:
    def __init__(self, rows):
        self.rows = rows

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        if self.rows is None:
            return []
        return list(self.rows)

    def first(self):
        if self.rows is None:
            return None
        if isinstance(self.rows, list):
            return self.rows[0] if self.rows else None
        return self.rows


class FakeSessionRecordContext:
    def __init__(self, session, class_row, students, records):
        self.session = session
        self.class_row = class_row
        self.students = students
        self.records = records


class FakeSessionReadDB:
    def __init__(self, session_results, session_record_context):
        self.session_results = session_results
        self.session_record_context = session_record_context

    def query(self, *entities):
        if len(entities) == 3:
            return FakeSessionReadQuery(self.session_results)

        entity = entities[0]
        entity_name = getattr(entity, "__name__", None)

        if entity_name == "AttendanceSession":
            return FakeSessionReadQuery(self.session_record_context.session)
        if entity_name == "Classes":
            return FakeSessionReadQuery(self.session_record_context.class_row)
        if entity_name == "AttendanceRecord":
            return FakeSessionReadQuery(self.session_record_context.records)

        entity_keys = tuple(getattr(entity, "key", None) for entity in entities)
        if entity_keys == ("id", "first_name", "last_name", "student_number"):
            return FakeSessionReadQuery(self.session_record_context.students)

        raise AssertionError(f"Unexpected query target: {entities!r}")


if __name__ == "__main__":
    unittest.main()
