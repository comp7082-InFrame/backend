import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import cv2
import numpy as np

from app.database import get_db
from app.models import ClassUsers, Person, Student, User
from app.schemas import AdminEnrollmentResponse, PersonResponse
from app.utils.encoding import encoding_to_bytes
from app.api.deps import add_person_to_services, remove_person_from_services, get_face_service
from app.config import get_settings

router = APIRouter()
settings = get_settings()

DEFAULT_STUDENT_EMAIL_DOMAIN = "students.inframe.local"


def _decode_upload_image(contents: bytes) -> np.ndarray:
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    return image


def _extract_face_encoding(image: np.ndarray) -> np.ndarray:
    face_service = get_face_service()
    if face_service is None:
        raise HTTPException(status_code=503, detail="Face recognition service is not initialized")

    encoding = face_service.extract_face_encoding(image)
    if encoding is None:
        raise HTTPException(status_code=400, detail="No face detected in image")

    return encoding


def _save_photo(image: np.ndarray) -> str:
    photo_filename = f"{uuid.uuid4()}.jpg"
    photo_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, photo_filename))
    cv2.imwrite(photo_path, image)
    return photo_path


def _remove_file_if_present(path: str | None):
    if path and os.path.exists(path):
        os.remove(path)


def _build_student_email(student_number: str) -> str:
    return f"{student_number}@{DEFAULT_STUDENT_EMAIL_DOMAIN}"


def _upsert_person_record(
    db: Session,
    user: User,
    display_name: str,
    encoding: np.ndarray,
    photo_path: str,
) -> Person:
    person = db.query(Person).filter(Person.user_id == user.id).first()
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
        _remove_file_if_present(person.photo_path)
        person.name = display_name
        person.face_encoding = encoding_to_bytes(encoding)
        person.photo_path = photo_path
        person.is_active = True

    user.photo_path = photo_path
    return person


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
    contents = await photo.read()
    image = _decode_upload_image(contents)
    encoding = _extract_face_encoding(image)

    # Save photo to disk (absolute path prevents working-directory fragility)
    photo_path = _save_photo(image)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        _remove_file_if_present(photo_path)
        raise HTTPException(status_code=404, detail="User not found")

    display_name = f"{user.first_name} {user.last_name}".strip()

    person = _upsert_person_record(db, user, display_name, encoding, photo_path)

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


@router.post("/admin", response_model=AdminEnrollmentResponse)
async def admin_enroll_student(
    first_name: str = Form(...),
    last_name: str = Form(...),
    student_number: str = Form(...),
    date_of_birth: str | None = Form(default=None),
    photo: UploadFile = File(...),
    government_id_photo: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    """
    Create or update a student and enroll their face from the uploaded photo.

    The government ID upload is accepted for UI parity but intentionally ignored
    until a later verification workflow exists.
    """
    del date_of_birth
    del government_id_photo

    contents = await photo.read()
    image = _decode_upload_image(contents)
    encoding = _extract_face_encoding(image)
    photo_path = _save_photo(image)

    student_number = student_number.strip()
    first_name = first_name.strip()
    last_name = last_name.strip()

    if not first_name or not last_name or not student_number:
        _remove_file_if_present(photo_path)
        raise HTTPException(status_code=400, detail="First name, last name, and student ID are required")

    student = db.query(Student).filter(Student.student_number == student_number).first()

    if student is not None:
        user = db.query(User).filter(User.id == student.user_id).first()
        if user is None:
            _remove_file_if_present(photo_path)
            raise HTTPException(status_code=500, detail="Student exists without a linked user")
    else:
        email = _build_student_email(student_number)
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=["student"],
            )
            db.add(user)
            db.flush()

        student = Student(
            user_id=user.id,
            student_number=student_number,
            first_name=first_name,
            last_name=last_name,
            email=user.email,
            active=True,
        )
        db.add(student)

    user.first_name = first_name
    user.last_name = last_name
    user.role = sorted(set((user.role or []) + ["student"]))

    student.first_name = first_name
    student.last_name = last_name
    student.email = user.email
    student.active = True

    person = _upsert_person_record(
        db=db,
        user=user,
        display_name=f"{first_name} {last_name}".strip(),
        encoding=encoding,
        photo_path=photo_path,
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        _remove_file_if_present(photo_path)
        raise

    db.refresh(user)
    add_person_to_services(person.id, person.name, encoding)

    return AdminEnrollmentResponse(
        user_id=user.id,
        student_number=student.student_number,
        name=person.name,
        photo_path=person.photo_path,
        enrolled=True,
    )


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
        contents = await photo.read()
        image = _decode_upload_image(contents)
        encoding = _extract_face_encoding(image)

        # Delete old photo
        _remove_file_if_present(person.photo_path)

        # Save new photo (absolute path)
        photo_path = _save_photo(image)

        person.photo_path = photo_path
        person.face_encoding = encoding_to_bytes(encoding)

        # Update running services
        add_person_to_services(person.id, person.name, encoding)

    db.commit()
    db.refresh(person)

    return person
