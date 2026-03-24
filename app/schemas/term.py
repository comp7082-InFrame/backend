from pydantic import BaseModel
from datetime import date

from uuid import UUID


class TermBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    active: bool = True


class TermCreate(TermBase):
    pass


class TermResponse(TermBase):
    id: UUID

    class Config:
        from_attributes = True