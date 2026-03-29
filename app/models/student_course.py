import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP, Column, ForeignKey, UniqueConstraint, Text, func
from app.database import Base


class StudentCourse(Base):
    __tablename__ = "student_course"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    enrollment_date = Column(TIMESTAMP, server_default=func.now())
    status = Column(Text, default="active")
