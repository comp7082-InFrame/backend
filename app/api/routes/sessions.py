from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import init_services
from app.database import get_db
from app.models import AttendanceSession
from app.models.attendance_record import AttendanceRecord
from app.models.classes import Classes
from app.models.course import Course
from app.models.user import User
from app.schemas import AttendanceSessionCreate, AttendanceSessionResponse

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
    query = (
        db.query(AttendanceRecord, User.first_name, User.last_name, User.student_number)
        .join(User, User.id == AttendanceRecord.student_id)
        .filter(AttendanceRecord.session_id == session_id)
        .order_by(User.student_number.asc())
         )

    results = query.all()

    response = [
        {
            **session.__dict__,
            "first_name": first_name,
            "last_name": last_name,
            "student_number": student_number
        }
        for session, first_name, last_name, student_number in results
    ]
    return response
