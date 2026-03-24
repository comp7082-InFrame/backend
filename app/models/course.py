import uuid
from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Course(Base):
    __tablename__ = "course"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term_id = Column(UUID(as_uuid=True), ForeignKey("term.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)
