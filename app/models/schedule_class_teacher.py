import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP, Column, ForeignKey, UniqueConstraint, Text, func
from app.database import Base


class TeacherScheduledClass(Base):
    __tablename__ = "scheduled_class_teacher"
    __table_args__ = (UniqueConstraint("teacher_id", "class_id", name="uq_teacher_class"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("class.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    role = Column(Text, default="lecturer")
