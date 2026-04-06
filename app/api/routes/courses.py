import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.classes import TeacherClass
from app.models.course import Course
from app.schemas.course import CourseResponse

router = APIRouter()


@router.get("/", response_model=List[CourseResponse])
def get_courses(
    term_id: uuid.UUID,
    course_id: Optional[uuid.UUID]=None,
    teacher_id: Optional[uuid.UUID]=None,
    db: Session = Depends(get_db)
):
    query = db.query(Course).filter(Course.term_id == term_id)
    if course_id:
        query = query.filter(Course.id == course_id)
    
    if teacher_id:
        query = (
            query.join(TeacherClass, TeacherClass.course_id == Course.id)
            .filter(TeacherClass.teacher_id == teacher_id)
            .distinct()
        )
    
    return query.all()
