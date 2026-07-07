from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import (
    User, ParentProfile, ParentStudentLink, ParentTeacherMeeting,
    ParentMeetingNote, ParentConsent, ParentNotificationPreference, ParentAudit,
    AttendanceRecord, AttendanceSession, AssignmentSubmission, Assignment,
    ExamSchedule, Exam, Result, ResultDetail, FeeInvoice, Payment,
    BookLoan, LibraryFine, LibraryMembership, HostelAllocation, HostelLeaveRequest, HostelComplaint,
    TransportSubscription, TransportRoute, TransportStop, TransportVehicleLocation,
    TransportTrip
)

router = APIRouter()

# Helper for Parent Auditing
def log_parent_audit(db: Session, parent_profile_id: Optional[str], user_id: str, action: str, details: str, ip: Optional[str] = None):
    audit = ParentAudit(
        parentId=parent_profile_id,
        userId=user_id,
        action=action,
        details=details,
        ipAddress=ip
    )
    db.add(audit)
    db.commit()

# Core security dependency
def check_parent_child_access(db: Session, parent_user: User, student_id: str, scope: Optional[str] = None) -> ParentStudentLink:
    if parent_user.role.name == "MASTER_ADMIN":
        # Master Admin has bypass authorization
        link = db.query(ParentStudentLink).filter_by(studentId=student_id).first()
        if not link:
            # Create a mock link container if admin requests directly
            return ParentStudentLink(studentId=student_id, relationship="ADMIN_OVERWRITE")
        return link

    if parent_user.role.name != "PARENT":
        raise HTTPException(status_code=403, detail="Access denied. User role must be PARENT.")

    parent_profile = db.query(ParentProfile).filter_by(userId=parent_user.id).first()
    if not parent_profile:
        raise HTTPException(status_code=403, detail="Active parent profile not found.")

    link = db.query(ParentStudentLink).filter_by(parentId=parent_profile.id, studentId=student_id).first()
    if not link:
        raise HTTPException(status_code=403, detail="Access denied. Parent is not linked to this student.")

    if link.status != "VERIFIED":
        raise HTTPException(status_code=403, detail=f"Access denied. Parent-child link status is currently {link.status}.")

    if scope:
        scope_attr = f"canView{scope}"
        if hasattr(link, scope_attr) and not getattr(link, scope_attr):
            raise HTTPException(status_code=403, detail=f"Access denied. Viewing child {scope.lower()} data is disabled by policy.")

    return link


# --- SCHEMAS ---
class ChildOut(BaseModel):
    id: str
    name: str
    email: str
    username: str
    relationship: str
    isPrimaryContact: bool = True
    status: str

    class Config:
        from_attributes = True

class OverviewOut(BaseModel):
    studentId: str
    studentName: str
    attendancePercentage: float
    presentDays: int
    absentDays: int
    lateDays: int
    pendingAssignments: int
    submittedAssignments: int
    upcomingExams: int
    latestSGPA: float
    outstandingFees: float
    overdueBooks: int
    hostelRoom: Optional[str] = None
    transportRoute: Optional[str] = None

class MeetingRequest(BaseModel):
    studentId: str
    teacherUserId: str
    scheduledAt: datetime
    durationMinutes: Optional[int] = 30
    meetingMode: Optional[str] = "ONLINE"
    agenda: str

class MeetingReview(BaseModel):
    status: str
    approvedBy: Optional[str] = None

class MeetingNoteCreate(BaseModel):
    noteText: str
    visibleToParent: Optional[bool] = True
    staffOnly: Optional[bool] = False

class ConsentResponse(BaseModel):
    status: str # APPROVED, DECLINED

class PreferenceUpdate(BaseModel):
    attendanceAlerts: Optional[bool] = None
    assignmentAlerts: Optional[bool] = None
    examAlerts: Optional[bool] = None
    resultAlerts: Optional[bool] = None
    feeAlerts: Optional[bool] = None
    libraryAlerts: Optional[bool] = None
    hostelAlerts: Optional[bool] = None
    transportAlerts: Optional[bool] = None
    emergencyAlerts: Optional[bool] = None
    eventAlerts: Optional[bool] = None
    channels: Optional[str] = None


# --- ENDPOINTS ---

@router.get("/children", response_model=List[ChildOut])
def get_linked_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve all student accounts linked to the logged-in parent."""
    if current_user.role.name == "MASTER_ADMIN":
        links = db.query(ParentStudentLink).all()
    else:
        parent_profile = db.query(ParentProfile).filter_by(userId=current_user.id).first()
        if not parent_profile:
            return []
        links = db.query(ParentStudentLink).filter_by(parentId=parent_profile.id).all()

    results = []
    for link in links:
        student = db.query(User).filter_by(id=link.studentId).first()
        if student:
            results.append({
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "username": student.username,
                "relationship": link.relationship,
                "isPrimaryContact": link.isPrimaryContact,
                "status": link.status
            })
    return results


@router.get("/children/{studentId}/overview", response_model=OverviewOut)
def get_child_overview(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Compile overall metrics ledger for a linked child."""
    check_parent_child_access(db, current_user, studentId)

    # 1. Attendance stats
    records = db.query(AttendanceRecord).filter_by(studentId=studentId).all()
    total_records = len(records)
    present = sum(1 for r in records if r.status == "PRESENT")
    absent = sum(1 for r in records if r.status == "ABSENT")
    late = sum(1 for r in records if r.status == "LATE")
    att_pct = (present / total_records * 100.0) if total_records > 0 else 100.0

    # 2. Assignments stats
    submissions = db.query(AssignmentSubmission).filter_by(studentId=studentId).all()
    submitted_count = len(submissions)

    # Outstanding assignments
    student_user = db.query(User).filter_by(id=studentId).first()
    section_id = student_user.sectionId if student_user else None

    total_defs = 0
    if section_id:
        total_defs = db.query(Assignment).filter_by(sectionId=section_id).count()
    pending_assignments = max(0, total_defs - submitted_count)

    # 3. Exams stats
    upcoming_exams = db.query(Exam).filter(Exam.examDate > datetime.utcnow()).count()

    # 4. Results SGPA
    sgpa = 0.0
    latest_res = db.query(Result).filter_by(studentId=studentId).order_by(Result.createdAt.desc()).first()
    if latest_res:
        sgpa = float(latest_res.sgpa)

    # 5. Finance
    invoices = db.query(FeeInvoice).filter_by(studentId=studentId).all()
    outstanding = sum(float(inv.balanceAmount) for inv in invoices)

    # 6. Library Fines / Loans
    membership = db.query(LibraryMembership).filter_by(userId=studentId).first()
    overdue_loans = 0
    if membership:
        overdue_loans = db.query(BookLoan).filter(
            BookLoan.membershipId == membership.id,
            BookLoan.returnedAt == None,
            BookLoan.dueAt < datetime.utcnow()
        ).count()

    # 7. Hostel status
    hostel_room = None
    alloc = db.query(HostelAllocation).filter_by(studentId=studentId, status="ACTIVE").first()
    if alloc and alloc.room:
        hostel_room = f"Block {alloc.room.block.name} - Room {alloc.room.roomNumber}"

    # 8. Transport route
    transport_route = None
    sub = db.query(TransportSubscription).filter_by(userId=studentId, status="ACTIVE").first()
    if sub and sub.route:
        transport_route = f"{sub.route.code} - {sub.route.name}"

    # Log parent audit trigger
    parent_prof = db.query(ParentProfile).filter_by(userId=current_user.id).first()
    parent_prof_id = parent_prof.id if parent_prof else None
    log_parent_audit(db, parent_prof_id, current_user.id, "VIEW_OVERVIEW", f"Viewed overview dashboard for student {studentId}")

    return {
        "studentId": studentId,
        "studentName": student_user.name if student_user else "Student",
        "attendancePercentage": att_pct,
        "presentDays": present,
        "absentDays": absent,
        "lateDays": late,
        "pendingAssignments": pending_assignments,
        "submittedAssignments": submitted_count,
        "upcomingExams": upcoming_exams,
        "latestSGPA": sgpa,
        "outstandingFees": outstanding,
        "overdueBooks": overdue_loans,
        "hostelRoom": hostel_room,
        "transportRoute": transport_route
    }


@router.get("/children/{studentId}/academics")
def get_child_academics(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve linked child's enrolled program, department, and section details."""
    check_parent_child_access(db, current_user, studentId, "Academics")
    student = db.query(User).filter_by(id=studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    return {
        "studentId": student.id,
        "studentName": student.name,
        "department": student.department.name if student.department else "General Academics",
        "section": student.section.name if student.section else "Not Assigned",
        "email": student.email,
        "status": student.status
    }


@router.get("/children/{studentId}/attendance")
def get_child_attendance(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve child's detailed attendance records list."""
    check_parent_child_access(db, current_user, studentId, "Attendance")
    records = db.query(AttendanceRecord).filter_by(studentId=studentId).order_by(AttendanceRecord.createdAt.desc()).all()

    return [
        {
            "id": r.id,
            "sessionDate": r.session.date.isoformat() if r.session else r.createdAt.date().isoformat(),
            "subject": r.session.subject.name if (r.session and r.session.subject) else "General Attendance",
            "status": r.status,
            "recordedAt": r.createdAt.isoformat(),
        } for r in records
    ]


@router.get("/children/{studentId}/assignments")
def get_child_assignments(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve assignments and child submission evaluation details."""
    check_parent_child_access(db, current_user, studentId, "Assignments")
    student = db.query(User).filter_by(id=studentId).first()
    section_id = student.sectionId if student else None

    if not section_id:
        return []

    assignments = db.query(Assignment).filter(Assignment.sectionId == section_id, Assignment.status == "PUBLISHED").all()
    submissions = {s.assignmentId: s for s in db.query(AssignmentSubmission).filter_by(studentId=studentId).all()}

    results = []
    for a in assignments:
        sub = submissions.get(a.id)
        results.append({
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "dueDate": a.dueDate.isoformat(),
            "submitted": sub is not None,
            "submittedAt": sub.submittedAt.isoformat() if (sub and sub.submittedAt) else None,
            "grade": sub.grade if sub else None,
            "marks": sub.marksObtained if sub else None,
            "feedback": sub.feedback if sub else None
        })
    return results


@router.get("/children/{studentId}/exams")
def get_child_exams(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve upcoming exam calendars."""
    check_parent_child_access(db, current_user, studentId, "Academics")
    student = db.query(User).filter_by(id=studentId).first()
    section_id = student.sectionId if student else None

    if not section_id:
        return []

    exams = db.query(Exam).filter_by(sectionId=section_id).order_by(Exam.examDate.asc()).all()
    return [
        {
            "id": e.id,
            "examName": e.examName,
            "subject": e.subject.name if e.subject else "General subject",
            "date": e.examDate.isoformat(),
            "startTime": e.startTime,
            "endTime": e.endTime,
            "room": "Allocated Exam Hall"
        } for e in exams
    ]


@router.get("/children/{studentId}/results")
def get_child_results(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve child's published academic grades. Filters out unpublished draft results."""
    check_parent_child_access(db, current_user, studentId, "Results")

    # Query results filtering only where result status is PUBLISHED
    db_results = db.query(Result).filter(
        Result.studentId == studentId,
        Result.status == "PUBLISHED"
    ).all()

    details_list = []
    for r in db_results:
        for d in r.details:
            details_list.append({
                "id": d.id,
                "examName": f"Semester {r.semesterNumber} Final",
                "subjectName": d.subject.name if d.subject else "Core subject",
                "marksObtained": float(d.totalMarks),
                "grade": d.grade,
                "credits": d.subject.credits if d.subject else 3,
                "publishedAt": r.createdAt.isoformat()
            })
    return details_list


@router.get("/children/{studentId}/fees")
def get_child_fees(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve child's invoices and payment transactions list."""
    check_parent_child_access(db, current_user, studentId, "Fees")
    invoices = db.query(FeeInvoice).filter_by(studentId=studentId).order_by(FeeInvoice.dueDate.desc()).all()

    return [
        {
            "id": i.id,
            "invoiceNumber": i.invoiceNumber,
            "title": "Tuition Fee Invoice",
            "amount": float(i.totalAmount),
            "paidAmount": float(i.paidAmount),
            "outstanding": float(i.balanceAmount),
            "dueDate": i.dueDate.isoformat(),
            "status": i.status
        } for i in invoices
    ]


@router.get("/children/{studentId}/library")
def get_child_library(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve child's currently checked out library items."""
    check_parent_child_access(db, current_user, studentId, "Library")
    membership = db.query(LibraryMembership).filter_by(userId=studentId).first()

    loans = []
    fines = []
    if membership:
        loans = db.query(BookLoan).filter(BookLoan.membershipId == membership.id, BookLoan.returnedAt == None).all()
        fines = db.query(LibraryFine).filter(LibraryFine.membershipId == membership.id).all()

    return {
        "activeLoans": [
            {
                "id": l.id,
                "bookTitle": l.copy.book.title if (l.copy and l.copy.book) else "Library Item",
                "issuedAt": l.issuedAt.isoformat(),
                "dueDate": l.dueAt.isoformat(),
                "status": "OVERDUE" if l.dueAt < datetime.utcnow() else "ACTIVE"
            } for l in loans
        ],
        "pendingFines": [
            {
                "id": f.id,
                "amount": float(f.amount),
                "reason": f.reason,
                "status": f.status
            } for f in fines
        ]
    }


@router.get("/children/{studentId}/hostel")
def get_child_hostel(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve child's hostel allocation summary and leave history."""
    check_parent_child_access(db, current_user, studentId, "Hostel")
    alloc = db.query(HostelAllocation).filter_by(studentId=studentId, status="ACTIVE").first()
    leaves = db.query(HostelLeaveRequest).filter_by(studentId=studentId).all()
    complaints = db.query(HostelComplaint).filter_by(studentId=studentId).all()

    return {
        "allocated": alloc is not None,
        "roomDetails": {
            "hostelName": alloc.room.block.hostel.name if (alloc and alloc.room) else None,
            "blockName": alloc.room.block.name if (alloc and alloc.room) else None,
            "roomNumber": alloc.room.roomNumber if (alloc and alloc.room) else None,
            "floor": alloc.room.floor if (alloc and alloc.room) else None
        } if alloc else None,
        "leaves": [
            {
                "id": l.id,
                "startDate": l.startDate.isoformat(),
                "endDate": l.endDate.isoformat(),
                "reason": l.reason,
                "status": l.status
            } for l in leaves
        ],
        "complaints": [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "createdAt": c.createdAt.isoformat()
            } for c in complaints
        ]
    }


@router.get("/children/{studentId}/transport")
def get_child_transport(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve child's transport route stops and simulated GPS tracking details."""
    check_parent_child_access(db, current_user, studentId, "Transport")
    sub = db.query(TransportSubscription).filter_by(userId=studentId, status="ACTIVE").first()
    if not sub:
        return {"assigned": False}

    vehicle = sub.vehicle
    location = db.query(TransportVehicleLocation).filter_by(vehicleId=vehicle.id).order_by(TransportVehicleLocation.timestamp.desc()).first() if vehicle else None

    return {
        "assigned": True,
        "routeCode": sub.route.code if sub.route else "N/A",
        "routeName": sub.route.name if sub.route else "N/A",
        "pickupStop": sub.pickupStop.name if sub.pickupStop else "N/A",
        "dropStop": sub.dropStop.name if sub.dropStop else "N/A",
        "vehicleCode": vehicle.vehicleCode if vehicle else "N/A",
        "driverName": vehicle.driverProfile.user.name if (vehicle and vehicle.driverProfile and vehicle.driverProfile.user) else "N/A",
        "gps": {
            "latitude": location.latitude if location else 12.9716,
            "longitude": location.longitude if location else 77.5946,
            "speedKph": location.speedKph if location else 0.0,
            "heading": location.heading if location else 0.0,
            "source": "SIMULATED DEMO DATA"
        }
    }


# --- MEETINGS ---

@router.get("/meetings")
def list_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve parent teacher meetings list."""
    if current_user.role.name == "MASTER_ADMIN":
        meetings = db.query(ParentTeacherMeeting).all()
    elif current_user.role.name == "PARENT":
        meetings = db.query(ParentTeacherMeeting).filter_by(parentUserId=current_user.id).all()
    else:
        # Teacher User
        meetings = db.query(ParentTeacherMeeting).filter_by(teacherUserId=current_user.id).all()

    return [
        {
            "id": m.id,
            "studentName": m.student.name if m.student else "Student",
            "teacherName": m.teacherUser.name if m.teacherUser else "Teacher",
            "parentName": m.parentUser.name if m.parentUser else "Parent",
            "scheduledAt": m.scheduledAt.isoformat(),
            "durationMinutes": m.durationMinutes,
            "meetingMode": m.meetingMode,
            "locationOrLink": m.locationOrLink,
            "agenda": m.agenda,
            "status": m.status,
            "requestedBy": m.requestedBy,
            "notes": [
                {
                    "id": n.id,
                    "authorName": n.author.name if n.author else "Staff",
                    "noteText": n.noteText,
                    "createdAt": n.createdAt.isoformat()
                } for n in m.notes if n.visibleToParent or current_user.role.name in ["MASTER_ADMIN", "TEACHER"]
            ]
        } for m in meetings
    ]


@router.post("/meetings")
def schedule_meeting(
    payload: MeetingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Create parent teacher meeting request."""
    # Ensure link exists to requested student
    check_parent_child_access(db, current_user, payload.studentId)

    meeting = ParentTeacherMeeting(
        parentUserId=current_user.id,
        studentId=payload.studentId,
        teacherUserId=payload.teacherUserId,
        scheduledAt=payload.scheduledAt,
        durationMinutes=payload.durationMinutes,
        meetingMode=payload.meetingMode,
        agenda=payload.agenda,
        requestedBy="PARENT"
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return {
        "id": meeting.id,
        "parentUserId": meeting.parentUserId,
        "studentId": meeting.studentId,
        "teacherUserId": meeting.teacherUserId,
        "scheduledAt": meeting.scheduledAt.isoformat(),
        "durationMinutes": meeting.durationMinutes,
        "meetingMode": meeting.meetingMode,
        "agenda": meeting.agenda,
        "status": meeting.status,
        "requestedBy": meeting.requestedBy
    }


@router.patch("/meetings/{id}")
def review_meeting(
    id: str,
    payload: MeetingReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Approve, reject, or update meeting states."""
    meeting = db.query(ParentTeacherMeeting).filter_by(id=id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"] and meeting.parentUserId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this meeting schedule.")

    meeting.status = payload.status
    if payload.approvedBy:
        meeting.approvedBy = payload.approvedBy

    db.commit()
    return {
        "id": meeting.id,
        "parentUserId": meeting.parentUserId,
        "studentId": meeting.studentId,
        "teacherUserId": meeting.teacherUserId,
        "scheduledAt": meeting.scheduledAt.isoformat(),
        "durationMinutes": meeting.durationMinutes,
        "meetingMode": meeting.meetingMode,
        "agenda": meeting.agenda,
        "status": meeting.status,
        "requestedBy": meeting.requestedBy
    }


@router.post("/meetings/{id}/notes")
def add_meeting_note(
    id: str,
    payload: MeetingNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Add feedback or staff notes to meeting files."""
    meeting = db.query(ParentTeacherMeeting).filter_by(id=id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    # Validate auth access
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"] and meeting.parentUserId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to write notes for this meeting.")

    note = ParentMeetingNote(
        meetingId=meeting.id,
        authorId=current_user.id,
        noteText=payload.noteText,
        visibleToParent=payload.visibleToParent,
        staffOnly=payload.staffOnly
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {
        "id": note.id,
        "meetingId": note.meetingId,
        "authorId": note.authorId,
        "noteText": note.noteText,
        "visibleToParent": note.visibleToParent,
        "staffOnly": note.staffOnly,
        "createdAt": note.createdAt.isoformat()
    }


# --- CONSENTS ---

@router.get("/consents")
def list_consents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Retrieve permission release consents checklist logs."""
    if current_user.role.name == "MASTER_ADMIN":
        consents = db.query(ParentConsent).all()
    else:
        consents = db.query(ParentConsent).filter_by(parentUserId=current_user.id).all()

    return [
        {
            "id": c.id,
            "studentName": c.student.name if c.student else "Student",
            "consentType": c.consentType,
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "respondedAt": c.respondedAt.isoformat() if c.respondedAt else None,
            "expiresAt": c.expiresAt.isoformat() if c.expiresAt else None
        } for c in consents
    ]


@router.post("/consents/{id}/respond")
def respond_consent(
    id: str,
    payload: ConsentResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Submit consent response details (approve/decline permissions)."""
    consent = db.query(ParentConsent).filter_by(id=id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent request not found.")

    if current_user.role.name != "MASTER_ADMIN" and consent.parentUserId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to sign this consent form.")

    if consent.expiresAt and consent.expiresAt < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This consent request has expired.")

    consent.status = payload.status
    consent.respondedAt = datetime.utcnow()
    db.commit()
    return {
        "id": consent.id,
        "parentUserId": consent.parentUserId,
        "studentId": consent.studentId,
        "consentType": consent.consentType,
        "title": consent.title,
        "description": consent.description,
        "status": consent.status,
        "respondedAt": consent.respondedAt.isoformat() if consent.respondedAt else None,
        "expiresAt": consent.expiresAt.isoformat() if consent.expiresAt else None
    }


# --- PREFERENCES ---

@router.get("/notification-preferences")
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Get parent alert channel preferences."""
    parent_prof = db.query(ParentProfile).filter_by(userId=current_user.id).first()
    if not parent_prof:
        raise HTTPException(status_code=404, detail="Parent profile not found.")

    pref = db.query(ParentNotificationPreference).filter_by(parentProfileId=parent_prof.id).first()
    if not pref:
        pref = ParentNotificationPreference(parentProfileId=parent_prof.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)

    return {
        "id": pref.id,
        "parentProfileId": pref.parentProfileId,
        "attendanceAlerts": pref.attendanceAlerts,
        "assignmentAlerts": pref.assignmentAlerts,
        "examAlerts": pref.examAlerts,
        "resultAlerts": pref.resultAlerts,
        "feeAlerts": pref.feeAlerts,
        "libraryAlerts": pref.libraryAlerts,
        "hostelAlerts": pref.hostelAlerts,
        "transportAlerts": pref.transportAlerts,
        "emergencyAlerts": pref.emergencyAlerts,
        "eventAlerts": pref.eventAlerts,
        "channels": pref.channels
    }


@router.put("/notification-preferences")
def update_preferences(
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Update parent alert channel preferences."""
    parent_prof = db.query(ParentProfile).filter_by(userId=current_user.id).first()
    if not parent_prof:
        raise HTTPException(status_code=404, detail="Parent profile not found.")

    pref = db.query(ParentNotificationPreference).filter_by(parentProfileId=parent_prof.id).first()
    if not pref:
        pref = ParentNotificationPreference(parentProfileId=parent_prof.id)
        db.add(pref)

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(pref, field, val)

    db.commit()
    db.refresh(pref)
    return {
        "id": pref.id,
        "parentProfileId": pref.parentProfileId,
        "attendanceAlerts": pref.attendanceAlerts,
        "assignmentAlerts": pref.assignmentAlerts,
        "examAlerts": pref.examAlerts,
        "resultAlerts": pref.resultAlerts,
        "feeAlerts": pref.feeAlerts,
        "libraryAlerts": pref.libraryAlerts,
        "hostelAlerts": pref.hostelAlerts,
        "transportAlerts": pref.transportAlerts,
        "emergencyAlerts": pref.emergencyAlerts,
        "eventAlerts": pref.eventAlerts,
        "channels": pref.channels
    }


# --- ALERTS ---

@router.get("/alerts")
def get_child_alerts(
    studentId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    """Compile aggregated risk indicators or reminders for the student."""
    check_parent_child_access(db, current_user, studentId)

    alerts = []

    # 1. Attendance warning check (Rule-based warning if under 75%)
    records = db.query(AttendanceRecord).filter_by(studentId=studentId).all()
    total = len(records)
    present = sum(1 for r in records if r.status == "PRESENT")
    att_pct = (present / total * 100.0) if total > 0 else 100.0
    if att_pct < 75.0:
        alerts.append({
            "category": "ATTENDANCE_RISK",
            "title": "Low Attendance Warning",
            "message": f"Attendance is currently at {round(att_pct, 1)}%, which is below the required 75.0% threshold. [RULE-BASED ALERT]",
            "severity": "HIGH"
        })

    # 2. Assignment warning check
    student = db.query(User).filter_by(id=studentId).first()
    section_id = student.sectionId if student else None
    if section_id:
        assignments = db.query(Assignment).filter_by(sectionId=section_id).all()
        submissions = {s.assignmentId for s in db.query(AssignmentSubmission).filter_by(studentId=studentId).all()}

        overdue_count = 0
        for a in assignments:
            if a.id not in submissions and a.dueDate < datetime.utcnow():
                overdue_count += 1
        if overdue_count > 0:
            alerts.append({
                "category": "ASSIGNMENT_OVERDUE",
                "title": "Overdue Assignments",
                "message": f"Student has {overdue_count} assignments past their due dates. [RULE-BASED ALERT]",
                "severity": "MEDIUM"
            })

    return alerts
