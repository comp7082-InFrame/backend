from datetime import datetime
import uuid
from sqlalchemy import Column, Boolean, ForeignKey, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Classes(Base):
    __tablename__ = "class"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("room.id", ondelete="CASCADE"))
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    status = Column(Boolean, default=True)


class TeacherClass(Base):
    """Read-only view: teacher's scheduled classes with full location info."""
    __tablename__ = "teacher_class_schedule_view"

    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    course_name: Mapped[str] = mapped_column(Text)

    start_time: Mapped[datetime] = mapped_column(TIMESTAMP)
    end_time: Mapped[datetime] = mapped_column(TIMESTAMP)

    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    room_name: Mapped[str] = mapped_column(Text)

    building_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    building_name: Mapped[str] = mapped_column(Text)

    campus_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    campus_name: Mapped[str] = mapped_column(Text)

    teacher_name: Mapped[str] = mapped_column(Text)
    status: Mapped[bool] = mapped_column(Boolean)


class StudentSchedule(Base):
    """Read-only view: student's full class schedule with location info."""
    __tablename__ = "student_schedule"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    student_number: Mapped[str] = mapped_column(Text)
    student_first_name: Mapped[str] = mapped_column(Text)
    student_last_name: Mapped[str] = mapped_column(Text)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    course_name: Mapped[str] = mapped_column(Text)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    term_name: Mapped[str] = mapped_column(Text)
    term_start_date: Mapped[datetime] = mapped_column(TIMESTAMP)
    term_end_date: Mapped[datetime] = mapped_column(TIMESTAMP)
    class_start_time: Mapped[datetime] = mapped_column(TIMESTAMP)
    class_end_time: Mapped[datetime] = mapped_column(TIMESTAMP)
    class_status: Mapped[bool] = mapped_column(Boolean)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    room_name: Mapped[str] = mapped_column(Text)
    building_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    building_name: Mapped[str] = mapped_column(Text)
    campus_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    campus_name: Mapped[str] = mapped_column(Text)
