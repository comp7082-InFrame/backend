import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import cv2
import numpy as np

from app.database import get_db
from app.models import ClassUsers, Person, User
from app.schemas import PersonResponse
from app.utils.encoding import encoding_to_bytes
from app.api.deps import add_person_to_services, remove_person_from_services, get_face_service
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=PersonResponse)
async def enroll_person(
    user_id: uuid.UUID = Form(...),
    photo: UploadFile = File(...),
    class_id: uuid.UUID | None = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    Enroll or update face recognition for an existing user.

    - Accepts a user id and image file
    - Detects face in the image
    - Extracts face encoding
    - Creates or updates the linked Person record
    - Optionally links the person to a class
    """
    # Read image file
    contents = await photo.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Extract face encoding using the global singleton (avoids reloading ML models)
    face_service = get_face_service()
    if face_service is None:
        raise HTTPException(status_code=503, detail="Face recognition service is not initialized")

    encoding = face_service.extract_face_encoding(image)

    if encoding is None:
        raise HTTPException(status_code=400, detail="No face detected in image")

    # Save photo to disk (absolute path prevents working-directory fragility)
    photo_filename = f"{uuid.uuid4()}.jpg"
    photo_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, photo_filename))
    cv2.imwrite(photo_path, image)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        raise HTTPException(status_code=404, detail="User not found")

    display_name = f"{user.first_name} {user.last_name}".strip()

    person = db.query(Person).filter(Person.user_id == user_id).first()
    if person is None:
        person = Person(
            user_id=user.id,
            name=display_name,
            face_encoding=encoding_to_bytes(encoding),
            photo_path=photo_path,
            is_active=True,
        )
        db.add(person)
    else:
        if person.photo_path and os.path.exists(person.photo_path):
            os.remove(person.photo_path)
        person.name = display_name
        person.face_encoding = encoding_to_bytes(encoding)
        person.photo_path = photo_path
        person.is_active = True

    user.photo_path = photo_path

    db.commit()
    db.refresh(person)

    if class_id is not None:
        membership = (
            db.query(ClassUsers)
            .filter(
                ClassUsers.class_id == class_id,
                ClassUsers.person_id == person.id,
            )
            .first()
        )
        if membership is None:
            membership = ClassUsers(
                class_id=class_id,
                person_id=person.id,
                user_id=user.id,
            )
            db.add(membership)
        else:
            membership.user_id = user.id
        db.commit()

    # Add to running services
    add_person_to_services(person.id, person.name, encoding)

    return person


@router.delete("/{person_id}")
async def remove_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a person (soft delete — preserves attendance history)."""
    person = db.query(Person).filter(Person.id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Delete photo file if exists
    if person.photo_path and os.path.exists(person.photo_path):
        os.remove(person.photo_path)

    # Soft-delete: mark as inactive to preserve attendance history
    person.is_active = False
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

        face_service = get_face_service()
        if face_service is None:
            raise HTTPException(status_code=503, detail="Face recognition service is not initialized")

        encoding = face_service.extract_face_encoding(image)

        if encoding is None:
            raise HTTPException(status_code=400, detail="No face detected in image")

        # Delete old photo
        if person.photo_path and os.path.exists(person.photo_path):
            os.remove(person.photo_path)

        # Save new photo (absolute path)
        photo_filename = f"{uuid.uuid4()}.jpg"
        photo_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, photo_filename))
        cv2.imwrite(photo_path, image)

        person.photo_path = photo_path
        person.face_encoding = encoding_to_bytes(encoding)

        # Update running services
        add_person_to_services(person.id, person.name, encoding)

    db.commit()
    db.refresh(person)

    return person
