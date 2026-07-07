import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, UniqueConstraint, Float, Numeric
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
    examsCreated = relationship("Exam", back_populates="creator", cascade="all, delete-orphan")
    examsInvigilated = relationship("ExamSchedule", foreign_keys="[ExamSchedule.invigilatorId]", back_populates="invigilator")
    examsSuperintended = relationship("ExamSchedule", foreign_keys="[ExamSchedule.chiefSuperintendentId]", back_populates="chiefSuperintendent")
    examsObserved = relationship("ExamSchedule", foreign_keys="[ExamSchedule.observerId]", back_populates="observer")
    examInvigilatorDuties = relationship("ExamInvigilator", back_populates="faculty", cascade="all, delete-orphan")
    hallTickets = relationship("HallTicket", back_populates="student", cascade="all, delete-orphan")
    approvedQuestionPapers = relationship("QuestionPaper", back_populates="approvedBy")
    examAudits = relationship("ExamAudit", back_populates="user", cascade="all, delete-orphan")
    resultsCompiled = relationship("Result", back_populates="student", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="student", cascade="all, delete-orphan")
    revaluationRequests = relationship("RevaluationRequest", foreign_keys="[RevaluationRequest.studentId]", back_populates="student", cascade="all, delete-orphan")
    revaluationApproved = relationship("RevaluationRequest", foreign_keys="[RevaluationRequest.facultyId]", back_populates="faculty")
    meritList = relationship("MeritList", back_populates="student", cascade="all, delete-orphan")
    resultAudits = relationship("ResultAudit", back_populates="user", cascade="all, delete-orphan")

    parentProfile = relationship("ParentProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    parentLinks = relationship("ParentStudentLink", back_populates="student", cascade="all, delete-orphan")
    sentParentMessages = relationship("ParentMessage", foreign_keys="[ParentMessage.senderId]", back_populates="sender", cascade="all, delete-orphan")
    receivedParentMessages = relationship("ParentMessage", foreign_keys="[ParentMessage.receiverId]", back_populates="receiver", cascade="all, delete-orphan")
    parentAudits = relationship("ParentAudit", back_populates="user", cascade="all, delete-orphan")

    libraryMembership = relationship("LibraryMembership", uselist=False, back_populates="user", cascade="all, delete-orphan")
    loansIssued = relationship("BookLoan", foreign_keys="[BookLoan.issuedBy]", back_populates="issuer", cascade="all, delete-orphan")
    renewalsCreated = relationship("LoanRenewal", foreign_keys="[LoanRenewal.renewedBy]", back_populates="renewer", cascade="all, delete-orphan")
    finesWaived = relationship("LibraryFine", foreign_keys="[LibraryFine.waivedBy]", back_populates="waiverUser", cascade="all, delete-orphan")
    inventoryEvents = relationship("LibraryInventoryEvent", foreign_keys="[LibraryInventoryEvent.reportedBy]", back_populates="reporter", cascade="all, delete-orphan")
    acquisitionRequests = relationship("BookAcquisitionRequest", foreign_keys="[BookAcquisitionRequest.requestedBy]", back_populates="requester", cascade="all, delete-orphan")
    acquisitionApprovals = relationship("BookAcquisitionRequest", foreign_keys="[BookAcquisitionRequest.approvedBy]", back_populates="approver", cascade="all, delete-orphan")
    inventoryAudits = relationship("InventoryAudit", foreign_keys="[InventoryAudit.conductedBy]", back_populates="conductor", cascade="all, delete-orphan")
    libraryAudits = relationship("LibraryAudit", back_populates="user", cascade="all, delete-orphan")

    hostelApplications = relationship("HostelApplication", foreign_keys="[HostelApplication.studentId]", back_populates="student", cascade="all, delete-orphan")
    reviewedHostelApplications = relationship("HostelApplication", foreign_keys="[HostelApplication.reviewedBy]", back_populates="reviewer", cascade="all, delete-orphan")
    hostelAllocations = relationship("HostelAllocation", foreign_keys="[HostelAllocation.studentId]", back_populates="student", cascade="all, delete-orphan")
    allocatedHostels = relationship("HostelAllocation", foreign_keys="[HostelAllocation.allocatedBy]", back_populates="allocator", cascade="all, delete-orphan")
    wardenAssignments = relationship("HostelWardenAssignment", back_populates="warden", cascade="all, delete-orphan")
    visitorRequests = relationship("HostelVisitor", foreign_keys="[HostelVisitor.studentId]", back_populates="student", cascade="all, delete-orphan")
    approvedVisitors = relationship("HostelVisitor", foreign_keys="[HostelVisitor.approvedBy]", back_populates="approver", cascade="all, delete-orphan")
    hostelComplaints = relationship("HostelComplaint", foreign_keys="[HostelComplaint.studentId]", back_populates="student", cascade="all, delete-orphan")
    assignedComplaints = relationship("HostelComplaint", foreign_keys="[HostelComplaint.assignedTo]", back_populates="assignee", cascade="all, delete-orphan")
    hostelComplaintComments = relationship("HostelComplaintComment", back_populates="user", cascade="all, delete-orphan")
    assignedMaintenance = relationship("HostelMaintenanceRequest", back_populates="assignee", cascade="all, delete-orphan")
    hostelLeaveRequests = relationship("HostelLeaveRequest", back_populates="student", cascade="all, delete-orphan")
    gatePasses = relationship("HostelGatePass", back_populates="student", cascade="all, delete-orphan")
    messSubscriptions = relationship("MessSubscription", back_populates="student", cascade="all, delete-orphan")
    messAttendances = relationship("MessAttendance", back_populates="student", cascade="all, delete-orphan")
    hostelFines = relationship("HostelFine", foreign_keys="[HostelFine.studentId]", back_populates="student", cascade="all, delete-orphan")
    waivedHostelFines = relationship("HostelFine", foreign_keys="[HostelFine.waivedBy]", back_populates="waiverUser", cascade="all, delete-orphan")
    reportedIncidents = relationship("HostelIncident", back_populates="reporter", cascade="all, delete-orphan")
    hostelAudits = relationship("HostelAudit", back_populates="user", cascade="all, delete-orphan")
    transportDriverProfile = relationship("TransportDriverProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    transportStaffProfile = relationship("TransportStaffProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    transportApplications = relationship("TransportApplication", foreign_keys="[TransportApplication.applicantUserId]", back_populates="applicant", cascade="all, delete-orphan")
    reviewedTransportApplications = relationship("TransportApplication", foreign_keys="[TransportApplication.reviewedBy]", back_populates="reviewer")
    transportSubscriptions = relationship("TransportSubscription", foreign_keys="[TransportSubscription.userId]", back_populates="user", cascade="all, delete-orphan")
    approvedSubscriptions = relationship("TransportSubscription", foreign_keys="[TransportSubscription.approvedBy]", back_populates="approver")
    allocatedSeats = relationship("TransportSeatAllocation", back_populates="allocator")
    transportPasses = relationship("TransportPass", back_populates="user", cascade="all, delete-orphan")
    boardedTrips = relationship("TransportBoarding", foreign_keys="[TransportBoarding.userId]", back_populates="user", cascade="all, delete-orphan")
    verifiedBoardings = relationship("TransportBoarding", foreign_keys="[TransportBoarding.verifiedBy]", back_populates="verifier")
    recordedFuelLogs = relationship("TransportFuelLog", back_populates="recorder")
    reportedTransportIncidents = relationship("TransportIncident", back_populates="reporter")
    transportAudits = relationship("TransportAudit", back_populates="user", cascade="all, delete-orphan")


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
    exams = relationship("Exam", back_populates="department", cascade="all, delete-orphan")
    resultAnalytics = relationship("ResultAnalytics", back_populates="department", cascade="all, delete-orphan")

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
    exams = relationship("Exam", back_populates="section", cascade="all, delete-orphan")

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
    exams = relationship("Exam", back_populates="academicYear", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="academicYear", cascade="all, delete-orphan")
    gradeSchemes = relationship("GradeScheme", back_populates="academicYear", cascade="all, delete-orphan")

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
    exams = relationship("Exam", back_populates="program", cascade="all, delete-orphan")
    gradeSchemes = relationship("GradeScheme", back_populates="program", cascade="all, delete-orphan")

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
    exams = relationship("Exam", back_populates="semester", cascade="all, delete-orphan")

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
    subjectExams = relationship("Exam", back_populates="subject", cascade="all, delete-orphan")
    resultDetails = relationship("ResultDetail", back_populates="subject", cascade="all, delete-orphan")

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
    examSchedules = relationship("ExamSchedule", back_populates="room")

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
    examSchedules = relationship("ExamSchedule", back_populates="lab")

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

class Exam(Base):
    __tablename__ = "Exam"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    examName = Column(String(191), nullable=False)
    examType = Column(String(191), nullable=False) # INTERNAL, MID, LAB, PRACTICAL, SEMESTER, SUPPLEMENTARY, IMPROVEMENT, CUSTOM
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    programId = Column(String(191), ForeignKey("Program.id", ondelete="CASCADE"), nullable=False)
    semesterId = Column(String(191), ForeignKey("Semester.id", ondelete="CASCADE"), nullable=False)
    sectionId = Column(String(191), ForeignKey("Section.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    examDate = Column(DateTime, nullable=False)
    startTime = Column(String(191), nullable=False) # HH:MM
    endTime = Column(String(191), nullable=False) # HH:MM
    durationMinutes = Column(Integer, nullable=False)
    maxMarks = Column(Float, nullable=False)
    passingMarks = Column(Float, nullable=False)
    instructions = Column(Text, nullable=True)
    status = Column(String(191), default="ACTIVE", nullable=False) # ACTIVE, CANCELLED, COMPLETED
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    academicYear = relationship("AcademicYear", back_populates="exams")
    department = relationship("Department", back_populates="exams")
    program = relationship("Program", back_populates="exams")
    semester = relationship("Semester", back_populates="exams")
    section = relationship("Section", back_populates="exams")
    subject = relationship("Subject", back_populates="subjectExams")
    creator = relationship("User", back_populates="examsCreated")
    schedules = relationship("ExamSchedule", back_populates="exam", cascade="all, delete-orphan")
    hallTickets = relationship("HallTicket", back_populates="exam", cascade="all, delete-orphan")
    questionPapers = relationship("QuestionPaper", back_populates="exam", cascade="all, delete-orphan")
    audits = relationship("ExamAudit", back_populates="exam")

class ExamSchedule(Base):
    __tablename__ = "ExamSchedule"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    examId = Column(String(191), ForeignKey("Exam.id", ondelete="CASCADE"), nullable=False)
    roomId = Column(String(191), ForeignKey("Room.id", ondelete="SET NULL"), nullable=True)
    labId = Column(String(191), ForeignKey("Laboratory.id", ondelete="SET NULL"), nullable=True)
    invigilatorId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    chiefSuperintendentId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    observerId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exam = relationship("Exam", back_populates="schedules")
    room = relationship("Room", back_populates="examSchedules")
    lab = relationship("Laboratory", back_populates="examSchedules")
    invigilator = relationship("User", foreign_keys=[invigilatorId], back_populates="examsInvigilated")
    chiefSuperintendent = relationship("User", foreign_keys=[chiefSuperintendentId], back_populates="examsSuperintended")
    observer = relationship("User", foreign_keys=[observerId], back_populates="examsObserved")

class ExamRoom(Base):
    __tablename__ = "ExamRoom"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    blockName = Column(String(191), nullable=False)
    roomNumber = Column(String(191), nullable=False)
    totalBenches = Column(Integer, nullable=False)
    seatsPerBench = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

class ExamInvigilator(Base):
    __tablename__ = "ExamInvigilator"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    roomNumber = Column(String(191), nullable=False)
    blockName = Column(String(191), nullable=False)
    shift = Column(String(191), nullable=False) # MORNING, AFTERNOON
    attendanceStatus = Column(String(191), default="PRESENT", nullable=False) # PRESENT, ABSENT
    dutyReport = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("User", back_populates="examInvigilatorDuties")

class HallTicket(Base):
    __tablename__ = "HallTicket"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    hallTicketNumber = Column(String(191), unique=True, nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    examId = Column(String(191), ForeignKey("Exam.id", ondelete="CASCADE"), nullable=False)
    qrCodeUrl = Column(String(191), nullable=True)
    examCenter = Column(String(191), nullable=False)
    seatNumber = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="hallTickets")
    exam = relationship("Exam", back_populates="hallTickets")
    seatAllocations = relationship("SeatAllocation", back_populates="hallTicket", cascade="all, delete-orphan")

class SeatAllocation(Base):
    __tablename__ = "SeatAllocation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    hallTicketId = Column(String(191), ForeignKey("HallTicket.id", ondelete="CASCADE"), nullable=False)
    blockName = Column(String(191), nullable=False)
    roomNumber = Column(String(191), nullable=False)
    benchNumber = Column(Integer, nullable=False)
    seatNumber = Column(String(191), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    hallTicket = relationship("HallTicket", back_populates="seatAllocations")

    __table_args__ = (
        UniqueConstraint("blockName", "roomNumber", "benchNumber", "seatNumber", name="uq_seat_bench_room"),
    )

class QuestionPaper(Base):
    __tablename__ = "QuestionPaper"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    examId = Column(String(191), ForeignKey("Exam.id", ondelete="CASCADE"), nullable=False)
    fileUrl = Column(String(191), nullable=False)
    fileName = Column(String(191), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(191), default="PENDING", nullable=False) # PENDING, APPROVED, REJECTED
    approvedById = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    exam = relationship("Exam", back_populates="questionPapers")
    approvedBy = relationship("User", back_populates="approvedQuestionPapers")

class ExamAudit(Base):
    __tablename__ = "ExamAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    examId = Column(String(191), ForeignKey("Exam.id", ondelete="SET NULL"), nullable=True)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False) # CREATE_EXAM, UPDATE_EXAM, SCHEDULE_EXAM, DOWNLOAD_HALL_TICKET, UPLOAD_QUESTION_PAPER, APPROVE_QUESTION_PAPER
    ipAddress = Column(String(191), nullable=True)
    userAgent = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    exam = relationship("Exam", back_populates="audits")
    user = relationship("User", back_populates="examAudits")

class Result(Base):
    __tablename__ = "Result"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    semesterNumber = Column(Integer, nullable=False)
    sgpa = Column(Float, default=0.0, nullable=False)
    cgpa = Column(Float, default=0.0, nullable=False)
    totalMarks = Column(Float, default=0.0, nullable=False)
    percentage = Column(Float, default=0.0, nullable=False)
    creditsEarned = Column(Integer, default=0, nullable=False)
    status = Column(String(191), default="DRAFT", nullable=False) # DRAFT, DEPT_REVIEW, EXAM_CELL_APPROVED, PUBLISHED, ARCHIVED, ROLLBACK
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("User", back_populates="resultsCompiled")
    academicYear = relationship("AcademicYear", back_populates="results")
    details = relationship("ResultDetail", back_populates="result", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("studentId", "academicYearId", "semesterNumber", name="uq_student_ay_sem"),
    )

class ResultDetail(Base):
    __tablename__ = "ResultDetail"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    resultId = Column(String(191), ForeignKey("Result.id", ondelete="CASCADE"), nullable=False)
    subjectId = Column(String(191), ForeignKey("Subject.id", ondelete="CASCADE"), nullable=False)
    internalMarks = Column(Float, default=0.0, nullable=False)
    assignmentMarks = Column(Float, default=0.0, nullable=False)
    labMarks = Column(Float, default=0.0, nullable=False)
    practicalMarks = Column(Float, default=0.0, nullable=False)
    projectMarks = Column(Float, default=0.0, nullable=False)
    semesterExamMarks = Column(Float, default=0.0, nullable=False)
    graceMarks = Column(Float, default=0.0, nullable=False)
    moderationMarks = Column(Float, default=0.0, nullable=False)
    totalMarks = Column(Float, default=0.0, nullable=False)
    grade = Column(String(191), default="F", nullable=False)
    gradePoint = Column(Float, default=0.0, nullable=False)
    passFail = Column(String(191), default="FAIL", nullable=False) # PASS, FAIL
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    result = relationship("Result", back_populates="details")
    subject = relationship("Subject", back_populates="resultDetails")
    revaluationRequests = relationship("RevaluationRequest", back_populates="resultDetail", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("resultId", "subjectId", name="uq_result_subject"),
    )

class GradeScheme(Base):
    __tablename__ = "GradeScheme"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    academicYearId = Column(String(191), ForeignKey("AcademicYear.id", ondelete="CASCADE"), nullable=False)
    programId = Column(String(191), ForeignKey("Program.id", ondelete="CASCADE"), nullable=False)
    gradeScale = Column(String(191), default="10-POINT", nullable=False) # 10-POINT, 4-POINT
    creditSystem = Column(String(191), default="CHOICE_BASED", nullable=False)
    graceRules = Column(Text, nullable=True)
    passingMarks = Column(Float, default=40.0, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    academicYear = relationship("AcademicYear", back_populates="gradeSchemes")
    program = relationship("Program", back_populates="gradeSchemes")
    boundaries = relationship("GradeBoundary", back_populates="gradeScheme", cascade="all, delete-orphan")

class GradeBoundary(Base):
    __tablename__ = "GradeBoundary"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    gradeSchemeId = Column(String(191), ForeignKey("GradeScheme.id", ondelete="CASCADE"), nullable=False)
    letterGrade = Column(String(191), nullable=False)
    gradePoint = Column(Float, nullable=False)
    minPercentage = Column(Float, nullable=False)
    maxPercentage = Column(Float, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    gradeScheme = relationship("GradeScheme", back_populates="boundaries")

class Transcript(Base):
    __tablename__ = "Transcript"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    transcriptType = Column(String(191), nullable=False) # SEMESTER, CONSOLIDATED
    semesterNumber = Column(Integer, nullable=True)
    qrCodeValue = Column(String(191), unique=True, nullable=False)
    digitalSignature = Column(String(191), nullable=False)
    issueDate = Column(DateTime, default=datetime.utcnow, nullable=False)
    isVerified = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="transcripts")

class RevaluationRequest(Base):
    __tablename__ = "RevaluationRequest"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    resultDetailId = Column(String(191), ForeignKey("ResultDetail.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    requestType = Column(String(191), nullable=False) # REVALUATION, PHOTOCOPY
    status = Column(String(191), default="PENDING", nullable=False) # PENDING, APPROVED, REJECTED
    paymentStatus = Column(String(191), default="PENDING", nullable=False) # PENDING, PAID
    remarks = Column(Text, nullable=True)
    originalMarks = Column(Float, nullable=False)
    updatedMarks = Column(Float, nullable=True)
    facultyId = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resultDetail = relationship("ResultDetail", back_populates="revaluationRequests")
    student = relationship("User", foreign_keys=[studentId], back_populates="revaluationRequests")
    faculty = relationship("User", foreign_keys=[facultyId], back_populates="revaluationApproved")

class ResultAnalytics(Base):
    __tablename__ = "ResultAnalytics"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    departmentId = Column(String(191), ForeignKey("Department.id", ondelete="CASCADE"), nullable=False)
    semesterNumber = Column(Integer, nullable=False)
    passPercentage = Column(Float, nullable=False)
    topPerformers = Column(Text, nullable=False)
    backlogCount = Column(Integer, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="resultAnalytics")

class MeritList(Base):
    __tablename__ = "MeritList"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    semesterNumber = Column(Integer, nullable=False)
    departmentRank = Column(Integer, nullable=False)
    semesterRank = Column(Integer, nullable=False)
    universityRank = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=False)
    isGoldMedalEligible = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="meritList")

class ResultAudit(Base):
    __tablename__ = "ResultAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    resultId = Column(String(191), nullable=True)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False) # MARKS_ENTRY, MARKS_MODERATION, RESULT_PUBLISH, TRANSCRIPT_GEN, REVALUATION_REQUEST, REVALUATION_APPROVE
    details = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resultAudits")

class AdmissionApplication(Base):
    __tablename__ = "AdmissionApplication"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    applicationNumber = Column(String(191), unique=True, nullable=False)
    academicYearId = Column(String(191), nullable=False)
    departmentId = Column(String(191), nullable=False)
    programId = Column(String(191), nullable=False)
    applicantName = Column(String(191), nullable=False)
    email = Column(String(191), nullable=False)
    phone = Column(String(191), nullable=False)
    dateOfBirth = Column(DateTime, nullable=False)
    gender = Column(String(191), nullable=False)
    nationality = Column(String(191), nullable=False)
    category = Column(String(191), nullable=False)
    quota = Column(String(191), nullable=False)
    entranceExam = Column(String(191), nullable=True)
    entranceScore = Column(Float, nullable=True)
    previousInstitution = Column(String(191), nullable=True)
    previousQualification = Column(String(191), nullable=True)
    previousPercentage = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    guardianName = Column(String(191), nullable=True)
    guardianPhone = Column(String(191), nullable=True)
    guardianEmail = Column(String(191), nullable=True)
    status = Column(String(191), default="DRAFT", nullable=False)
    submittedAt = Column(DateTime, nullable=True)
    reviewedAt = Column(DateTime, nullable=True)
    approvedAt = Column(DateTime, nullable=True)
    rejectedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    statusHistory = relationship("AdmissionStatusHistory", back_populates="application", cascade="all, delete-orphan")
    documents = relationship("AdmissionDocument", back_populates="application", cascade="all, delete-orphan")
    reviews = relationship("AdmissionReview", back_populates="application", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="application", cascade="all, delete-orphan")

class AdmissionStatusHistory(Base):
    __tablename__ = "AdmissionStatusHistory"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    applicationId = Column(String(191), ForeignKey("AdmissionApplication.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(191), nullable=False)
    changedBy = Column(String(191), nullable=False)
    remarks = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    application = relationship("AdmissionApplication", back_populates="statusHistory")

class AdmissionDocument(Base):
    __tablename__ = "AdmissionDocument"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    applicationId = Column(String(191), ForeignKey("AdmissionApplication.id", ondelete="CASCADE"), nullable=False)
    documentCategory = Column(String(191), nullable=False)
    fileName = Column(String(191), nullable=False)
    fileUrl = Column(String(191), nullable=False)
    verificationStatus = Column(String(191), default="PENDING", nullable=False)
    reviewerComments = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("AdmissionApplication", back_populates="documents")
    versions = relationship("AdmissionDocumentVersion", back_populates="document", cascade="all, delete-orphan")

class AdmissionDocumentVersion(Base):
    __tablename__ = "AdmissionDocumentVersion"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    documentId = Column(String(191), ForeignKey("AdmissionDocument.id", ondelete="CASCADE"), nullable=False)
    fileUrl = Column(String(191), nullable=False)
    uploadedAt = Column(DateTime, default=datetime.utcnow)

    document = relationship("AdmissionDocument", back_populates="versions")

class AdmissionReview(Base):
    __tablename__ = "AdmissionReview"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    applicationId = Column(String(191), ForeignKey("AdmissionApplication.id", ondelete="CASCADE"), nullable=False)
    reviewerId = Column(String(191), nullable=False)
    action = Column(String(191), nullable=False)
    comment = Column(Text, nullable=True)
    previousStatus = Column(String(191), nullable=False)
    newStatus = Column(String(191), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    application = relationship("AdmissionApplication", back_populates="reviews")

class Enrollment(Base):
    __tablename__ = "Enrollment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    applicationId = Column(String(191), ForeignKey("AdmissionApplication.id", ondelete="CASCADE"), nullable=False)
    enrollmentNumber = Column(String(191), unique=True, nullable=False)
    studentId = Column(String(191), nullable=False)
    usn = Column(String(191), unique=True, nullable=False)
    rollNumber = Column(String(191), nullable=False)
    academicYearId = Column(String(191), nullable=False)
    departmentId = Column(String(191), nullable=False)
    programId = Column(String(191), nullable=False)
    semesterNumber = Column(Integer, default=1, nullable=False)
    sectionId = Column(String(191), nullable=True)
    enrollmentDate = Column(DateTime, default=datetime.utcnow)
    createdAt = Column(DateTime, default=datetime.utcnow)

    application = relationship("AdmissionApplication", back_populates="enrollments")

class FeeStructure(Base):
    __tablename__ = "FeeStructure"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    academicYearId = Column(String(191), nullable=False)
    programId = Column(String(191), nullable=False)
    category = Column(String(191), nullable=True)
    quota = Column(String(191), nullable=True)
    currency = Column(String(191), default="INR", nullable=False)
    status = Column(String(191), default="DRAFT", nullable=False)
    version = Column(Integer, default=1, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    components = relationship("FeeComponent", back_populates="feeStructure", cascade="all, delete-orphan")
    assignments = relationship("StudentFeeAssignment", back_populates="feeStructure", cascade="all, delete")

class FeeComponent(Base):
    __tablename__ = "FeeComponent"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    feeStructureId = Column(String(191), ForeignKey("FeeStructure.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(191), nullable=False)
    code = Column(String(191), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    mandatory = Column(Boolean, default=True, nullable=False)
    refundable = Column(Boolean, default=False, nullable=False)
    dueDate = Column(DateTime, nullable=False)
    sortOrder = Column(Integer, default=0, nullable=False)

    feeStructure = relationship("FeeStructure", back_populates="components")

class StudentFeeAssignment(Base):
    __tablename__ = "StudentFeeAssignment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), nullable=False)
    feeStructureId = Column(String(191), ForeignKey("FeeStructure.id", ondelete="RESTRICT"), nullable=False)
    netPayable = Column(Numeric(12, 2), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    feeStructure = relationship("FeeStructure", back_populates="assignments")

class FeeInvoice(Base):
    __tablename__ = "FeeInvoice"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    invoiceNumber = Column(String(191), unique=True, nullable=False)
    studentId = Column(String(191), nullable=False)
    enrollmentId = Column(String(191), nullable=True)
    currency = Column(String(191), default="INR", nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    scholarshipAmount = Column(Numeric(12, 2), default=0.0, nullable=False)
    discountAmount = Column(Numeric(12, 2), default=0.0, nullable=False)
    adjustmentAmount = Column(Numeric(12, 2), default=0.0, nullable=False)
    taxAmount = Column(Numeric(12, 2), default=0.0, nullable=False)
    totalAmount = Column(Numeric(12, 2), nullable=False)
    paidAmount = Column(Numeric(12, 2), default=0.0, nullable=False)
    balanceAmount = Column(Numeric(12, 2), nullable=False)
    dueDate = Column(DateTime, nullable=False)
    status = Column(String(191), default="DRAFT", nullable=False)
    issuedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete")

class InvoiceItem(Base):
    __tablename__ = "InvoiceItem"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    invoiceId = Column(String(191), ForeignKey("FeeInvoice.id", ondelete="CASCADE"), nullable=False)
    componentName = Column(String(191), nullable=False)
    componentCode = Column(String(191), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)

    invoice = relationship("FeeInvoice", back_populates="items")

class Payment(Base):
    __tablename__ = "Payment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    paymentNumber = Column(String(191), unique=True, nullable=False)
    invoiceId = Column(String(191), ForeignKey("FeeInvoice.id", ondelete="RESTRICT"), nullable=False)
    studentId = Column(String(191), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(191), default="INR", nullable=False)
    method = Column(String(191), nullable=False)
    status = Column(String(191), default="INITIATED", nullable=False)
    provider = Column(String(191), default="MOCK", nullable=False)
    providerOrderId = Column(String(191), nullable=True)
    providerPaymentId = Column(String(191), nullable=True)
    idempotencyKey = Column(String(191), unique=True, nullable=False)
    paidAt = Column(DateTime, nullable=True)
    failureReason = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("FeeInvoice", back_populates="payments")
    receipts = relationship("Receipt", back_populates="payment", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

class WebhookEvent(Base):
    __tablename__ = "WebhookEvent"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    eventId = Column(String(191), unique=True, nullable=False)
    provider = Column(String(191), nullable=False)
    payload = Column(Text, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

class Receipt(Base):
    __tablename__ = "Receipt"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    receiptNumber = Column(String(191), unique=True, nullable=False)
    paymentId = Column(String(191), ForeignKey("Payment.id", ondelete="RESTRICT"), nullable=False)
    studentId = Column(String(191), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(191), default="INR", nullable=False)
    issuedAt = Column(DateTime, default=datetime.utcnow)
    verificationToken = Column(String(191), unique=True, nullable=False)

    payment = relationship("Payment", back_populates="receipts")

class Scholarship(Base):
    __tablename__ = "Scholarship"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    type = Column(String(191), nullable=False)
    description = Column(Text, nullable=True)
    percentageAmount = Column(Float, nullable=True)
    fixedAmount = Column(Numeric(12, 2), nullable=True)
    maximumBenefit = Column(Numeric(12, 2), nullable=True)
    eligibility = Column(Text, nullable=True)
    validFrom = Column(DateTime, nullable=False)
    validTo = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)

    applications = relationship("ScholarshipApplication", back_populates="scholarship", cascade="all, delete-orphan")

class ScholarshipApplication(Base):
    __tablename__ = "ScholarshipApplication"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    scholarshipId = Column(String(191), ForeignKey("Scholarship.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), nullable=False)
    status = Column(String(191), default="SUBMITTED", nullable=False)
    remarks = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    scholarship = relationship("Scholarship", back_populates="applications")

class StudentScholarship(Base):
    __tablename__ = "StudentScholarship"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), nullable=False)
    scholarshipId = Column(String(191), nullable=False)
    amountAwarded = Column(Numeric(12, 2), nullable=False)
    awardedAt = Column(DateTime, default=datetime.utcnow)

class Discount(Base):
    __tablename__ = "Discount"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    discountType = Column(String(191), nullable=False)
    percentage = Column(Float, nullable=True)
    fixedAmount = Column(Numeric(12, 2), nullable=True)
    status = Column(String(191), default="ACTIVE", nullable=False)

class StudentDiscount(Base):
    __tablename__ = "StudentDiscount"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), nullable=False)
    discountId = Column(String(191), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    appliedAt = Column(DateTime, default=datetime.utcnow)

class FeeAdjustment(Base):
    __tablename__ = "FeeAdjustment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), nullable=False)
    invoiceId = Column(String(191), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(191), nullable=False)
    createdBy = Column(String(191), nullable=False)
    approvedBy = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

class Refund(Base):
    __tablename__ = "Refund"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    paymentId = Column(String(191), ForeignKey("Payment.id", ondelete="RESTRICT"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(191), nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="refunds")

class PaymentAdjustment(Base):
    __tablename__ = "PaymentAdjustment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    paymentId = Column(String(191), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    adjustmentType = Column(String(191), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

class FeeReminder(Base):
    __tablename__ = "FeeReminder"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), nullable=False)
    invoiceId = Column(String(191), nullable=False)
    reminderType = Column(String(191), nullable=False)
    channel = Column(String(191), nullable=False)
    sentAt = Column(DateTime, default=datetime.utcnow)

class FinancialAudit(Base):
    __tablename__ = "FinancialAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    entityType = Column(String(191), nullable=False)
    entityId = Column(String(191), nullable=False)
    action = Column(String(191), nullable=False)
    userId = Column(String(191), nullable=False)
    previousData = Column(Text, nullable=True)
    newData = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

class ParentProfile(Base):
    __tablename__ = "ParentProfile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    fatherName = Column(String(191), nullable=True)
    motherName = Column(String(191), nullable=True)
    guardianName = Column(String(191), nullable=True)
    relationshipType = Column(String(191), default="GUARDIAN", nullable=False)
    occupation = Column(String(191), nullable=True)
    phoneNumber = Column(String(191), nullable=False)
    address = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="parentProfile")
    studentLinks = relationship("ParentStudentLink", back_populates="parent", cascade="all, delete-orphan")
    notifications = relationship("ParentNotification", back_populates="parent", cascade="all, delete-orphan")
    audits = relationship("ParentAudit", back_populates="parent", cascade="all, delete-orphan")

class ParentStudentLink(Base):
    __tablename__ = "ParentStudentLink"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    parentId = Column(String(191), ForeignKey("ParentProfile.id", ondelete="CASCADE"), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)

    parent = relationship("ParentProfile", back_populates="studentLinks")
    student = relationship("User", back_populates="parentLinks")

    relationship = Column(String(191), nullable=False)
    isPrimaryContact = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("parentId", "studentId", name="uix_parent_student"),
    )

class ParentMessage(Base):
    __tablename__ = "ParentMessage"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    senderId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    receiverId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    isRead = Column(Boolean, default=False, nullable=False)
    readAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[senderId], back_populates="sentParentMessages")
    receiver = relationship("User", foreign_keys=[receiverId], back_populates="receivedParentMessages")

class ParentNotification(Base):
    __tablename__ = "ParentNotification"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    parentId = Column(String(191), ForeignKey("ParentProfile.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(191), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(191), nullable=False)
    isRead = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    parent = relationship("ParentProfile", back_populates="notifications")

class ParentAudit(Base):
    __tablename__ = "ParentAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    parentId = Column(String(191), ForeignKey("ParentProfile.id", ondelete="SET NULL"), nullable=True)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False)
    details = Column(Text, nullable=True)
    ipAddress = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    parent = relationship("ParentProfile", back_populates="audits")
    user = relationship("User", back_populates="parentAudits")

class LibraryBranch(Base):
    __tablename__ = "LibraryBranch"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(191), nullable=True)
    contactEmail = Column(String(191), nullable=True)
    contactPhone = Column(String(191), nullable=True)
    openingTime = Column(String(191), nullable=True)
    closingTime = Column(String(191), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    copies = relationship("BookCopy", back_populates="branch", cascade="all, delete-orphan")
    memberships = relationship("LibraryMembership", back_populates="branch")
    policies = relationship("LibraryPolicy", back_populates="branch", cascade="all, delete-orphan")
    audits = relationship("InventoryAudit", back_populates="branch")

class Author(Base):
    __tablename__ = "Author"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    biography = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookAuthors = relationship("BookAuthor", back_populates="author", cascade="all, delete-orphan")

class Publisher(Base):
    __tablename__ = "Publisher"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    books = relationship("Book", back_populates="publisher")

class BookCategory(Base):
    __tablename__ = "BookCategory"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    books = relationship("Book", back_populates="category")

class Book(Base):
    __tablename__ = "Book"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    isbn10 = Column(String(191), nullable=True)
    isbn13 = Column(String(191), unique=True, nullable=False)
    title = Column(String(191), nullable=False)
    subtitle = Column(String(191), nullable=True)
    description = Column(Text, nullable=True)
    edition = Column(String(191), nullable=True)
    publicationYear = Column(Integer, nullable=False)
    language = Column(String(191), nullable=False)
    pageCount = Column(Integer, nullable=False)
    coverImageUrl = Column(String(191), nullable=True)
    publisherId = Column(String(191), ForeignKey("Publisher.id"), nullable=False)
    categoryId = Column(String(191), ForeignKey("BookCategory.id"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publisher = relationship("Publisher", back_populates="books")
    category = relationship("BookCategory", back_populates="books")
    bookAuthors = relationship("BookAuthor", back_populates="book", cascade="all, delete-orphan")
    tags = relationship("BookTag", back_populates="book", cascade="all, delete-orphan")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    reservations = relationship("BookReservation", back_populates="book", cascade="all, delete-orphan")
    acquisitionItems = relationship("BookAcquisitionItem", back_populates="book")

class BookAuthor(Base):
    __tablename__ = "BookAuthor"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    bookId = Column(String(191), ForeignKey("Book.id", ondelete="CASCADE"), nullable=False)
    authorId = Column(String(191), ForeignKey("Author.id", ondelete="CASCADE"), nullable=False)

    book = relationship("Book", back_populates="bookAuthors")
    author = relationship("Author", back_populates="bookAuthors")

    __table_args__ = (UniqueConstraint("bookId", "authorId", name="BookAuthor_bookId_authorId_key"),)

class BookTag(Base):
    __tablename__ = "BookTag"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    bookId = Column(String(191), ForeignKey("Book.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(191), nullable=False)

    book = relationship("Book", back_populates="tags")

    __table_args__ = (UniqueConstraint("bookId", "name", name="BookTag_bookId_name_key"),)

class BookCopy(Base):
    __tablename__ = "BookCopy"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    bookId = Column(String(191), ForeignKey("Book.id", ondelete="CASCADE"), nullable=False)
    branchId = Column(String(191), ForeignKey("LibraryBranch.id"), nullable=False)
    accessionNumber = Column(String(191), unique=True, nullable=False)
    barcode = Column(String(191), unique=True, nullable=False)
    qrCode = Column(String(191), nullable=True)
    shelfLocation = Column(String(191), nullable=True)
    rackNumber = Column(String(191), nullable=True)
    acquisitionDate = Column(DateTime, nullable=False)
    acquisitionPrice = Column(Numeric(10, 2), nullable=False)
    source = Column(String(191), nullable=True)
    condition = Column(String(191), default="GOOD", nullable=False)
    status = Column(String(191), default="AVAILABLE", nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    book = relationship("Book", back_populates="copies")
    branch = relationship("LibraryBranch", back_populates="copies")
    loans = relationship("BookLoan", back_populates="copy", cascade="all, delete-orphan")
    events = relationship("LibraryInventoryEvent", back_populates="copy", cascade="all, delete-orphan")
    auditItems = relationship("InventoryAuditItem", back_populates="copy", cascade="all, delete-orphan")

class LibraryMembership(Base):
    __tablename__ = "LibraryMembership"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    membershipNumber = Column(String(191), unique=True, nullable=False)
    memberType = Column(String(191), nullable=False) # STUDENT, FACULTY, STAFF, ALUMNI, OTHER
    branchId = Column(String(191), ForeignKey("LibraryBranch.id"), nullable=True)
    activatedAt = Column(DateTime, nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False) # ACTIVE, SUSPENDED, EXPIRED, BLOCKED
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="libraryMembership")
    branch = relationship("LibraryBranch", back_populates="memberships")
    loans = relationship("BookLoan", back_populates="membership", cascade="all, delete-orphan")
    reservations = relationship("BookReservation", back_populates="membership", cascade="all, delete-orphan")
    fines = relationship("LibraryFine", back_populates="membership", cascade="all, delete-orphan")

class LibraryPolicy(Base):
    __tablename__ = "LibraryPolicy"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    memberType = Column(String(191), nullable=False) # STUDENT, FACULTY, STAFF, ALUMNI, OTHER
    branchId = Column(String(191), ForeignKey("LibraryBranch.id", ondelete="CASCADE"), nullable=False)
    maxBooks = Column(Integer, nullable=False)
    loanDays = Column(Integer, nullable=False)
    renewalLimit = Column(Integer, nullable=False)
    reservationLimit = Column(Integer, nullable=False)
    finePerDay = Column(Numeric(10, 2), nullable=False)
    graceDays = Column(Integer, nullable=False)
    maxFine = Column(Numeric(10, 2), nullable=False)
    allowRenewal = Column(Boolean, default=True, nullable=False)
    allowReservation = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch = relationship("LibraryBranch", back_populates="policies")

    __table_args__ = (UniqueConstraint("memberType", "branchId", name="LibraryPolicy_memberType_branchId_key"),)

class BookLoan(Base):
    __tablename__ = "BookLoan"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    copyId = Column(String(191), ForeignKey("BookCopy.id", ondelete="CASCADE"), nullable=False)
    membershipId = Column(String(191), ForeignKey("LibraryMembership.id", ondelete="CASCADE"), nullable=False)
    issuedBy = Column(String(191), ForeignKey("User.id"), nullable=False)
    issuedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    dueAt = Column(DateTime, nullable=False)
    returnedAt = Column(DateTime, nullable=True)
    status = Column(String(191), default="ACTIVE", nullable=False) # ACTIVE, OVERDUE, RETURNED, LOST, DAMAGED
    renewalCount = Column(Integer, default=0, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    copy = relationship("BookCopy", back_populates="loans")
    membership = relationship("LibraryMembership", back_populates="loans")
    issuer = relationship("User", foreign_keys=[issuedBy], back_populates="loansIssued")
    renewals = relationship("LoanRenewal", back_populates="loan", cascade="all, delete-orphan")
    fines = relationship("LibraryFine", back_populates="loan", cascade="all, delete-orphan")

class LoanRenewal(Base):
    __tablename__ = "LoanRenewal"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    loanId = Column(String(191), ForeignKey("BookLoan.id", ondelete="CASCADE"), nullable=False)
    renewedBy = Column(String(191), ForeignKey("User.id"), nullable=False)
    renewedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    originalDueAt = Column(DateTime, nullable=False)
    newDueAt = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    loan = relationship("BookLoan", back_populates="renewals")
    renewer = relationship("User", foreign_keys=[renewedBy], back_populates="renewalsCreated")

class BookReservation(Base):
    __tablename__ = "BookReservation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    bookId = Column(String(191), ForeignKey("Book.id", ondelete="CASCADE"), nullable=False)
    membershipId = Column(String(191), ForeignKey("LibraryMembership.id", ondelete="CASCADE"), nullable=False)
    reservedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(191), default="WAITING", nullable=False) # WAITING, READY_FOR_PICKUP, FULFILLED, CANCELLED, EXPIRED
    pickupDeadline = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    book = relationship("Book", back_populates="reservations")
    membership = relationship("LibraryMembership", back_populates="reservations")

class LibraryFine(Base):
    __tablename__ = "LibraryFine"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    loanId = Column(String(191), ForeignKey("BookLoan.id", ondelete="SET NULL"), nullable=True)
    membershipId = Column(String(191), ForeignKey("LibraryMembership.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(191), default="INR", nullable=False)
    reason = Column(String(191), nullable=False) # OVERDUE, LOST, DAMAGED, OTHER
    status = Column(String(191), default="PENDING", nullable=False) # PENDING, PAID, WAIVED, CANCELLED
    assessedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    paidAt = Column(DateTime, nullable=True)
    waivedAt = Column(DateTime, nullable=True)
    waivedBy = Column(String(191), ForeignKey("User.id"), nullable=True)
    waiverReason = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    loan = relationship("BookLoan", back_populates="fines")
    membership = relationship("LibraryMembership", back_populates="fines")
    waiverUser = relationship("User", foreign_keys=[waivedBy], back_populates="finesWaived")

class LibraryInventoryEvent(Base):
    __tablename__ = "LibraryInventoryEvent"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    copyId = Column(String(191), ForeignKey("BookCopy.id", ondelete="CASCADE"), nullable=False)
    eventType = Column(String(191), nullable=False) # CONDITION_CHANGE, DAMAGE_REPORT, LOST_REPORT, REPAIR_SENT, REPAIR_RETURNED, WITHDRAWN
    description = Column(Text, nullable=False)
    reportedBy = Column(String(191), ForeignKey("User.id"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    copy = relationship("BookCopy", back_populates="events")
    reporter = relationship("User", foreign_keys=[reportedBy], back_populates="inventoryEvents")

class DigitalResource(Base):
    __tablename__ = "DigitalResource"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    title = Column(String(191), nullable=False)
    type = Column(String(191), nullable=False) # EBOOK, JOURNAL, RESEARCH_PAPER, INSTITUTIONAL_REPOSITORY
    description = Column(Text, nullable=True)
    accessUrl = Column(String(191), nullable=False)
    licenseType = Column(String(191), nullable=False)
    accessLevel = Column(String(191), nullable=False) # PUBLIC, STUDENT, FACULTY, ADMIN
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LibraryVendor(Base):
    __tablename__ = "LibraryVendor"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    contactPerson = Column(String(191), nullable=True)
    email = Column(String(191), nullable=True)
    phone = Column(String(191), nullable=True)
    address = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requests = relationship("BookAcquisitionRequest", back_populates="vendor")

class BookAcquisitionRequest(Base):
    __tablename__ = "BookAcquisitionRequest"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    vendorId = Column(String(191), ForeignKey("LibraryVendor.id"), nullable=True)
    status = Column(String(191), default="DRAFT", nullable=False) # DRAFT, SUBMITTED, APPROVED, REJECTED, ORDERED, RECEIVED, CANCELLED
    requestedBy = Column(String(191), ForeignKey("User.id"), nullable=False)
    approvedBy = Column(String(191), ForeignKey("User.id"), nullable=True)
    totalCost = Column(Numeric(10, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("LibraryVendor", back_populates="requests")
    requester = relationship("User", foreign_keys=[requestedBy], back_populates="acquisitionRequests")
    approver = relationship("User", foreign_keys=[approvedBy], back_populates="acquisitionApprovals")
    items = relationship("BookAcquisitionItem", back_populates="request", cascade="all, delete-orphan")

class BookAcquisitionItem(Base):
    __tablename__ = "BookAcquisitionItem"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    requestId = Column(String(191), ForeignKey("BookAcquisitionRequest.id", ondelete="CASCADE"), nullable=False)
    bookId = Column(String(191), ForeignKey("Book.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unitPrice = Column(Numeric(10, 2), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    request = relationship("BookAcquisitionRequest", back_populates="items")
    book = relationship("Book", back_populates="acquisitionItems")

class InventoryAudit(Base):
    __tablename__ = "InventoryAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    branchId = Column(String(191), ForeignKey("LibraryBranch.id"), nullable=False)
    status = Column(String(191), default="DRAFT", nullable=False) # DRAFT, IN_PROGRESS, COMPLETED, CANCELLED
    conductedBy = Column(String(191), ForeignKey("User.id"), nullable=False)
    startedAt = Column(DateTime, nullable=False)
    endedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch = relationship("LibraryBranch", back_populates="audits")
    conductor = relationship("User", foreign_keys=[conductedBy], back_populates="inventoryAudits")
    items = relationship("InventoryAuditItem", back_populates="audit", cascade="all, delete-orphan")

class InventoryAuditItem(Base):
    __tablename__ = "InventoryAuditItem"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    auditId = Column(String(191), ForeignKey("InventoryAudit.id", ondelete="CASCADE"), nullable=False)
    copyId = Column(String(191), ForeignKey("BookCopy.id", ondelete="CASCADE"), nullable=False)
    scannedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    scannedCondition = Column(String(191), nullable=False)
    status = Column(String(191), nullable=False) # MATCHED, MISPLACED, MISSING
    notes = Column(Text, nullable=True)

    audit = relationship("InventoryAudit", back_populates="items")
    copy = relationship("BookCopy", back_populates="auditItems")

class LibraryAudit(Base):
    __tablename__ = "LibraryAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False)
    details = Column(Text, nullable=True)
    ipAddress = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="libraryAudits")


class Hostel(Base):
    __tablename__ = "Hostel"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    hostelType = Column(String(191), nullable=False)  # BOYS, GIRLS, COED, STAFF, GUEST
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=False)
    contactPhone = Column(String(191), nullable=True)
    contactEmail = Column(String(191), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blocks = relationship("HostelBlock", back_populates="hostel", cascade="all, delete-orphan")
    applications = relationship("HostelApplication", back_populates="preferredHostel")
    visitors = relationship("HostelVisitor", back_populates="hostel")
    incidents = relationship("HostelIncident", back_populates="hostel", cascade="all, delete-orphan")


class HostelBlock(Base):
    __tablename__ = "HostelBlock"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    hostelId = Column(String(191), ForeignKey("Hostel.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(191), nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    totalFloors = Column(Integer, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hostel = relationship("Hostel", back_populates="blocks")
    floors = relationship("HostelFloor", back_populates="block", cascade="all, delete-orphan")


class HostelFloor(Base):
    __tablename__ = "HostelFloor"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    blockId = Column(String(191), ForeignKey("HostelBlock.id", ondelete="CASCADE"), nullable=False)
    floorNumber = Column(Integer, nullable=False)
    name = Column(String(191), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    block = relationship("HostelBlock", back_populates="floors")
    rooms = relationship("HostelRoom", back_populates="floor", cascade="all, delete-orphan")


class HostelRoom(Base):
    __tablename__ = "HostelRoom"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    floorId = Column(String(191), ForeignKey("HostelFloor.id", ondelete="CASCADE"), nullable=False)
    roomNumber = Column(String(191), unique=True, nullable=False)
    roomType = Column(String(191), nullable=False)  # SINGLE, DOUBLE, TRIPLE, FOUR_SHARING, DORMITORY, GUEST
    capacity = Column(Integer, nullable=False)
    monthlyRate = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    status = Column(String(191), default="AVAILABLE", nullable=False)  # AVAILABLE, PARTIALLY_OCCUPIED, FULL, MAINTENANCE, BLOCKED
    amenities = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    floor = relationship("HostelFloor", back_populates="rooms")
    beds = relationship("HostelBed", back_populates="room", cascade="all, delete-orphan")


class HostelBed(Base):
    __tablename__ = "HostelBed"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    roomId = Column(String(191), ForeignKey("HostelRoom.id", ondelete="CASCADE"), nullable=False)
    bedNumber = Column(String(191), nullable=False)
    status = Column(String(191), default="AVAILABLE", nullable=False)  # AVAILABLE, ALLOCATED, RESERVED, MAINTENANCE, BLOCKED
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = relationship("HostelRoom", back_populates="beds")
    allocations = relationship("HostelAllocation", back_populates="bed", cascade="all, delete-orphan")


class HostelApplication(Base):
    __tablename__ = "HostelApplication"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    academicYearId = Column(String(191), nullable=False)
    preferredHostelId = Column(String(191), ForeignKey("Hostel.id"), nullable=False)
    preferredRoomType = Column(String(191), nullable=False)
    reason = Column(Text, nullable=True)
    medicalNotes = Column(Text, nullable=True)
    emergencyContact = Column(String(191), nullable=False)
    status = Column(String(191), default="SUBMITTED", nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, WAITLISTED, ALLOCATED, CANCELLED
    submittedAt = Column(DateTime, default=datetime.utcnow)
    reviewedAt = Column(DateTime, nullable=True)
    reviewedBy = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)

    student = relationship("User", foreign_keys=[studentId], back_populates="hostelApplications")
    reviewer = relationship("User", foreign_keys=[reviewedBy], back_populates="reviewedHostelApplications")
    preferredHostel = relationship("Hostel", back_populates="applications")
    allocations = relationship("HostelAllocation", back_populates="application", cascade="all, delete-orphan")


class HostelAllocation(Base):
    __tablename__ = "HostelAllocation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    applicationId = Column(String(191), ForeignKey("HostelApplication.id"), nullable=False)
    bedId = Column(String(191), ForeignKey("HostelBed.id"), nullable=False)
    allocatedBy = Column(String(191), ForeignKey("User.id"), nullable=False)
    allocatedAt = Column(DateTime, default=datetime.utcnow)
    startDate = Column(DateTime, nullable=False)
    expectedEndDate = Column(DateTime, nullable=False)
    actualEndDate = Column(DateTime, nullable=True)
    status = Column(String(191), default="ACTIVE", nullable=False)  # RESERVED, ACTIVE, TRANSFERRED, COMPLETED, CANCELLED

    student = relationship("User", foreign_keys=[studentId], back_populates="hostelAllocations")
    allocator = relationship("User", foreign_keys=[allocatedBy], back_populates="allocatedHostels")
    application = relationship("HostelApplication", back_populates="allocations")
    bed = relationship("HostelBed", back_populates="allocations")
    checkIns = relationship("HostelCheckIn", back_populates="allocation", cascade="all, delete-orphan")
    checkOuts = relationship("HostelCheckOut", back_populates="allocation", cascade="all, delete-orphan")
    leaves = relationship("HostelLeaveRequest", back_populates="allocation", cascade="all, delete-orphan")
    fines = relationship("HostelFine", back_populates="allocation")


class HostelCheckIn(Base):
    __tablename__ = "HostelCheckIn"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    allocationId = Column(String(191), ForeignKey("HostelAllocation.id", ondelete="CASCADE"), nullable=False)
    checkedInAt = Column(DateTime, default=datetime.utcnow)
    checkedInBy = Column(String(191), nullable=False)
    inventoryNotes = Column(Text, nullable=True)
    conditionNotes = Column(Text, nullable=True)
    acknowledgement = Column(Boolean, default=False, nullable=False)

    allocation = relationship("HostelAllocation", back_populates="checkIns")


class HostelCheckOut(Base):
    __tablename__ = "HostelCheckOut"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    allocationId = Column(String(191), ForeignKey("HostelAllocation.id", ondelete="CASCADE"), nullable=False)
    checkedOutAt = Column(DateTime, default=datetime.utcnow)
    checkedOutBy = Column(String(191), nullable=False)
    damageNotes = Column(Text, nullable=True)
    damageCost = Column(Numeric(precision=10, scale=2, asdecimal=True), default=0.0, nullable=False)
    inventoryNotes = Column(Text, nullable=True)
    status = Column(String(191), default="COMPLETED", nullable=False)  # COMPLETED, PENALIZED

    allocation = relationship("HostelAllocation", back_populates="checkOuts")


class HostelTransferRequest(Base):
    __tablename__ = "HostelTransferRequest"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), nullable=False)
    currentAllocationId = Column(String(191), nullable=False)
    preferredBedId = Column(String(191), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, COMPLETED, CANCELLED
    reviewedBy = Column(String(191), nullable=True)
    reviewedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HostelWardenAssignment(Base):
    __tablename__ = "HostelWardenAssignment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    wardenId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    hostelId = Column(String(191), nullable=False)
    blockId = Column(String(191), nullable=True)
    assignmentType = Column(String(191), nullable=False)  # CHIEF_WARDEN, HOSTEL_WARDEN, ASSISTANT_WARDEN
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warden = relationship("User", back_populates="wardenAssignments")


class HostelVisitor(Base):
    __tablename__ = "HostelVisitor"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    visitorName = Column(String(191), nullable=False)
    phone = Column(String(191), nullable=False)
    relation = Column(String(191), nullable=False)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    hostelId = Column(String(191), ForeignKey("Hostel.id"), nullable=False)
    purpose = Column(String(191), nullable=False)
    identityType = Column(String(191), nullable=False)
    identityReferenceMasked = Column(String(191), nullable=False)
    checkInAt = Column(DateTime, default=datetime.utcnow)
    checkOutAt = Column(DateTime, nullable=True)
    approvedBy = Column(String(191), ForeignKey("User.id"), nullable=True)
    status = Column(String(191), default="PENDING", nullable=False)  # PENDING, APPROVED, CHECKED_IN, CHECKED_OUT, REJECTED

    student = relationship("User", foreign_keys=[studentId], back_populates="visitorRequests")
    approver = relationship("User", foreign_keys=[approvedBy], back_populates="approvedVisitors")
    hostel = relationship("Hostel", back_populates="visitors")


class HostelComplaint(Base):
    __tablename__ = "HostelComplaint"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(191), nullable=False)  # ELECTRICAL, PLUMBING, CLEANING, INTERNET, FURNITURE, SECURITY, MESS, OTHER
    priority = Column(String(191), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    assignedTo = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(191), default="OPEN", nullable=False)  # OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, REJECTED
    openedAt = Column(DateTime, default=datetime.utcnow)
    resolvedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("User", foreign_keys=[studentId], back_populates="hostelComplaints")
    assignee = relationship("User", foreign_keys=[assignedTo], back_populates="assignedComplaints")
    comments = relationship("HostelComplaintComment", back_populates="complaint", cascade="all, delete-orphan")


class HostelComplaintComment(Base):
    __tablename__ = "HostelComplaintComment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    complaintId = Column(String(191), ForeignKey("HostelComplaint.id", ondelete="CASCADE"), nullable=False)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    commentText = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("HostelComplaint", back_populates="comments")
    user = relationship("User", back_populates="hostelComplaintComments")


class HostelMaintenanceRequest(Base):
    __tablename__ = "HostelMaintenanceRequest"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    hostelId = Column(String(191), nullable=False)
    roomId = Column(String(191), nullable=True)
    bedId = Column(String(191), nullable=True)
    category = Column(String(191), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(191), nullable=False)
    assignedTo = Column(String(191), ForeignKey("User.id"), nullable=False)
    status = Column(String(191), default="OPEN", nullable=False)
    estimatedCost = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    actualCost = Column(Numeric(precision=10, scale=2, asdecimal=True), default=0.0, nullable=False)
    openedAt = Column(DateTime, default=datetime.utcnow)
    completedAt = Column(DateTime, nullable=True)

    assignee = relationship("User", back_populates="assignedMaintenance")


class HostelLeaveRequest(Base):
    __tablename__ = "HostelLeaveRequest"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    allocationId = Column(String(191), ForeignKey("HostelAllocation.id", ondelete="CASCADE"), nullable=False)
    leaveType = Column(String(191), nullable=False)
    reason = Column(Text, nullable=False)
    destination = Column(String(191), nullable=False)
    startAt = Column(DateTime, nullable=False)
    expectedReturnAt = Column(DateTime, nullable=False)
    actualReturnAt = Column(DateTime, nullable=True)
    guardianContact = Column(String(191), nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, OUT, RETURNED, OVERDUE, CANCELLED

    student = relationship("User", back_populates="hostelLeaveRequests")
    allocation = relationship("HostelAllocation", back_populates="leaves")


class HostelGatePass(Base):
    __tablename__ = "HostelGatePass"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    leaveRequestId = Column(String(191), nullable=True)
    passToken = Column(String(191), unique=True, nullable=False)
    purpose = Column(String(191), nullable=False)
    expiryAt = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, USED, EXPIRED

    student = relationship("User", back_populates="gatePasses")


class MessPlan(Base):
    __tablename__ = "MessPlan"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    costPerMonth = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    foodType = Column(String(191), nullable=False)  # VEG, NON_VEG, MIXED, CUSTOM
    active = Column(Boolean, default=True, nullable=False)

    subscriptions = relationship("MessSubscription", back_populates="plan", cascade="all, delete-orphan")
    attendances = relationship("MessAttendance", back_populates="plan", cascade="all, delete-orphan")


class MessSubscription(Base):
    __tablename__ = "MessSubscription"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    planId = Column(String(191), ForeignKey("MessPlan.id"), nullable=False)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, SUSPENDED, EXPIRED

    student = relationship("User", back_populates="messSubscriptions")
    plan = relationship("MessPlan", back_populates="subscriptions")


class MessMenu(Base):
    __tablename__ = "MessMenu"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    planId = Column(String(191), nullable=False)
    dayOfWeek = Column(String(191), nullable=False)
    mealType = Column(String(191), nullable=False)  # BREAKFAST, LUNCH, SNACK, DINNER
    menuDetails = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MessAttendance(Base):
    __tablename__ = "MessAttendance"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    planId = Column(String(191), ForeignKey("MessPlan.id"), nullable=False)
    mealDate = Column(DateTime, nullable=False)
    mealType = Column(String(191), nullable=False)  # BREAKFAST, LUNCH, SNACK, DINNER
    status = Column(String(191), default="PRESENT", nullable=False)  # PRESENT, ABSENT
    qrCodeScanned = Column(Boolean, default=False, nullable=False)

    student = relationship("User", back_populates="messAttendances")
    plan = relationship("MessPlan", back_populates="attendances")


class HostelFine(Base):
    __tablename__ = "HostelFine"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    studentId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    allocationId = Column(String(191), ForeignKey("HostelAllocation.id"), nullable=True)
    fineType = Column(String(191), nullable=False)  # DAMAGE, LATE_RETURN, RULE_VIOLATION, LOST_PROPERTY, OTHER
    amount = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    reason = Column(String(191), nullable=False)
    status = Column(String(191), default="PENDING", nullable=False)  # PENDING, PAID, WAIVED, CANCELLED
    assessedAt = Column(DateTime, default=datetime.utcnow)
    paidAt = Column(DateTime, nullable=True)
    waivedAt = Column(DateTime, nullable=True)
    waivedBy = Column(String(191), ForeignKey("User.id"), nullable=True)
    waiverReason = Column(Text, nullable=True)

    student = relationship("User", foreign_keys=[studentId], back_populates="hostelFines")
    waiverUser = relationship("User", foreign_keys=[waivedBy], back_populates="waivedHostelFines")
    allocation = relationship("HostelAllocation", back_populates="fines")


class HostelIncident(Base):
    __tablename__ = "HostelIncident"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    hostelId = Column(String(191), ForeignKey("Hostel.id", ondelete="CASCADE"), nullable=False)
    reporterId = Column(String(191), ForeignKey("User.id"), nullable=False)
    title = Column(String(191), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(191), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    reportedAt = Column(DateTime, default=datetime.utcnow)
    actionTaken = Column(Text, nullable=True)
    status = Column(String(191), default="OPEN", nullable=False)  # OPEN, INVESTIGATING, RESOLVED, CLOSED

    hostel = relationship("Hostel", back_populates="incidents")
    reporter = relationship("User", back_populates="reportedIncidents")


class HostelAudit(Base):
    __tablename__ = "HostelAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False)
    details = Column(Text, nullable=True)
    ipAddress = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="hostelAudits")


class TransportVehicle(Base):
    __tablename__ = "TransportVehicle"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    registrationNumber = Column(String(191), unique=True, nullable=False)
    vehicleCode = Column(String(191), unique=True, nullable=False)
    vehicleType = Column(String(191), nullable=False)  # BUS, MINI_BUS, VAN, CAR, SHUTTLE, ELECTRIC_BUS
    manufacturer = Column(String(191), nullable=False)
    model = Column(String(191), nullable=False)
    manufactureYear = Column(Integer, nullable=False)
    seatingCapacity = Column(Integer, nullable=False)
    standingCapacity = Column(Integer, nullable=False)
    fuelType = Column(String(191), nullable=False)  # DIESEL, PETROL, CNG, ELECTRIC, HYBRID
    chassisNumberMasked = Column(String(191), nullable=False)
    engineNumberMasked = Column(String(191), nullable=False)
    insuranceExpiry = Column(DateTime, nullable=False)
    fitnessExpiry = Column(DateTime, nullable=False)
    pollutionExpiry = Column(DateTime, nullable=False)
    permitExpiry = Column(DateTime, nullable=False)
    gpsDeviceId = Column(String(191), unique=True, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, MAINTENANCE, BREAKDOWN, RETIRED
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("TransportVehicleAssignment", back_populates="vehicle", cascade="all, delete-orphan")
    seats = relationship("TransportSeat", back_populates="vehicle", cascade="all, delete-orphan")
    trips = relationship("TransportTrip", back_populates="vehicle", cascade="all, delete-orphan")
    locations = relationship("TransportVehicleLocation", back_populates="vehicle", cascade="all, delete-orphan")
    maintenances = relationship("TransportMaintenance", back_populates="vehicle", cascade="all, delete-orphan")
    fuelLogs = relationship("TransportFuelLog", back_populates="vehicle", cascade="all, delete-orphan")
    incidents = relationship("TransportIncident", back_populates="vehicle", cascade="all, delete-orphan")


class TransportDriverProfile(Base):
    __tablename__ = "TransportDriverProfile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    employeeCode = Column(String(191), unique=True, nullable=False)
    licenseNumberMasked = Column(String(191), nullable=False)
    licenseType = Column(String(191), nullable=False)
    licenseExpiry = Column(DateTime, nullable=False)
    emergencyContact = Column(String(191), nullable=False)
    joiningDate = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, ON_LEAVE
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transportDriverProfile")
    assignments = relationship("TransportVehicleAssignment", back_populates="driver", cascade="all, delete-orphan")
    trips = relationship("TransportTrip", back_populates="driver", cascade="all, delete-orphan")


class TransportStaffProfile(Base):
    __tablename__ = "TransportStaffProfile"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    employeeCode = Column(String(191), unique=True, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    emergencyContact = Column(String(191), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transportStaffProfile")
    assignments = relationship("TransportVehicleAssignment", back_populates="conductor", cascade="all, delete-orphan")
    trips = relationship("TransportTrip", back_populates="conductor", cascade="all, delete-orphan")


class TransportRoute(Base):
    __tablename__ = "TransportRoute"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    origin = Column(String(191), nullable=False)
    destination = Column(String(191), nullable=False)
    estimatedDistanceKm = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    estimatedDurationMinutes = Column(Integer, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, SUSPENDED
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stops = relationship("TransportRouteStop", back_populates="route", order_by="TransportRouteStop.stopOrder", cascade="all, delete-orphan")
    assignments = relationship("TransportVehicleAssignment", back_populates="route", cascade="all, delete-orphan")
    applications = relationship("TransportApplication", back_populates="route", cascade="all, delete-orphan")
    subscriptions = relationship("TransportSubscription", back_populates="route", cascade="all, delete-orphan")
    trips = relationship("TransportTrip", back_populates="route", cascade="all, delete-orphan")


class TransportStop(Base):
    __tablename__ = "TransportStop"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    name = Column(String(191), nullable=False)
    code = Column(String(191), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    landmark = Column(String(191), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    routes = relationship("TransportRouteStop", back_populates="stop", cascade="all, delete-orphan")
    applicationsPickup = relationship("TransportApplication", foreign_keys="[TransportApplication.pickupStopId]", back_populates="pickupStop", cascade="all, delete-orphan")
    applicationsDrop = relationship("TransportApplication", foreign_keys="[TransportApplication.dropStopId]", back_populates="dropStop", cascade="all, delete-orphan")
    subscriptionsPickup = relationship("TransportSubscription", foreign_keys="[TransportSubscription.pickupStopId]", back_populates="pickupStop", cascade="all, delete-orphan")
    subscriptionsDrop = relationship("TransportSubscription", foreign_keys="[TransportSubscription.dropStopId]", back_populates="dropStop", cascade="all, delete-orphan")
    boardings = relationship("TransportBoarding", back_populates="stop", cascade="all, delete-orphan")


class TransportRouteStop(Base):
    __tablename__ = "TransportRouteStop"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    routeId = Column(String(191), ForeignKey("TransportRoute.id", ondelete="CASCADE"), nullable=False)
    stopId = Column(String(191), ForeignKey("TransportStop.id", ondelete="CASCADE"), nullable=False)
    stopOrder = Column(Integer, nullable=False)
    scheduledArrivalTime = Column(String(191), nullable=False)
    scheduledDepartureTime = Column(String(191), nullable=False)
    pickupAllowed = Column(Boolean, default=True, nullable=False)
    dropAllowed = Column(Boolean, default=True, nullable=False)
    distanceFromOriginKm = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    route = relationship("TransportRoute", back_populates="stops")
    stop = relationship("TransportStop", back_populates="routes")

    __table_args__ = (
        UniqueConstraint("routeId", "stopId", name="uix_route_stop"),
        UniqueConstraint("routeId", "stopOrder", name="uix_route_stop_order"),
    )


class TransportVehicleAssignment(Base):
    __tablename__ = "TransportVehicleAssignment"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    vehicleId = Column(String(191), ForeignKey("TransportVehicle.id", ondelete="CASCADE"), nullable=False)
    routeId = Column(String(191), ForeignKey("TransportRoute.id", ondelete="CASCADE"), nullable=False)
    driverId = Column(String(191), ForeignKey("TransportDriverProfile.id", ondelete="CASCADE"), nullable=False)
    conductorId = Column(String(191), ForeignKey("TransportStaffProfile.id", ondelete="SET NULL"), nullable=True)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=True)
    shift = Column(String(191), nullable=False)  # MORNING, EVENING, FULL_DAY, CUSTOM
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("TransportVehicle", back_populates="assignments")
    route = relationship("TransportRoute", back_populates="assignments")
    driver = relationship("TransportDriverProfile", back_populates="assignments")
    conductor = relationship("TransportStaffProfile", back_populates="assignments")


class TransportApplication(Base):
    __tablename__ = "TransportApplication"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    applicantUserId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    academicYearId = Column(String(191), nullable=False)
    routeId = Column(String(191), ForeignKey("TransportRoute.id", ondelete="CASCADE"), nullable=False)
    pickupStopId = Column(String(191), ForeignKey("TransportStop.id", ondelete="CASCADE"), nullable=False)
    dropStopId = Column(String(191), ForeignKey("TransportStop.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(191), default="SUBMITTED", nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, WAITLISTED, ALLOCATED, CANCELLED
    submittedAt = Column(DateTime, default=datetime.utcnow)
    reviewedAt = Column(DateTime, nullable=True)
    reviewedBy = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applicant = relationship("User", foreign_keys=[applicantUserId], back_populates="transportApplications")
    reviewer = relationship("User", foreign_keys=[reviewedBy], back_populates="reviewedTransportApplications")
    route = relationship("TransportRoute", back_populates="applications")
    pickupStop = relationship("TransportStop", foreign_keys=[pickupStopId], back_populates="applicationsPickup")
    dropStop = relationship("TransportStop", foreign_keys=[dropStopId], back_populates="applicationsDrop")


class TransportSubscription(Base):
    __tablename__ = "TransportSubscription"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    routeId = Column(String(191), ForeignKey("TransportRoute.id", ondelete="CASCADE"), nullable=False)
    pickupStopId = Column(String(191), ForeignKey("TransportStop.id", ondelete="CASCADE"), nullable=False)
    dropStopId = Column(String(191), ForeignKey("TransportStop.id", ondelete="CASCADE"), nullable=False)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # PENDING, ACTIVE, SUSPENDED, EXPIRED, CANCELLED
    approvedBy = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[userId], back_populates="transportSubscriptions")
    approver = relationship("User", foreign_keys=[approvedBy], back_populates="approvedSubscriptions")
    route = relationship("TransportRoute", back_populates="subscriptions")
    pickupStop = relationship("TransportStop", foreign_keys=[pickupStopId], back_populates="subscriptionsPickup")
    dropStop = relationship("TransportStop", foreign_keys=[dropStopId], back_populates="subscriptionsDrop")
    allocations = relationship("TransportSeatAllocation", back_populates="subscription", cascade="all, delete-orphan")
    passes = relationship("TransportPass", back_populates="subscription", cascade="all, delete-orphan")


class TransportSeat(Base):
    __tablename__ = "TransportSeat"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    vehicleId = Column(String(191), ForeignKey("TransportVehicle.id", ondelete="CASCADE"), nullable=False)
    seatNumber = Column(String(191), nullable=False)
    seatType = Column(String(191), default="REGULAR", nullable=False)  # REGULAR, PRIORITY, ACCESSIBLE, STAFF
    status = Column(String(191), default="AVAILABLE", nullable=False)  # AVAILABLE, ALLOCATED, BLOCKED, MAINTENANCE
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("TransportVehicle", back_populates="seats")
    allocations = relationship("TransportSeatAllocation", back_populates="seat", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("vehicleId", "seatNumber", name="uix_vehicle_seat"),
    )


class TransportSeatAllocation(Base):
    __tablename__ = "TransportSeatAllocation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    subscriptionId = Column(String(191), ForeignKey("TransportSubscription.id", ondelete="CASCADE"), nullable=False)
    seatId = Column(String(191), ForeignKey("TransportSeat.id", ondelete="CASCADE"), nullable=False)
    allocatedBy = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    allocatedAt = Column(DateTime, default=datetime.utcnow)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscription = relationship("TransportSubscription", back_populates="allocations")
    seat = relationship("TransportSeat", back_populates="allocations")
    allocator = relationship("User", back_populates="allocatedSeats")


class TransportPass(Base):
    __tablename__ = "TransportPass"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    subscriptionId = Column(String(191), ForeignKey("TransportSubscription.id", ondelete="CASCADE"), nullable=False)
    passNumber = Column(String(191), unique=True, nullable=False)
    tokenHash = Column(String(191), unique=True, nullable=False)
    issuedAt = Column(DateTime, default=datetime.utcnow)
    expiresAt = Column(DateTime, nullable=False)
    status = Column(String(191), default="ACTIVE", nullable=False)  # ACTIVE, EXPIRED, REVOKED, SUSPENDED
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)

    subscription = relationship("TransportSubscription", back_populates="passes")
    user = relationship("User", back_populates="transportPasses")


class TransportTrip(Base):
    __tablename__ = "TransportTrip"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    routeId = Column(String(191), ForeignKey("TransportRoute.id", ondelete="CASCADE"), nullable=False)
    vehicleId = Column(String(191), ForeignKey("TransportVehicle.id", ondelete="CASCADE"), nullable=False)
    driverId = Column(String(191), ForeignKey("TransportDriverProfile.id", ondelete="CASCADE"), nullable=False)
    conductorId = Column(String(191), ForeignKey("TransportStaffProfile.id", ondelete="SET NULL"), nullable=True)
    scheduledStartAt = Column(DateTime, nullable=False)
    actualStartAt = Column(DateTime, nullable=True)
    scheduledEndAt = Column(DateTime, nullable=False)
    actualEndAt = Column(DateTime, nullable=True)
    status = Column(String(191), default="SCHEDULED", nullable=False)  # SCHEDULED, BOARDING, IN_PROGRESS, DELAYED, COMPLETED, CANCELLED, BREAKDOWN
    delayMinutes = Column(Integer, default=0, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    route = relationship("TransportRoute", back_populates="trips")
    vehicle = relationship("TransportVehicle", back_populates="trips")
    driver = relationship("TransportDriverProfile", back_populates="trips")
    conductor = relationship("TransportStaffProfile", back_populates="trips")
    boardings = relationship("TransportBoarding", back_populates="trip", cascade="all, delete-orphan")
    locations = relationship("TransportVehicleLocation", back_populates="trip", cascade="all, delete-orphan")
    delays = relationship("TransportDelay", back_populates="trip", cascade="all, delete-orphan")
    incidents = relationship("TransportIncident", back_populates="trip", cascade="all, delete-orphan")


class TransportBoarding(Base):
    __tablename__ = "TransportBoarding"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    tripId = Column(String(191), ForeignKey("TransportTrip.id", ondelete="CASCADE"), nullable=False)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    stopId = Column(String(191), ForeignKey("TransportStop.id", ondelete="CASCADE"), nullable=False)
    boardingType = Column(String(191), nullable=False)  # PICKUP, DROP
    boardedAt = Column(DateTime, default=datetime.utcnow)
    verifiedBy = Column(String(191), ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(191), default="VERIFIED", nullable=False)  # VERIFIED, FLAGGED
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trip = relationship("TransportTrip", back_populates="boardings")
    user = relationship("User", foreign_keys=[userId], back_populates="boardedTrips")
    verifier = relationship("User", foreign_keys=[verifiedBy], back_populates="verifiedBoardings")
    stop = relationship("TransportStop", back_populates="boardings")


class TransportVehicleLocation(Base):
    __tablename__ = "TransportVehicleLocation"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    vehicleId = Column(String(191), ForeignKey("TransportVehicle.id", ondelete="CASCADE"), nullable=False)
    tripId = Column(String(191), ForeignKey("TransportTrip.id", ondelete="CASCADE"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speedKph = Column(Float, nullable=False)
    heading = Column(Float, nullable=False)
    recordedAt = Column(DateTime, default=datetime.utcnow)
    source = Column(String(191), nullable=False)  # GPS_DEVICE, DRIVER_APP, SIMULATOR, MANUAL

    vehicle = relationship("TransportVehicle", back_populates="locations")
    trip = relationship("TransportTrip", back_populates="locations")


class TransportMaintenance(Base):
    __tablename__ = "TransportMaintenance"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    vehicleId = Column(String(191), ForeignKey("TransportVehicle.id", ondelete="CASCADE"), nullable=False)
    maintenanceType = Column(String(191), nullable=False)  # PREVENTIVE, CORRECTIVE, BREAKDOWN, INSPECTION, SERVICE
    description = Column(Text, nullable=False)
    scheduledDate = Column(DateTime, nullable=False)
    startedAt = Column(DateTime, nullable=True)
    completedAt = Column(DateTime, nullable=True)
    odometerKm = Column(Integer, nullable=False)
    estimatedCost = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    actualCost = Column(Numeric(precision=10, scale=2, asdecimal=True), default=0.0, nullable=False)
    vendorName = Column(String(191), nullable=False)
    status = Column(String(191), default="SCHEDULED", nullable=False)  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("TransportVehicle", back_populates="maintenances")


class TransportFuelLog(Base):
    __tablename__ = "TransportFuelLog"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    vehicleId = Column(String(191), ForeignKey("TransportVehicle.id", ondelete="CASCADE"), nullable=False)
    filledAt = Column(DateTime, nullable=False)
    quantityLitres = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    unitPrice = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    totalAmount = Column(Numeric(precision=10, scale=2, asdecimal=True), nullable=False)
    odometerKm = Column(Integer, nullable=False)
    fuelStation = Column(String(191), nullable=False)
    recordedBy = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("TransportVehicle", back_populates="fuelLogs")
    recorder = relationship("User", back_populates="recordedFuelLogs")


class TransportIncident(Base):
    __tablename__ = "TransportIncident"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    tripId = Column(String(191), ForeignKey("TransportTrip.id", ondelete="CASCADE"), nullable=True)
    vehicleId = Column(String(191), ForeignKey("TransportVehicle.id", ondelete="CASCADE"), nullable=False)
    reportedBy = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(191), nullable=False)  # ACCIDENT, BREAKDOWN, DELAY, MEDICAL, SECURITY, BEHAVIOR, OTHER
    severity = Column(String(191), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    locationText = Column(String(191), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    occurredAt = Column(DateTime, nullable=False)
    status = Column(String(191), default="OPEN", nullable=False)  # OPEN, INVESTIGATING, RESOLVED, CLOSED
    resolution = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trip = relationship("TransportTrip", back_populates="incidents")
    vehicle = relationship("TransportVehicle", back_populates="incidents")
    reporter = relationship("User", back_populates="reportedTransportIncidents")


class TransportDelay(Base):
    __tablename__ = "TransportDelay"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    tripId = Column(String(191), ForeignKey("TransportTrip.id", ondelete="CASCADE"), nullable=False)
    delayMinutes = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    reportedAt = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False, nullable=False)

    trip = relationship("TransportTrip", back_populates="delays")


class TransportAudit(Base):
    __tablename__ = "TransportAudit"
    id = Column(String(191), primary_key=True, default=generate_uuid)
    userId = Column(String(191), ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(191), nullable=False)
    details = Column(Text, nullable=True)
    ipAddress = Column(String(191), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transportAudits")
