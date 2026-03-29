import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.attendance_session import AttendanceSession
from app.models.classes import Classes
from app.models.course import Course
from app.schemas.attendance_session import AttendanceSessionResponse

router = APIRouter()


@router.get("/teacher/", response_model=List[AttendanceSessionResponse])
def get_attendance_sessions(
    teacher_id: uuid.UUID,
    course_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    query = (db.query(AttendanceSession)
             .join(Classes, Classes.id == AttendanceSession.class_id)
             .join(Course, Course.id == Classes.course_id)
             .filter(AttendanceSession.teacher_id == teacher_id)
            )

    if course_id:
        query = query.filter(Course.id == course_id)

    return query.all()