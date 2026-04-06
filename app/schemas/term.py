from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
