from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(10), nullable=False)  # 'entry' or 'exit'
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    person = relationship("Person", back_populates="attendance_events")


class CurrentPresence(Base):
    __tablename__ = "current_presence"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), unique=True, nullable=False)
    entered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    person = relationship("Person", back_populates="current_presence")

# ------------------------------------------------------------
#               Added more potentially useful models 
# ------------------------------------------------------------ 

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    class_ = relationship("Class", back_populates="attendance_sessions")
    created_by_user = relationship("User", back_populates="attendance_sessions")
    attendance_records = relationship("PersonAttendanceRecord", back_populates="attendance_session")


class PersonAttendanceRecord(Base):
    __tablename__ = "person_attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    attendance_session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)  # 'present', 'absent', 'late', 'excused'
    confidence = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    attendance_session = relationship("AttendanceSession", back_populates="attendance_records")
    person = relationship("Person", back_populates="attendance_records")
