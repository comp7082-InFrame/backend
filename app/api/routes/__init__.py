from fastapi import APIRouter
from app.api.routes import enrollment, roster, attendance, streaming

api_router = APIRouter()

api_router.include_router(enrollment.router, prefix="/enrollment", tags=["enrollment"])
api_router.include_router(roster.router, prefix="/roster", tags=["roster"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
