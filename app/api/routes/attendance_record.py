import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.attendance_session import AttendanceSession
from app.models.building import Building
from app.models.classes import Classes
from app.models.course import Course
from app.schemas import BuildingResponse

router = APIRouter()


@router.get("/teacher/", response_model=List[BuildingResponse])
def get_attendance_sessions(
    teacher_id: uuid.UUID, 
    course_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    query = (db.query(AttendanceSession)
             .join(Classes, Classes.id == AttendanceSession.class_id)
             .join(Course, Course.id == Classes.course_id)
             .filter(AttendanceSession.teacher_id == teacher_id,
                     Course.id == course_id).all()
            )

    return query