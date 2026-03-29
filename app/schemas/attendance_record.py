from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class AttendanceRecordBase(BaseModel):
    student_id: UUID
    status: Optional[str] = "absent"
    face_recognized: Optional[bool] = False
    timestamp: datetime


class AttendanceRecordCreate(AttendanceRecordBase):
    session_id: UUID


class AttendanceRecordResponse(AttendanceRecordBase):
    id: UUID

    class Config:
        from_attributes = True
