import uuid
from datetime import datetime, timedelta, timezone


class LivePresenceTracker:
    """Tracks which recognized users are visible right now on the live camera."""

    def __init__(self, ttl_seconds: float = 2.0):
        self.ttl = timedelta(seconds=ttl_seconds)
        self.last_seen: dict[uuid.UUID, datetime] = {}

    def mark_seen(self, user_ids: list[uuid.UUID], seen_at: datetime | None = None):
        timestamp = seen_at or datetime.now(timezone.utc)
        for user_id in user_ids:
            self.last_seen[user_id] = timestamp

    def prune(self, now: datetime | None = None):
        current_time = now or datetime.now(timezone.utc)
        expired = [
            user_id for user_id, seen_at in self.last_seen.items()
            if current_time - seen_at > self.ttl
        ]
        for user_id in expired:
            del self.last_seen[user_id]

    def is_currently_seen(self, user_id: uuid.UUID, now: datetime | None = None) -> bool:
        self.prune(now)
        return user_id in self.last_seen

    def get_current_ids(self, now: datetime | None = None) -> set[uuid.UUID]:
        self.prune(now)
        return set(self.last_seen.keys())
