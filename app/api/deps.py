from typing import Dict
import numpy as np
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Person
from app.utils.encoding import bytes_to_encoding
from app.services import FaceService, PresenceTracker

# Global instances (initialized on startup)
face_service: FaceService = None
presence_tracker: PresenceTracker = None
person_names: Dict[int, str] = {}


def init_services(db: Session):
    """Initialize global services with data from database."""
    global face_service, presence_tracker, person_names

    # Load all active persons and their encodings
    persons = db.query(Person).filter(Person.is_active == True).all()

    known_encodings = {}
    person_names.clear()

    for person in persons:
        known_encodings[person.id] = bytes_to_encoding(person.face_encoding)
        person_names[person.id] = person.name

    # Initialize services
    face_service = FaceService(known_encodings)
    presence_tracker = PresenceTracker()


def get_face_service() -> FaceService:
    """Get the global face service instance."""
    return face_service


def get_presence_tracker() -> PresenceTracker:
    """Get the global presence tracker instance."""
    return presence_tracker


def get_person_names() -> Dict[int, str]:
    """Get the mapping of person IDs to names."""
    return person_names


def add_person_to_services(person_id: int, name: str, encoding: np.ndarray):
    """Add a new person to running services."""
    global face_service, person_names
    if face_service:
        face_service.add_encoding(person_id, encoding)
    person_names[person_id] = name


def remove_person_from_services(person_id: int):
    """Remove a person from running services."""
    global face_service, person_names
    if face_service:
        face_service.remove_encoding(person_id)
    if person_id in person_names:
        del person_names[person_id]
