from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import add_user_to_services
from app.database import get_db
from app.models.user import User
from app.schemas.user import AdminTeacherResponse
from app.services.user_photo_service import apply_prepared_user_photo, prepare_user_photo

router = APIRouter()


def build_admin_teacher_response(teacher: User) -> AdminTeacherResponse:
    return AdminTeacherResponse(
        id=teacher.id,
        first_name=teacher.first_name,
        last_name=teacher.last_name,
        email=teacher.email,
        employee_number=teacher.employee_number,
        department=teacher.department,
        title=teacher.title,
        face_registered=teacher.photo_encoding is not None,
        photo_path=teacher.photo_path,
        active=bool(teacher.active),
    )


@router.get("/", response_model=List[AdminTeacherResponse])
def get_teachers(db: Session = Depends(get_db)):
    teachers = (
        db.query(User)
        .filter(User.role.contains(["teacher"]))
        .order_by(User.last_name.asc(), User.first_name.asc())
        .all()
    )
    return [build_admin_teacher_response(teacher) for teacher in teachers]


@router.post("/", response_model=AdminTeacherResponse)
async def create_teacher(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    employee_number: str = Form(...),
    department: str = Form(...),
    title: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    existing_teacher = (
        db.query(User)
        .filter((User.email == email) | (User.employee_number == employee_number))
        .first()
    )
    if existing_teacher:
        raise HTTPException(status_code=400, detail="Teacher email or employee number already exists")

    prepared_photo = await prepare_user_photo(photo)

    teacher = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=["teacher"],
        employee_number=employee_number,
        department=department,
        title=title,
        active=True,
    )
    apply_prepared_user_photo(teacher, prepared_photo)
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    add_user_to_services(teacher.id, f"{teacher.first_name} {teacher.last_name}".strip(), prepared_photo.encoding)

    return build_admin_teacher_response(teacher)
