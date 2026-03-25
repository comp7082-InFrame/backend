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
    session_id: int


class AttendanceRecordResponse(AttendanceRecordBase):
    id: int

    class Config:
        from_attributes = True
