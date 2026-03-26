from sqlalchemy import Column, Double, Integer, Boolean, ForeignKey, TIMESTAMP, Float, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class RecognitionHistory(Base):
    __tablename__ = "recognition_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    confidence = Column(Double)
    attendance_session_id = Column(Integer, ForeignKey("attendance_session.id", ondelete="CASCADE"), nullable=False)
    recognized = Column(Boolean, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    note = Column(Text)

    session = relationship("AttendanceSession", back_populates="recognition")
