from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.security import decode_token
from app.models.models import User
from datetime import datetime

# Support both HTTP Bearer header and Cookie-based authentication
security_bearer = HTTPBearer(auto_error=False)
security_cookie = APIKeyCookie(name="access_token", auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    cookie_token: str = Depends(security_cookie),
    db: Session = Depends(get_db)
) -> User:
    """Extracts, decodes, and validates the current user session from access tokens."""
    token = None
    if credentials:
        token = credentials.credentials
    elif cookie_token:
        token = cookie_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided."
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject index."
        )

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session could not be resolved."
        )

    # Validate active constraints
    if user.isDisabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled."
        )

    if user.isSuspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is currently suspended."
        )

    if user.lockedUntil and user.lockedUntil > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked. Try again later."
        )

    return user

def get_current_user_no_password_force(
    user: User = Depends(get_current_user)
) -> User:
    """Enforces that the user has changed their password before calling any core API routes."""
    if user.mustChangePassword:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="First-time login: Password change is required."
        )
    return user
