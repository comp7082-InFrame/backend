from http.client import HTTPException
import json
import os
import shutil
from uuid import UUID
import uuid

from app.api.deps import get_face_service
import cv2
import numpy as np

from app.config import get_settings
from app.utils.encoding import encoding_to_bytes
from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()
settings = get_settings()


"""
 Get all users, optionally filtered by role.
"""
@router.get("/", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all active users, optionally filtered by role.

    Args:
        role: Optional role filter (e.g. 'student', 'teacher', 'admin')

    Returns:
        List of users with id, name, email, and roles
    """
    query = db.query(User).filter(User.active == True)

    if role:
        query = query.filter(User.role.contains([role]))

    users = query.order_by(User.last_name.asc(), User.first_name.asc()).all()

    return users


@router.get("/{user_id}/", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a user by ID.

    Args:
        user_id: The ID of the user to retrieve
        db: The database session

    Returns:
        The user with the specified ID
    """
    return db.query(User).filter(User.id == user_id).first()


@router.post("/{user_uuid}/", response_model=UserResponse)
async def update_user(
    user_uuid: str,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    role: Optional[str] = Form(None),  # JSON stringified array
    student_number: Optional[str] = Form(None),
    major: Optional[str] = Form(None),
    employee_number: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    active: Optional[bool] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Get existing user
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build update dictionary, only include non-None values
    update_data = {}
    for field_name, value in [
        ("first_name", first_name),
        ("last_name", last_name),
        ("email", email),
        ("student_number", student_number),
        ("major", major),
        ("employee_number", employee_number),
        ("department", department),
        ("title", title),
        ("active", active),
    ]:
        if value is not None:
            update_data[field_name] = value

    # Parse role if provided
    if role:
        try:
            parsed_role = json.loads(role)  
            if not isinstance(parsed_role, list):
                parsed_role = [parsed_role] 
        except json.JSONDecodeError:
            parsed_role = [role]  
        update_data["role"] = parsed_role

    # Handle photo upload
    if photo:
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

        photo_filename = f"{uuid.uuid4()}.jpg"
        photo_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, photo_filename))
        cv2.imwrite(photo_path, image)
        update_data["photo_path"] = photo_path
        update_data["photo_encoding"] = encoding_to_bytes(encoding)

    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user