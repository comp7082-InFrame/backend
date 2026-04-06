import uuid
from datetime import datetime, timezone
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.classes import Classes
from app.models.recognition_history import RecognitionHistory
from app.models.schedule_class_teacher import TeacherScheduledClass
from app.models.student_course import StudentCourse


def select_single_active_class(class_ids: Iterable[uuid.UUID]) -> Optional[uuid.UUID]:
    unique_ids: list[uuid.UUID] = []
    seen: set[uuid.UUID] = set()

    for class_id in class_ids:
        if class_id not in seen:
            unique_ids.append(class_id)
            seen.add(class_id)

    if len(unique_ids) != 1:
        return None

    return unique_ids[0]


def resolve_active_class_for_student(
    db: Session,
    student_id: uuid.UUID,
    seen_at: datetime,
) -> Optional[uuid.UUID]:
    candidate_rows = (
        db.query(Classes.id)
        .join(StudentCourse, StudentCourse.course_id == Classes.course_id)
        .filter(
            StudentCourse.student_id == student_id,
            StudentCourse.status == "active",
            Classes.status == True,
            Classes.start_time <= seen_at,
            Classes.end_time >= seen_at,
        )
        .all()
    )

    return select_single_active_class(row.id for row in candidate_rows)


def get_or_create_session_for_class(
    db: Session,
    class_id: uuid.UUID,
    seen_at: datetime,
) -> Optional[AttendanceSession]:
    existing = (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.class_id == class_id,
            AttendanceSession.start_time <= seen_at,
            AttendanceSession.end_time >= seen_at,
        )
        .order_by(AttendanceSession.start_time.desc())
        .first()
    )
    if existing is not None:
        return existing

    class_row = db.query(Classes).filter(Classes.id == class_id).one_or_none()
    if class_row is None:
        return None

    teacher_assignment = (
        db.query(TeacherScheduledClass)
        .filter(TeacherScheduledClass.class_id == class_id)
        .order_by(TeacherScheduledClass.created_at.asc())
        .first()
    )
    if teacher_assignment is None:
        return None

    created = AttendanceSession(
        class_id=class_row.id,
        teacher_id=teacher_assignment.teacher_id,
        room_id=class_row.room_id,
        start_time=class_row.start_time,
        end_time=class_row.end_time,
    )
    db.add(created)
    db.flush()
    return created


def mark_absent_students_for_session(
    db: Session,
    session: AttendanceSession,
    recorded_at: datetime | None = None,
) -> int:
    class_row = db.query(Classes).filter(Classes.id == session.class_id).first()
    if class_row is None:
        return 0

    enrolled_rows = (
        db.query(StudentCourse.student_id)
        .filter(
            StudentCourse.course_id == class_row.course_id,
            StudentCourse.status == "active",
        )
        .all()
    )
    enrolled_student_ids = {row.student_id for row in enrolled_rows}

    existing_rows = (
        db.query(AttendanceRecord.student_id)
        .filter(AttendanceRecord.session_id == session.id)
        .all()
    )
    existing_student_ids = {row.student_id for row in existing_rows}

    missing_student_ids = sorted(enrolled_student_ids - existing_student_ids, key=str)
    if not missing_student_ids:
        return 0

    absent_timestamp = recorded_at or datetime.now(timezone.utc)
    for student_id in missing_student_ids:
        db.add(
            AttendanceRecord(
                session_id=session.id,
                student_id=student_id,
                status="absent",
                face_recognized=False,
                timestamp=absent_timestamp,
            )
        )

    return len(missing_student_ids)


def record_attendance_from_recognition(
    db: Session,
    user_id: uuid.UUID,
    confidence: float,
    timestamp: datetime,
    explicit_session_id: uuid.UUID | None = None,
) -> uuid.UUID | None:
    session_row: AttendanceSession | None = None

    if explicit_session_id is not None:
        session_row = (
            db.query(AttendanceSession)
            .filter(AttendanceSession.id == explicit_session_id)
            .one_or_none()
        )
    else:
        class_id = resolve_active_class_for_student(db, user_id, timestamp)
        if class_id is not None:
            session_row = get_or_create_session_for_class(db, class_id, timestamp)

    if session_row is None:
        return None

    recognition = RecognitionHistory(
        attendance_session_id=session_row.id,
        user_id=user_id,
        confidence=confidence,
        recognized=True,
        timestamp=timestamp,
    )
    db.add(recognition)

    attendance_record = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.session_id == session_row.id,
            AttendanceRecord.student_id == user_id,
        )
        .one_or_none()
    )

    if attendance_record is None:
        attendance_record = AttendanceRecord(
            session_id=session_row.id,
            student_id=user_id,
            status="present",
            face_recognized=True,
            timestamp=timestamp,
        )
        db.add(attendance_record)
    else:
        attendance_record.status = "present"
        attendance_record.face_recognized = True
        attendance_record.timestamp = timestamp

    db.commit()
    return session_row.id
