import uuid
from sqlalchemy import Column, String, Text, Boolean, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(Text, unique=True, nullable=False)
    role = Column(ARRAY(Text), default=list)
    photo_path = Column(Text)
    photo_encoding = Column(LargeBinary)
    student_number = Column(String(12), unique=True)
    major = Column(Text)
    employee_number = Column(String(12), unique=True)
    department = Column(Text)
    title = Column(Text)
    active = Column(Boolean, default=True)


class ClassUsers(Base):
    """Read-only view: all users (teachers + students) per class with face encodings."""
    __tablename__ = "class_users"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(Text)
    role = Column(Text)
    class_id = Column(UUID(as_uuid=True), primary_key=True)
    photo_path = Column(Text)
    photo_encoding = Column(LargeBinary)
