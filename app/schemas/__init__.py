from app.schemas.person import PersonResponse, PersonListResponse
from app.schemas.attendance import (
    AttendanceEventResponse,
    CurrentPresenceResponse,
    AttendanceCurrentResponse,
    FaceDetection,
    StreamFrame,
    AttendanceUpdate,
)
from app.schemas.attendance_record import AttendanceRecordCreate, AttendanceRecordResponse
from app.schemas.attendance_session import AttendanceSessionCreate, AttendanceSessionResponse
from app.schemas.building import BuildingCreate, BuildingResponse, BuildingUpdate
from app.schemas.campus import CampusCreate, CampusResponse, CampusUpdate
from app.schemas.classes import ClassResponse, StudentScheduleResponse, TeacherClassViewResponse
from app.schemas.course import CourseCreate, CourseResponse
from app.schemas.regconition_history import RecognitionHistoryCreate, RecognitionHistoryResponse
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.schemas.schedule_class_teacher import TeacherScheduledClassCreate, TeacherScheduledClassResponse
from app.schemas.student import StudentCreate, StudentResponse
from app.schemas.student_course import StudentCourseCreate, StudentCourseResponse
from app.schemas.teacher import TeacherCreate, TeacherResponse
from app.schemas.term import TermCreate, TermResponse
from app.schemas.user import ClassUserResponse, UserCreate, UserResponse

__all__ = [
    "PersonResponse",
    "PersonListResponse",
    "AttendanceEventResponse",
    "CurrentPresenceResponse",
    "AttendanceCurrentResponse",
    "FaceDetection",
    "StreamFrame",
    "AttendanceUpdate",
    "AttendanceRecordCreate",
    "AttendanceRecordResponse",
    "AttendanceSessionCreate",
    "AttendanceSessionResponse",
    "BuildingCreate",
    "BuildingResponse",
    "BuildingUpdate",
    "CampusCreate",
    "CampusResponse",
    "CampusUpdate",
    "ClassResponse",
    "StudentScheduleResponse",
    "TeacherClassViewResponse",
    "CourseCreate",
    "CourseResponse",
    "RecognitionHistoryCreate",
    "RecognitionHistoryResponse",
    "RoomCreate",
    "RoomResponse",
    "RoomUpdate",
    "TeacherScheduledClassCreate",
    "TeacherScheduledClassResponse",
    "StudentCreate",
    "StudentResponse",
    "StudentCourseCreate",
    "StudentCourseResponse",
    "TeacherCreate",
    "TeacherResponse",
    "TermCreate",
    "TermResponse",
    "ClassUserResponse",
    "UserCreate",
    "UserResponse",
]
