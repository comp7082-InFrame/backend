
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, UniqueConstraint, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class StudentCourse(Base):
    __tablename__ = "student_course"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    enrollment_date = Column(TIMESTAMP, server_default=func.now())
    status = Column(Text, default="active")

    student = relationship("Student", back_populates="courses")
