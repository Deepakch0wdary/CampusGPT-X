import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, Department, Section, AcademicYear, Program, Course, Semester, Subject,
    StudentAttendanceSummary, StudentResult, StudentAssignment, StudentCertificate,
    StudentDocument, StudentNotification, UserProfile, AuditLog
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class StudentProfileUpdateSchema(BaseModel):
    phoneNumber: Optional[str] = None
    address: Optional[str] = None
    parentName: Optional[str] = None
    parentPhone: Optional[str] = None
    emergencyContact: Optional[str] = None
    bloodGroup: Optional[str] = None

class AssignmentSubmitSchema(BaseModel):
    submissionUrl: str

class CertificateRequestSchema(BaseModel):
    certificateType: str # BONAFIDE, STUDY, TRANSFER, FEE_RECEIPT

# -------------------------------------------------------------
# HELPER GATES
# -------------------------------------------------------------
def get_target_student_id(current_user: User, student_id: Optional[str] = None) -> str:
    """Enforces broken access control checks. Students can only query their own ID."""
    if current_user.role.name == "STUDENT":
        if student_id and student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You cannot inspect other student directories."
            )
        return current_user.id
    else:
        # Admins, teachers, mentors can query specific student ID
        if not student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing student_id query parameter."
            )
        return student_id

# -------------------------------------------------------------
# 1. STUDENT DASHBOARD & WIDGETS
# -------------------------------------------------------------
@router.get("/dashboard")
def get_student_dashboard(student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    student = db.query(User).filter_by(id=uid).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student user not found.")
        
    profile = student.profile
    
    # Calculate overall attendance %
    attendance_records = db.query(StudentAttendanceSummary).filter_by(userId=uid).all()
    overall_percentage = 0.0
    if attendance_records:
        overall_percentage = sum(x.percentage for x in attendance_records) / len(attendance_records)
        
    # Calculate CGPA from results
    results_records = db.query(StudentResult).filter_by(userId=uid).all()
    cgpa = 0.0
    credits_completed = 0
    if results_records:
        total_points = 0.0
        for r in results_records:
            # Map grade to score
            grade_scores = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "F": 0}
            score = grade_scores.get(r.grade, 8.0) # default mock 8.0
            total_points += score * r.credits
            credits_completed += r.credits
        if credits_completed > 0:
            cgpa = total_points / credits_completed
            
    # Mock some default info if no records exist yet
    if not results_records:
        cgpa = 8.5
        credits_completed = 64
        
    # Pending assignments count
    pending_assignments = db.query(StudentAssignment).filter_by(userId=uid, submissionStatus="PENDING").count()

    # Dynamic Welcome & widgets wrap
    dashboard_data = {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "username": student.username,
            "usn": profile.usn if profile else None,
            "department": student.department.name if student.department else "Not Assigned",
            "section": student.section.name if student.section else "Not Assigned",
            "semester": student.section.semester.semesterNumber if (student.section and student.section.semester) else 1,
            "avatarUrl": profile.avatarUrl if profile else None
        },
        "widgets": {
            "attendancePercentage": round(overall_percentage, 2) if overall_percentage > 0 else 85.5, # default fallback
            "cgpa": round(cgpa, 2),
            "creditsCompleted": credits_completed,
            "creditsRemaining": max(0, 160 - credits_completed),
            "pendingAssignmentsCount": pending_assignments,
            "upcomingExamsCount": 3,
            "pendingFees": 12000,
            "noticesCount": 4,
            "aiStudyRecommendation": "Focus on revision of Data Structures. Your attendance in Subject CSE-101 is slightly below average (78%)."
        }
    }
    return make_response(success=True, message="Student dashboard loaded successfully.", data=dashboard_data, extra_compat=dashboard_data)

# -------------------------------------------------------------
# 2. PROFILE MANAGE
# -------------------------------------------------------------
@router.get("/profile")
def get_student_profile(student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    student = db.query(User).filter_by(id=uid).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
        
    profile = student.profile
    data = {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "username": student.username,
        "phoneNumber": profile.phoneNumber if profile else None,
        "address": profile.address if profile else None,
        "usn": profile.usn if profile else None,
        "parentName": profile.parentName if profile else None,
        "parentPhone": profile.parentPhone if profile else None,
        "emergencyContact": profile.emergencyContact if profile else None,
        "bloodGroup": profile.bloodGroup if profile else None,
        "avatarUrl": profile.avatarUrl if profile else None
    }
    return make_response(success=True, message="Student profile loaded.", data=data, extra_compat=data)

@router.put("/profile")
def update_student_profile(payload: StudentProfileUpdateSchema, student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    student = db.query(User).filter_by(id=uid).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
        
    profile = student.profile
    if not profile:
        profile = UserProfile(id=str(uuid.uuid4()), userId=uid)
        db.add(profile)
        
    if payload.phoneNumber is not None: profile.phoneNumber = payload.phoneNumber
    if payload.address is not None: profile.address = payload.address
    if payload.parentName is not None: profile.parentName = payload.parentName
    if payload.parentPhone is not None: profile.parentPhone = payload.parentPhone
    if payload.emergencyContact is not None: profile.emergencyContact = payload.emergencyContact
    if payload.bloodGroup is not None: profile.bloodGroup = payload.bloodGroup
    
    db.commit()
    
    # Audit log
    audit = AuditLog(id=str(uuid.uuid4()), userId=current_user.id, action="STUDENT_PROFILE_UPDATE", details=f"Student updated profile fields.")
    db.add(audit)
    db.commit()
    
    return make_response(success=True, message="Student profile updated successfully.", data={})

# -------------------------------------------------------------
# 3. ATTENDANCE API
# -------------------------------------------------------------
@router.get("/attendance")
def get_student_attendance(student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    records = db.query(StudentAttendanceSummary).filter_by(userId=uid).all()
    
    data = [{
        "id": r.id,
        "subjectId": r.subjectId,
        "subjectName": r.subject.name if r.subject else "Unknown",
        "subjectCode": r.subject.code if r.subject else "N/A",
        "totalClasses": r.totalClasses,
        "presentClasses": r.presentClasses,
        "percentage": r.percentage
    } for r in records]
    
    return make_response(success=True, message="Attendance list retrieved.", data={"records": data}, extra_compat={"records": data})

# -------------------------------------------------------------
# 4. RESULTS API
# -------------------------------------------------------------
@router.get("/results")
def get_student_results(student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    records = db.query(StudentResult).filter_by(userId=uid).all()
    
    data = [{
        "id": r.id,
        "subjectName": r.subject.name if r.subject else "Unknown",
        "subjectCode": r.subject.code if r.subject else "N/A",
        "semesterNumber": r.semesterNumber,
        "internalMarks": r.internalMarks,
        "externalMarks": r.externalMarks,
        "grade": r.grade,
        "credits": r.credits
    } for r in records]
    
    return make_response(success=True, message="Academic results retrieved.", data={"results": data}, extra_compat={"results": data})

# -------------------------------------------------------------
# 5. ASSIGNMENTS API
# -------------------------------------------------------------
@router.get("/assignments")
def get_student_assignments(student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    records = db.query(StudentAssignment).filter_by(userId=uid).all()
    
    data = [{
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "dueDate": r.dueDate,
        "subjectName": r.subject.name if r.subject else "Unknown",
        "submissionStatus": r.submissionStatus,
        "submissionUrl": r.submissionUrl,
        "submittedAt": r.submittedAt,
        "grade": r.grade
    } for r in records]
    
    return make_response(success=True, message="Assignments retrieved.", data={"assignments": data}, extra_compat={"assignments": data})

@router.post("/assignments/{id}/submit")
def submit_student_assignment(id: str, payload: AssignmentSubmitSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    # Find assignment and verify ownership
    assign = db.query(StudentAssignment).filter_by(id=id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found.")
        
    if current_user.role.name == "STUDENT" and assign.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden. You cannot submit assignments for other students.")
        
    assign.submissionUrl = payload.submissionUrl
    assign.submittedAt = datetime.utcnow()
    
    # Check if late
    if assign.submittedAt > assign.dueDate:
        assign.submissionStatus = "LATE"
    else:
        assign.submissionStatus = "SUBMITTED"
        
    db.commit()
    return make_response(success=True, message="Assignment submitted successfully.", data={})

# -------------------------------------------------------------
# 6. CERTIFICATES API
# -------------------------------------------------------------
@router.post("/certificates/request")
def request_certificate(payload: CertificateRequestSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can request certification documents.")
        
    cert = StudentCertificate(
        id=str(uuid.uuid4()),
        userId=current_user.id,
        certificateType=payload.certificateType,
        status="PENDING",
        requestedAt=datetime.utcnow()
    )
    db.add(cert)
    db.commit()
    return make_response(success=True, message="Certificate request logged successfully.", data={"id": cert.id})

@router.get("/certificates")
def get_student_certificates(student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    records = db.query(StudentCertificate).filter_by(userId=uid).all()
    
    data = [{
        "id": r.id,
        "certificateType": r.certificateType,
        "status": r.status,
        "requestedAt": r.requestedAt,
        "issuedAt": r.issuedAt,
        "documentUrl": r.documentUrl
    } for r in records]
    
    return make_response(success=True, message="Certificates list retrieved.", data={"certificates": data}, extra_compat={"certificates": data})

# -------------------------------------------------------------
# 7. DOCUMENTS API
# -------------------------------------------------------------
@router.get("/documents")
def get_student_documents(student_id: Optional[str] = None, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    uid = get_target_student_id(current_user, student_id)
    records = db.query(StudentDocument).filter_by(userId=uid).all()
    
    data = [{
        "id": r.id,
        "name": r.name,
        "documentUrl": r.documentUrl,
        "uploadedAt": r.uploadedAt
    } for r in records]
    
    return make_response(success=True, message="Documents list retrieved.", data={"documents": data}, extra_compat={"documents": data})

# -------------------------------------------------------------
# 8. NOTIFICATIONS API
# -------------------------------------------------------------
@router.get("/notifications")
def get_student_notifications(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    # Alerts relevant to the student
    records = db.query(StudentNotification).filter_by(userId=current_user.id).all()
    
    data = [{
        "id": r.id,
        "title": r.title,
        "content": r.content,
        "type": r.type,
        "read": r.read,
        "createdAt": r.createdAt
    } for r in records]
    
    return make_response(success=True, message="Notifications list retrieved.", data={"notifications": data}, extra_compat={"notifications": data})

@router.put("/notifications/{id}/read")
def read_student_notification(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    notif = db.query(StudentNotification).filter_by(id=id, userId=current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.read = True
    db.commit()
    return make_response(success=True, message="Notification marked as read.", data={})
