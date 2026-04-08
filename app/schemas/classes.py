from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional


class ClassBase(BaseModel):
    course_name: str
    course_id: UUID
    room_id: Optional[UUID] = None
    room_name: Optional[str] = None
    building_id: Optional[UUID] = None
    building_name: Optional[str] = None
    campus_id: Optional[UUID] = None
    campus_name: Optional[str] = None
    teacher_id: Optional[UUID] = None
    teacher_name: Optional[str] = None
    status: Optional[bool] = True
    start_time: datetime
    end_time: datetime


class TeacherClassViewResponse(BaseModel):
    class_id: UUID
    course_id: UUID
    course_name: str
    start_time: datetime
    end_time: datetime
    room_id: UUID
    room_name: str
    building_id: UUID
    building_name: str
    campus_id: UUID
    campus_name: str
    teacher_id: Optional[UUID] = None
    teacher_name: Optional[str] = None
    status: bool

    model_config = ConfigDict(from_attributes=True)


class ClassResponse(ClassBase):
    class_id: UUID

    model_config = ConfigDict(from_attributes=True)


class StudentScheduleBase(BaseModel):
    student_id: UUID
    student_number: Optional[str] = None
    student_first_name: Optional[str] = None
    student_last_name: Optional[str] = None
    course_id: UUID
    course_name: Optional[str] = None
    term_id: UUID
    term_name: Optional[str] = None
    term_start_date: Optional[datetime] = None
    term_end_date: Optional[datetime] = None
    class_id: UUID
    class_start_time: Optional[datetime] = None
    class_end_time: Optional[datetime] = None
    class_status: Optional[bool] = None
    room_id: UUID
    room_name: Optional[str] = None
    building_id: UUID
    building_name: Optional[str] = None
    campus_id: UUID
    campus_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StudentScheduleResponse(StudentScheduleBase):
    pass
