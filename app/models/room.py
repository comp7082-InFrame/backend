import uuid
from sqlalchemy import Column, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Room(Base):
    __tablename__ = "room"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id = Column(UUID(as_uuid=True), ForeignKey("building.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    capacity = Column(Integer)
    status = Column(Boolean, default=True)
    description = Column(Text)
    camera_connection = Column(Text)