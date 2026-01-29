from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class FaceDetection(BaseModel):
    person_id: Optional[int] = None
    name: Optional[str] = None
    confidence: float
    bbox: BoundingBox
    status: str  # 'present', 'entering', 'exiting', 'unknown'


class StreamFrame(BaseModel):
    type: str = "frame"
    image: str  # base64-encoded JPEG
    faces: List[FaceDetection]
    timestamp: str


class AttendanceUpdate(BaseModel):
    type: str = "attendance_update"
    event: str  # 'entry' or 'exit'
    person_id: int
    name: str
    timestamp: str


class AttendanceEventResponse(BaseModel):
    id: int
    person_id: int
    person_name: str
    event_type: str
    confidence: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class CurrentPresenceResponse(BaseModel):
    person_id: int
    name: str
    entered_at: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class AttendanceCurrentResponse(BaseModel):
    present: List[CurrentPresenceResponse]
    absent: List[dict]  # List of {id, name}
    total_enrolled: int
