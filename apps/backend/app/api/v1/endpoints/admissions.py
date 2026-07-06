import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, AcademicYear, Department, Program, Semester, Section,
    AdmissionApplication, AdmissionStatusHistory, AdmissionDocument,
    AdmissionDocumentVersion, AdmissionReview, Enrollment
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class DocumentUploadPayload(BaseModel):
    documentCategory: str
    fileName: str
    fileUrl: str

class AdmissionCreatePayload(BaseModel):
    academicYearId: str
    departmentId: str
    programId: str
    applicantName: str
    email: EmailStr
    phone: str
    dateOfBirth: datetime
    gender: str
    nationality: str
    category: str
    quota: str
    entranceExam: Optional[str] = None
    entranceScore: Optional[float] = None
    previousInstitution: Optional[str] = None
    previousQualification: Optional[str] = None
    previousPercentage: Optional[float] = None
    address: Optional[str] = None
    guardianName: Optional[str] = None
    guardianPhone: Optional[str] = None
    guardianEmail: Optional[EmailStr] = None

class AdmissionUpdatePayload(BaseModel):
    applicantName: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    dateOfBirth: Optional[datetime] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    category: Optional[str] = None
    quota: Optional[str] = None
    entranceExam: Optional[str] = None
    entranceScore: Optional[float] = None
    previousInstitution: Optional[str] = None
    previousQualification: Optional[str] = None
    previousPercentage: Optional[float] = None
    address: Optional[str] = None
    guardianName: Optional[str] = None
    guardianPhone: Optional[str] = None
    guardianEmail: Optional[EmailStr] = None

class ReviewPayload(BaseModel):
    action: str # COMMENT, VERIFY, REQUEST_CORRECTION
    comment: str

class RejectVerifyPayload(BaseModel):
    comment: str

class EnrollPayload(BaseModel):
    applicationId: str
    academicYearId: str
    departmentId: str
    programId: str
    semesterNumber: int = 1
    sectionId: Optional[str] = None

# Mock Local Storage Abstraction
class StorageProvider:
    @staticmethod
    def validate_file(file_name: str, file_size: int, content_type: str):
        # Validate extensions
        allowed_exts = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
        ext = f".{file_name.split('.')[-1].lower()}"
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed.")
        # Size limit: 5MB
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 5MB.")
        # MIME types
        allowed_mimes = {"application/pdf", "image/jpeg", "image/png", "application/msword"}
        if content_type not in allowed_mimes:
            # Tolerant logging but allow in mock
            pass

# Helper to generate unique collision-resistant application numbers in transactions
def generate_application_number(db: Session) -> str:
    # Use transactional UUID substring + timestamp to guarantee uniqueness and avoid count + 1 race conditions
    timestamp = int(datetime.utcnow().timestamp())
    rand_hex = uuid.uuid4().hex[:4].upper()
    app_num = f"APP-{timestamp}-{rand_hex}"
    # Verify unique in DB
    exists = db.query(AdmissionApplication).filter(AdmissionApplication.applicationNumber == app_num).first()
    if exists:
        return generate_application_number(db)
    return app_num

# -------------------------------------------------------------
# ADMISSIONS APPLICATION ENDPOINTS
# -------------------------------------------------------------

@router.post("")
def create_admission_application(
    payload: AdmissionCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    app_num = generate_application_number(db)
    app = AdmissionApplication(
        applicationNumber=app_num,
        academicYearId=payload.academicYearId,
        departmentId=payload.departmentId,
        programId=payload.programId,
        applicantName=payload.applicantName,
        email=payload.email,
        phone=payload.phone,
        dateOfBirth=payload.dateOfBirth,
        gender=payload.gender,
        nationality=payload.nationality,
        category=payload.category,
        quota=payload.quota,
        entranceExam=payload.entranceExam,
        entranceScore=payload.entranceScore,
        previousInstitution=payload.previousInstitution,
        previousQualification=payload.previousQualification,
        previousPercentage=payload.previousPercentage,
        address=payload.address,
        guardianName=payload.guardianName,
        guardianPhone=payload.guardianPhone,
        guardianEmail=payload.guardianEmail,
        status="DRAFT"
    )
    db.add(app)
    db.flush()

    # Track initial status history
    history = AdmissionStatusHistory(
        applicationId=app.id,
        status="DRAFT",
        changedBy=current_user.id,
        remarks="Draft application created."
    )
    db.add(history)
    db.commit()
    db.refresh(app)

    return make_response(success=True, message="Draft application created successfully.", data={"id": app.id, "applicationNumber": app.applicationNumber})

@router.get("")
def list_admission_applications(
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    query = db.query(AdmissionApplication)

    # RBAC context filter
    if current_user.role.name == "STUDENT":
        # Students can only inspect their own applications mapped by email
        query = query.filter(AdmissionApplication.email == current_user.email)
    elif current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    if status:
        query = query.filter(AdmissionApplication.status == status)

    if search:
        query = query.filter(
            or_(
                AdmissionApplication.applicantName.icontains(search),
                AdmissionApplication.applicationNumber.icontains(search),
                AdmissionApplication.email.icontains(search)
            )
        )

    total = query.count()
    apps = query.order_by(desc(AdmissionApplication.createdAt)).offset(skip).limit(limit).all()

    return make_response(
        success=True,
        message="Applications retrieved.",
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "applications": [{
                "id": a.id,
                "applicationNumber": a.applicationNumber,
                "applicantName": a.applicantName,
                "email": a.email,
                "status": a.status,
                "createdAt": a.createdAt.isoformat()
            } for a in apps]
        }
    )

@router.get("/{id}")
def get_admission_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Prevent IDOR
    if current_user.role.name == "STUDENT" and app.email != current_user.email:
        raise HTTPException(status_code=403, detail="Forbidden from viewing this application.")

    return make_response(
        success=True,
        message="Application details retrieved.",
        data={
            "id": app.id,
            "applicationNumber": app.applicationNumber,
            "applicantName": app.applicantName,
            "email": app.email,
            "phone": app.phone,
            "status": app.status,
            "academicYearId": app.academicYearId,
            "departmentId": app.departmentId,
            "programId": app.programId,
            "quota": app.quota,
            "category": app.category,
            "entranceScore": app.entranceScore,
            "previousPercentage": app.previousPercentage
        }
    )

@router.put("/{id}")
def update_admission_application(
    id: str,
    payload: AdmissionUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Restrict modifications to DRAFT or CORRECTION_REQUIRED states
    if app.status not in ["DRAFT", "CORRECTION_REQUIRED"]:
        raise HTTPException(status_code=400, detail="Cannot edit application in this state.")

    # Prevent IDOR
    if current_user.role.name == "STUDENT" and app.email != current_user.email:
        raise HTTPException(status_code=403, detail="Forbidden from updating this application.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(app, field, value)

    db.commit()
    return make_response(success=True, message="Application draft updated successfully.")

@router.post("/{id}/submit")
def submit_admission_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if app.status not in ["DRAFT", "CORRECTION_REQUIRED"]:
        raise HTTPException(status_code=400, detail="Invalid status transition. Must be DRAFT or CORRECTION_REQUIRED.")

    app.status = "SUBMITTED"
    app.submittedAt = datetime.utcnow()

    # Track status history
    history = AdmissionStatusHistory(
        applicationId=app.id,
        status="SUBMITTED",
        changedBy=current_user.id,
        remarks="Application submitted for verification."
    )
    db.add(history)
    db.commit()

    return make_response(success=True, message="Application submitted successfully.")

@router.post("/{id}/review")
def review_admission_application(
    id: str,
    payload: ReviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    prev_status = app.status

    if payload.action == "VERIFY":
        new_status = "VERIFIED"
    elif payload.action == "REQUEST_CORRECTION":
        new_status = "CORRECTION_REQUIRED"
    else:
        new_status = "UNDER_REVIEW"

    app.status = new_status
    app.reviewedAt = datetime.utcnow()

    review = AdmissionReview(
        applicationId=app.id,
        reviewerId=current_user.id,
        action=payload.action,
        comment=payload.comment,
        previousStatus=prev_status,
        newStatus=new_status
    )
    db.add(review)

    history = AdmissionStatusHistory(
        applicationId=app.id,
        status=new_status,
        changedBy=current_user.id,
        remarks=f"Reviewer action: {payload.action}. Comments: {payload.comment}"
    )
    db.add(history)
    db.commit()

    return make_response(success=True, message=f"Application status changed to {new_status}.")

@router.post("/{id}/approve")
def approve_admission_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    app.status = "APPROVED"
    app.approvedAt = datetime.utcnow()

    history = AdmissionStatusHistory(
        applicationId=app.id,
        status="APPROVED",
        changedBy=current_user.id,
        remarks="Application approved by Admission Officer."
    )
    db.add(history)
    db.commit()

    return make_response(success=True, message="Application approved.")

@router.post("/{id}/reject")
def reject_admission_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    app.status = "REJECTED"
    app.rejectedAt = datetime.utcnow()

    history = AdmissionStatusHistory(
        applicationId=app.id,
        status="REJECTED",
        changedBy=current_user.id,
        remarks="Application rejected by Admission Officer."
    )
    db.add(history)
    db.commit()

    return make_response(success=True, message="Application rejected.")

@router.post("/{id}/waitlist")
def waitlist_admission_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    app.status = "WAITLISTED"

    history = AdmissionStatusHistory(
        applicationId=app.id,
        status="WAITLISTED",
        changedBy=current_user.id,
        remarks="Application waitlisted by Admission Officer."
    )
    db.add(history)
    db.commit()

    return make_response(success=True, message="Application waitlisted.")

# -------------------------------------------------------------
# DOCUMENTS ENDPOINTS
# -------------------------------------------------------------

@router.post("/{id}/documents")
def upload_admission_document(
    id: str,
    payload: DocumentUploadPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Prevent IDOR
    if current_user.role.name == "STUDENT" and app.email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Validate extensions/mimes mock constraints
    StorageProvider.validate_file(payload.fileName, 2 * 1024 * 1024, "application/pdf")

    # Add or update AdmissionDocument
    doc = db.query(AdmissionDocument).filter(
        AdmissionDocument.applicationId == app.id,
        AdmissionDocument.documentCategory == payload.documentCategory
    ).first()

    if not doc:
        doc = AdmissionDocument(
            applicationId=app.id,
            documentCategory=payload.documentCategory,
            fileName=payload.fileName,
            fileUrl=payload.fileUrl,
            verificationStatus="PENDING"
        )
        db.add(doc)
        db.flush()
    else:
        # Create new version
        ver = AdmissionDocumentVersion(
            documentId=doc.id,
            fileUrl=doc.fileUrl
        )
        db.add(ver)
        doc.fileName = payload.fileName
        doc.fileUrl = payload.fileUrl
        doc.verificationStatus = "PENDING"

    db.commit()
    return make_response(success=True, message="Document metadata uploaded successfully.")

@router.get("/{id}/documents")
def list_admission_documents(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if current_user.role.name == "STUDENT" and app.email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied.")

    docs = db.query(AdmissionDocument).filter(AdmissionDocument.applicationId == id).all()

    return make_response(
        success=True,
        message="Documents list retrieved.",
        data=[{
            "id": d.id,
            "documentCategory": d.documentCategory,
            "fileName": d.fileName,
            "fileUrl": d.fileUrl,
            "verificationStatus": d.verificationStatus,
            "comments": d.reviewerComments
        } for d in docs]
    )

@router.post("/admission-documents/{id}/verify")
def verify_document(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    doc = db.query(AdmissionDocument).filter(AdmissionDocument.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc.verificationStatus = "VERIFIED"
    doc.reviewerComments = "Verified by officer."
    db.commit()

    return make_response(success=True, message="Document marked as VERIFIED.")

@router.post("/admission-documents/{id}/reject")
def reject_document(
    id: str,
    payload: RejectVerifyPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    doc = db.query(AdmissionDocument).filter(AdmissionDocument.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc.verificationStatus = "REJECTED"
    doc.reviewerComments = payload.comment
    db.commit()

    return make_response(success=True, message="Document marked as REJECTED.")

# -------------------------------------------------------------
# STUDENT ENROLLMENT ENDPOINTS
# -------------------------------------------------------------
enroll_router = APIRouter()

@enroll_router.post("")
def enroll_student(
    payload: EnrollPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    app = db.query(AdmissionApplication).filter(AdmissionApplication.id == payload.applicationId).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Idempotent enrollment check to prevent duplicate enrollments
    existing = db.query(Enrollment).filter(Enrollment.applicationId == payload.applicationId).first()
    if existing:
        return make_response(success=True, message="Applicant already enrolled.", data={"id": existing.id, "enrollmentNumber": existing.enrollmentNumber})

    if app.status != "APPROVED":
        raise HTTPException(status_code=400, detail="Cannot enroll student. Application is not approved.")

    # Search for an existing User account for this student to link to
    student_user = db.query(User).filter(User.email == app.email).first()
    if not student_user:
        # Create a new User account for the student
        student_role = db.query(Role).filter(Role.name == "STUDENT").first()
        student_user = User(
            email=app.email,
            username=app.email.split("@")[0] + "_" + uuid.uuid4().hex[:4],
            passwordHash="PBKDF2_INSECURE_MOCK",
            name=app.applicantName,
            roleId=student_role.id,
            departmentId=payload.departmentId,
            sectionId=payload.sectionId
        )
        db.add(student_user)
        db.flush()

    # Generate unique usn & rollNumber safely
    timestamp = int(datetime.utcnow().timestamp())
    rand_hex = uuid.uuid4().hex[:4].upper()
    usn = f"USN-{timestamp}-{rand_hex}"
    roll_num = f"ROLL-{timestamp}-{rand_hex}"
    enroll_num = f"ENR-{timestamp}-{rand_hex}"

    enroll = Enrollment(
        applicationId=app.id,
        enrollmentNumber=enroll_num,
        studentId=student_user.id,
        usn=usn,
        rollNumber=roll_num,
        academicYearId=payload.academicYearId,
        departmentId=payload.departmentId,
        programId=payload.programId,
        semesterNumber=payload.semesterNumber,
        sectionId=payload.sectionId
    )
    db.add(enroll)

    # Transition application status to ENROLLED
    app.status = "ENROLLED"

    history = AdmissionStatusHistory(
        applicationId=app.id,
        status="ENROLLED",
        changedBy=current_user.id,
        remarks="Student successfully enrolled into program."
    )
    db.add(history)
    db.commit()
    db.refresh(enroll)

    return make_response(
        success=True,
        message="Student enrolled successfully.",
        data={
            "id": enroll.id,
            "enrollmentNumber": enroll.enrollmentNumber,
            "studentId": enroll.studentId,
            "usn": enroll.usn,
            "rollNumber": enroll.rollNumber
        }
    )

@enroll_router.get("")
def list_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    enrollments = db.query(Enrollment).all()
    return make_response(
        success=True,
        message="Enrollments retrieved.",
        data=[{
            "id": e.id,
            "enrollmentNumber": e.enrollmentNumber,
            "studentId": e.studentId,
            "usn": e.usn,
            "rollNumber": e.rollNumber,
            "academicYearId": e.academicYearId,
            "programId": e.programId
        } for e in enrollments]
    )

@enroll_router.get("/{id}")
def get_enrollment(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    enroll = db.query(Enrollment).filter(Enrollment.id == id).first()
    if not enroll:
        raise HTTPException(status_code=404, detail="Enrollment not found.")

    return make_response(
        success=True,
        message="Enrollment details retrieved.",
        data={
            "id": enroll.id,
            "enrollmentNumber": enroll.enrollmentNumber,
            "studentId": enroll.studentId,
            "usn": enroll.usn,
            "rollNumber": enroll.rollNumber,
            "academicYearId": enroll.academicYearId
        }
    )

# -------------------------------------------------------------
# ANALYTICS ENDPOINTS
# -------------------------------------------------------------

@router.get("/admission-analytics")
def get_admission_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "ADMISSION_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    total = db.query(AdmissionApplication).count()
    submitted = db.query(AdmissionApplication).filter(AdmissionApplication.status == "SUBMITTED").count()
    approved = db.query(AdmissionApplication).filter(AdmissionApplication.status == "APPROVED").count()
    rejected = db.query(AdmissionApplication).filter(AdmissionApplication.status == "REJECTED").count()
    waitlisted = db.query(AdmissionApplication).filter(AdmissionApplication.status == "WAITLISTED").count()
    enrolled = db.query(AdmissionApplication).filter(AdmissionApplication.status == "ENROLLED").count()

    return make_response(
        success=True,
        message="Admission analytics summary compiled.",
        data={
            "totalApplications": total,
            "submitted": submitted,
            "approved": approved,
            "rejected": rejected,
            "waitlisted": waitlisted,
            "enrolled": enrolled,
            "conversionRate": (enrolled / approved * 100.0) if approved > 0 else 0.0
        }
    )
