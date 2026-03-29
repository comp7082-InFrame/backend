from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    role: Optional[List[str]] = []


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: UUID
    photo_path: Optional[str] = None
    student_number: Optional[str] = None
    major: Optional[str] = None
    employee_number: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    active: Optional[bool] = True

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[List[str]] = None
    photo_path: Optional[str] = None
    student_number: Optional[str] = None
    major: Optional[str] = None
    employee_number: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    active: Optional[bool] = None


class ClassUserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    role: str
    class_id: UUID
    photo_path: Optional[str] = None

    class Config:
        from_attributes = True


class AdminStudentResponse(BaseModel):
    id: UUID
    student_number: Optional[str] = None
    first_name: str
    last_name: str
    email: str
    course_ids: List[UUID] = Field(default_factory=list)
    current_seen: bool = False
    face_registered: bool = False
    photo_path: Optional[str] = None
    active: bool = True

    class Config:
        from_attributes = True
