from fastapi import Depends, HTTPException, status
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import User, UserPermission, Permission
from sqlalchemy.orm import Session
from app.core.dependencies import get_db

class PermissionChecker:
    """RBAC dependency checking if the user is authorized with a specific permission."""
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(
        self,
        current_user: User = Depends(get_current_user_no_password_force),
        db: Session = Depends(get_db)
    ) -> User:
        # Master Admin bypasses permission checks
        if current_user.role.name == "MASTER_ADMIN":
            return current_user

        # Resolve explicit direct user permissions in database
        has_perm = db.query(UserPermission).join(Permission).filter(
            UserPermission.userId == current_user.id,
            Permission.name == self.required_permission
        ).first()

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Required permission not met."
            )

        return current_user

class RoleChecker:
    """RBAC dependency checking if the user holds an allowed role."""
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(get_current_user_no_password_force)
    ) -> User:
        if current_user.role.name in self.allowed_roles:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Role not authorized."
        )
