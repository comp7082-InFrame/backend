import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Building(Base):
    __tablename__ = "building"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id = Column(UUID(as_uuid=True), ForeignKey("campus.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    description = Column(Text)