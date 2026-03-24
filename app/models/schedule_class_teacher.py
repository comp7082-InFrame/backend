
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from app.models.teacher import Teacher
from app.database import Base


class TeacherScheduledClass(Base):
    __tablename__ = "scheduled_class_teacher"
    __table_args__ = (UniqueConstraint("teacher_id", "class_id", name="uq_teacher_class"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teacher.user_id", ondelete="CASCADE"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("class.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    role = Column(Text, default='lecturer')

