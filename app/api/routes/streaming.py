import base64
import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import AttendanceEvent as AttendanceEventModel, CurrentPresence
from app.services import CameraService
from app.services.face_service import draw_face_boxes
from app.api.deps import (
    get_face_service,
    get_presence_tracker,
    get_person_names,
    init_services
)

router = APIRouter()


async def save_attendance_event(event, db: Session):
    """Save attendance event to database."""
    db_event = AttendanceEventModel(
        person_id=event.person_id,
        event_type=event.event_type,
        confidence=event.confidence,
        timestamp=event.timestamp
    )
    db.add(db_event)

    # Update current presence
    if event.event_type == "entry":
        presence = CurrentPresence(
            person_id=event.person_id,
            entered_at=event.timestamp,
            last_seen=event.timestamp
        )
        db.merge(presence)
    else:  # exit
        db.query(CurrentPresence).filter(
            CurrentPresence.person_id == event.person_id
        ).delete()

    db.commit()


@router.websocket("/ws/stream")
async def video_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video streaming with face recognition.

    Sends two types of messages:
    1. Frame messages with annotated video and face detections
    2. Attendance update messages for entry/exit events
    """
    await websocket.accept()

    # Get database session
    db = SessionLocal()

    try:
        # Initialize services if needed
        face_service = get_face_service()
        if face_service is None:
            init_services(db)
            face_service = get_face_service()

        presence_tracker = get_presence_tracker()
        person_names = get_person_names()

        # Initialize camera
        camera = CameraService()
        if not camera.start():
            await websocket.send_json({
                "type": "error",
                "message": "Failed to start camera"
            })
            return

        try:
            async for frame in camera.get_frames():
                # Process frame for face detection
                faces = face_service.process_frame(frame)

                # Add names to face detections
                for face in faces:
                    person_id = face.get("person_id")
                    if person_id:
                        face["name"] = person_names.get(person_id, f"ID: {person_id}")
                        face["status"] = presence_tracker.get_status_for_display(person_id)
                    else:
                        face["name"] = None
                        face["status"] = "unknown"

                # Update presence tracking
                events = presence_tracker.update(faces)

                # Save events to database and send updates
                for event in events:
                    await save_attendance_event(event, db)

                    await websocket.send_json({
                        "type": "attendance_update",
                        "event": event.event_type,
                        "person_id": event.person_id,
                        "name": person_names.get(event.person_id, f"ID: {event.person_id}"),
                        "confidence": event.confidence,
                        "timestamp": event.timestamp.isoformat()
                    })

                # Draw annotations on frame
                annotated_frame = draw_face_boxes(frame, faces, person_names)

                # Encode frame
                jpeg_bytes = camera.encode_frame(annotated_frame)
                frame_b64 = base64.b64encode(jpeg_bytes).decode('utf-8')

                # Send frame message
                await websocket.send_json({
                    "type": "frame",
                    "image": frame_b64,
                    "faces": faces,
                    "timestamp": datetime.utcnow().isoformat()
                })

        except WebSocketDisconnect:
            pass
        finally:
            camera.stop()

    finally:
        db.close()
