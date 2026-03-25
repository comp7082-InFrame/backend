from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class PersonResponse(BaseModel):
    id: int
    user_id: Optional[UUID] = None
    name: str
    photo_path: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PersonListResponse(BaseModel):
    persons: List[PersonResponse]
    total: int
