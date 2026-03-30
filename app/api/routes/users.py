from http.client import HTTPException
import json
import os
import shutil
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


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
    photo: Optional[UploadFile] = File(None),
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
        upload_dir = "uploads/photos"
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = os.path.splitext(photo.filename)[1]
        filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        update_data["photo_path"] = file_path

    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user