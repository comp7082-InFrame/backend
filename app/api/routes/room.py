import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.campus import Campus
from app.models.room import Room
from app.models.building import Building
from app.schemas import RoomResponse

router = APIRouter()


@router.get("/", response_model=List[RoomResponse])
def get_rooms(
    campus_id: Optional[uuid.UUID] = None,
    building_id: Optional[uuid.UUID] = None,
    room_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    query = (db.query(Room)
        .join(Building, Room.building_id == Building.id)
        .join(Campus, Campus.id == Building.campus_id)
    )

    if campus_id:
        query = query.filter(
            Campus.id == campus_id
        )
    if building_id:
        query = query.filter(
            Building.id == building_id
        )
    
    if room_id:
        query = query.filter(
            Room.id == room_id
        )
        
    return query.all()