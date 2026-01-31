from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Set, Optional
from app.config import get_settings

settings = get_settings()


class PresenceState(Enum):
    """Presence state for a person."""
    ABSENT = "absent"
    ENTERING = "entering"
    PRESENT = "present"
    EXITING = "exiting"


@dataclass
class AttendanceEvent:
    """Represents an entry or exit event."""
    person_id: int
    event_type: str  # 'entry' or 'exit'
    confidence: float
    timestamp: datetime


class PresenceTracker:
    """
    Tracks presence state for enrolled people using a debounced state machine.

    State transitions:
    - ABSENT -> ENTERING: Face detected
    - ENTERING -> PRESENT: Face detected for entry_threshold consecutive frames
    - ENTERING -> ABSENT: Face not detected (reset counter)
    - PRESENT -> EXITING: Face not detected
    - EXITING -> ABSENT: Face not detected for exit_threshold consecutive frames
    - EXITING -> PRESENT: Face detected again (reset counter)
    """

    def __init__(
        self,
        entry_threshold: int = None,
        exit_threshold: int = None
    ):
        """
        Initialize presence tracker.

        Args:
            entry_threshold: Frames to confirm entry
            exit_threshold: Frames to confirm exit
        """
        self.entry_threshold = entry_threshold or settings.ENTRY_FRAME_THRESHOLD
        self.exit_threshold = exit_threshold or settings.EXIT_FRAME_THRESHOLD

        # Track state and counters for each person
        self.states: Dict[int, PresenceState] = {}
        self.counters: Dict[int, int] = {}
        self.confidences: Dict[int, float] = {}  # Store last confidence for events

        # Track who is currently present
        self.present_ids: Set[int] = set()

    def reset(self):
        """Reset all tracking state."""
        self.states.clear()
        self.counters.clear()
        self.confidences.clear()
        self.present_ids.clear()

    def get_present_ids(self) -> Set[int]:
        """Get set of currently present person IDs."""
        return self.present_ids.copy()

    def get_state(self, person_id: int) -> PresenceState:
        """Get current state for a person."""
        return self.states.get(person_id, PresenceState.ABSENT)

    def update(self, detections: List[dict]) -> List[AttendanceEvent]:
        """
        Update presence tracking with new frame detections.

        Args:
            detections: List of face detection results with person_id and confidence

        Returns:
            List of attendance events (entries/exits) triggered by this update
        """
        events = []
        now = datetime.utcnow()

        # Get set of detected person IDs (excluding unknown faces)
        detected_ids = set()
        for det in detections:
            person_id = det.get("person_id")
            if person_id is not None:
                detected_ids.add(person_id)
                self.confidences[person_id] = det.get("confidence", 0.0)

        # Process detected persons
        for person_id in detected_ids:
            current_state = self.states.get(person_id, PresenceState.ABSENT)

            if current_state == PresenceState.ABSENT:
                # Start entering
                self.states[person_id] = PresenceState.ENTERING
                self.counters[person_id] = 1

            elif current_state == PresenceState.ENTERING:
                # Increment counter
                self.counters[person_id] += 1

                # Check if threshold reached
                if self.counters[person_id] >= self.entry_threshold:
                    self.states[person_id] = PresenceState.PRESENT
                    self.present_ids.add(person_id)
                    events.append(AttendanceEvent(
                        person_id=person_id,
                        event_type="entry",
                        confidence=self.confidences.get(person_id, 0.0),
                        timestamp=now
                    ))

            elif current_state == PresenceState.EXITING:
                # Cancel exit, return to present
                self.states[person_id] = PresenceState.PRESENT
                self.counters[person_id] = 0

            # PRESENT state - no action needed, just continue

        # Process persons not detected (potential exits)
        all_tracked = set(self.states.keys())
        not_detected = all_tracked - detected_ids

        for person_id in not_detected:
            current_state = self.states.get(person_id)

            if current_state == PresenceState.ENTERING:
                # Cancel entering, return to absent
                self.states[person_id] = PresenceState.ABSENT
                self.counters[person_id] = 0

            elif current_state == PresenceState.PRESENT:
                # Start exiting
                self.states[person_id] = PresenceState.EXITING
                self.counters[person_id] = 1

            elif current_state == PresenceState.EXITING:
                # Increment exit counter
                self.counters[person_id] += 1

                # Check if threshold reached
                if self.counters[person_id] >= self.exit_threshold:
                    self.states[person_id] = PresenceState.ABSENT
                    self.present_ids.discard(person_id)
                    events.append(AttendanceEvent(
                        person_id=person_id,
                        event_type="exit",
                        confidence=self.confidences.get(person_id, 0.0),
                        timestamp=now
                    ))

        return events

    def get_status_for_display(self, person_id: int) -> str:
        """Get display status string for a person."""
        state = self.get_state(person_id)
        return state.value
