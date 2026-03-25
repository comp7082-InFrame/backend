from typing import Optional
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.campus import Campus
from app.schemas import CampusResponse

router = APIRouter()

@router.get("/", response_model=list[CampusResponse])
def get_campuses(campus_id: Optional[uuid.UUID] = None,db: Session = Depends(get_db)):
    query = db.query(Campus)
    if campus_id:
        query = query.filter(
            Campus.id == campus_id
        )
    return query.all()