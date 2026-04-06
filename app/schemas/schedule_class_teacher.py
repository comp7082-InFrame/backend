from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TeacherScheduledClassBase(BaseModel):
    teacher_id: UUID
    class_id: UUID
    role: str


class TeacherScheduledClassCreate(TeacherScheduledClassBase):
    pass


class TeacherScheduledClassResponse(TeacherScheduledClassBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
