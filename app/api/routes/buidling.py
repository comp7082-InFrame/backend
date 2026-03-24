import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.building import Building
from app.schemas import BuildingResponse

router = APIRouter()


@router.get("/", response_model=List[BuildingResponse])
def get_buildings(
    campus_id: Optional[uuid.UUID]=None, 
    building_id: Optional[uuid.UUID] =None,
    db: Session = Depends(get_db)
):
    query = db.query(Building)
    if campus_id:
        query = query.filter(
            Building.campus_id == campus_id,
        )
    if building_id:
        query = query.filter(
            Building.id == building_id,
        )

    return query.all()