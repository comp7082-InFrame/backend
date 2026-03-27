import uuid
from sqlalchemy import Column, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AttendanceSession(Base):
    __tablename__ = "attendance_session"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("class.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("room.id", ondelete="CASCADE"), nullable=False)

    records = relationship("AttendanceRecord", back_populates="session")
    recognition = relationship("RecognitionHistory", back_populates="session")
