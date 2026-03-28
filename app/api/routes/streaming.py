import base64
import logging
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.regconition_history import RecognitionHistory
from app.services import CameraService
from app.utils.drawing import draw_face_boxes
from app.api.deps import (
    get_face_service,
    get_live_presence_tracker,
    get_presence_tracker,
    get_user_names,
    init_services,
    start_services_for_session,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def save_recognition_event(user_id: uuid.UUID, session_id: uuid.UUID, confidence: float, timestamp: datetime, db: Session):
    """Save a confirmed face recognition event to recognition_history.
    The Postgres trigger on recognition_history will update attendance_record automatically.
    """
    db_event = RecognitionHistory(
        attendance_session_id=session_id,
        user_id=user_id,
        confidence=confidence,
        recognized=True,
        timestamp=timestamp
    )
    db.add(db_event)
    db.commit()


@router.websocket("/ws/stream")
async def video_stream(
    websocket: WebSocket,
    session_id: uuid.UUID | None = None,
    class_id: uuid.UUID | None = None,
):
    """
    WebSocket endpoint for real-time video streaming with face recognition.

    Sends two types of messages:
    1. Frame messages with annotated video and face detections
    2. Attendance update messages when a user is confirmed present
    """
    await websocket.accept()

    # SessionLocal() used directly — WebSocket connections are long-lived and
    # FastAPI's request-scoped DI does not apply to WebSocket handlers.
    db = SessionLocal()

    try:
        face_service = get_face_service()
        if session_id is not None:
            face_service = start_services_for_session(session_id, db)
        elif class_id is not None:
            init_services(db, class_id=class_id)
            face_service = get_face_service()

        if face_service is None:
            await websocket.send_json({
                "type": "error",
                "message": "Face recognition service is not initialized"
            })
            return

        presence_tracker = get_presence_tracker()
        live_presence_tracker = get_live_presence_tracker()
        user_names = get_user_names()

        camera = CameraService()
        if not camera.start():
            await websocket.send_json({
                "type": "error",
                "message": "Failed to start camera"
            })
            return

        try:
            async for frame in camera.get_frames():
                try:
                    faces = face_service.process_frame(frame)

                    # Attach names and status to each detection
                    for face in faces:
                        user_id = face.get("user_id")
                        if user_id:
                            face["name"] = user_names.get(user_id, f"ID: {user_id}")
                            face["status"] = presence_tracker.get_status_for_display(user_id)
                        else:
                            face["name"] = None
                            face["status"] = "unknown"

                    if live_presence_tracker is not None:
                        live_presence_tracker.mark_seen(
                            [face["user_id"] for face in faces if face.get("user_id") is not None]
                        )

                    # Check for newly confirmed entries
                    events = presence_tracker.update(faces)

                    for event in events:
                        # Save to recognition_history — trigger marks student present
                        if session_id is not None:
                            await save_recognition_event(
                                user_id=event.user_id,
                                session_id=session_id,
                                confidence=event.confidence,
                                timestamp=event.timestamp,
                                db=db
                            )

                        await websocket.send_json({
                            "type": "attendance_update",
                            "user_id": str(event.user_id),
                            "name": user_names.get(event.user_id, f"ID: {event.user_id}"),
                            "confidence": event.confidence,
                            "timestamp": event.timestamp.isoformat()
                        })

                    # Draw annotations and send frame
                    annotated_frame = draw_face_boxes(frame, faces, user_names)
                    jpeg_bytes = camera.encode_frame(annotated_frame)
                    frame_b64 = base64.b64encode(jpeg_bytes).decode("utf-8")

                    await websocket.send_json({
                        "type": "frame",
                        "image": frame_b64,
                        "faces": faces,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                except Exception as e:
                    logger.error("Frame processing error: %s", e)
                    continue

        except WebSocketDisconnect:
            pass
        finally:
            camera.stop()

    finally:
        db.close()
