from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False)  # e.g., 'admin', 'teacher', 'staff'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    classes = relationship("Class", back_populates="teacher")
    attendance_sessions = relationship("AttendanceSession", back_populates="created_by_user")
