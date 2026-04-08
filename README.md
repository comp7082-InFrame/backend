# InFrame Backend

This repository contains the FastAPI backend for the attendance system. It manages academic data, stores attendance sessions and records, and runs the face-recognition pipeline used for live attendance tracking.

## What The Backend Does

- Exposes REST endpoints for users, students, teachers, courses, classes, terms, campuses, buildings, and rooms
- Registers, updates, and removes face photos and embeddings for users
- Creates and lists attendance sessions, returns session records, and marks absent students when a session ends
- Returns current attendance and attendance history for sessions, students, and courses
- Streams webcam frames over WebSocket and records attendance when recognized users are confirmed present


## Requirements

- Python 3.11
- A camera

## Installation

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```


## Configuration

`.env.example`:

```env
DATABASE_URL=
ARCFACE_MODEL_PACK=buffalo_l
YUNET_MODEL_PATH=models/face_detection_yunet_2023mar.onnx
SIMILARITY_THRESHOLD=0.35
ENTRY_FRAME_THRESHOLD=5
EXIT_FRAME_THRESHOLD=10
PROCESSING_FPS=10
```

### Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` |  | SQLAlchemy connection string for the application database |
| `ARCFACE_MODEL_PACK` | `buffalo_l` | InsightFace model pack used for detection/recognition components |
| `YUNET_MODEL_PATH` | `models/face_detection_yunet_2023mar.onnx` | Local ONNX model path used when the YuNet detector is configured |
| `SIMILARITY_THRESHOLD` | `0.35` | Minimum cosine similarity required to accept a face match |
| `ENTRY_FRAME_THRESHOLD` | `5` | Number of consecutive frames needed to confirm an entry |
| `EXIT_FRAME_THRESHOLD` | `10` | Number of consecutive missed frames before a user is treated as gone |
| `PROCESSING_FPS` | `10` | Target frame-processing rate for webcam streaming |


## Running The API

From the repo root with the virtual environment activated:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```


## Tests

Run the unit test suite with:

```powershell
python -m unittest discover -s tests -t . -p "test_*.py"
```

