import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Subject, Section, TimeSlot, AcademicYear, Department, Program,
    AttendanceSession, AttendanceRecord, AttendanceCorrection, AttendanceAudit,
    DefaulterList, StudentAttendanceSummary
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class SessionCreateSchema(BaseModel):
    academicYearId: str
    departmentId: str
    programId: str
    semesterId: str
    sectionId: str
    subjectId: str
    timeSlotId: Optional[str] = None
    date: datetime

class RecordMarkItem(BaseModel):
    studentId: str
    status: str # PRESENT, ABSENT, LATE, MEDICAL_LEAVE, ON_DUTY

class BatchMarkSchema(BaseModel):
    records: List[RecordMarkItem]
    finalize: bool = False
    reason: Optional[str] = None

class CorrectionRequestSchema(BaseModel):
    recordId: str
    requestedStatus: str
    reason: str

class CorrectionReviewSchema(BaseModel):
    status: str # APPROVED, REJECTED
    comments: Optional[str] = None

# -------------------------------------------------------------
# HELPER METHOD: RECALCULATE ATTENDANCE PERCENTAGE
# -------------------------------------------------------------
def recalculate_attendance_summary(db: Session, student_id: str, subject_id: str, section_id: str):
    # Count sessions that are CLOSED/FINALIZED
    records = db.query(AttendanceRecord).join(AttendanceSession).filter(
        AttendanceRecord.studentId == student_id,
        AttendanceSession.subjectId == subject_id,
        AttendanceSession.status == "CLOSED"
    ).all()
    
    total = len(records)
    present = sum(1 for r in records if r.status in ["PRESENT", "LATE", "ON_DUTY"])
    percentage = (present / total * 100.0) if total > 0 else 100.0
    
    # Update StudentAttendanceSummary
    summary = db.query(StudentAttendanceSummary).filter_by(userId=student_id, subjectId=subject_id).first()
    if not summary:
        summary = StudentAttendanceSummary(
            id=str(uuid.uuid4()),
            userId=student_id,
            subjectId=subject_id,
            totalClasses=total,
            presentClasses=present,
            percentage=percentage
        )
        db.add(summary)
    else:
        summary.totalClasses = total
        summary.presentClasses = present
        summary.percentage = percentage
        
    # Check Defaulter Status
    db.query(DefaulterList).filter_by(studentId=student_id, subjectId=subject_id).delete()
    if percentage < 75.0:
        cat = "BELOW_75"
        if percentage < 65.0:
            cat = "BELOW_65"
        if percentage < 50.0:
            cat = "BELOW_50"
            
        defaulter = DefaulterList(
            id=str(uuid.uuid4()),
            subjectId=subject_id,
            sectionId=section_id,
            studentId=student_id,
            percentage=percentage,
            category=cat
        )
        db.add(defaulter)
        
    db.commit()

# -------------------------------------------------------------
# ROUTERS
# -------------------------------------------------------------

# Create Attendance Session
@router.post("/session")
def create_attendance_session(payload: SessionCreateSchema, request: Request, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    sess = AttendanceSession(
        id=str(uuid.uuid4()),
        academicYearId=payload.academicYearId,
        departmentId=payload.departmentId,
        programId=payload.programId,
        semesterId=payload.semesterId,
        sectionId=payload.sectionId,
        subjectId=payload.subjectId,
        timeSlotId=payload.timeSlotId,
        date=payload.date,
        status="ACTIVE",
        facultyId=current_user.id
    )
    db.add(sess)
    
    # Log Audit
    audit = AttendanceAudit(
        id=str(uuid.uuid4()),
        sessionId=sess.id,
        userId=current_user.id,
        action="CREATE",
        ipAddress=request.client.host if request.client else None,
        userAgent=request.headers.get("user-agent"),
        reason="Attendance session initialized."
    )
    db.add(audit)
    db.commit()
    
    return make_response(success=True, message="Attendance session created.", data={"id": sess.id})

# Get session details & student roster list
@router.get("/session/{id}/students")
def get_session_student_roster(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    sess = db.query(AttendanceSession).filter_by(id=id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    # Security: Faculty advisor or assigned teacher check
    if current_user.role.name == "TEACHER" and sess.facultyId != current_user.id:
         raise HTTPException(status_code=403, detail="Access denied.")
         
    # Load all students belonging to the session section
    students = db.query(User).filter_by(sectionId=sess.sectionId).all()
    
    # Fetch existing records if already marked
    marked_records = {r.studentId: r.status for r in db.query(AttendanceRecord).filter_by(sessionId=id).all()}
    
    roster = [{
        "id": s.id,
        "name": s.name,
        "email": s.email,
        "status": marked_records.get(s.id, "PRESENT") # default to present
    } for s in students]
    
    return make_response(success=True, message="Session student roster loaded.", data={
        "session": {
            "id": sess.id,
            "subject": sess.subject.name if sess.subject else "",
            "date": sess.date,
            "status": sess.status
        },
        "roster": roster
    }, extra_compat={
        "session": {
            "id": sess.id,
            "subject": sess.subject.name if sess.subject else "",
            "date": sess.date,
            "status": sess.status
        },
        "roster": roster
    })

# Mark Batch Attendance
@router.post("/session/{id}/records")
def mark_session_attendance(id: str, payload: BatchMarkSchema, request: Request, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    sess = db.query(AttendanceSession).filter_by(id=id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    if current_user.role.name == "TEACHER" and sess.facultyId != current_user.id:
         raise HTTPException(status_code=403, detail="Access denied.")
         
    # Clear existing marks to prevent duplication
    db.query(AttendanceRecord).filter_by(sessionId=id).delete()
    
    for item in payload.records:
        rec = AttendanceRecord(
            id=str(uuid.uuid4()),
            sessionId=id,
            studentId=item.studentId,
            status=item.status
        )
        db.add(rec)
        
    if payload.finalize:
        sess.status = "CLOSED"
        
    # Log Audit
    audit = AttendanceAudit(
        id=str(uuid.uuid4()),
        sessionId=id,
        userId=current_user.id,
        action="FINALIZE" if payload.finalize else "MODIFY",
        ipAddress=request.client.host if request.client else None,
        userAgent=request.headers.get("user-agent"),
        reason=payload.reason or ("Attendance finalized." if payload.finalize else "Attendance updated.")
    )
    db.add(audit)
    db.commit()
    
    # Recalculate metrics for all marked students if finalized
    if payload.finalize:
        for item in payload.records:
            recalculate_attendance_summary(db, item.studentId, sess.subjectId, sess.sectionId)
            
    return make_response(success=True, message="Attendance marks saved.")

# List Attendance Sessions (Faculty Dashboard View)
@router.get("/sessions")
def list_attendance_sessions(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    query = db.query(AttendanceSession)
    if current_user.role.name == "TEACHER":
        query = query.filter_by(facultyId=current_user.id)
        
    sessions = query.order_by(AttendanceSession.date.desc()).all()
    data = [{
        "id": s.id,
        "date": s.date,
        "subject": s.subject.name if s.subject else "N/A",
        "section": s.section.name if s.section else "N/A",
        "status": s.status
    } for s in sessions]
    
    return make_response(success=True, message="Attendance sessions fetched.", data={"sessions": data}, extra_compat={"sessions": data})

# Student view own attendance subject-wise
@router.get("/student/my-attendance")
def get_student_attendance(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    summaries = db.query(StudentAttendanceSummary).filter_by(userId=current_user.id).all()
    data = [{
        "subjectId": s.subjectId,
        "subjectName": s.subject.name if s.subject else "N/A",
        "total": s.totalClasses,
        "present": s.presentClasses,
        "percentage": s.percentage
    } for s in summaries]
    
    # Detailed records
    records = db.query(AttendanceRecord).join(AttendanceSession).filter(
        AttendanceRecord.studentId == current_user.id,
        AttendanceSession.status == "CLOSED"
    ).order_by(AttendanceSession.date.desc()).all()
    
    detailed = [{
        "recordId": r.id,
        "date": r.session.date,
        "subjectName": r.session.subject.name if r.session.subject else "N/A",
        "status": r.status
    } for r in records]
    
    return make_response(success=True, message="Attendance loaded.", data={
        "summaries": data,
        "records": detailed
    }, extra_compat={
        "summaries": data,
        "records": detailed
    })

# Submit correction request (Student)
@router.post("/corrections")
def submit_correction_request(payload: CorrectionRequestSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Access denied.")
        
    req = AttendanceCorrection(
        id=str(uuid.uuid4()),
        recordId=payload.recordId,
        studentId=current_user.id,
        requestedStatus=payload.requestedStatus,
        reason=payload.reason,
        status="PENDING"
    )
    db.add(req)
    db.commit()
    return make_response(success=True, message="Correction request submitted successfully.")

# Get correction requests
@router.get("/corrections")
def list_correction_requests(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    query = db.query(AttendanceCorrection)
    if current_user.role.name == "STUDENT":
        query = query.filter_by(studentId=current_user.id)
    elif current_user.role.name == "TEACHER":
        query = query.join(AttendanceRecord).join(AttendanceSession).filter(
            AttendanceSession.facultyId == current_user.id
        )
        
    requests = query.all()
    data = [{
        "id": r.id,
        "studentName": r.student.name if r.student else "N/A",
        "subjectName": r.record.session.subject.name if r.record and r.record.session and r.record.session.subject else "N/A",
        "date": r.record.session.date if r.record and r.record.session else None,
        "currentStatus": r.record.status if r.record else "",
        "requestedStatus": r.requestedStatus,
        "reason": r.reason,
        "status": r.status,
        "comments": r.comments
    } for r in requests]
    
    return make_response(success=True, message="Correction requests loaded.", data={"requests": data}, extra_compat={"requests": data})

# Approve / Reject Correction Request
@router.post("/corrections/{id}/review")
def review_correction_request(id: str, payload: CorrectionReviewSchema, request: Request, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    req = db.query(AttendanceCorrection).filter_by(id=id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
        
    req.status = payload.status
    req.comments = payload.comments
    
    if payload.status == "APPROVED":
        # Modify the actual attendance record
        record = db.query(AttendanceRecord).filter_by(id=req.recordId).first()
        if record:
            record.status = req.requestedStatus
            
            # Audit trace log
            audit = AttendanceAudit(
                id=str(uuid.uuid4()),
                recordId=record.id,
                userId=current_user.id,
                action="APPROVE_CORRECTION",
                ipAddress=request.client.host if request.client else None,
                userAgent=request.headers.get("user-agent"),
                reason=f"Correction approved: {req.requestedStatus}. Remarks: {payload.comments}"
            )
            db.add(audit)
            db.commit()
            
            # Recalculate percentages
            recalculate_attendance_summary(db, record.studentId, record.session.subjectId, record.session.sectionId)
            
    db.commit()
    return make_response(success=True, message=f"Correction request {payload.status.lower()}.")

# Defaulters Listing
@router.get("/defaulters")
def list_defaulters(subjectId: Optional[str] = None, sectionId: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DefaulterList)
    if subjectId:
        query = query.filter_by(subjectId=subjectId)
    if sectionId:
        query = query.filter_by(sectionId=sectionId)
        
    defaulters = query.all()
    data = [{
        "id": d.id,
        "studentName": d.student.name if d.student else "N/A",
        "subjectName": d.subject.name if d.subject else "N/A",
        "sectionName": d.section.name if d.section else "N/A",
        "percentage": d.percentage,
        "category": d.category
    } for d in defaulters]
    
    return make_response(success=True, message="Defaulters listed.", data={"defaulters": data}, extra_compat={"defaulters": data})
