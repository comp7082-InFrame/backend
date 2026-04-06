import uuid

from sqlalchemy import Boolean, Column, Double, ForeignKey, TIMESTAMP, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RecognitionHistory(Base):
    __tablename__ = "recognition_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    confidence = Column(Double)
    attendance_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attendance_session.id", ondelete="CASCADE"),
        nullable=False,
    )
    recognized = Column(Boolean, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    note = Column(Text)

    session = relationship("AttendanceSession", back_populates="recognition")
