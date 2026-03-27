import uuid
from sqlalchemy import Column, Text, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Term(Base):
    __tablename__ = "term"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    active = Column(Boolean, default=True)
