from datetime import datetime
from pyclbr import Class
from typing import Optional
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.classes import StudentSchedule, TeacherClass, Classes
from app.models.schedule_class_teacher import TeacherScheduledClass
from app.models.course import Course
from app.models.student_course import StudentCourse
from app.models.term import Term
from app.schemas.classes import StudentScheduleResponse, TeacherClassViewResponse

router = APIRouter()

@router.get("/teacher_classes/", response_model=list[TeacherClassViewResponse])
def get_classes_by_teacher(teacher_id: uuid.UUID, start_date: datetime, end_date: datetime, course_id: Optional[uuid.UUID]=None, db: Session = Depends(get_db)):
    query = db.query(TeacherClass).filter(
        TeacherClass.teacher_id == teacher_id,
        TeacherClass.start_time <= end_date,
        TeacherClass.end_time >= start_date
    )
    if course_id:
        query = query.filter(TeacherClass.course_id == course_id)

    return query.all()

@router.get("/student_classes/", response_model=list[StudentScheduleResponse])
def get_classes_by_student(student_id: uuid.UUID, start_date: datetime, end_date: datetime, db: Session = Depends(get_db)):
    classes = db.query(StudentSchedule).filter(
        StudentSchedule.student_id == student_id,
        StudentSchedule.class_start_time >= start_date,
        StudentSchedule.class_end_time <= end_date
    ).all()
    return classes


@router.get('/teacher/term_course/')
def get_term_course_by_teacher(
    teacher_id: uuid.UUID, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)): 

    query = (
        db.query(Term.id.label("term_id"), Term.name.label("term_name"), Course.name.label("course_name"), Course.id.label("course_id"), Term.start_date, Term.end_date)
        .join(Course, Course.term_id == Term.id)
        .join(Classes, Classes.course_id == Course.id)
        .join(TeacherScheduledClass, TeacherScheduledClass.class_id == Classes.id)
        .filter(TeacherScheduledClass.teacher_id == teacher_id)
        .distinct()
        .order_by(Term.start_date, Course.name)
    )

    if start_date:
        query = query.filter(Term.start_date >= start_date)
    
    if end_date:
        query = query.filter(Term.end_date <= end_date)

    results = query.all()
    return [dict(row._mapping) for row in results]



@router.get('/student/term_course/')
def get_term_course_by_student(
    student_id: uuid.UUID, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)): 

    query = (
        db.query(Term.id.label("term_id"), Term.name.label("term_name"), Course.name.label("course_name"), Course.id.label("course_id"), Term.start_date, Term.end_date)
        .join(Course, Course.term_id == Term.id)
        .join(StudentCourse, StudentCourse.course_id == Course.id)
        .filter(StudentCourse.student_id == student_id)
        .distinct()
        .order_by(Term.start_date, Course.name)
    )

    if start_date:
        query = query.filter(Term.start_date >= start_date)
    
    if end_date:
        query = query.filter(Term.end_date <= end_date)
    

    results = query.all()
    return [dict(row._mapping) for row in results]