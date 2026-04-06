from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import init_services
from app.database import get_db
from app.models import AttendanceSession
from app.models.attendance_record import AttendanceRecord
from app.models.classes import Classes
from app.models.course import Course
from app.models.student_course import StudentCourse
from app.models.user import User
from app.schemas import AttendanceSessionCreate, AttendanceSessionResponse
from app.services.session_attendance_service import mark_absent_students_for_session

router = APIRouter()

@router.post("/", response_model=AttendanceSessionResponse)
def create_session(
    payload: AttendanceSessionCreate,
    db: Session = Depends(get_db),
):
    db_sess = AttendanceSession(**payload.model_dump())
    db.add(db_sess)
    db.commit()
    db.refresh(db_sess)
    init_services(db, class_id=db_sess.class_id)

    return db_sess

@router.get("/")
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

    response = [
        {
            **session.__dict__,
            "course_name": course_name,
            "term_id": term_id
        }
        for session, course_name, term_id in results
    ]
    return response
    

@router.get("/records")
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

    response = []
    for student_id, first_name, last_name, student_number in students:
        record = record_map.get(student_id)
        response.append(
            {
                "id": str(record.id) if record else f"{session_id}:{student_id}",
                "session_id": session_id,
                "student_id": student_id,
                "status": record.status if record else "absent",
                "face_recognized": record.face_recognized if record else False,
                "timestamp": record.timestamp if record else None,
                "first_name": first_name,
                "last_name": last_name,
                "student_number": student_number,
            }
        )

    return response


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
