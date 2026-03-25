from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class CampusBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    description: Optional[str] = None


class CampusCreate(CampusBase):
    pass


class CampusUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    description: Optional[str] = None


class CampusResponse(CampusBase):
    id: UUID

    class Config:
        from_attributes = True