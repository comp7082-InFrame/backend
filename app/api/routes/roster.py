import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.models.user import ClassUsers

router = APIRouter()


class RosterEntry(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    class_id: uuid.UUID
    face_registered: bool

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[RosterEntry])
async def get_roster(
    class_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get all students in a class with their face registration status."""
    rows = (
        db.query(ClassUsers)
        .filter(ClassUsers.class_id == class_id, ClassUsers.role == "student")
        .all()
    )

    return [
        RosterEntry(
            id=row.id,
            first_name=row.first_name,
            last_name=row.last_name,
            email=row.email,
            class_id=row.class_id,
            face_registered=row.photo_encoding is not None,
        )
        for row in rows
    ]
