import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import ClassUsers, Person
from app.schemas import PersonResponse, PersonListResponse

router = APIRouter()


@router.get("/", response_model=PersonListResponse)
async def get_roster(class_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    """Get all enrolled people, optionally filtered by class."""
    query = db.query(Person).filter(Person.is_active == True)
    if class_id is not None:
        query = (
            query.join(ClassUsers, ClassUsers.person_id == Person.id)
            .filter(ClassUsers.class_id == class_id)
        )
    persons = query.all()
    return PersonListResponse(
        persons=[PersonResponse.model_validate(p) for p in persons],
        total=len(persons)
    )


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(person_id: int, db: Session = Depends(get_db)):
    """Get a specific person by ID."""
    person = db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    return person


@router.get("/{person_id}/photo")
async def get_person_photo(person_id: int, db: Session = Depends(get_db)):
    """Get a person's enrolled photo."""
    person = db.query(Person).filter(Person.id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if not person.photo_path or not os.path.exists(person.photo_path):
        raise HTTPException(status_code=404, detail="Photo not found")

    return FileResponse(person.photo_path, media_type="image/jpeg")
