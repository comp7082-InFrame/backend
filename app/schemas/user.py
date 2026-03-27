from pydantic import BaseModel
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

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[List[str]] = None
    photo_path: Optional[str] = None



class ClassUserResponse(BaseModel):
    class_id: UUID
    person_id: int
    user_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class AdminEnrollmentResponse(BaseModel):
    user_id: UUID
    student_number: str
    name: str
    photo_path: Optional[str] = None
    enrolled: bool = True
