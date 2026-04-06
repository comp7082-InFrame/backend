import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy import inspect

from app.database import engine, SessionLocal
from app.api.routes import api_router
from app.api.routes.streaming import router as streaming_router
from app.api.deps import init_services
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

REQUIRED_TABLES = frozenset(
    {
        "attendance_record",
        "attendance_session",
        "building",
        "campus",
        "class",
        "course",
        "recognition_history",
        "room",
        "scheduled_class_teacher",
        "student_course",
        "term",
        "users",
    }
)
REQUIRED_VIEWS = frozenset(
    {
        "class_users",
        "student_schedule",
        "teacher_class_schedule_view",
    }
)


def verify_schema_objects(db_engine) -> None:
    schema_inspector = inspect(db_engine)
    existing_tables = set(schema_inspector.get_table_names())
    existing_views = set(schema_inspector.get_view_names())

    missing_tables = sorted(REQUIRED_TABLES - existing_tables)
    missing_views = sorted(REQUIRED_VIEWS - existing_views)
    if not missing_tables and not missing_views:
        return

    missing_parts = []
    if missing_tables:
        missing_parts.append(f"tables: {', '.join(missing_tables)}")
    if missing_views:
        missing_parts.append(f"views: {', '.join(missing_views)}")

    raise RuntimeError(
        "Database schema is not ready. Missing "
        + "; ".join(missing_parts)
        + ". Run the Supabase migrations before starting the backend."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting up...")

    # Verify schema is present instead of mutating it at runtime.
    verify_schema_objects(engine)

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize face recognition services
    db = SessionLocal()
    try:
        from app.models import AttendanceSession

        latest_session = (
            db.query(AttendanceSession)
            .order_by(AttendanceSession.id.desc())
            .first()
        )
        if latest_session is not None:
            init_services(db, class_id=latest_session.class_id)
            logger.info("Services initialized for session %s", latest_session.id)
        else:
            init_services(db)
            logger.info("Services initialized with global roster")
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Facial Recognition Attendance System",
    description="Real-time attendance tracking using facial recognition",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Include WebSocket route (no prefix)
app.include_router(streaming_router)

# Serve uploaded photos
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "Facial Recognition Attendance System API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
