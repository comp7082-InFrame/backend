from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class CourseBase(BaseModel):
    term_id: UUID
    name: str
    description: Optional[str] = None
    active: bool = True


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: UUID

    class Config:
        from_attributes = True
