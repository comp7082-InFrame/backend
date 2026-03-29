import uuid
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional
from app.config import get_settings

settings = get_settings()


class PresenceState(Enum):
    ABSENT = "absent"
    ENTERING = "entering"
    PRESENT = "present"


@dataclass
class AttendanceEvent:
    """Represents a confirmed entry event."""
    user_id: uuid.UUID
    confidence: float
    timestamp: datetime


class PresenceTracker:
    """
    Tracks presence state for enrolled users using a debounced state machine.
    Only tracks entry confirmation — once a user is marked PRESENT, they are
    done for the session.

    State transitions:
    - ABSENT -> ENTERING: Face detected
    - ENTERING -> PRESENT: Face detected for entry_threshold consecutive frames (fires event once)
    - ENTERING -> ABSENT: Face not detected (reset counter)
    - PRESENT: no further transitions
    """

    def __init__(self, entry_threshold: int = None):
        self.entry_threshold = entry_threshold or settings.ENTRY_FRAME_THRESHOLD

        self.states: Dict[uuid.UUID, PresenceState] = {}
        self.counters: Dict[uuid.UUID, int] = {}
        self.confidences: Dict[uuid.UUID, float] = {}
        self.confirmed_ids: Set[uuid.UUID] = set()

    def reset(self):
        self.states.clear()
        self.counters.clear()
        self.confidences.clear()
        self.confirmed_ids.clear()

    def get_confirmed_ids(self) -> Set[uuid.UUID]:
        return self.confirmed_ids.copy()

    def update(self, detections: List[dict]) -> List[AttendanceEvent]:
        """
        Update presence tracking with new frame detections.
        Returns a list of newly confirmed entry events (at most one per user ever).
        """
        events = []
        now = datetime.now(timezone.utc)

        detected_ids = set()
        for det in detections:
            user_id = det.get("user_id")
            if user_id is not None:
                detected_ids.add(user_id)
                self.confidences[user_id] = det.get("confidence", 0.0)

        for user_id in detected_ids:
            # Already confirmed this session — skip
            if user_id in self.confirmed_ids:
                continue

            current_state = self.states.get(user_id, PresenceState.ABSENT)

            if current_state == PresenceState.ABSENT:
                self.states[user_id] = PresenceState.ENTERING
                self.counters[user_id] = 1

            elif current_state == PresenceState.ENTERING:
                self.counters[user_id] += 1
                if self.counters[user_id] >= self.entry_threshold:
                    self.states[user_id] = PresenceState.PRESENT
                    self.confirmed_ids.add(user_id)
                    events.append(AttendanceEvent(
                        user_id=user_id,
                        confidence=self.confidences.get(user_id, 0.0),
                        timestamp=now
                    ))

        # Reset entering state for users not detected this frame
        for user_id, state in list(self.states.items()):
            if user_id not in detected_ids and state == PresenceState.ENTERING:
                self.states[user_id] = PresenceState.ABSENT
                self.counters[user_id] = 0

        return events

    def get_status_for_display(self, user_id: uuid.UUID) -> str:
        state = self.states.get(user_id, PresenceState.ABSENT)
        return state.value
