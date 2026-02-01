from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Person, AttendanceEvent as AttendanceEventModel, CurrentPresence
from app.schemas import AttendanceEventResponse, AttendanceCurrentResponse, CurrentPresenceResponse
from app.api.deps import get_presence_tracker

router = APIRouter()


@router.get("/current", response_model=AttendanceCurrentResponse)
async def get_current_attendance(db: Session = Depends(get_db)):
    """Get current attendance status - who is present vs absent."""
    # Get all active persons
    all_persons = db.query(Person).filter(Person.is_active == True).all()
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
    event_type: Optional[str] = Query(None, description="Filter by event type (entry/exit)"),
    since: Optional[datetime] = Query(None, description="Filter events after this time"),
    limit: int = Query(100, le=1000, description="Maximum number of events to return"),
    db: Session = Depends(get_db)
):
    """Get attendance event history."""
    query = db.query(AttendanceEventModel).join(Person)

    if person_id:
        query = query.filter(AttendanceEventModel.person_id == person_id)

    if event_type:
        query = query.filter(AttendanceEventModel.event_type == event_type)

    if since:
        query = query.filter(AttendanceEventModel.timestamp >= since)

    events = query.order_by(desc(AttendanceEventModel.timestamp)).limit(limit).all()

    return [
        AttendanceEventResponse(
            id=e.id,
            person_id=e.person_id,
            person_name=e.person.name,
            event_type=e.event_type,
            confidence=e.confidence,
            timestamp=e.timestamp
        )
        for e in events
    ]


@router.get("/today", response_model=List[AttendanceEventResponse])
async def get_today_attendance(db: Session = Depends(get_db)):
    """Get today's attendance events."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    events = db.query(AttendanceEventModel).join(Person).filter(
        AttendanceEventModel.timestamp >= today_start
    ).order_by(desc(AttendanceEventModel.timestamp)).all()

    return [
        AttendanceEventResponse(
            id=e.id,
            person_id=e.person_id,
            person_name=e.person.name,
            event_type=e.event_type,
            confidence=e.confidence,
            timestamp=e.timestamp
        )
        for e in events
    ]
