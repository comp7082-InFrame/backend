import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.database import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.student_course import StudentCourse
from app.models.classes import Classes
from app.models.course import Course
from app.models.user import User

router = APIRouter()


class AttendanceStatus(BaseModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str
    student_number: Optional[str] = None
    status: str  # 'present' or 'absent'
    face_recognized: Optional[bool] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceRecordResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    student_id: uuid.UUID
    status: str
    face_recognized: bool
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/current", response_model=List[AttendanceStatus])
def get_current_attendance(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get full attendance status for an active session.
    Returns all enrolled students with present/absent status.
    Absent students are derived from student_course since mark_absent
    only runs at session end.
    """
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        return []

    # Get all students enrolled in this course
    enrolled = (
        db.query(User)
        .join(StudentCourse, StudentCourse.student_id == User.id)
        .join(Classes, Classes.course_id == StudentCourse.course_id)
        .filter(Classes.id == session.class_id)
        .all()
    )

    # Get present records for this session
    present_records = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.status == "present"
        )
        .all()
    )
    present_map = {r.student_id: r for r in present_records}

    result = []
    for user in enrolled:
        record = present_map.get(user.id)
        result.append(AttendanceStatus(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            student_number=user.student_number,
            status="present" if record else "absent",
            face_recognized=record.face_recognized if record else None,
            timestamp=record.timestamp if record else None,
        ))

    return result


@router.get("/history", response_model=List[AttendanceRecordResponse])
def get_attendance_history(
    session_id: Optional[uuid.UUID] = None,
    student_id: Optional[uuid.UUID] = None,
    course_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Query attendance records with optional filters.
    Use session_id for a specific session, student_id for a student's history,
    or course_id for all records across a course.
    """
    query = db.query(AttendanceRecord)

    if session_id:
        query = query.filter(AttendanceRecord.session_id == session_id)

    if student_id:
        query = query.filter(AttendanceRecord.student_id == student_id)

    if course_id:
        query = (
            query.join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
            .join(Classes, Classes.id == AttendanceSession.class_id)
            .join(Course, Course.id == Classes.course_id)
            .filter(Course.id == course_id)
        )

    return query.order_by(desc(AttendanceRecord.timestamp)).all()
