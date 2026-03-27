from fastapi import APIRouter
from app.api.routes import (
    attendance,
    attendance_record,
    buidling,
    campus,
    classes,
    courses,
    face_registration,
    room,
    roster,
    sessions,
    students,
    term,
)

api_router = APIRouter()

api_router.include_router(face_registration.router, prefix="/face-registration", tags=["face-registration"])
api_router.include_router(roster.router, prefix="/roster", tags=["roster"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(campus.router, prefix="/campuses", tags=["campuses"])
api_router.include_router(buidling.router, prefix="/buildings", tags=["buildings"])
api_router.include_router(room.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(term.router, prefix="/terms", tags=["terms"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(attendance_record.router, prefix="/attendances", tags=["attendances"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
