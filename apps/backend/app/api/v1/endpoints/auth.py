from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.core.dependencies import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.auth_middleware import get_current_user
from app.models.models import User, RefreshToken, UserSession, LoginHistory, AuditLog

router = APIRouter()

# ----------------------------------------------------
# Request / Response Schemas
# ----------------------------------------------------
class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ----------------------------------------------------
# Endpoints
# ----------------------------------------------------
@router.post("/login")
def login(request: Request, payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Verifies credentials, manages failed logs, account locks, and spawns JWTs."""
    user = db.query(User).filter(
        (User.email == payload.username_or_email) | (User.username == payload.username_or_email)
    ).first()

    ip_address = request.client.host if request.client else None
    device_info = request.headers.get("user-agent", "Unknown Device")

    if not user:
        # Failed attempts can't lock non-existent accounts, just return standard 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    # Brute-force account lock check
    if user.lockedUntil and user.lockedUntil > datetime.utcnow():
        lock_seconds = int((user.lockedUntil - datetime.utcnow()).total_seconds())
        # Record lock failure
        hist = LoginHistory(id=str(uuid.uuid4()), userId=user.id, ipAddress=ip_address, deviceInfo=device_info, status="LOCKED")
        db.add(hist)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account temporarily locked. Try again in {lock_seconds}s."
        )

    if user.isDisabled or user.isSuspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is currently suspended or disabled."
        )

    if not verify_password(payload.password, user.passwordHash):
        # Handle incorrect password logic
        user.failedLoginAttempts += 1
        hist_status = "FAILED_PASSWORD"
        
        if user.failedLoginAttempts >= 5:
            user.lockedUntil = datetime.utcnow() + timedelta(minutes=15)
            hist_status = "FAILED_LOCKED"
            print(f"[!] User {user.username} locked due to consecutive failures.")
        
        hist = LoginHistory(id=str(uuid.uuid4()), userId=user.id, ipAddress=ip_address, deviceInfo=device_info, status=hist_status)
        db.add(hist)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    # Correct credentials - reset tracking state
    user.failedLoginAttempts = 0
    user.lockedUntil = None

    # Track login history
    hist = LoginHistory(id=str(uuid.uuid4()), userId=user.id, ipAddress=ip_address, deviceInfo=device_info, status="SUCCESS")
    db.add(hist)

    # Spawn UserSession
    session_id = str(uuid.uuid4())
    session = UserSession(
        id=session_id,
        userId=user.id,
        deviceInfo=device_info,
        ipAddress=ip_address,
        expiresAt=datetime.utcnow() + timedelta(hours=24),
        isActive=True
    )
    db.add(session)

    # Create Access & Refresh Tokens
    access_token = create_access_token(subject=user.id)
    refresh_token_str = create_refresh_token(subject=user.id)

    # Save Refresh Token
    db_refresh = RefreshToken(
        id=str(uuid.uuid4()),
        token=refresh_token_str,
        userId=user.id,
        expiresAt=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_refresh)

    # Audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        userId=user.id,
        action="LOGIN_SUCCESS",
        details=f"Login verified from IP {ip_address} using device {device_info}.",
        ipAddress=ip_address
    )
    db.add(audit)
    db.commit()

    # Set secure HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax",
        max_age=900  # 15 mins
    )

    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "must_change_password": user.mustChangePassword,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "role": user.role.name
        }
    }

@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes the current user's session states."""
    # Revoke sessions
    db.query(UserSession).filter_by(userId=current_user.id, isActive=True).update({"isActive": False})
    # Revoke refresh tokens
    db.query(RefreshToken).filter_by(userId=current_user.id, revoked=False).update({"revoked": True})
    
    # Audit log
    audit = AuditLog(id=str(uuid.uuid4()), userId=current_user.id, action="LOGOUT")
    db.add(audit)
    db.commit()

    # Clear authorization cookies
    response.delete_cookie("access_token")
    return {"success": True, "message": "Successfully logged out."}

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    """Validates refresh token, rotates tokens, and distributes replacements."""
    # Get refresh token from header
    auth_header = request.headers.get("authorization")
    refresh_token = None
    if auth_header and auth_header.startswith("Bearer "):
        refresh_token = auth_header.replace("Bearer ", "", 1)
        
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required."
        )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id = payload.get("sub")
    db_token = db.query(RefreshToken).filter_by(token=refresh_token, revoked=False).first()
    
    if not db_token or db_token.expiresAt < datetime.utcnow():
        # Revoke all tokens for this user in case of reuse breach
        if db_token:
            db.query(RefreshToken).filter_by(userId=user_id).update({"revoked": True})
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked or expired."
        )

    # Rotate token: revoke current, issue new
    db_token.revoked = True

    new_access = create_access_token(subject=user_id)
    new_refresh = create_refresh_token(subject=user_id)

    db_new_refresh = RefreshToken(
        id=str(uuid.uuid4()),
        token=new_refresh,
        userId=user_id,
        expiresAt=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_new_refresh)
    db.commit()

    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=900
    )

    return {
        "success": True,
        "access_token": new_access,
        "refresh_token": new_refresh
    }

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Simulates email verification triggers for password retrieval."""
    user = db.query(User).filter_by(email=payload.email).first()
    if not user:
        # Avoid user enumeration attacks: return success anyway
        return {"success": True, "message": "Verification instructions emitted if account exists."}

    # Simulate token distribution (mock email flow)
    reset_token = str(uuid.uuid4())
    # Save action to Audit Log for developer extraction
    audit = AuditLog(
        id=str(uuid.uuid4()),
        userId=user.id,
        action="FORGOT_PASSWORD_REQUEST",
        details=f"Reset token spawned: {reset_token}"
    )
    db.add(audit)
    db.commit()

    print(f"\n[MOCK EMAIL SYSTEM] To reset user password for {user.email}, use token: {reset_token}\n")

    return {
        "success": True, 
        "message": "Verification instructions emitted if account exists.",
        "mock_token": reset_token  # Returned for easy testing
    }

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Applies password change if reset token validation succeeds."""
    # Find Reset action audit log containing the target token
    audit = db.query(AuditLog).filter(
        AuditLog.action == "FORGOT_PASSWORD_REQUEST",
        AuditLog.details.like(f"%{payload.token}%")
    ).first()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    # Limit token validity to 30 minutes
    if datetime.utcnow() - audit.createdAt > timedelta(minutes=30):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired."
        )

    user = db.query(User).filter_by(id=audit.userId).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not resolved."
        )

    user.passwordHash = get_password_hash(payload.new_password)
    user.mustChangePassword = False  # Reset force conditions if reset by email
    
    # Consume token
    db.delete(audit)
    
    # Log reset success
    new_audit = AuditLog(id=str(uuid.uuid4()), userId=user.id, action="PASSWORD_RESET_SUCCESS")
    db.add(new_audit)
    db.commit()

    return {"success": True, "message": "Password changed successfully."}

@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Applies password update for the currently authenticated user session."""
    if not verify_password(payload.current_password, current_user.passwordHash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )

    current_user.passwordHash = get_password_hash(payload.new_password)
    current_user.mustChangePassword = False

    audit = AuditLog(id=str(uuid.uuid4()), userId=current_user.id, action="PASSWORD_CHANGE")
    db.add(audit)
    db.commit()

    return {"success": True, "message": "Password updated successfully."}
