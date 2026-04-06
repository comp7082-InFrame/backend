from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AttendanceSession
from app.models.attendance_record import AttendanceRecord
from app.models.classes import Classes
from app.models.course import Course
from app.models.room import Room
from app.models.schedule_class_teacher import TeacherScheduledClass
from app.models.student_course import StudentCourse
from app.models.user import User
from app.schemas import (
    AttendanceSessionCreate,
    AttendanceSessionListItem,
    AttendanceSessionResponse,
    SessionAttendanceRecordItem,
)
from app.services.session_attendance_service import mark_absent_students_for_session

router = APIRouter()


def _validate_session_payload(
    payload: AttendanceSessionCreate,
    db: Session,
) -> None:
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    class_row = db.query(Classes).filter(Classes.id == payload.class_id).first()
    if class_row is None:
        raise HTTPException(status_code=404, detail="Class not found")

    teacher = (
        db.query(User)
        .filter(User.id == payload.teacher_id, User.role.contains(["teacher"]))
        .first()
    )
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    room = db.query(Room).filter(Room.id == payload.room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    teacher_assignment = (
        db.query(TeacherScheduledClass)
        .filter(
            TeacherScheduledClass.class_id == payload.class_id,
            TeacherScheduledClass.teacher_id == payload.teacher_id,
        )
        .first()
    )
    if teacher_assignment is None:
        raise HTTPException(status_code=400, detail="Teacher is not assigned to class")

    if class_row.room_id != payload.room_id:
        raise HTTPException(status_code=400, detail="Room does not match class")


@router.post("/", response_model=AttendanceSessionResponse)
def create_session(
    payload: AttendanceSessionCreate,
    db: Session = Depends(get_db),
):
    _validate_session_payload(payload, db)
    db_sess = AttendanceSession(**payload.model_dump())
    db.add(db_sess)
    db.commit()
    db.refresh(db_sess)

    return db_sess

@router.get("/", response_model=list[AttendanceSessionListItem])
def getSessions(course_id: uuid.UUID, class_id:Optional[uuid.UUID]=None, db: Session = Depends(get_db)):
    query = (
        db.query(AttendanceSession, Course.name.label('course_name'), Course.term_id )
        .join(Classes, Classes.id == AttendanceSession.class_id)
        .join(Course, Course.id == Classes.course_id)
        .filter(Course.id == course_id)
        .order_by(AttendanceSession.start_time.desc())
    )
    if class_id:
        query = query.filter(Classes.id == class_id)
    results = query.all()

    return [
        AttendanceSessionListItem(
            id=session.id,
            class_id=session.class_id,
            teacher_id=session.teacher_id,
            room_id=session.room_id,
            start_time=session.start_time,
            end_time=session.end_time,
            course_name=course_name,
            term_id=term_id,
        )
        for session, course_name, term_id in results
    ]
    

@router.get("/records", response_model=list[SessionAttendanceRecordItem])
def getSessionRecords(session_id: uuid.UUID, db: Session = Depends(get_db)):
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    class_row = db.query(Classes).filter(Classes.id == session.class_id).first()
    if class_row is None:
        raise HTTPException(status_code=404, detail="Class not found")

    students = (
        db.query(User.id, User.first_name, User.last_name, User.student_number)
        .join(StudentCourse, StudentCourse.student_id == User.id)
        .filter(StudentCourse.course_id == class_row.course_id)
        .filter(User.active.is_(True))
        .order_by(User.student_number.asc(), User.last_name.asc(), User.first_name.asc())
        .all()
    )

    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.session_id == session_id)
        .all()
    )
    record_map = {record.student_id: record for record in records}

    return [
        SessionAttendanceRecordItem(
            id=str(record.id) if record else f"{session_id}:{student_id}",
            session_id=session_id,
            student_id=student_id,
            status=record.status if record else "absent",
            face_recognized=record.face_recognized if record else False,
            timestamp=record.timestamp if record else None,
            first_name=first_name,
            last_name=last_name,
            student_number=student_number,
        )
        for student_id, first_name, last_name, student_number in students
        for record in [record_map.get(student_id)]
    ]


class EndSessionRequest(BaseModel):
    session_id: uuid.UUID


@router.post("/end")
def end_session(request: EndSessionRequest, db: Session = Depends(get_db)):
    """End a session and mark absent students."""
    session_id = request.session_id

    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    mark_absent_students_for_session(db, session)
    db.commit()

    return {"status": "success", "message": "Session ended and absent students marked"}
