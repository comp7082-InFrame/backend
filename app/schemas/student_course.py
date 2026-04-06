from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class StudentCourseBase(BaseModel):
    student_id: UUID
    course_id: UUID
    status: Optional[str] = "active"


class StudentCourseCreate(StudentCourseBase):
    pass


class StudentCourseResponse(StudentCourseBase):
    id: UUID
    enrollment_date: datetime

    model_config = ConfigDict(from_attributes=True)
