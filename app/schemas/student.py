from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class StudentBase(BaseModel):
    student_number: str
    first_name: str
    last_name: str
    email: str
    major: Optional[str] = None
    active: Optional[bool] = True


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    user_id: UUID
    student_number: str

    class Config:
        from_attributes = True