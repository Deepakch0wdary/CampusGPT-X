from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, sessions, audits

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(audits.router, prefix="/audits", tags=["Audits"])
