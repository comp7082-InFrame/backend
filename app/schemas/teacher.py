from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class TeacherBase(BaseModel):
    employee_number: Optional[str]
    first_name: str
    last_name: str
    email: str
    department: Optional[str] = None
    title: Optional[str] = None
    active: Optional[bool] = True


class TeacherCreate(TeacherBase):
    pass


class TeacherResponse(TeacherBase):
    user_id: UUID

    class Config:
        from_attributes = True