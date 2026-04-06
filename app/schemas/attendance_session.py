from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.schemas.attendance_record import AttendanceRecordResponse


class AttendanceSessionBase(BaseModel):
    class_id: UUID
    teacher_id: UUID
    room_id: UUID
    start_time: datetime
    end_time: datetime


class AttendanceSessionCreate(AttendanceSessionBase):
    pass


class AttendanceSessionResponse(AttendanceSessionBase):
    id: UUID
    records: List[AttendanceRecordResponse] = []

    class Config:
        from_attributes = True


class AttendanceSessionListItem(AttendanceSessionBase):
    id: UUID
    course_name: str
    term_id: UUID


class SessionAttendanceRecordItem(BaseModel):
    id: str
    session_id: UUID
    student_id: UUID
    status: str
    face_recognized: bool
    timestamp: Optional[datetime] = None
    first_name: str
    last_name: str
    student_number: Optional[str] = None
