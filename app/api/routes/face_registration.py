import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.api.deps import add_user_to_services, remove_user_from_services
from app.services.user_photo_service import apply_prepared_user_photo, prepare_user_photo

router = APIRouter()


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

    prepared_photo = await prepare_user_photo(photo, existing_photo_path=user.photo_path)
    apply_prepared_user_photo(user, prepared_photo)
    db.commit()
    db.refresh(user)

    add_user_to_services(user.id, f"{user.first_name} {user.last_name}".strip(), prepared_photo.encoding)

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

    prepared_photo = await prepare_user_photo(photo, existing_photo_path=user.photo_path)
    apply_prepared_user_photo(user, prepared_photo)
    db.commit()
    db.refresh(user)

    add_user_to_services(user.id, f"{user.first_name} {user.last_name}".strip(), prepared_photo.encoding)

    return user
