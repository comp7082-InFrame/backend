import unittest
import uuid
import importlib.util
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from fastapi import HTTPException


class FakePresenceTracker:
    pass


class FakeLivePresenceTracker:
    def __init__(self, ttl_seconds):
        self.ttl_seconds = ttl_seconds


class FakeFaceService:
    def __init__(self, known_encodings):
        self.known_encodings = known_encodings


class RuntimeIsolationTests(unittest.TestCase):
    def test_build_runtime_creates_isolated_trackers_and_names(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.deps import build_runtime

        user_one = SimpleNamespace(
            id=uuid.uuid4(),
            first_name="Splinter",
            last_name="Sensei",
            photo_encoding=b"\x00" * 2048,
        )
        user_two = SimpleNamespace(
            id=uuid.uuid4(),
            first_name="Shredder",
            last_name="Oroku",
            photo_encoding=b"\x00" * 2048,
        )

        with patch("app.api.deps._load_runtime_users", side_effect=[[user_one], [user_two]]):
            with patch("app.api.deps.bytes_to_encoding", side_effect=lambda _: "embedding"):
                with patch("app.api.deps.FaceService", FakeFaceService):
                    with patch("app.api.deps.PresenceTracker", FakePresenceTracker):
                        with patch("app.api.deps.LivePresenceTracker", FakeLivePresenceTracker):
                            runtime_one = build_runtime(object())
                            runtime_two = build_runtime(object())

        self.assertIsNot(runtime_one.presence_tracker, runtime_two.presence_tracker)
        self.assertIsNot(runtime_one.live_presence_tracker, runtime_two.live_presence_tracker)
        self.assertEqual(runtime_one.user_names[user_one.id], "Splinter Sensei")
        self.assertEqual(runtime_two.user_names[user_two.id], "Shredder Oroku")
        self.assertNotIn(user_two.id, runtime_one.user_names)

    def test_build_runtime_for_session_uses_session_class_scope(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.deps import build_runtime_for_session

        session_id = uuid.uuid4()
        class_id = uuid.uuid4()
        db = FakeRuntimeDB(SimpleNamespace(id=session_id, class_id=class_id))

        with patch("app.api.deps.build_runtime", return_value="runtime-bundle") as build_runtime_mock:
            result = build_runtime_for_session(session_id, db)

        self.assertEqual(result, "runtime-bundle")
        build_runtime_mock.assert_called_once_with(db, class_id=class_id)

    def test_build_runtime_for_session_raises_404_when_session_missing(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.deps import build_runtime_for_session

        db = FakeRuntimeDB(None)

        with self.assertRaises(HTTPException) as exc_info:
            build_runtime_for_session(uuid.uuid4(), db)

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "Attendance session not found")


class RecordingLivePresenceTracker:
    def __init__(self):
        self.calls = []

    def mark_seen(self, user_ids):
        self.calls.append(list(user_ids))


class FakeRuntimePresenceTracker:
    def __init__(self):
        self.updated_faces = []

    def get_status_for_display(self, user_id):
        return "present"

    def update(self, faces):
        self.updated_faces.append(list(faces))
        return []


class FakeRuntimeFaceService:
    def __init__(self, user_id):
        self.user_id = user_id

    def process_frame(self, frame):
        return [
            {
                "user_id": self.user_id,
                "confidence": 0.93,
                "bbox": {"x": 2, "y": 2, "width": 12, "height": 12},
            }
        ]


class FakeCameraService:
    last_instance = None

    def __init__(self):
        self.started = False
        self.stopped = False
        FakeCameraService.last_instance = self

    def start(self):
        self.started = True
        return True

    async def get_frames(self):
        yield np.zeros((24, 24, 3), dtype=np.uint8)

    def encode_frame(self, frame):
        return b"jpeg-bytes"

    def stop(self):
        self.stopped = True


class FakeStreamingDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.messages = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        self.messages.append(payload)


class StreamingRuntimeRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_video_stream_uses_session_scoped_runtime_and_mirrors_live_presence(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.routes.streaming import video_stream

        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        db = FakeStreamingDB()
        local_live_presence = RecordingLivePresenceTracker()
        shared_live_presence = RecordingLivePresenceTracker()
        runtime = SimpleNamespace(
            face_service=FakeRuntimeFaceService(user_id),
            presence_tracker=FakeRuntimePresenceTracker(),
            live_presence_tracker=local_live_presence,
            user_names={user_id: "Raphael Turtle"},
        )
        websocket = FakeWebSocket()

        with patch("app.api.routes.streaming.SessionLocal", return_value=db):
            with patch("app.api.routes.streaming.build_runtime_for_session", return_value=runtime) as build_runtime_mock:
                with patch("app.api.routes.streaming.get_live_presence_tracker", return_value=shared_live_presence):
                    with patch("app.api.routes.streaming.CameraService", FakeCameraService):
                        with patch("app.api.routes.streaming.draw_face_boxes", side_effect=lambda frame, faces, names: frame):
                            with patch("app.api.routes.streaming.record_attendance_from_recognition") as record_mock:
                                await video_stream(websocket, session_id=session_id)

        self.assertTrue(websocket.accepted)
        self.assertEqual(len(websocket.messages), 1)
        self.assertEqual(websocket.messages[0]["type"], "frame")
        self.assertEqual(websocket.messages[0]["faces"][0]["user_id"], str(user_id))
        build_runtime_mock.assert_called_once_with(session_id, db)
        self.assertEqual(local_live_presence.calls, [[user_id]])
        self.assertEqual(shared_live_presence.calls, [[user_id]])
        self.assertEqual(runtime.presence_tracker.updated_faces[0][0]["user_id"], user_id)
        self.assertFalse(record_mock.called)
        self.assertTrue(db.closed)
        self.assertTrue(FakeCameraService.last_instance.started)
        self.assertTrue(FakeCameraService.last_instance.stopped)


class FakeRuntimeQuery:
    def __init__(self, row):
        self.row = row

    def filter(self, *args, **kwargs):
        return self

    def one_or_none(self):
        return self.row


class FakeRuntimeDB:
    def __init__(self, session_row):
        self.session_row = session_row

    def query(self, model):
        return FakeRuntimeQuery(self.session_row)


if __name__ == "__main__":
    unittest.main()
