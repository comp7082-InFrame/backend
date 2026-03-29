from typing import List
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
