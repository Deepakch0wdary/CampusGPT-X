from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.rbac_middleware import PermissionChecker
from app.models.models import AuditLog

router = APIRouter()

@router.get("", dependencies=[Depends(PermissionChecker("audits:read"))])
def list_audit_logs(db: Session = Depends(get_db)):
    """Lists system action audit trails for compliance validation."""
    logs = db.query(AuditLog).order_by(AuditLog.createdAt.desc()).limit(100).all()
    return {
        "success": True,
        "logs": [
            {
                "id": l.id,
                "userId": l.userId,
                "user": l.user.username if l.user else "System",
                "action": l.action,
                "details": l.details,
                "ipAddress": l.ipAddress,
                "createdAt": l.createdAt
            } for l in logs
        ]
    }
