import uuid
import os

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import add_user_to_services, get_face_service, get_presence_tracker
from app.config import get_settings
from app.database import get_db
from app.models.course import Course
from app.models.student_course import StudentCourse
from app.models.user import User
from app.schemas.user import AdminStudentResponse, UserResponse
from app.utils.admin_students import is_currently_seen, parse_course_ids
from app.utils.encoding import encoding_to_bytes

router = APIRouter()
settings = get_settings()


def build_admin_student_response(student: User, course_ids: list[uuid.UUID]) -> AdminStudentResponse:
    tracker = get_presence_tracker()
    current_status = tracker.get_status_for_display(student.id) if tracker is not None else None

    return AdminStudentResponse(
        id=student.id,
        student_number=student.student_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        course_ids=course_ids,
        current_seen=is_currently_seen(current_status),
        face_registered=student.photo_encoding is not None,
        photo_path=student.photo_path,
        active=bool(student.active),
    )


@router.get("/{student_id}", response_model=UserResponse)
def get_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = db.query(User).filter(User.id == student_id, User.role.contains(["student"])).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/", response_model=List[AdminStudentResponse])
def get_students(db: Session = Depends(get_db)):
    students = (
        db.query(User)
        .filter(User.role.contains(["student"]))
        .order_by(User.last_name.asc(), User.first_name.asc())
        .all()
    )

    student_ids = [student.id for student in students]
    course_map: dict[uuid.UUID, list[uuid.UUID]] = {student.id: [] for student in students}

    if student_ids:
        enrollments = (
            db.query(StudentCourse.student_id, StudentCourse.course_id)
            .filter(StudentCourse.student_id.in_(student_ids), StudentCourse.status == "active")
            .all()
        )
        for student_id, course_id in enrollments:
            course_map.setdefault(student_id, []).append(course_id)

    return [build_admin_student_response(student, course_map.get(student.id, [])) for student in students]


@router.post("/", response_model=AdminStudentResponse)
async def create_student(
    student_number: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    course_ids: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        parsed_course_ids = parse_course_ids(course_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not parsed_course_ids:
        raise HTTPException(status_code=400, detail="At least one class must be assigned")

    existing_student = (
        db.query(User)
        .filter((User.email == email) | (User.student_number == student_number))
        .first()
    )
    if existing_student:
        raise HTTPException(status_code=400, detail="Student email or number already exists")

    existing_courses = (
        db.query(Course.id)
        .filter(Course.id.in_(parsed_course_ids), Course.active == True)
        .all()
    )
    valid_course_ids = {row.id for row in existing_courses}
    if len(valid_course_ids) != len(parsed_course_ids):
        raise HTTPException(status_code=400, detail="One or more selected classes are invalid")

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

    student = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=["student"],
        photo_path=photo_path,
        photo_encoding=encoding_to_bytes(encoding),
        student_number=student_number,
        active=True,
    )
    db.add(student)
    db.flush()

    for course_id in parsed_course_ids:
        db.add(
            StudentCourse(
                student_id=student.id,
                course_id=course_id,
                status="active",
            )
        )

    db.commit()
    db.refresh(student)

    add_user_to_services(student.id, f"{student.first_name} {student.last_name}".strip(), encoding)

    return build_admin_student_response(student, parsed_course_ids)
