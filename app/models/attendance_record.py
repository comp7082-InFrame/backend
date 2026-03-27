import uuid
from sqlalchemy import Column, Boolean, ForeignKey, TIMESTAMP, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_record"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("attendance_session.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(127), default="absent")
    face_recognized = Column(Boolean, default=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    session = relationship("AttendanceSession", back_populates="records")
