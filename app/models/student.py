from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Student(Base):
    __tablename__ = "student"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    student_number = Column(String(12), unique=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String, unique=True, nullable=False)
    major = Column(String)
    active = Column(Boolean, default=True)

    courses = relationship("StudentCourse", back_populates="student")