import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, ParentProfile, ParentStudentLink, ParentMessage,
    ParentNotification, ParentAudit, AttendanceRecord, StudentResult,
    StudentAssignment, FeeInvoice, Receipt, Scholarship, StudentScholarship
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class ParentCreatePayload(BaseModel):
    email: EmailStr
    username: str
    name: str
    fatherName: Optional[str] = None
    motherName: Optional[str] = None
    guardianName: Optional[str] = None
    relationshipType: str = "GUARDIAN"
    occupation: Optional[str] = None
    phoneNumber: str
    address: Optional[str] = None

class StudentLinkPayload(BaseModel):
    parentId: str
    studentId: str
    relationship: str
    isPrimaryContact: bool = True

class SendMessagePayload(BaseModel):
    receiverId: str
    content: str

# -------------------------------------------------------------
# HELPER OWNERSHIP VALIDATION
# -------------------------------------------------------------
def verify_linked_student(db: Session, parent_user: User, student_id: str) -> ParentProfile:
    # Ensure role is PARENT
    if parent_user.role.name != "PARENT":
        raise HTTPException(status_code=403, detail="User is not authorized as a parent.")
    
    profile = db.query(ParentProfile).filter(ParentProfile.userId == parent_user.id).first()
    if not profile:
        raise HTTPException(status_code=403, detail="Parent profile record not found.")

    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.parentId == profile.id,
        ParentStudentLink.studentId == student_id
    ).first()

    if not link:
        raise HTTPException(status_code=403, detail="Unauthorized: Selected student is not linked to your parent account.")

    return profile

def log_parent_audit(db: Session, parent_id: Optional[str], user_id: str, action: str, details: str, request: Request = None):
    ip_addr = request.client.host if request and request.client else "127.0.0.1"
    audit = ParentAudit(
        parentId=parent_id,
        userId=user_id,
        action=action,
        details=details,
        ipAddress=ip_addr
    )
    db.add(audit)
    db.commit()

# -------------------------------------------------------------
# PARENT MANAGEMENT ENDPOINTS (ADMIN / ADMISSION)
# -------------------------------------------------------------

@router.post("")
def create_parent_profile(
    payload: ParentCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    # Restricted to Master Admin or Admission Office
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied. Admin permissions required.")

    # Check if user already exists
    user = db.query(User).filter(or_(User.email == payload.email, User.username == payload.username)).first()
    if not user:
        parent_role = db.query(Role).filter(Role.name == "PARENT").first()
        if not parent_role:
            parent_role = Role(name="PARENT", description="Parent role")
            db.add(parent_role)
            db.flush()

        user = User(
            email=payload.email,
            username=payload.username,
            passwordHash="PBKDF2_INSECURE_MOCK",
            name=payload.name,
            roleId=parent_role.id
        )
        db.add(user)
        db.flush()

    # Verify profile does not already exist
    existing_profile = db.query(ParentProfile).filter(ParentProfile.userId == user.id).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Parent profile already configured for this user.")

    profile = ParentProfile(
        userId=user.id,
        fatherName=payload.fatherName,
        motherName=payload.motherName,
        guardianName=payload.guardianName,
        relationshipType=payload.relationshipType,
        occupation=payload.occupation,
        phoneNumber=payload.phoneNumber,
        address=payload.address
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return make_response(success=True, message="Parent profile created successfully.", data={"id": profile.id})

@router.post("/link")
def link_student_to_parent(
    payload: StudentLinkPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied. Admin permissions required.")

    parent = db.query(ParentProfile).filter(ParentProfile.id == payload.parentId).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent profile not found.")

    student = db.query(User).filter(User.id == payload.studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student user not found.")

    # Prevent duplicate linkages
    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.parentId == parent.id,
        ParentStudentLink.studentId == student.id
    ).first()
    if link:
        return make_response(success=True, message="Student already linked to parent.", data={"id": link.id})

    link = ParentStudentLink(
        parentId=parent.id,
        studentId=student.id,
        relationship=payload.relationship,
        isPrimaryContact=payload.isPrimaryContact
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    log_parent_audit(db, parent.id, current_user.id, "LINK_STUDENT", f"Linked student {student.name} to parent profile.")

    return make_response(success=True, message="Student successfully linked to parent.", data={"id": link.id})

# -------------------------------------------------------------
# STUDENT DATA VIEW ENDPOINTS (PARENT CONTEXT)
# -------------------------------------------------------------

@router.get("/students")
def get_linked_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "PARENT":
        raise HTTPException(status_code=403, detail="Access denied.")

    profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Parent profile not found.")

    links = db.query(ParentStudentLink).filter(ParentStudentLink.parentId == profile.id).all()
    students_list = []
    for l in links:
        stud = db.query(User).filter(User.id == l.studentId).first()
        if stud:
            students_list.append({
                "studentId": stud.id,
                "name": stud.name,
                "email": stud.email,
                "relationship": l.relationship
            })

    return make_response(success=True, message="Linked students retrieved.", data=students_list)

@router.get("/students/{studentId}/attendance")
def get_student_attendance(
    studentId: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    profile = verify_linked_student(db, current_user, studentId)
    
    # Query attendance records
    records = db.query(AttendanceRecord).filter(AttendanceRecord.studentId == studentId).all()
    total = len(records)
    present = sum(1 for r in records if r.status == "PRESENT")
    ratio = (present / total * 100.0) if total > 0 else 100.0

    log_parent_audit(db, profile.id, current_user.id, "VIEW_ATTENDANCE", f"Inspected attendance for student: {studentId}", request)

    return make_response(
        success=True,
        message="Attendance data calculated.",
        data={
            "attendancePercentage": ratio,
            "totalSessions": total,
            "presentCount": present,
            "lowAttendanceAlert": ratio < 75.0,
            "history": [{
                "id": r.id,
                "status": r.status,
                "date": r.createdAt.isoformat() if r.createdAt else None
            } for r in records]
        }
    )

@router.get("/students/{studentId}/results")
def get_student_results(
    studentId: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    profile = verify_linked_student(db, current_user, studentId)

    results = db.query(StudentResult).filter(StudentResult.studentId == studentId).all()

    log_parent_audit(db, profile.id, current_user.id, "VIEW_RESULTS", f"Inspected academic results for student: {studentId}", request)

    return make_response(
        success=True,
        message="Results data fetched.",
        data={
            "sgpa": 8.4, # mock summary fallback
            "cgpa": 8.2,
            "transcriptsCount": len(results),
            "results": [{
                "id": r.id,
                "courseName": r.courseId, # mock course field mapping
                "grade": r.grade,
                "marksObtained": float(r.marksObtained) if r.marksObtained else 0.0,
                "status": r.status
            } for r in results]
        }
    )

@router.get("/students/{studentId}/assignments")
def get_student_assignments(
    studentId: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    profile = verify_linked_student(db, current_user, studentId)

    assignments = db.query(StudentAssignment).filter(StudentAssignment.studentId == studentId).all()

    log_parent_audit(db, profile.id, current_user.id, "VIEW_ASSIGNMENTS", f"Inspected assignments for student: {studentId}", request)

    return make_response(
        success=True,
        message="Assignments list compiled.",
        data=[{
            "id": a.id,
            "title": a.assignmentDefId, # mock def mapping
            "status": a.status,
            "marks": float(a.obtainedMarks) if a.obtainedMarks else None,
            "feedback": a.feedback
        } for a in assignments]
    )

@router.get("/students/{studentId}/fees")
def get_student_fees(
    studentId: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    profile = verify_linked_student(db, current_user, studentId)

    invoices = db.query(FeeInvoice).filter(FeeInvoice.studentId == studentId).all()
    scholarships = db.query(StudentScholarship).filter(StudentScholarship.studentId == studentId).all()

    log_parent_audit(db, profile.id, current_user.id, "VIEW_FEES", f"Inspected fee status ledger for student: {studentId}", request)

    return make_response(
        success=True,
        message="Fee summaries retrieved.",
        data={
            "outstandingBalance": float(sum(i.balanceAmount for i in invoices)),
            "invoices": [{
                "id": i.id,
                "invoiceNumber": i.invoiceNumber,
                "totalAmount": float(i.totalAmount),
                "paidAmount": float(i.paidAmount),
                "balanceAmount": float(i.balanceAmount),
                "status": i.status,
                "dueDate": i.dueDate.isoformat() if i.dueDate else None
            } for i in invoices],
            "scholarships": [{
                "id": s.id,
                "amountAwarded": float(s.amountAwarded)
            } for s in scholarships]
        }
    )

# -------------------------------------------------------------
# MESSAGING & ALERTS ENDPOINTS
# -------------------------------------------------------------

@router.get("/messages")
def get_parent_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    # Fetch direct messages sent or received by current parent user
    msgs = db.query(ParentMessage).filter(
        or_(
            ParentMessage.senderId == current_user.id,
            ParentMessage.receiverId == current_user.id
        )
    ).order_by(desc(ParentMessage.createdAt)).all()

    return make_response(
        success=True,
        message="Message history compiled.",
        data=[{
            "id": m.id,
            "senderId": m.senderId,
            "receiverId": m.receiverId,
            "content": m.content,
            "isRead": m.isRead,
            "createdAt": m.createdAt.isoformat()
        } for m in msgs]
    )

@router.post("/messages")
def send_parent_message(
    payload: SendMessagePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    receiver = db.query(User).filter(User.id == payload.receiverId).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver user not found.")

    msg = ParentMessage(
        senderId=current_user.id,
        receiverId=receiver.id,
        content=payload.content,
        isRead=False
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Auditing
    profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
    log_parent_audit(db, profile.id if profile else None, current_user.id, "SEND_MESSAGE", f"Sent message to user {receiver.name}")

    return make_response(success=True, message="Message sent successfully.", data={"id": msg.id})

@router.get("/notifications")
def get_parent_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Parent profile not found.")

    notifs = db.query(ParentNotification).filter(ParentNotification.parentId == profile.id).all()
    return make_response(
        success=True,
        message="Parent notifications retrieved.",
        data=[{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "category": n.category,
            "isRead": n.isRead,
            "createdAt": n.createdAt.isoformat()
        } for n in notifs]
    )

@router.post("/notifications/{id}/read")
def mark_notification_read(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Parent profile not found.")

    notif = db.query(ParentNotification).filter(
        ParentNotification.id == id,
        ParentNotification.parentId == profile.id
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.isRead = True
    db.commit()

    return make_response(success=True, message="Notification marked as read.")
