from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


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
