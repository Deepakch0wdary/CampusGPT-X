import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"
    PENDING = "PENDING"

class Role(Base):
    __tablename__ = "Role"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    description = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="role")

class Permission(Base):
    __tablename__ = "Permission"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    description = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_permissions = relationship("UserPermission", back_populates="permission", cascade="all, delete-orphan")

class UserPermission(Base):
    __tablename__ = "UserPermission"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    permissionId = Column(String(191), ForeignKey("Permission.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("userId", "permissionId", name="UserPermission_userId_permissionId_key"),)

    user = relationship("User", back_populates="userPermissions")
    permission = relationship("Permission", back_populates="user_permissions")

class User(Base):
    __tablename__ = "User"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    email = Column(String(191), unique=True, nullable=False, index=True)
    username = Column(String(191), unique=True, nullable=False, index=True)
    passwordHash = Column(String(191), nullable=False)
    name = Column(String(191), nullable=False)
    roleId = Column(String(191), ForeignKey("Role.id"), nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="SET NULL"), nullable=True)
    sectionId = Column(String(191), ForeignKey("Section.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(191), default="ACTIVE", nullable=False)
    
    isSuspended = Column(Boolean, default=False, nullable=False)
    isDisabled = Column(Boolean, default=False, nullable=False)
    mustChangePassword = Column(Boolean, default=True, nullable=False)
    failedLoginAttempts = Column(Integer, default=0, nullable=False)
    lockedUntil = Column(DateTime, nullable=True)
    verified = Column(Boolean, default=False, nullable=False)
    
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    section = relationship("Section", back_populates="users")
    profile = relationship("UserProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    
    userPermissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    refreshTokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    loginHistories = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    auditLogs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "UserProfile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    phoneNumber = Column(String(191), nullable=True)
    bio = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    avatarUrl = Column(String(191), nullable=True)
    designationId = Column(String(191), ForeignKey("Designation.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    designation = relationship("Designation", back_populates="user_profiles")

class Department(Base):
    __tablename__ = "Department"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="department")
    sections = relationship("Section", back_populates="department", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "Section"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="sections")
    users = relationship("User", back_populates="section")

class Designation(Base):
    __tablename__ = "Designation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    description = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_profiles = relationship("UserProfile", back_populates="designation")

class UserSession(Base):
    __tablename__ = "UserSession"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    deviceInfo = Column(String(191), nullable=True)
    ipAddress = Column(String(191), nullable=True)
    lastActivity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiresAt = Column(DateTime, nullable=False)
    isActive = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class RefreshToken(Base):
    __tablename__ = "RefreshToken"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    token = Column(String(191), unique=True, nullable=False)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refreshTokens")

class LoginHistory(Base):
    __tablename__ = "LoginHistory"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    ipAddress = Column(String(191), nullable=True)
    deviceInfo = Column(String(191), nullable=True)
    status = Column(String(191), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="loginHistories")

class AuditLog(Base):
    __tablename__ = "AuditLog"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(191), nullable=False)
    details = Column(Text, nullable=True)
    ipAddress = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="auditLogs")
