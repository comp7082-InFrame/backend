import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import cv2
import numpy as np

from app.database import get_db
from app.models import Person
from app.schemas import PersonResponse
from app.services import FaceService
from app.utils.encoding import encoding_to_bytes
from app.api.deps import add_person_to_services, remove_person_from_services
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=PersonResponse)
async def enroll_person(
    name: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Enroll a new person with their photo.

    - Accepts an image file and person's name
    - Detects face in the image
    - Extracts face encoding
    - Stores in database
    """
    # Read image file
    contents = await photo.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Extract face encoding
    face_service = FaceService()
    encoding = face_service.extract_face_encoding(image)

    if encoding is None:
        raise HTTPException(status_code=400, detail="No face detected in image")

    # Save photo to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    photo_filename = f"{uuid.uuid4()}.jpg"
    photo_path = os.path.join(settings.UPLOAD_DIR, photo_filename)
    cv2.imwrite(photo_path, image)

    # Create person record
    person = Person(
        name=name,
        face_encoding=encoding_to_bytes(encoding),
        photo_path=photo_path
    )
    db.add(person)
    db.commit()
    db.refresh(person)

    # Add to running services
    add_person_to_services(person.id, person.name, encoding)

    return person


@router.delete("/{person_id}")
async def remove_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    """Remove a person from the system."""
    person = db.query(Person).filter(Person.id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Delete photo file if exists
    if person.photo_path and os.path.exists(person.photo_path):
        os.remove(person.photo_path)

    # Remove from database
    db.delete(person)
    db.commit()

    # Remove from running services
    remove_person_from_services(person_id)

    return {"message": "Person removed successfully"}


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: int,
    name: str = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Update a person's name or photo."""
    person = db.query(Person).filter(Person.id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if name:
        person.name = name

    if photo:
        # Read and process new photo
        contents = await photo.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        face_service = FaceService()
        encoding = face_service.extract_face_encoding(image)

        if encoding is None:
            raise HTTPException(status_code=400, detail="No face detected in image")

        # Delete old photo
        if person.photo_path and os.path.exists(person.photo_path):
            os.remove(person.photo_path)

        # Save new photo
        photo_filename = f"{uuid.uuid4()}.jpg"
        photo_path = os.path.join(settings.UPLOAD_DIR, photo_filename)
        cv2.imwrite(photo_path, image)

        person.photo_path = photo_path
        person.face_encoding = encoding_to_bytes(encoding)

        # Update running services
        add_person_to_services(person.id, person.name, encoding)

    db.commit()
    db.refresh(person)

    return person
