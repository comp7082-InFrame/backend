import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/{student_id}", response_model=UserResponse)
def get_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = db.query(User).filter(User.id == student_id, User.role.contains(["student"])).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/", response_model=List[UserResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role.contains(["student"])).all()
