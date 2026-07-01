import json
import math
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.core.security import create_access_token
from app.models.models import (
    User, FaceProfile, FaceEmbedding, FaceRegistration, 
    FaceVerification, FaceAttendance, FaceAudit, LivenessCheck, 
    SpoofDetection, AttendanceSession, AttendanceRecord
)
from app.api.v1.endpoints.attendances import recalculate_attendance_summary

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class SingleEmbeddingSchema(BaseModel):
    angle: str # FRONT, LEFT, RIGHT, UP, DOWN
    embeddingJson: str

class FaceRegisterSchema(BaseModel):
    embeddings: List[SingleEmbeddingSchema]

class LivenessSchema(BaseModel):
    blinkCount: int
    smileDetected: bool
    headRotationDegrees: float

class SpoofingSchema(BaseModel):
    spoofProbability: float
    spoofCategory: str # PRINTED_PHOTO, PHONE_SCREEN, REPLAY_VIDEO, NONE

class FaceLoginSchema(BaseModel):
    username_or_email: str
    queryEmbeddingJson: str
    liveness: LivenessSchema
    spoofing: SpoofingSchema

class FaceAttendanceSchema(BaseModel):
    sessionId: str
    queryEmbeddingJson: str
    latitude: float
    longitude: float
    deviceId: str
    liveness: LivenessSchema
    spoofing: SpoofingSchema

class FaceVerifySchema(BaseModel):
    userId: str
    queryEmbeddingJson: str

class ReviewRegistrationSchema(BaseModel):
    status: str # APPROVED, REJECTED
    rejectionReason: Optional[str] = None

# -------------------------------------------------------------
# COSINE SIMILARITY HELPER
# -------------------------------------------------------------
def calculate_cosine_similarity(vec1_json: str, vec2_json: str) -> float:
    try:
        v1 = json.loads(vec1_json)
        v2 = json.loads(vec2_json)
        if len(v1) != len(v2) or len(v1) == 0:
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)
    except Exception:
        return 0.0

# -------------------------------------------------------------
# REST ENDPOINTS
# -------------------------------------------------------------

# Capture and register face embeddings
@router.post("/register")
def register_face(payload: FaceRegisterSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    # Prevent duplicate registrations
    existing_profile = db.query(FaceProfile).filter_by(userId=current_user.id).first()
    if existing_profile and existing_profile.status == "APPROVED":
        raise HTTPException(status_code=400, detail="Biometric face profile has already been registered and approved.")

    # Validate embedding quality (FRONT, LEFT, RIGHT, UP, DOWN angles must be present)
    angles_provided = {emb.angle.upper() for emb in payload.embeddings}
    required_angles = {"FRONT", "LEFT", "RIGHT", "UP", "DOWN"}
    
    if not required_angles.issubset(angles_provided):
        raise HTTPException(status_code=400, detail="Missing required face angles. Captures of FRONT, LEFT, RIGHT, UP, and DOWN are required.")

    # Quality check vector dimensions (reproduce 512 floats array)
    for emb in payload.embeddings:
        try:
            vec = json.loads(emb.embeddingJson)
            if not isinstance(vec, list) or len(vec) != 512:
                raise HTTPException(status_code=400, detail=f"Invalid embedding vector dimension for angle {emb.angle}. Must be 512 float values.")
        except HTTPException as he:
            raise he
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid embedding payload for angle {emb.angle}.")

    # Create/Update profile
    if existing_profile:
        # Clear old rejected embeddings
        db.query(FaceEmbedding).filter_by(faceProfileId=existing_profile.id).delete()
        profile = existing_profile
        profile.status = "PENDING"
    else:
        profile = FaceProfile(
            id=str(uuid.uuid4()),
            userId=current_user.id,
            status="PENDING"
        )
        db.add(profile)
        db.flush()

    # Save embeddings
    for emb in payload.embeddings:
        embedding = FaceEmbedding(
            id=str(uuid.uuid4()),
            faceProfileId=profile.id,
            angle=emb.angle.upper(),
            embeddingJson=emb.embeddingJson
        )
        db.add(embedding)

    # Log audit trail
    audit = FaceAudit(
        id=str(uuid.uuid4()),
        userId=current_user.id,
        action="REGISTER_BIOMETRICS"
    )
    db.add(audit)
    db.commit()

    return make_response(success=True, message="Biometric registration submitted successfully. Awaiting administrator approval.")

# Face Recognition Sign-in JWT authentication
@router.post("/login")
def face_login(payload: FaceLoginSchema, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == payload.username_or_email) | 
        (User.email == payload.username_or_email)
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    profile = db.query(FaceProfile).filter_by(userId=user.id).first()
    if not profile or profile.status != "APPROVED":
        raise HTTPException(status_code=400, detail="Biometric face sign-in is not registered or approved for this account.")

    # 1. Anti-Spoofing Glare/Replay Checks
    if payload.spoofing.spoofProbability > 0.5 or payload.spoofing.spoofCategory != "NONE":
        # Log failed spoof attempt
        verification = FaceVerification(
            id=str(uuid.uuid4()), userId=user.id, faceProfileId=profile.id,
            isSuccess=False, confidence=0.0, verificationType="LOGIN"
        )
        db.add(verification)
        db.flush()
        
        spoof = SpoofDetection(
            id=str(uuid.uuid4()), faceProfileId=profile.id, verificationId=verification.id,
            spoofProbability=payload.spoofing.spoofProbability, spoofCategory=payload.spoofing.spoofCategory,
            isSpoofed=True
        )
        db.add(spoof)
        db.commit()
        raise HTTPException(status_code=400, detail="Login rejected: Spoofing attempt detected.")

    # 2. Liveness Check (Blinks, Yaw/Pitch Degrees)
    if payload.liveness.blinkCount == 0 and abs(payload.liveness.headRotationDegrees) < 2.0:
        # Fail liveness
        verification = FaceVerification(
            id=str(uuid.uuid4()), userId=user.id, faceProfileId=profile.id,
            isSuccess=False, confidence=0.0, verificationType="LOGIN"
        )
        db.add(verification)
        db.flush()
        
        liveness = LivenessCheck(
            id=str(uuid.uuid4()), faceProfileId=profile.id, verificationId=verification.id,
            blinkCount=payload.liveness.blinkCount, smileDetected=payload.liveness.smileDetected,
            headRotationDegrees=payload.liveness.headRotationDegrees, isPassed=False
        )
        db.add(liveness)
        db.commit()
        raise HTTPException(status_code=400, detail="Login rejected: Liveness checks failed (No blinks or head movement).")

    # 3. Biometric Comparison against FRONT angle
    front_emb = db.query(FaceEmbedding).filter_by(faceProfileId=profile.id, angle="FRONT").first()
    if not front_emb:
        raise HTTPException(status_code=400, detail="Stale profile: FRONT angle registration missing.")

    similarity = calculate_cosine_similarity(payload.queryEmbeddingJson, front_emb.embeddingJson)
    
    # Save verification attempt
    verification = FaceVerification(
        id=str(uuid.uuid4()), userId=user.id, faceProfileId=profile.id,
        isSuccess=(similarity >= 0.85), confidence=similarity, verificationType="LOGIN"
    )
    db.add(verification)
    db.flush()

    # Log validations
    liveness = LivenessCheck(
        id=str(uuid.uuid4()), faceProfileId=profile.id, verificationId=verification.id,
        blinkCount=payload.liveness.blinkCount, smileDetected=payload.liveness.smileDetected,
        headRotationDegrees=payload.liveness.headRotationDegrees, isPassed=True
    )
    db.add(liveness)
    
    spoof = SpoofDetection(
        id=str(uuid.uuid4()), faceProfileId=profile.id, verificationId=verification.id,
        spoofProbability=payload.spoofing.spoofProbability, spoofCategory="NONE",
        isSpoofed=False
    )
    db.add(spoof)
    db.commit()

    if similarity < 0.85:
        raise HTTPException(status_code=400, detail="Biometric face identification failed: Unmatched face features.")

    # Success: Generate Token
    access_token = create_access_token(subject=user.username)
    return make_response(success=True, message="Biometric sign-in successful.", data={"access_token": access_token, "token_type": "bearer"})

# Compare face query with User biometrics profile
@router.post("/verify")
def verify_face_embedding(payload: FaceVerifySchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    profile = db.query(FaceProfile).filter_by(userId=payload.userId).first()
    if not profile or profile.status != "APPROVED":
         raise HTTPException(status_code=404, detail="Approved face profile not found.")
         
    front_emb = db.query(FaceEmbedding).filter_by(faceProfileId=profile.id, angle="FRONT").first()
    if not front_emb:
        raise HTTPException(status_code=400, detail="FRONT embedding missing.")
        
    similarity = calculate_cosine_similarity(payload.queryEmbeddingJson, front_emb.embeddingJson)
    return make_response(success=True, message="Face comparison completed.", data={"similarity": similarity, "matched": similarity >= 0.85})

# Facial recognition student check-in
@router.post("/attendance")
def face_attendance(payload: FaceAttendanceSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can verify attendance.")

    sess = db.query(AttendanceSession).filter_by(id=payload.sessionId).first()
    if not sess:
         raise HTTPException(status_code=404, detail="Attendance session not found.")
    if sess.status != "ACTIVE":
         raise HTTPException(status_code=400, detail="Session has closed.")

    profile = db.query(FaceProfile).filter_by(userId=current_user.id).first()
    if not profile or profile.status != "APPROVED":
        raise HTTPException(status_code=400, detail="You do not have an approved Face Profile.")

    # 1. Anti-Spoofing Check
    if payload.spoofing.spoofProbability > 0.5:
        raise HTTPException(status_code=400, detail="Spoof attempt blocked.")

    # 2. Liveness Check
    if payload.liveness.blinkCount == 0:
        raise HTTPException(status_code=400, detail="Liveness check failed.")

    # 3. Match Biometrics
    front_emb = db.query(FaceEmbedding).filter_by(faceProfileId=profile.id, angle="FRONT").first()
    similarity = calculate_cosine_similarity(payload.queryEmbeddingJson, front_emb.embeddingJson)
    if similarity < 0.85:
        raise HTTPException(status_code=400, detail="Biometric validation mismatch.")

    # Duplicate Record Check
    existing_rec = db.query(AttendanceRecord).filter_by(sessionId=payload.sessionId, studentId=current_user.id).first()
    if existing_rec:
        raise HTTPException(status_code=400, detail="Attendance has already been marked.")

    # Save verification attempt log
    verification = FaceVerification(
        id=str(uuid.uuid4()), userId=current_user.id, faceProfileId=profile.id,
        isSuccess=True, confidence=similarity, verificationType="ATTENDANCE"
    )
    db.add(verification)
    db.flush()

    # Log record
    rec = AttendanceRecord(
        id=str(uuid.uuid4()),
        sessionId=payload.sessionId,
        studentId=current_user.id,
        status="PRESENT"
    )
    db.add(rec)
    db.flush()

    # Link with FaceAttendance
    face_att = FaceAttendance(
        id=str(uuid.uuid4()),
        attendanceSessionId=payload.sessionId,
        attendanceRecordId=rec.id,
        verificationId=verification.id
    )
    db.add(face_att)
    db.commit()

    recalculate_attendance_summary(db, current_user.id, sess.subjectId, sess.sectionId)
    return make_response(success=True, message="Face Attendance verified and registered successfully.")

# Lists biometric registration applications
@router.get("/registrations")
def get_face_registrations(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")
        
    profiles = db.query(FaceProfile).order_by(FaceProfile.createdAt.desc()).all()
    out = [{
        "id": p.id,
        "userId": p.userId,
        "name": p.user.name if p.user else "N/A",
        "status": p.status,
        "createdAt": p.createdAt
    } for p in profiles]
    return make_response(success=True, message="Face profiles loaded.", data=out)

# Review registration (Approve / Reject)
@router.post("/registrations/{id}/review")
def review_face_registration(id: str, payload: ReviewRegistrationSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
         raise HTTPException(status_code=403, detail="Admin only")
         
    profile = db.query(FaceProfile).filter_by(id=id).first()
    if not profile:
         raise HTTPException(status_code=404, detail="Profile not found.")
         
    profile.status = payload.status
    
    # Save registration history
    reg_log = FaceRegistration(
        id=str(uuid.uuid4()),
        faceProfileId=profile.id,
        adminId=current_user.id,
        status=payload.status,
        rejectionReason=payload.rejectionReason
    )
    db.add(reg_log)

    # Log audit
    audit = FaceAudit(
        id=str(uuid.uuid4()),
        userId=current_user.id,
        action="APPROVE_BIOMETRICS" if payload.status == "APPROVED" else "REJECT_BIOMETRICS"
    )
    db.add(audit)
    db.commit()
    
    return make_response(success=True, message=f"Biometric registration status updated to {payload.status}.")

# Delete biometric profile
@router.delete("/registrations/{id}")
def delete_face_profile(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
         raise HTTPException(status_code=403, detail="Admin only")
         
    profile = db.query(FaceProfile).filter_by(id=id).first()
    if not profile:
         raise HTTPException(status_code=404, detail="Profile not found.")
         
    db.delete(profile)
    
    # Log audit
    audit = FaceAudit(
        id=str(uuid.uuid4()),
        userId=current_user.id,
        action="DELETE_EMBEDDINGS"
    )
    db.add(audit)
    db.commit()
    return make_response(success=True, message="Biometric profile deleted successfully.")

# Recognition and attendance statistics
@router.get("/statistics")
def get_face_statistics(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Access denied.")

    total_registered = db.query(FaceProfile).filter_by(status="APPROVED").count()
    pending_profiles = db.query(FaceProfile).filter_by(status="PENDING").count()
    
    failed_verifications = db.query(FaceVerification).filter_by(isSuccess=False).count()
    spoof_attempts = db.query(SpoofDetection).filter_by(isSpoofed=True).count()
    
    return make_response(success=True, message="Face stats loaded.", data={
        "totalRegisteredCount": total_registered,
        "pendingReviewCount": pending_profiles,
        "failedRecognitionAttempts": failed_verifications,
        "spoofedLockdownTriggers": spoof_attempts
    }, extra_compat={
        "totalRegisteredCount": total_registered,
        "pendingReviewCount": pending_profiles,
        "failedRecognitionAttempts": failed_verifications,
        "spoofedLockdownTriggers": spoof_attempts
    })
