from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional


class RoomBase(BaseModel):
    building_id: UUID
    name: str
    capacity: Optional[int] = None
    status: Optional[bool] = True
    description: Optional[str] = None
    camera_connection: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[bool] = None
    description: Optional[str] = None
    camera_connection: Optional[str] = None


class RoomResponse(RoomBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
