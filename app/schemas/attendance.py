from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class FaceDetection(BaseModel):
    user_id: Optional[UUID] = None
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
    user_id: UUID
    name: str
    timestamp: str
