import logging
from typing import Dict
import uuid
import numpy as np
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import AttendanceSession, ClassUsers, User
from app.utils.encoding import bytes_to_encoding
from app.config import get_settings
from app.services import FaceService, LivePresenceTracker, PresenceTracker

# Global instances (initialized on startup)
face_service: FaceService = None
presence_tracker: PresenceTracker = None
live_presence_tracker: LivePresenceTracker = None
user_names: Dict[uuid.UUID, str] = {}

logger = logging.getLogger(__name__)
settings = get_settings()

EXPECTED_EMBEDDING_BYTES = 512 * 4  # 2048 bytes for 512-dim float32


def init_services(db: Session, class_id: uuid.UUID | None = None):
    """Initialize recognition services from the database.

    When class_id is provided, only users linked to that class are loaded.
    Otherwise all active users with face encodings are loaded.
    """
    global face_service, presence_tracker, live_presence_tracker, user_names

    if class_id is not None:
        rows = (
            db.query(ClassUsers)
            .filter(ClassUsers.class_id == class_id, ClassUsers.photo_encoding != None)
            .all()
        )
        user_ids = [row.id for row in rows]
        users = db.query(User).filter(User.id.in_(user_ids), User.photo_encoding != None).all()
    else:
        users = db.query(User).filter(User.photo_encoding != None, User.active == True).all()

    known_encodings = {}
    user_names.clear()

    for user in users:
        if len(user.photo_encoding) != EXPECTED_EMBEDDING_BYTES:
            logger.warning(
                "User %s %s (id=%s) has a stale encoding (%d bytes) — "
                "re-enroll to enable recognition.",
                user.first_name, user.last_name, user.id, len(user.photo_encoding)
            )
            continue
        known_encodings[user.id] = bytes_to_encoding(user.photo_encoding)
        user_names[user.id] = f"{user.first_name} {user.last_name}".strip()

    face_service = FaceService(known_encodings)
    presence_tracker = PresenceTracker()
    live_presence_tracker = LivePresenceTracker(ttl_seconds=settings.LIVE_PRESENCE_TTL_SECONDS)


def start_services_for_session(session_id: uuid.UUID, db: Session) -> FaceService:
    """Initialize services for a specific attendance session."""
    sess = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).one_or_none()
    if sess is None:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    init_services(db, class_id=sess.class_id)
    return get_face_service()


def get_face_service() -> FaceService:
    return face_service


def get_presence_tracker() -> PresenceTracker:
    return presence_tracker


def get_user_names() -> Dict[uuid.UUID, str]:
    return user_names


def get_live_presence_tracker() -> LivePresenceTracker:
    return live_presence_tracker


def add_user_to_services(user_id: uuid.UUID, name: str, encoding: np.ndarray):
    """Add a new user to running services."""
    global face_service, user_names
    if face_service:
        face_service.add_encoding(user_id, encoding)
    else:
        logger.warning(
            "face_service is None — enrollment for user_id=%s saved to DB "
            "but recognition not updated. Restart the server to apply.",
            user_id
        )
    user_names[user_id] = name


def remove_user_from_services(user_id: uuid.UUID):
    """Remove a user from running services."""
    global face_service, user_names
    if face_service:
        face_service.remove_encoding(user_id)
    if user_id in user_names:
        del user_names[user_id]
