import uuid
import math
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Subject, Section, AttendanceSession, AttendanceRecord,
    QRSession, QRCode, QRScanLog, GeoValidation, DeviceValidation
)
from app.api.v1.endpoints.attendances import recalculate_attendance_summary

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class QRSessionCreateSchema(BaseModel):
    academicYearId: str
    departmentId: str
    programId: str
    semesterId: str
    sectionId: str
    subjectId: str
    timeSlotId: Optional[str] = None
    date: datetime
    latitude: float
    longitude: float
    allowedRadius: float = 100.0 # meters
    intervalSeconds: int = 30 # rotation timer

class QRScanSchema(BaseModel):
    qrSessionId: str
    scannedToken: str
    latitude: float
    longitude: float
    deviceId: str

# -------------------------------------------------------------
# HAVERSINE METERS DISTANCE VALIDATOR
# -------------------------------------------------------------
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Radius of the Earth in km
    R = 6371.0
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
         
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = R * c
    return distance_km * 1000.0 # return meters

# -------------------------------------------------------------
# API ROUTERS
# -------------------------------------------------------------

# Start QR Attendance Session
@router.post("/session")
def start_qr_session(payload: QRSessionCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    # 1. Create standard attendance session first
    att_sess = AttendanceSession(
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
    db.add(att_sess)
    
    # 2. Hook QRSession
    qr_sess = QRSession(
        id=str(uuid.uuid4()),
        attendanceSessionId=att_sess.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        allowedRadius=payload.allowedRadius,
        intervalSeconds=payload.intervalSeconds,
        status="ACTIVE"
    )
    db.add(qr_sess)
    
    # 3. Create first active validation code
    code_val = str(uuid.uuid4().hex)
    code = QRCode(
        id=str(uuid.uuid4()),
        qrSessionId=qr_sess.id,
        codeValue=code_val,
        expiresAt=datetime.utcnow() + timedelta(seconds=payload.intervalSeconds)
    )
    db.add(code)
    db.commit()
    
    return make_response(success=True, message="QR attendance session started.", data={"id": qr_sess.id, "code": code_val})

# Retrieve / Rotate Dynamic QR Code
@router.get("/session/{id}/code")
def get_or_rotate_qr_code(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    qr_sess = db.query(QRSession).filter_by(id=id).first()
    if not qr_sess:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    # Rotate code if expired
    active_code = db.query(QRCode).filter(
        QRCode.qrSessionId == id,
        QRCode.expiresAt > datetime.utcnow()
    ).order_by(QRCode.createdAt.desc()).first()
    
    if not active_code:
        new_val = str(uuid.uuid4().hex)
        active_code = QRCode(
            id=str(uuid.uuid4()),
            qrSessionId=id,
            codeValue=new_val,
            expiresAt=datetime.utcnow() + timedelta(seconds=qr_sess.intervalSeconds)
        )
        db.add(active_code)
        db.commit()
        
    remaining = int((active_code.expiresAt - datetime.utcnow()).total_seconds())
    return make_response(success=True, message="QR code loaded.", data={
        "code": active_code.codeValue,
        "expiresAt": active_code.expiresAt,
        "remainingSeconds": remaining if remaining > 0 else 0
    }, extra_compat={
        "code": active_code.codeValue,
        "expiresAt": active_code.expiresAt,
        "remainingSeconds": remaining if remaining > 0 else 0
    })

# Student Scan QR Submission
@router.post("/scan")
def scan_qr_attendance(payload: QRScanSchema, request: Request, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can scan.")
        
    qr_sess = db.query(QRSession).filter_by(id=payload.qrSessionId).first()
    if not qr_sess:
        raise HTTPException(status_code=404, detail="QR Session not found.")
    if qr_sess.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Attendance session has closed.")

    # 1. Section Validation Check
    if current_user.sectionId != qr_sess.attendanceSession.sectionId:
        # Log failure
        log = QRScanLog(id=str(uuid.uuid4()), qrSessionId=payload.qrSessionId, studentId=current_user.id, scannedToken=payload.scannedToken, isSuccess=False, failReason="Section mismatch")
        db.add(log)
        db.commit()
        raise HTTPException(status_code=400, detail="You do not belong to the target class section.")

    # 2. Token Expiry Check
    valid_code = db.query(QRCode).filter_by(qrSessionId=payload.qrSessionId, codeValue=payload.scannedToken).first()
    if not valid_code or valid_code.expiresAt < datetime.utcnow():
        log = QRScanLog(id=str(uuid.uuid4()), qrSessionId=payload.qrSessionId, studentId=current_user.id, scannedToken=payload.scannedToken, isSuccess=False, failReason="Token expired")
        db.add(log)
        db.commit()
        raise HTTPException(status_code=400, detail="QR code is expired or invalid.")

    # 3. Geofencing Coordinates Check
    distance = haversine_distance(qr_sess.latitude, qr_sess.longitude, payload.latitude, payload.longitude)
    if distance > qr_sess.allowedRadius:
        log = QRScanLog(id=str(uuid.uuid4()), qrSessionId=payload.qrSessionId, studentId=current_user.id, scannedToken=payload.scannedToken, isSuccess=False, failReason=f"Geofence breach: {distance:.1f}m away")
        db.add(log)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Scan failed: Out of bounds (distance: {distance:.1f}m).")

    # 4. Device Duplication Check
    dup_device = db.query(DeviceValidation).join(QRScanLog).filter(
        QRScanLog.qrSessionId == payload.qrSessionId,
        DeviceValidation.deviceId == payload.deviceId
    ).first()
    if dup_device:
        log = QRScanLog(id=str(uuid.uuid4()), qrSessionId=payload.qrSessionId, studentId=current_user.id, scannedToken=payload.scannedToken, isSuccess=False, failReason="Duplicate device ID scan attempt")
        db.add(log)
        db.commit()
        raise HTTPException(status_code=400, detail="Scan failed: Device has already logged attendance for another student.")

    # 5. Student Duplicate Scan Check
    existing_rec = db.query(AttendanceRecord).filter_by(
        sessionId=qr_sess.attendanceSessionId,
        studentId=current_user.id
    ).first()
    if existing_rec:
        raise HTTPException(status_code=400, detail="You have already scanned successfully.")

    # Mark attendance
    rec = AttendanceRecord(
        id=str(uuid.uuid4()),
        sessionId=qr_sess.attendanceSessionId,
        studentId=current_user.id,
        status="PRESENT"
    )
    db.add(rec)

    # Log successful scan log
    log = QRScanLog(id=str(uuid.uuid4()), qrSessionId=payload.qrSessionId, studentId=current_user.id, scannedToken=payload.scannedToken, isSuccess=True)
    db.add(log)
    db.flush() # get log id

    # Geo validation logging
    geo = GeoValidation(id=str(uuid.uuid4()), scanLogId=log.id, studentLatitude=payload.latitude, studentLongitude=payload.longitude, distanceMeters=distance)
    db.add(geo)

    # Device validation logging
    dev = DeviceValidation(id=str(uuid.uuid4()), scanLogId=log.id, deviceId=payload.deviceId, browser=request.headers.get("user-agent"), os=None, ipAddress=request.client.host if request.client else None)
    db.add(dev)
    
    db.commit()
    
    # Recalculate summary percentages
    recalculate_attendance_summary(db, current_user.id, qr_sess.attendanceSession.subjectId, qr_sess.attendanceSession.sectionId)
    
    return make_response(success=True, message="Attendance successfully verified and logged via QR scan.")

# Close QR Session
@router.post("/session/{id}/close")
def close_qr_session(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    qr_sess = db.query(QRSession).filter_by(id=id).first()
    if not qr_sess:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    if current_user.role.name == "TEACHER" and qr_sess.attendanceSession.facultyId != current_user.id:
         raise HTTPException(status_code=403, detail="Access denied.")
         
    qr_sess.status = "CLOSED"
    qr_sess.attendanceSession.status = "CLOSED"
    db.commit()
    return make_response(success=True, message="QR session closed successfully.")

# Faculty Session Live Status
@router.get("/session/{id}/status")
def get_qr_session_live_status(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    qr_sess = db.query(QRSession).filter_by(id=id).first()
    if not qr_sess:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    # Get marked students roster
    records = db.query(AttendanceRecord).filter_by(sessionId=qr_sess.attendanceSessionId).all()
    present_list = [{
        "studentId": r.studentId,
        "name": r.student.name if r.student else "N/A"
    } for r in records]
    
    # Load all section students to check pending
    all_students = db.query(User).filter_by(sectionId=qr_sess.attendanceSession.sectionId).all()
    marked_ids = {r.studentId for r in records}
    
    pending_list = [{
        "studentId": s.id,
        "name": s.name
    } for s in all_students if s.id not in marked_ids]
    
    total = len(all_students)
    present_count = len(present_list)
    percentage = (present_count / total * 100.0) if total > 0 else 0.0
    
    return make_response(success=True, message="Live status loaded.", data={
        "status": qr_sess.status,
        "presentCount": present_count,
        "pendingCount": len(pending_list),
        "attendancePercentage": percentage,
        "presentList": present_list,
        "pendingList": pending_list
    }, extra_compat={
        "status": qr_sess.status,
        "presentCount": present_count,
        "pendingCount": len(pending_list),
        "attendancePercentage": percentage,
        "presentList": present_list,
        "pendingList": pending_list
    })
