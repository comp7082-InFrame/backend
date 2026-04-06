import unittest
import uuid
import importlib.util
from datetime import datetime, timedelta, timezone


class LivePresenceTrackerTests(unittest.TestCase):
    def test_presence_expires_after_ttl(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.services.live_presence_service import LivePresenceTracker

        tracker = LivePresenceTracker(ttl_seconds=1.0)
        user_id = uuid.uuid4()
        seen_at = datetime.now(timezone.utc)

        tracker.mark_seen([user_id], seen_at=seen_at)

        self.assertTrue(tracker.is_currently_seen(user_id, now=seen_at + timedelta(milliseconds=500)))
        self.assertFalse(tracker.is_currently_seen(user_id, now=seen_at + timedelta(seconds=2)))


if __name__ == "__main__":
    unittest.main()
