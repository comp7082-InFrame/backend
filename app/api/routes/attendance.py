import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import ClassUsers, Person, AttendanceEvent as AttendanceEventModel, CurrentPresence
from app.schemas import AttendanceEventResponse, AttendanceCurrentResponse, CurrentPresenceResponse

router = APIRouter()


def _to_event_response(e: AttendanceEventModel) -> AttendanceEventResponse:
    return AttendanceEventResponse(
        id=e.id,
        person_id=e.person_id,
        person_name=e.person.name,
        event_type=e.event_type,
        confidence=e.confidence,
        timestamp=e.timestamp
    )


@router.get("/current", response_model=AttendanceCurrentResponse)
async def get_current_attendance(
    class_id: Optional[uuid.UUID] = Query(None, description="Filter by class ID"),
    db: Session = Depends(get_db),
):
    """Get current attendance status - who is present vs absent."""
    # Get all active persons
    query = db.query(Person).filter(Person.is_active == True)
    if class_id is not None:
        query = (
            query.join(ClassUsers, ClassUsers.person_id == Person.id)
            .filter(ClassUsers.class_id == class_id)
        )
    all_persons = query.all()
    all_person_ids = {p.id for p in all_persons}
    person_map = {p.id: p for p in all_persons}

    # Get currently present from database
    current_presence = db.query(CurrentPresence).all()
    present_ids = {cp.person_id for cp in current_presence}

    # Build present list
    present = []
    for cp in current_presence:
        if cp.person_id in person_map:
            present.append(CurrentPresenceResponse(
                person_id=cp.person_id,
                name=person_map[cp.person_id].name,
                entered_at=cp.entered_at,
                last_seen=cp.last_seen
            ))

    # Build absent list
    absent_ids = all_person_ids - present_ids
    absent = [{"id": pid, "name": person_map[pid].name} for pid in absent_ids]

    return AttendanceCurrentResponse(
        present=present,
        absent=absent,
        total_enrolled=len(all_persons)
    )


@router.get("/history", response_model=List[AttendanceEventResponse])
async def get_attendance_history(
    person_id: Optional[int] = Query(None, description="Filter by person ID"),
    class_id: Optional[uuid.UUID] = Query(None, description="Filter by class ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type (entry/exit)"),
    since: Optional[datetime] = Query(None, description="Filter events after this time"),
    limit: int = Query(100, le=1000, description="Maximum number of events to return"),
    db: Session = Depends(get_db)
):
    """Get attendance event history."""
    query = db.query(AttendanceEventModel).join(Person)

    if person_id:
        query = query.filter(AttendanceEventModel.person_id == person_id)

    if class_id:
        query = (
            query.join(ClassUsers, ClassUsers.person_id == AttendanceEventModel.person_id)
            .filter(ClassUsers.class_id == class_id)
        )

    if event_type:
        query = query.filter(AttendanceEventModel.event_type == event_type)

    if since:
        query = query.filter(AttendanceEventModel.timestamp >= since)

    events = query.order_by(desc(AttendanceEventModel.timestamp)).limit(limit).all()

    return [_to_event_response(e) for e in events]


@router.get("/today", response_model=List[AttendanceEventResponse])
async def get_today_attendance(
    class_id: Optional[uuid.UUID] = Query(None, description="Filter by class ID"),
    db: Session = Depends(get_db),
):
    """Get today's attendance events."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    query = db.query(AttendanceEventModel).join(Person).filter(
        AttendanceEventModel.timestamp >= today_start
    )
    if class_id is not None:
        query = (
            query.join(ClassUsers, ClassUsers.person_id == AttendanceEventModel.person_id)
            .filter(ClassUsers.class_id == class_id)
        )
    events = query.order_by(desc(AttendanceEventModel.timestamp)).all()

    return [_to_event_response(e) for e in events]
