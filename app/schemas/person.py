from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PersonCreate(BaseModel):
    name: str


class PersonResponse(BaseModel):
    id: int
    name: str
    photo_path: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PersonListResponse(BaseModel):
    persons: List[PersonResponse]
    total: int
