import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from app.services.attendance_service import PresenceState, PresenceTracker


class PresenceTrackerTests(unittest.TestCase):
    def test_update_confirms_user_after_threshold(self):
        user_id = uuid.uuid4()
        tracker = PresenceTracker(entry_threshold=2)
        now = datetime.now(timezone.utc)

        with patch("app.services.attendance_service.datetime") as datetime_mock:
            datetime_mock.now.return_value = now
            first_events = tracker.update([{"user_id": user_id, "confidence": 0.82}])
            second_events = tracker.update([{"user_id": user_id, "confidence": 0.91}])

        self.assertEqual(first_events, [])
        self.assertEqual(len(second_events), 1)
        self.assertEqual(second_events[0].user_id, user_id)
        self.assertEqual(second_events[0].confidence, 0.91)
        self.assertEqual(second_events[0].timestamp, now)
        self.assertEqual(tracker.get_status_for_display(user_id), "present")
        self.assertEqual(tracker.get_confirmed_ids(), {user_id})

    def test_update_resets_entering_user_when_detection_disappears(self):
        user_id = uuid.uuid4()
        tracker = PresenceTracker(entry_threshold=3)

        tracker.update([{"user_id": user_id, "confidence": 0.6}])
        tracker.update([])

        self.assertEqual(tracker.states[user_id], PresenceState.ABSENT)
        self.assertEqual(tracker.counters[user_id], 0)
        self.assertEqual(tracker.get_status_for_display(user_id), "absent")

    def test_reset_clears_all_tracking_state(self):
        user_id = uuid.uuid4()
        tracker = PresenceTracker(entry_threshold=1)
        tracker.update([{"user_id": user_id, "confidence": 0.6}])

        tracker.reset()

        self.assertEqual(tracker.states, {})
        self.assertEqual(tracker.counters, {})
        self.assertEqual(tracker.confidences, {})
        self.assertEqual(tracker.confirmed_ids, set())
