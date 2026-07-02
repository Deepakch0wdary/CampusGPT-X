import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, UniqueConstraint, Float
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
    section = relationship("Section", back_populates="users", foreign_keys=[sectionId])
    profile = relationship("UserProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    
    userPermissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    refreshTokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    loginHistories = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    auditLogs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    facultyAssignments = relationship("FacultyAssignment", back_populates="faculty", cascade="all, delete-orphan")
    advisedSections = relationship("Section", back_populates="facultyAdvisor", foreign_keys="[Section.facultyAdvisorId]")
    attendanceSummaries = relationship("StudentAttendanceSummary", back_populates="user", cascade="all, delete-orphan")
    results = relationship("StudentResult", back_populates="user", cascade="all, delete-orphan")
    assignments = relationship("StudentAssignment", back_populates="user", cascade="all, delete-orphan")
    certificates = relationship("StudentCertificate", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("StudentDocument", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("StudentNotification", back_populates="user", cascade="all, delete-orphan")
    facultyProfile = relationship("FacultyProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    assignmentDefs = relationship("AssignmentDef", back_populates="faculty", cascade="all, delete-orphan")
    facultyNotes = relationship("FacultyNotes", back_populates="faculty", cascade="all, delete-orphan")
    quizzes = relationship("FacultyQuiz", back_populates="faculty", cascade="all, delete-orphan")
    leaves = relationship("FacultyLeave", back_populates="faculty", cascade="all, delete-orphan")
    facultyNotifications = relationship("FacultyNotification", back_populates="faculty", cascade="all, delete-orphan")
    timetableEntries = relationship("TimetableEntry", back_populates="faculty")
    substituteRequestsOriginal = relationship("SubstituteFaculty", foreign_keys="[SubstituteFaculty.originalFacultyId]", back_populates="originalFaculty", cascade="all, delete-orphan")
    substituteRequestsSubstitute = relationship("SubstituteFaculty", foreign_keys="[SubstituteFaculty.substituteFacultyId]", back_populates="substituteFaculty", cascade="all, delete-orphan")
    timetableApprovals = relationship("TimetableApproval", back_populates="user", cascade="all, delete-orphan")
    attendanceSessions = relationship("AttendanceSession", back_populates="faculty", cascade="all, delete-orphan")
    attendanceRecords = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    attendanceCorrections = relationship("AttendanceCorrection", back_populates="student", cascade="all, delete-orphan")
    attendanceAudits = relationship("AttendanceAudit", back_populates="user", cascade="all, delete-orphan")
    defaulters = relationship("DefaulterList", back_populates="student", cascade="all, delete-orphan")
    qrScanLogs = relationship("QRScanLog", back_populates="student", cascade="all, delete-orphan")
    faceProfile = relationship("FaceProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    faceVerifications = relationship("FaceVerification", back_populates="user", cascade="all, delete-orphan")
    faceAudits = relationship("FaceAudit", back_populates="user", cascade="all, delete-orphan")
    faceApprovedRegistrations = relationship("FaceRegistration", back_populates="admin")
    assignmentsCreated = relationship("Assignment", back_populates="faculty", cascade="all, delete-orphan")
    assignmentSubmissions = relationship("AssignmentSubmission", back_populates="student", cascade="all, delete-orphan")
    assignmentFeedbacks = relationship("AssignmentFeedback", back_populates="faculty", cascade="all, delete-orphan")
    assignmentAudits = relationship("AssignmentAudit", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "UserProfile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    phoneNumber = Column(String(191), nullable=True)
    bio = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    avatarUrl = Column(String(191), nullable=True)
    designationId = Column(String(191), ForeignKey("Designation.id", ondelete="SET NULL"), nullable=True)
    usn = Column(String(191), unique=True, nullable=True)
    parentName = Column(String(191), nullable=True)
    parentPhone = Column(String(191), nullable=True)
    emergencyContact = Column(String(191), nullable=True)
    bloodGroup = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    designation = relationship("Designation", back_populates="user_profiles")

class Department(Base):
    __tablename__ = "Department"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    description = Column(String(191), nullable=True)
    deanHod = Column(String(191), nullable=True)
    email = Column(String(191), nullable=True)
    phone = Column(String(191), nullable=True)
    building = Column(String(191), nullable=True)
    status = Column(String(191), default="ACTIVE", nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="department")
    programs = relationship("Program", back_populates="department", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="department", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="department", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="department", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="department", cascade="all, delete-orphan")
    laboratories = relationship("Laboratory", back_populates="department", cascade="all, delete-orphan")
    facultyAssignments = relationship("FacultyAssignment", back_populates="department", cascade="all, delete-orphan")
    attendanceSessions = relationship("AttendanceSession", back_populates="department", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="department", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "Section"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    capacity = Column(Integer, nullable=False)
    semesterId = Column(String(191), ForeignKey("Semester.id", ondelete="CASCADE"), nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    programId = Column(String(191), ForeignKey("Program.id", ondelete="CASCADE"), nullable=False)
    facultyAdvisorId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="sections")
    semester = relationship("Semester", back_populates="sections")
    program = relationship("Program", back_populates="sections")
    facultyAdvisor = relationship("User", back_populates="advisedSections", foreign_keys=[facultyAdvisorId])
    academicYear = relationship("AcademicYear", back_populates="sections")
    users = relationship("User", back_populates="section", foreign_keys=[User.sectionId])
    facultyAssignments = relationship("FacultyAssignment", back_populates="section", cascade="all, delete-orphan")
    timetables = relationship("Timetable", back_populates="section", cascade="all, delete-orphan")
    attendanceSessions = relationship("AttendanceSession", back_populates="section", cascade="all, delete-orphan")
    defaulters = relationship("DefaulterList", back_populates="section", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="section", cascade="all, delete-orphan")

class AcademicYear(Base):
    __tablename__ = "AcademicYear"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)
    currentAcademicYear = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    semesters = relationship("Semester", back_populates="academicYear", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="academicYear")
    facultyAssignments = relationship("FacultyAssignment", back_populates="academicYear", cascade="all, delete-orphan")
    calendars = relationship("AcademicCalendar", back_populates="academicYear", cascade="all, delete-orphan")
    timetables = relationship("Timetable", back_populates="academicYear", cascade="all, delete-orphan")
    attendanceSessions = relationship("AttendanceSession", back_populates="academicYear", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="academicYear", cascade="all, delete-orphan")

class Program(Base):
    __tablename__ = "Program"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    description = Column(String(191), nullable=True)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="programs")
    courses = relationship("Course", back_populates="program", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="program", cascade="all, delete-orphan")
    semesters = relationship("Semester", back_populates="program", cascade="all, delete-orphan")
    attendanceSessions = relationship("AttendanceSession", back_populates="program", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="program", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "Course"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    code = Column(String(191), unique=True, nullable=False)
    name = Column(String(191), nullable=False)
    credits = Column(Integer, nullable=False)
    duration = Column(String(191), nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    programId = Column(String(191), ForeignKey("Program.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(191), nullable=True)
    status = Column(String(191), default="ACTIVE", nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="courses")
    program = relationship("Program", back_populates="courses")
    subjects = relationship("Subject", back_populates="course", cascade="all, delete-orphan")

class Semester(Base):
    __tablename__ = "Semester"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    semesterNumber = Column(Integer, nullable=False)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    programId = Column(String(191), ForeignKey("Program.id", ondelete="CASCADE"), nullable=False)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    currentSemester = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    academicYear = relationship("AcademicYear", back_populates="semesters")
    program = relationship("Program", back_populates="semesters")
    subjects = relationship("Subject", back_populates="semester", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="semester", cascade="all, delete-orphan")
    facultyAssignments = relationship("FacultyAssignment", back_populates="semester", cascade="all, delete-orphan")
    timetables = relationship("Timetable", back_populates="semester", cascade="all, delete-orphan")
    attendanceSessions = relationship("AttendanceSession", back_populates="semester", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="semester", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "Subject"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    code = Column(String(191), unique=True, nullable=False)
    name = Column(String(191), nullable=False)
    credits = Column(Integer, nullable=False)
    theoryHours = Column(Integer, default=0, nullable=False)
    labHours = Column(Integer, default=0, nullable=False)
    elective = Column(Boolean, default=False, nullable=False)
    mandatory = Column(Boolean, default=True, nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    semesterId = Column(String(191), ForeignKey("Semester.id", ondelete="CASCADE"), nullable=False)
    courseId = Column(String(191), ForeignKey("Course.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="subjects")
    semester = relationship("Semester", back_populates="subjects")
    course = relationship("Course", back_populates="subjects")
    facultyAssignments = relationship("FacultyAssignment", back_populates="subject", cascade="all, delete-orphan")
    attendanceSummaries = relationship("StudentAttendanceSummary", back_populates="subject", cascade="all, delete-orphan")
    results = relationship("StudentResult", back_populates="subject", cascade="all, delete-orphan")
    assignments = relationship("StudentAssignment", back_populates="subject", cascade="all, delete-orphan")
    assignmentDefs = relationship("AssignmentDef", back_populates="subject", cascade="all, delete-orphan")
    facultyNotes = relationship("FacultyNotes", back_populates="subject", cascade="all, delete-orphan")
    quizzes = relationship("FacultyQuiz", back_populates="subject", cascade="all, delete-orphan")
    timetableEntries = relationship("TimetableEntry", back_populates="subject")
    attendanceSessions = relationship("AttendanceSession", back_populates="subject", cascade="all, delete-orphan")
    defaulters = relationship("DefaulterList", back_populates="subject", cascade="all, delete-orphan")
    subjectAssignments = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")

class Building(Base):
    __tablename__ = "Building"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    floors = Column(Integer, nullable=False)
    description = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rooms = relationship("Room", back_populates="building", cascade="all, delete-orphan")

class Room(Base):
    __tablename__ = "Room"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    roomNumber = Column(String(191), unique=True, nullable=False)
    roomType = Column(String(191), default="CLASSROOM", nullable=False)
    capacity = Column(Integer, nullable=False)
    buildingId = Column(String(191), ForeignKey("Building.id", ondelete="CASCADE"), nullable=False)
    floor = Column(Integer, nullable=False)
    projector = Column(Boolean, default=False, nullable=False)
    smartBoard = Column(Boolean, default=False, nullable=False)
    airConditioning = Column(Boolean, default=False, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    building = relationship("Building", back_populates="rooms")
    department = relationship("Department", back_populates="rooms")
    timetableEntries = relationship("TimetableEntry", back_populates="room")

class Laboratory(Base):
    __tablename__ = "Laboratory"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    labName = Column(String(191), unique=True, nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    capacity = Column(Integer, nullable=False)
    systems = Column(Integer, default=0, nullable=False)
    software = Column(Text, nullable=True)
    labAssistant = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="laboratories")
    timetableEntries = relationship("TimetableEntry", back_populates="lab")

class FacultyAssignment(Base):
    __tablename__ = "FacultyAssignment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    sectionId = Column(String(191), ForeignKey("Section.id", ondelete="CASCADE"), nullable=False)
    semesterId = Column(String(191), ForeignKey("Semester.id", ondelete="CASCADE"), nullable=False)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("facultyId", "subjectId", "sectionId", "semesterId", "academicYearId", name="FacultyAssignment_unique_key"),)

    department = relationship("Department", back_populates="facultyAssignments")
    subject = relationship("Subject", back_populates="facultyAssignments")
    faculty = relationship("User", back_populates="facultyAssignments")
    section = relationship("Section", back_populates="facultyAssignments")
    semester = relationship("Semester", back_populates="facultyAssignments")
    academicYear = relationship("AcademicYear", back_populates="facultyAssignments")

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

class StudentAttendanceSummary(Base):
    __tablename__ = "StudentAttendanceSummary"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    totalClasses = Column(Integer, nullable=False, default=0)
    presentClasses = Column(Integer, nullable=False, default=0)
    percentage = Column(Float, nullable=False, default=0.0)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("userId", "subjectId", name="StudentAttendanceSummary_userId_subjectId_key"),)

    user = relationship("User", back_populates="attendanceSummaries")
    subject = relationship("Subject", back_populates="attendanceSummaries")

class StudentResult(Base):
    __tablename__ = "StudentResult"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    semesterNumber = Column(Integer, nullable=False)
    internalMarks = Column(Integer, nullable=False, default=0)
    externalMarks = Column(Integer, nullable=False, default=0)
    grade = Column(String(191), nullable=False)
    credits = Column(Integer, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("userId", "subjectId", name="StudentResult_userId_subjectId_key"),)

    user = relationship("User", back_populates="results")
    subject = relationship("Subject", back_populates="results")

class StudentAssignment(Base):
    __tablename__ = "StudentAssignment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(191), nullable=False)
    description = Column(Text, nullable=True)
    dueDate = Column(DateTime, nullable=False)
    submissionStatus = Column(String(191), nullable=False, default="PENDING")
    submissionUrl = Column(String(191), nullable=True)
    submittedAt = Column(DateTime, nullable=True)
    grade = Column(String(191), nullable=True)
    assignmentDefId = Column(String(191), ForeignKey("AssignmentDef.id", ondelete="CASCADE"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="assignments")
    subject = relationship("Subject", back_populates="assignments")
    assignmentDef = relationship("AssignmentDef", back_populates="studentSubmissions")

class StudentCertificate(Base):
    __tablename__ = "StudentCertificate"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    certificateType = Column(String(191), nullable=False)
    status = Column(String(191), nullable=False, default="PENDING")
    documentUrl = Column(String(191), nullable=True)
    requestedAt = Column(DateTime, default=datetime.utcnow)
    issuedAt = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="certificates")

class StudentDocument(Base):
    __tablename__ = "StudentDocument"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(191), nullable=False)
    documentUrl = Column(String(191), nullable=False)
    uploadedAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")

class StudentNotification(Base):
    __tablename__ = "StudentNotification"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(191), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(191), nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class FacultyProfile(Base):
    __tablename__ = "FacultyProfile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    employeeId = Column(String(191), unique=True, nullable=False)
    officeHours = Column(String(191), nullable=True)
    qualification = Column(String(191), nullable=True)
    experience = Column(String(191), nullable=True)
    researchArea = Column(String(191), nullable=True)
    specialization = Column(String(191), nullable=True)
    officeLocation = Column(String(191), nullable=True)
    emergencyContact = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="facultyProfile")

class AssignmentDef(Base):
    __tablename__ = "AssignmentDef"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    title = Column(String(191), nullable=False)
    description = Column(Text, nullable=True)
    dueDate = Column(DateTime, nullable=False)
    allowResubmission = Column(Boolean, default=False, nullable=False)
    attachmentUrl = Column(String(191), nullable=True)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject = relationship("Subject", back_populates="assignmentDefs")
    faculty = relationship("User", back_populates="assignmentDefs")
    studentSubmissions = relationship("StudentAssignment", back_populates="assignmentDef", cascade="all, delete-orphan")

class FacultyNotes(Base):
    __tablename__ = "FacultyNotes"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    title = Column(String(191), nullable=False)
    fileUrl = Column(String(191), nullable=False)
    fileType = Column(String(191), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject = relationship("Subject", back_populates="facultyNotes")
    faculty = relationship("User", back_populates="facultyNotes")

class FacultyQuiz(Base):
    __tablename__ = "FacultyQuiz"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    title = Column(String(191), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    questionsJson = Column(Text, nullable=False)
    status = Column(String(191), default="DRAFT", nullable=False)
    scheduledAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject = relationship("Subject", back_populates="quizzes")
    faculty = relationship("User", back_populates="quizzes")

class FacultyLeave(Base):
    __tablename__ = "FacultyLeave"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    leaveType = Column(String(191), nullable=False)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)
    requestedAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    faculty = relationship("User", back_populates="leaves")

class FacultyNotification(Base):
    __tablename__ = "FacultyNotification"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(191), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(191), nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("User", back_populates="facultyNotifications")

class AcademicCalendar(Base):
    __tablename__ = "AcademicCalendar"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    workingDays = Column(String(191), nullable=False) # JSON array like ["MONDAY"]
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    academicYear = relationship("AcademicYear", back_populates="calendars")
    events = relationship("CalendarEvent", back_populates="calendar", cascade="all, delete-orphan")

class CalendarEvent(Base):
    __tablename__ = "CalendarEvent"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    calendarId = Column(String(191), ForeignKey("AcademicCalendar.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(191), nullable=False)
    eventDate = Column(DateTime, nullable=False)
    type = Column(String(191), nullable=False) # HOLIDAY, EXAM_DAY, COLLEGE_EVENT, SPECIAL_WORKING_DAY
    description = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    calendar = relationship("AcademicCalendar", back_populates="events")

class TimeSlot(Base):
    __tablename__ = "TimeSlot"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    startTime = Column(String(191), nullable=False)
    endTime = Column(String(191), nullable=False)
    type = Column(String(191), nullable=False) # CLASS, BREAK, LAB, EXTRA
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    timetableEntries = relationship("TimetableEntry", back_populates="timeSlot", cascade="all, delete-orphan")
    attendanceSessions = relationship("AttendanceSession", back_populates="timeSlot", cascade="all, delete-orphan")

class Timetable(Base):
    __tablename__ = "Timetable"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    semesterId = Column(String(191), ForeignKey("Semester.id", ondelete="CASCADE"), nullable=False)
    sectionId = Column(String(191), ForeignKey("Section.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(191), default="DRAFT", nullable=False) # DRAFT, REVIEW_PENDING, PUBLISHED, ARCHIVED
    version = Column(Integer, default=1, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    academicYear = relationship("AcademicYear", back_populates="timetables")
    semester = relationship("Semester", back_populates="timetables")
    section = relationship("Section", back_populates="timetables")
    entries = relationship("TimetableEntry", back_populates="timetable", cascade="all, delete-orphan")
    approvals = relationship("TimetableApproval", back_populates="timetable", cascade="all, delete-orphan")

class TimetableEntry(Base):
    __tablename__ = "TimetableEntry"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    timetableId = Column(String(191), ForeignKey("Timetable.id", ondelete="CASCADE"), nullable=False)
    dayOfWeek = Column(String(191), nullable=False)
    timeSlotId = Column(String(191), ForeignKey("TimeSlot.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="SET NULL"), nullable=True)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    roomId = Column(String(191), ForeignKey("Room.id", ondelete="SET NULL"), nullable=True)
    labId = Column(String(191), ForeignKey("Laboratory.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    timetable = relationship("Timetable", back_populates="entries")
    timeSlot = relationship("TimeSlot", back_populates="timetableEntries")
    subject = relationship("Subject", back_populates="timetableEntries")
    faculty = relationship("User", back_populates="timetableEntries")
    room = relationship("Room", back_populates="timetableEntries")
    lab = relationship("Laboratory", back_populates="timetableEntries")
    substituteRequests = relationship("SubstituteFaculty", back_populates="timetableEntry", cascade="all, delete-orphan")

class SubstituteFaculty(Base):
    __tablename__ = "SubstituteFaculty"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    date = Column(DateTime, nullable=False)
    timetableEntryId = Column(String(191), ForeignKey("TimetableEntry.id", ondelete="CASCADE"), nullable=False)
    originalFacultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    substituteFacultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    timetableEntry = relationship("TimetableEntry", back_populates="substituteRequests")
    originalFaculty = relationship("User", foreign_keys=[originalFacultyId], back_populates="substituteRequestsOriginal")
    substituteFaculty = relationship("User", foreign_keys=[substituteFacultyId], back_populates="substituteRequestsSubstitute")

class TimetableApproval(Base):
    __tablename__ = "TimetableApproval"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    timetableId = Column(String(191), ForeignKey("Timetable.id", ondelete="CASCADE"), nullable=False)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(191), nullable=False)
    status = Column(String(191), nullable=False)
    remarks = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    timetable = relationship("Timetable", back_populates="approvals")
    user = relationship("User", back_populates="timetableApprovals")

class AttendanceSession(Base):
    __tablename__ = "AttendanceSession"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    programId = Column(String(191), ForeignKey("Program.id", ondelete="CASCADE"), nullable=False)
    semesterId = Column(String(191), ForeignKey("Semester.id", ondelete="CASCADE"), nullable=False)
    sectionId = Column(String(191), ForeignKey("Section.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    timeSlotId = Column(String(191), ForeignKey("TimeSlot.id", ondelete="SET NULL"), nullable=True)
    date = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    academicYear = relationship("AcademicYear", back_populates="attendanceSessions")
    department = relationship("Department", back_populates="attendanceSessions")
    program = relationship("Program", back_populates="attendanceSessions")
    semester = relationship("Semester", back_populates="attendanceSessions")
    section = relationship("Section", back_populates="attendanceSessions")
    subject = relationship("Subject", back_populates="attendanceSessions")
    timeSlot = relationship("TimeSlot", back_populates="attendanceSessions")
    faculty = relationship("User", back_populates="attendanceSessions")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")
    audits = relationship("AttendanceAudit", back_populates="session", cascade="all, delete-orphan")
    qrSession = relationship("QRSession", uselist=False, back_populates="attendanceSession", cascade="all, delete-orphan")
    faceAttendances = relationship("FaceAttendance", back_populates="attendanceSession", cascade="all, delete-orphan")

class AttendanceRecord(Base):
    __tablename__ = "AttendanceRecord"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    sessionId = Column(String(191), ForeignKey("AttendanceSession.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(191), nullable=False) # PRESENT, ABSENT, LATE, MEDICAL_LEAVE, ON_DUTY
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("User", back_populates="attendanceRecords")
    corrections = relationship("AttendanceCorrection", back_populates="record", cascade="all, delete-orphan")
    audits = relationship("AttendanceAudit", back_populates="record", cascade="all, delete-orphan")
    faceAttendance = relationship("FaceAttendance", uselist=False, back_populates="attendanceRecord", cascade="all, delete-orphan")

class AttendanceCorrection(Base):
    __tablename__ = "AttendanceCorrection"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    recordId = Column(String(191), ForeignKey("AttendanceRecord.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    requestedStatus = Column(String(191), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)
    comments = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    record = relationship("AttendanceRecord", back_populates="corrections")
    student = relationship("User", back_populates="attendanceCorrections")

class AttendanceAudit(Base):
    __tablename__ = "AttendanceAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    sessionId = Column(String(191), ForeignKey("AttendanceSession.id", ondelete="SET NULL"), nullable=True)
    recordId = Column(String(191), ForeignKey("AttendanceRecord.id", ondelete="SET NULL"), nullable=True)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False)
    ipAddress = Column(String(191), nullable=True)
    userAgent = Column(String(191), nullable=True)
    reason = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    session = relationship("AttendanceSession", back_populates="audits")
    record = relationship("AttendanceRecord", back_populates="audits")
    user = relationship("User", back_populates="attendanceAudits")

class DefaulterList(Base):
    __tablename__ = "DefaulterList"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    sectionId = Column(String(191), ForeignKey("Section.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    percentage = Column(Float, nullable=False)
    category = Column(String(191), nullable=False) # BELOW_75, BELOW_65, BELOW_50
    createdAt = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="defaulters")
    section = relationship("Section", back_populates="defaulters")
    student = relationship("User", back_populates="defaulters")

class QRSession(Base):
    __tablename__ = "QRSession"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    attendanceSessionId = Column(String(191), ForeignKey("AttendanceSession.id", ondelete="CASCADE"), unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    allowedRadius = Column(Float, default=100.0, nullable=False)
    intervalSeconds = Column(Integer, default=30, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attendanceSession = relationship("AttendanceSession", back_populates="qrSession")
    codes = relationship("QRCode", back_populates="qrSession", cascade="all, delete-orphan")
    scanLogs = relationship("QRScanLog", back_populates="qrSession", cascade="all, delete-orphan")

class QRCode(Base):
    __tablename__ = "QRCode"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    qrSessionId = Column(String(191), ForeignKey("QRSession.id", ondelete="CASCADE"), nullable=False)
    codeValue = Column(String(191), unique=True, nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    qrSession = relationship("QRSession", back_populates="codes")

class QRScanLog(Base):
    __tablename__ = "QRScanLog"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    qrSessionId = Column(String(191), ForeignKey("QRSession.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    scannedToken = Column(String(191), nullable=False)
    isSuccess = Column(Boolean, nullable=False)
    failReason = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    qrSession = relationship("QRSession", back_populates="scanLogs")
    student = relationship("User", back_populates="qrScanLogs")
    geoValidation = relationship("GeoValidation", uselist=False, back_populates="scanLog", cascade="all, delete-orphan")
    deviceValidation = relationship("DeviceValidation", uselist=False, back_populates="scanLog", cascade="all, delete-orphan")

class GeoValidation(Base):
    __tablename__ = "GeoValidation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    scanLogId = Column(String(191), ForeignKey("QRScanLog.id", ondelete="CASCADE"), unique=True, nullable=False)
    studentLatitude = Column(Float, nullable=False)
    studentLongitude = Column(Float, nullable=False)
    distanceMeters = Column(Float, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    scanLog = relationship("QRScanLog", back_populates="geoValidation")

class DeviceValidation(Base):
    __tablename__ = "DeviceValidation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    scanLogId = Column(String(191), ForeignKey("QRScanLog.id", ondelete="CASCADE"), unique=True, nullable=False)
    deviceId = Column(String(191), nullable=False)
    browser = Column(String(191), nullable=True)
    os = Column(String(191), nullable=True)
    ipAddress = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    scanLog = relationship("QRScanLog", back_populates="deviceValidation")

class FaceProfile(Base):
    __tablename__ = "FaceProfile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="faceProfile")
    embeddings = relationship("FaceEmbedding", back_populates="faceProfile", cascade="all, delete-orphan")
    verifications = relationship("FaceVerification", back_populates="faceProfile", cascade="all, delete-orphan")
    livenessChecks = relationship("LivenessCheck", back_populates="faceProfile", cascade="all, delete-orphan")
    spoofDetections = relationship("SpoofDetection", back_populates="faceProfile", cascade="all, delete-orphan")
    registrations = relationship("FaceRegistration", back_populates="faceProfile", cascade="all, delete-orphan")

class FaceEmbedding(Base):
    __tablename__ = "FaceEmbedding"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    faceProfileId = Column(String(191), ForeignKey("FaceProfile.id", ondelete="CASCADE"), nullable=False)
    angle = Column(String(191), nullable=False) # FRONT, LEFT, RIGHT, UP, DOWN
    embeddingJson = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    faceProfile = relationship("FaceProfile", back_populates="embeddings")

class FaceRegistration(Base):
    __tablename__ = "FaceRegistration"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    faceProfileId = Column(String(191), ForeignKey("FaceProfile.id", ondelete="CASCADE"), nullable=False)
    adminId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(191), nullable=False) # APPROVED, REJECTED
    rejectionReason = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    faceProfile = relationship("FaceProfile", back_populates="registrations")
    admin = relationship("User", back_populates="faceApprovedRegistrations")

class FaceVerification(Base):
    __tablename__ = "FaceVerification"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=True)
    faceProfileId = Column(String(191), ForeignKey("FaceProfile.id", ondelete="CASCADE"), nullable=True)
    isSuccess = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    verificationType = Column(String(191), nullable=False) # LOGIN, ATTENDANCE, GENERAL
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="faceVerifications")
    faceProfile = relationship("FaceProfile", back_populates="verifications")
    faceAttendance = relationship("FaceAttendance", uselist=False, back_populates="verification", cascade="all, delete-orphan")
    livenessChecks = relationship("LivenessCheck", back_populates="verification", cascade="all, delete-orphan")
    spoofDetections = relationship("SpoofDetection", back_populates="verification", cascade="all, delete-orphan")

class FaceAttendance(Base):
    __tablename__ = "FaceAttendance"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    attendanceSessionId = Column(String(191), ForeignKey("AttendanceSession.id", ondelete="CASCADE"), nullable=False)
    attendanceRecordId = Column(String(191), ForeignKey("AttendanceRecord.id", ondelete="CASCADE"), unique=True, nullable=False)
    verificationId = Column(String(191), ForeignKey("FaceVerification.id", ondelete="CASCADE"), unique=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    attendanceSession = relationship("AttendanceSession", back_populates="faceAttendances")
    attendanceRecord = relationship("AttendanceRecord", back_populates="faceAttendance")
    verification = relationship("FaceVerification", back_populates="faceAttendance")

class FaceAudit(Base):
    __tablename__ = "FaceAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False) # RESET_REGISTRATION, DELETE_EMBEDDING, APPROVE_BIOMETRICS, REJECT_BIOMETRICS
    ipAddress = Column(String(191), nullable=True)
    userAgent = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="faceAudits")

class LivenessCheck(Base):
    __tablename__ = "LivenessCheck"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    faceProfileId = Column(String(191), ForeignKey("FaceProfile.id", ondelete="CASCADE"), nullable=True)
    verificationId = Column(String(191), ForeignKey("FaceVerification.id", ondelete="CASCADE"), nullable=True)
    blinkCount = Column(Integer, default=0, nullable=False)
    smileDetected = Column(Boolean, default=False, nullable=False)
    headRotationDegrees = Column(Float, default=0.0, nullable=False)
    isPassed = Column(Boolean, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    faceProfile = relationship("FaceProfile", back_populates="livenessChecks")
    verification = relationship("FaceVerification", back_populates="livenessChecks")

class SpoofDetection(Base):
    __tablename__ = "SpoofDetection"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    faceProfileId = Column(String(191), ForeignKey("FaceProfile.id", ondelete="CASCADE"), nullable=True)
    verificationId = Column(String(191), ForeignKey("FaceVerification.id", ondelete="CASCADE"), nullable=True)
    spoofProbability = Column(Float, nullable=False)
    spoofCategory = Column(String(191), nullable=False) # PRINTED_PHOTO, PHONE_SCREEN, REPLAY_VIDEO, NONE
    isSpoofed = Column(Boolean, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    faceProfile = relationship("FaceProfile", back_populates="spoofDetections")
    verification = relationship("FaceVerification", back_populates="spoofDetections")

class Assignment(Base):
    __tablename__ = "Assignment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    programId = Column(String(191), ForeignKey("Program.id", ondelete="CASCADE"), nullable=False)
    semesterId = Column(String(191), ForeignKey("Semester.id", ondelete="CASCADE"), nullable=False)
    sectionId = Column(String(191), ForeignKey("Section.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    assignmentType = Column(String(191), nullable=False) # HOMEWORK, PROJECT, LAB, EXAM
    title = Column(String(191), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    dueDate = Column(DateTime, nullable=False)
    maxMarks = Column(Float, nullable=False)
    allowedFileTypes = Column(String(191), nullable=False) # e.g. "PDF,ZIP"
    maxUploadSizeMb = Column(Float, default=10.0, nullable=False)
    status = Column(String(191), default="DRAFT", nullable=False) # DRAFT, PUBLISHED
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    academicYear = relationship("AcademicYear", back_populates="assignments")
    department = relationship("Department", back_populates="assignments")
    program = relationship("Program", back_populates="assignments")
    semester = relationship("Semester", back_populates="assignments")
    section = relationship("Section", back_populates="assignments")
    subject = relationship("Subject", back_populates="subjectAssignments")
    faculty = relationship("User", back_populates="assignmentsCreated")
    files = relationship("AssignmentFile", back_populates="assignment", cascade="all, delete-orphan")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")
    audits = relationship("AssignmentAudit", back_populates="assignment")

class AssignmentFile(Base):
    __tablename__ = "AssignmentFile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    assignmentId = Column(String(191), ForeignKey("Assignment.id", ondelete="CASCADE"), nullable=False)
    fileName = Column(String(191), nullable=False)
    fileUrl = Column(String(191), nullable=False)
    fileSize = Column(Integer, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="files")

class AssignmentSubmission(Base):
    __tablename__ = "AssignmentSubmission"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    assignmentId = Column(String(191), ForeignKey("Assignment.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(191), default="SUBMITTED", nullable=False) # SUBMITTED, LATE, GRADED
    submittedAt = Column(DateTime, default=datetime.utcnow)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="assignmentSubmissions")
    attachments = relationship("SubmissionAttachment", back_populates="submission", cascade="all, delete-orphan")
    grade = relationship("AssignmentGrade", uselist=False, back_populates="submission", cascade="all, delete-orphan")
    feedback = relationship("AssignmentFeedback", back_populates="submission", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("assignmentId", "studentId", name="uq_assignment_student"),
    )

class SubmissionAttachment(Base):
    __tablename__ = "SubmissionAttachment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    submissionId = Column(String(191), ForeignKey("AssignmentSubmission.id", ondelete="CASCADE"), nullable=False)
    fileName = Column(String(191), nullable=False)
    fileUrl = Column(String(191), nullable=False)
    fileSize = Column(Integer, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    submission = relationship("AssignmentSubmission", back_populates="attachments")

class AssignmentFeedback(Base):
    __tablename__ = "AssignmentFeedback"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    submissionId = Column(String(191), ForeignKey("AssignmentSubmission.id", ondelete="CASCADE"), nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    comments = Column(Text, nullable=False)
    annotatedFileUrl = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    submission = relationship("AssignmentSubmission", back_populates="feedback")
    faculty = relationship("User", back_populates="assignmentFeedbacks")

class AssignmentGrade(Base):
    __tablename__ = "AssignmentGrade"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    submissionId = Column(String(191), ForeignKey("AssignmentSubmission.id", ondelete="CASCADE"), unique=True, nullable=False)
    marksObtained = Column(Float, nullable=False)
    isPublished = Column(Boolean, default=False, nullable=False)
    gradedAt = Column(DateTime, default=datetime.utcnow)

    submission = relationship("AssignmentSubmission", back_populates="grade")

class AssignmentAudit(Base):
    __tablename__ = "AssignmentAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    assignmentId = Column(String(191), ForeignKey("Assignment.id", ondelete="SET NULL"), nullable=True)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False) # CREATE_ASSIGNMENT, SUBMIT_ASSIGNMENT, GRADE_ASSIGNMENT, PUBLISH_GRADES
    ipAddress = Column(String(191), nullable=True)
    userAgent = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="audits")
    user = relationship("User", back_populates="assignmentAudits")



