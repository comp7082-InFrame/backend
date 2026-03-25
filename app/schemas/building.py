from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class BuildingBase(BaseModel):
    campus_id: UUID
    name: str
    description: Optional[str] = None


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class BuildingResponse(BuildingBase):
    id: UUID

    class Config:
        from_attributes = True