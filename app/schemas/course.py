from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
