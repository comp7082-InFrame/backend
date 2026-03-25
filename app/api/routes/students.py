from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.student import Student
from app.models.term import Term
from app.schemas.student import StudentResponse
from app.schemas.term import TermResponse

router = APIRouter()

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.user_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/", response_model=List[TermResponse])
def get_students(
    db: Session = Depends(get_db)
):
    student = db.query(Student).all()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
