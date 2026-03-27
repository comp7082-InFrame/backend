import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import cv2
import numpy as np

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.encoding import encoding_to_bytes
from app.api.deps import add_user_to_services, remove_user_from_services, get_face_service
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=UserResponse)
async def register_face(
    user_id: uuid.UUID = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Register or update face encoding for an existing user.
    Accepts a user_id and photo, extracts face embedding,
    and stores it in users.photo_encoding.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

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

    # Delete old photo file if it exists
    if user.photo_path and os.path.exists(user.photo_path):
        os.remove(user.photo_path)

    # Save new photo to disk
    photo_filename = f"{uuid.uuid4()}.jpg"
    photo_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, photo_filename))
    cv2.imwrite(photo_path, image)

    user.photo_path = photo_path
    user.photo_encoding = encoding_to_bytes(encoding)
    db.commit()
    db.refresh(user)

    add_user_to_services(user.id, f"{user.first_name} {user.last_name}".strip(), encoding)

    return user


@router.delete("/{user_id}")
async def remove_face(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Clear face encoding and photo for a user (removes them from face recognition)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.photo_path and os.path.exists(user.photo_path):
        os.remove(user.photo_path)

    user.photo_path = None
    user.photo_encoding = None
    db.commit()

    remove_user_from_services(user_id)

    return {"message": "Face registration removed successfully"}


@router.put("/{user_id}", response_model=UserResponse)
async def update_face(
    user_id: uuid.UUID,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Update face encoding and photo for an existing user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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

    if user.photo_path and os.path.exists(user.photo_path):
        os.remove(user.photo_path)

    photo_filename = f"{uuid.uuid4()}.jpg"
    photo_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, photo_filename))
    cv2.imwrite(photo_path, image)

    user.photo_path = photo_path
    user.photo_encoding = encoding_to_bytes(encoding)
    db.commit()
    db.refresh(user)

    add_user_to_services(user.id, f"{user.first_name} {user.last_name}".strip(), encoding)

    return user
