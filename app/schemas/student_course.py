from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class StudentCourseBase(BaseModel):
    student_id: UUID
    course_id: UUID
    status: Optional[str] = "active"


class StudentCourseCreate(StudentCourseBase):
    pass


class StudentCourseResponse(StudentCourseBase):
    id: int
    enrollment_date: datetime

    class Config:
        from_attributes = True
