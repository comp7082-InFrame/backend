import unittest
import uuid
from datetime import datetime, timedelta, timezone

from app.services.live_presence_service import LivePresenceTracker


class LivePresenceTrackerTests(unittest.TestCase):
    def test_presence_expires_after_ttl(self):
        tracker = LivePresenceTracker(ttl_seconds=1.0)
        user_id = uuid.uuid4()
        seen_at = datetime.now(timezone.utc)

        tracker.mark_seen([user_id], seen_at=seen_at)

        self.assertTrue(tracker.is_currently_seen(user_id, now=seen_at + timedelta(milliseconds=500)))
        self.assertFalse(tracker.is_currently_seen(user_id, now=seen_at + timedelta(seconds=2)))

    def test_get_current_ids_prunes_expired_users(self):
        tracker = LivePresenceTracker(ttl_seconds=1.0)
        fresh_user = uuid.uuid4()
        expired_user = uuid.uuid4()
        seen_at = datetime.now(timezone.utc)

        tracker.mark_seen([fresh_user], seen_at=seen_at)
        tracker.mark_seen([expired_user], seen_at=seen_at - timedelta(seconds=5))

        current_ids = tracker.get_current_ids(now=seen_at)

        self.assertEqual(current_ids, {fresh_user})
