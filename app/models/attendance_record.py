from sqlalchemy import Column, Integer, Boolean, ForeignKey, TIMESTAMP, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class AttendanceRecord(Base):
    __tablename__ = "attendance_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("attendance_session.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(127), default="absent")
    face_recognized = Column(Boolean, default=False)
    timestamp = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    session = relationship("AttendanceSession", back_populates="records")

