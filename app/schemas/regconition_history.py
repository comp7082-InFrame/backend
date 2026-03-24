from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RecognitionHistoryBase(BaseModel):
    confidence: Optional[float] = None
    recognized: bool
    user_id: Optional[UUID] = None
    note: Optional[str] = None


class RecognitionHistoryCreate(RecognitionHistoryBase):
    attendance_session_id: int


class RecognitionHistoryResponse(RecognitionHistoryBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
