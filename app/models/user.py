import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(Text, unique=True, nullable=False)
    role = Column(JSON, default=list)
    photo_path = Column(Text)




class ClassUsers(Base):
    __tablename__ = "class_users"  
    __table_args__ = {"extend_existing": True} 

    class_id = Column(UUID(as_uuid=True), primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
