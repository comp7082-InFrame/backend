from sqlalchemy import Column, Integer, String, LargeBinary, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    id_num = Column(String(50), unique=True, nullable=False, index=True)
    face_encoding = Column(LargeBinary, nullable=False)
    photo_path = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    attendance_events = relationship("AttendanceEvent", back_populates="person")
    current_presence = relationship("CurrentPresence", back_populates="person", uselist=False)
    enrollments = relationship("Enrollment", back_populates="person")
    attendance_records = relationship("PersonAttendanceRecord", back_populates="person")
