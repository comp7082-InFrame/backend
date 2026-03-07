import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine, Base, SessionLocal
from app.api.routes import api_router
from app.api.routes.streaming import router as streaming_router
from app.api.deps import init_services
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting up...")

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize face recognition services
    db = SessionLocal()
    try:
        init_services(db)
        logger.info("Services initialized successfully")
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
