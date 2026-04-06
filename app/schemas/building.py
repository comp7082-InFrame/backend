from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
