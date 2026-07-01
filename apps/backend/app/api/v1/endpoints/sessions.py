from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import User, UserSession

router = APIRouter()

@router.get("")
def list_sessions(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    """Lists all active device/agent sessions for the logged-in user."""
    sessions = db.query(UserSession).filter_by(userId=current_user.id, isActive=True).all()
    return {
        "success": True,
        "sessions": [
            {
                "id": s.id,
                "deviceInfo": s.deviceInfo,
                "ipAddress": s.ipAddress,
                "lastActivity": s.lastActivity,
                "expiresAt": s.expiresAt,
                "createdAt": s.createdAt
            } for s in sessions
        ]
    }
