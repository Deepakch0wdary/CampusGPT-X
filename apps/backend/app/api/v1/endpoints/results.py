import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, AcademicYear, Department, Program, Semester, Section, Subject,
    Result, ResultDetail, GradeScheme, GradeBoundary, Transcript,
    RevaluationRequest, ResultAnalytics, MeritList, ResultAudit
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class GradeBoundaryPayload(BaseModel):
    letterGrade: str
    gradePoint: float
    minPercentage: float
    maxPercentage: float

class GradeSchemeCreatePayload(BaseModel):
    academicYearId: str
    programId: str
    gradeScale: str = "10-POINT"
    creditSystem: str = "CHOICE_BASED"
    graceRules: Optional[str] = None
    passingMarks: float = 40.0
    boundaries: List[GradeBoundaryPayload]

class MarkEntryPayload(BaseModel):
    studentId: str
    subjectId: str
    academicYearId: str
    semesterNumber: int
    internalMarks: float = 0.0
    assignmentMarks: float = 0.0
    labMarks: float = 0.0
    practicalMarks: float = 0.0
    projectMarks: float = 0.0
    semesterExamMarks: float = 0.0
    graceMarks: float = 0.0
    moderationMarks: float = 0.0

class ResultPublishPayload(BaseModel):
    status: str # DRAFT, DEPT_REVIEW, EXAM_CELL_APPROVED, PUBLISHED, ARCHIVED, ROLLBACK

class TranscriptCreatePayload(BaseModel):
    studentId: str
    transcriptType: str # SEMESTER, CONSOLIDATED
    semesterNumber: Optional[int] = None

class RevaluationRequestPayload(BaseModel):
    resultDetailId: str
    requestType: str # REVALUATION, PHOTOCOPY
    remarks: Optional[str] = None

class RevaluationReviewPayload(BaseModel):
    status: str # APPROVED, REJECTED
    updatedMarks: Optional[float] = None

# -------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------
def calculate_results(db: Session, result_id: str):
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        return

    details = db.query(ResultDetail).filter(ResultDetail.resultId == result_id).all()
    if not details:
        return

    # Find GradeScheme for this academic year and student program
    # Mapped from Student -> Program
    student_user = db.query(User).filter(User.id == result.studentId).first()
    program_id = None
    if student_user and student_user.section and student_user.section.programId:
        program_id = student_user.section.programId

    scheme = None
    if program_id:
        scheme = db.query(GradeScheme).filter(
            GradeScheme.academicYearId == result.academicYearId,
            GradeScheme.programId == program_id
        ).first()

    # Fallback to general default scheme if none matches
    if not scheme:
        scheme = db.query(GradeScheme).filter(GradeScheme.academicYearId == result.academicYearId).first()

    total_max_marks = 0.0
    total_obtained_marks = 0.0
    total_grade_points = 0.0
    total_credits = 0

    for d in details:
        # Total Marks = Sum of internal, assignment, lab, practical, project, semester exams, grace, and moderation marks
        d.totalMarks = (
            d.internalMarks + d.assignmentMarks + d.labMarks + d.practicalMarks + 
            d.projectMarks + d.semesterExamMarks + d.graceMarks + d.moderationMarks
        )

        subject = db.query(Subject).filter(Subject.id == d.subjectId).first()
        subj_credits = subject.credits if subject else 3
        total_credits += subj_credits

        # Calculate percentage (assuming default max 100 for simplicity)
        percentage = d.totalMarks # since base is 100

        # Assign Grade and GradePoint
        assigned_grade = "F"
        assigned_point = 0.0
        is_pass = "FAIL"

        if scheme:
            # Check boundaries
            for bound in scheme.boundaries:
                if bound.minPercentage <= percentage <= bound.maxPercentage:
                    assigned_grade = bound.letterGrade
                    assigned_point = bound.gradePoint
                    break
            
            passing_cutoff = scheme.passingMarks
            if d.totalMarks >= passing_cutoff:
                is_pass = "PASS"
        else:
            # Default boundary logic if no scheme configured
            if percentage >= 90:
                assigned_grade, assigned_point = "O", 10.0
            elif percentage >= 80:
                assigned_grade, assigned_point = "A+", 9.0
            elif percentage >= 70:
                assigned_grade, assigned_point = "A", 8.0
            elif percentage >= 60:
                assigned_grade, assigned_point = "B+", 7.0
            elif percentage >= 50:
                assigned_grade, assigned_point = "B", 6.0
            elif percentage >= 40:
                assigned_grade, assigned_point = "C", 5.0
            else:
                assigned_grade, assigned_point = "F", 0.0

            if percentage >= 40.0:
                is_pass = "PASS"

        d.grade = assigned_grade
        d.gradePoint = assigned_point
        d.passFail = is_pass

        total_obtained_marks += d.totalMarks
        total_max_marks += 100.0
        total_grade_points += (assigned_point * subj_credits)

    # Compute overall aggregates
    result.totalMarks = total_obtained_marks
    result.percentage = (total_obtained_marks / total_max_marks * 100.0) if total_max_marks > 0 else 0.0
    result.creditsEarned = total_credits
    result.sgpa = (total_grade_points / total_credits) if total_credits > 0 else 0.0
    result.cgpa = result.sgpa # Assuming SGPA equals CGPA for single-semester calculation

    db.commit()

# -------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------

@router.post("/marks")
def enter_student_marks(
    payload: MarkEntryPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Unauthorized role for mark entry")

    # Find or create Result parent
    result = db.query(Result).filter(
        Result.studentId == payload.studentId,
        Result.academicYearId == payload.academicYearId,
        Result.semesterNumber == payload.semesterNumber
    ).first()

    if not result:
        result = Result(
            studentId=payload.studentId,
            academicYearId=payload.academicYearId,
            semesterNumber=payload.semesterNumber,
            status="DRAFT"
        )
        db.add(result)
        db.flush()

    # Find or create ResultDetail
    detail = db.query(ResultDetail).filter(
        ResultDetail.resultId == result.id,
        ResultDetail.subjectId == payload.subjectId
    ).first()

    if not detail:
        detail = ResultDetail(
            resultId=result.id,
            subjectId=payload.subjectId
        )
        db.add(detail)

    # Map marks
    detail.internalMarks = payload.internalMarks
    detail.assignmentMarks = payload.assignmentMarks
    detail.labMarks = payload.labMarks
    detail.practicalMarks = payload.practicalMarks
    detail.projectMarks = payload.projectMarks
    detail.semesterExamMarks = payload.semesterExamMarks
    detail.graceMarks = payload.graceMarks
    detail.moderationMarks = payload.moderationMarks

    db.commit()

    # Recalculate aggregates
    calculate_results(db, result.id)

    # Log audit
    audit = ResultAudit(
        resultId=result.id,
        userId=current_user.id,
        action="MARKS_ENTRY",
        details=f"Entered marks for student {payload.studentId}, Subject: {payload.subjectId}"
    )
    db.add(audit)
    db.commit()

    return make_response(success=True, message="Student marks updated and results calculated.")

@router.post("/schemes", status_code=status.HTTP_201_CREATED)
def create_grade_scheme(
    payload: GradeSchemeCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Admin exclusive grade configuration")

    scheme = GradeScheme(
        academicYearId=payload.academicYearId,
        programId=payload.programId,
        gradeScale=payload.gradeScale,
        creditSystem=payload.creditSystem,
        graceRules=payload.graceRules,
        passingMarks=payload.passingMarks
    )
    db.add(scheme)
    db.flush()

    for bound in payload.boundaries:
        db.add(GradeBoundary(
            gradeSchemeId=scheme.id,
            letterGrade=bound.letterGrade,
            gradePoint=bound.gradePoint,
            minPercentage=bound.minPercentage,
            maxPercentage=bound.maxPercentage
        ))

    db.commit()
    return make_response(success=True, message="Grade scheme configured successfully.", data={"id": scheme.id})

@router.get("/schemes")
def list_grade_schemes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    schemes = db.query(GradeScheme).all()
    return make_response(
        success=True,
        message="Grade schemes retrieved",
        data=[{
            "id": s.id,
            "academicYearId": s.academicYearId,
            "programId": s.programId,
            "gradeScale": s.gradeScale,
            "passingMarks": s.passingMarks
        } for s in schemes]
    )

@router.post("/{id}/publish")
def publish_results(
    id: str,
    payload: ResultPublishPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Unauthorized to publish results")

    result = db.query(Result).filter(Result.id == id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result compile card not found")

    # Workflow permissions
    if payload.status == "PUBLISHED" and current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Only Exam Cell Admins can final publish results")

    result.status = payload.status
    db.commit()

    # Log audit
    audit = ResultAudit(
        resultId=result.id,
        userId=current_user.id,
        action="RESULT_PUBLISH",
        details=f"Result status transitioned to {payload.status}"
    )
    db.add(audit)
    db.commit()

    return make_response(success=True, message=f"Result card transition set to {payload.status}.")

@router.post("/transcripts")
def generate_transcript(
    payload: TranscriptCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Admin exclusive action")

    # Prevent duplicates
    dup = db.query(Transcript).filter(
        Transcript.studentId == payload.studentId,
        Transcript.transcriptType == payload.transcriptType,
        Transcript.semesterNumber == payload.semesterNumber
    ).first()

    if dup:
        return make_response(success=True, message="Transcript already generated.", data={"id": dup.id, "qrCodeValue": dup.qrCodeValue})

    qr_val = f"TR-{payload.transcriptType[:3]}-{payload.studentId[:6]}-{datetime.utcnow().timestamp()}"
    signature = f"SIG-EXAMCELL-{uuid.uuid4().hex[:12]}"

    transcript = Transcript(
        studentId=payload.studentId,
        transcriptType=payload.transcriptType,
        semesterNumber=payload.semesterNumber,
        qrCodeValue=qr_val,
        digitalSignature=signature
    )
    db.add(transcript)

    audit = ResultAudit(
        userId=current_user.id,
        action="TRANSCRIPT_GEN",
        details=f"Generated {payload.transcriptType} transcript for student {payload.studentId}"
    )
    db.add(audit)
    db.commit()
    db.refresh(transcript)

    return make_response(
        success=True,
        message="Transcript generated successfully",
        data={
            "id": transcript.id,
            "qrCodeValue": transcript.qrCodeValue,
            "digitalSignature": transcript.digitalSignature
        }
    )

@router.get("/transcripts")
def get_transcripts(
    studentId: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    query = db.query(Transcript)
    if current_user.role.name == "STUDENT":
        query = query.filter(Transcript.studentId == current_user.id)
    elif studentId:
        query = query.filter(Transcript.studentId == studentId)

    transcripts = query.all()
    return make_response(
        success=True,
        message="Transcripts retrieved",
        data=[{
            "id": t.id,
            "transcriptType": t.transcriptType,
            "semesterNumber": t.semesterNumber,
            "qrCodeValue": t.qrCodeValue,
            "issueDate": t.issueDate.isoformat()
        } for t in transcripts]
    )

@router.post("/revaluation")
def apply_revaluation(
    payload: RevaluationRequestPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Student exclusive application portal")

    detail = db.query(ResultDetail).filter(ResultDetail.id == payload.resultDetailId).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Subject result details not found")

    # Prevent duplicate requests
    dup = db.query(RevaluationRequest).filter(
        RevaluationRequest.resultDetailId == payload.resultDetailId,
        RevaluationRequest.studentId == current_user.id
    ).first()

    if dup:
        raise HTTPException(status_code=400, detail="Revaluation request already logged for this subject result")

    request = RevaluationRequest(
        resultDetailId=payload.resultDetailId,
        studentId=current_user.id,
        requestType=payload.requestType,
        status="PENDING",
        paymentStatus="PAID", # Mocking immediate payment for simplicity
        remarks=payload.remarks,
        originalMarks=detail.totalMarks
    )
    db.add(request)

    audit = ResultAudit(
        userId=current_user.id,
        action="REVALUATION_REQUEST",
        details=f"Applied for {payload.requestType} on resultDetail {payload.resultDetailId}"
    )
    db.add(audit)
    db.commit()
    db.refresh(request)

    return make_response(
        success=True,
        message="Revaluation request registered successfully",
        data={"id": request.id, "status": request.status}
    )

@router.post("/revaluation/{id}/review")
def review_revaluation(
    id: str,
    payload: RevaluationReviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Unauthorized role for revaluation reviews")

    request = db.query(RevaluationRequest).filter(RevaluationRequest.id == id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Revaluation request not found")

    request.status = payload.status
    request.facultyId = current_user.id

    if payload.status == "APPROVED" and payload.updatedMarks is not None:
        request.updatedMarks = payload.updatedMarks
        # Propagate changes to ResultDetail
        detail = db.query(ResultDetail).filter(ResultDetail.id == request.resultDetailId).first()
        if detail:
            # Overwrite external/semester marks with diff
            diff = payload.updatedMarks - request.originalMarks
            detail.semesterExamMarks += diff
            db.commit()
            calculate_results(db, detail.resultId)

    db.commit()

    audit = ResultAudit(
        userId=current_user.id,
        action="REVALUATION_APPROVE",
        details=f"Reviewed revaluation {id} as {payload.status} with updated marks: {payload.updatedMarks}"
    )
    db.add(audit)
    db.commit()

    return make_response(success=True, message=f"Revaluation request review updated as {payload.status}.")

@router.get("/revaluation")
def list_revaluation_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    query = db.query(RevaluationRequest)
    if current_user.role.name == "STUDENT":
        query = query.filter(RevaluationRequest.studentId == current_user.id)

    requests = query.all()
    return make_response(
        success=True,
        message="Revaluation requests retrieved",
        data=[{
            "id": r.id,
            "resultDetailId": r.resultDetailId,
            "studentId": r.studentId,
            "requestType": r.requestType,
            "status": r.status,
            "originalMarks": r.originalMarks,
            "updatedMarks": r.updatedMarks
        } for r in requests]
    )

@router.get("/merit-list")
def get_merit_list(
    semesterNumber: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    # Dynamically compile ranks based on CGPA of active results in this semester
    results = db.query(Result).filter(
        Result.semesterNumber == semesterNumber,
        Result.status == "PUBLISHED"
    ).order_by(desc(Result.cgpa), desc(Result.totalMarks)).all()

    merit_data = []
    for rank, res in enumerate(results, start=1):
        # Prevent details crash if User doesn't exist
        std_user = db.query(User).filter(User.id == res.studentId).first()
        std_name = std_user.name if std_user else "Student"

        merit_data.append({
            "rank": rank,
            "studentId": res.studentId,
            "studentName": std_name,
            "cgpa": res.cgpa,
            "totalMarks": res.totalMarks,
            "isGoldMedalEligible": res.cgpa >= 9.5
        })

    return make_response(
        success=True,
        message="Merit list generated successfully",
        data=merit_data
    )

@router.get("/analytics")
def get_analytics(
    departmentId: str,
    semesterNumber: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    # Fetch results compiled for this dept & semester
    results = db.query(Result).join(User).filter(
        User.departmentId == departmentId,
        Result.semesterNumber == semesterNumber,
        Result.status == "PUBLISHED"
    ).all()

    total = len(results)
    passed = sum(1 for r in results if r.sgpa >= 4.0) # assuming passing SGPA is 4.0

    pass_percentage = (passed / total * 100.0) if total > 0 else 100.0
    backlogs = total - passed

    return make_response(
        success=True,
        message="Analytics summary retrieved",
        data={
            "departmentId": departmentId,
            "semesterNumber": semesterNumber,
            "totalStudents": total,
            "passPercentage": pass_percentage,
            "backlogCount": backlogs
        }
    )
