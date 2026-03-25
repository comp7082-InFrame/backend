from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Teacher(Base):
    __tablename__ = "teacher"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    employee_number = Column(String(12), unique=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(Text, unique=True, nullable=False)
    department = Column(Text)
    title = Column(Text)
    active = Column(Boolean, default=True)