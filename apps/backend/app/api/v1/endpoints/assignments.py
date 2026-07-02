import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, AcademicYear, Department, Program, Semester, Section, Subject,
    Assignment, AssignmentFile, AssignmentSubmission, SubmissionAttachment,
    AssignmentFeedback, AssignmentGrade, AssignmentAudit
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class AssignmentFileSchema(BaseModel):
    fileName: str
    fileUrl: str
    fileSize: int

class AssignmentCreateSchema(BaseModel):
    academicYearId: str
    departmentId: str
    programId: str
    semesterId: str
    sectionId: str
    subjectId: str
    assignmentType: str # HOMEWORK, PROJECT, LAB, EXAM
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    dueDate: datetime
    maxMarks: float
    allowedFileTypes: str # e.g. "PDF,ZIP,DOCX"
    maxUploadSizeMb: float = 10.0
    status: str = "DRAFT" # DRAFT, PUBLISHED
    files: Optional[List[AssignmentFileSchema]] = None

class AssignmentUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    dueDate: Optional[datetime] = None
    maxMarks: Optional[float] = None
    allowedFileTypes: Optional[str] = None
    maxUploadSizeMb: Optional[float] = None
    status: Optional[str] = None
    files: Optional[List[AssignmentFileSchema]] = None

class AttachmentSchema(BaseModel):
    fileName: str
    fileUrl: str
    fileSize: int

class SubmissionCreateSchema(BaseModel):
    attachments: List[AttachmentSchema]

class GradeCreateSchema(BaseModel):
    marksObtained: float
    isPublished: bool = False
    comments: Optional[str] = None
    annotatedFileUrl: Optional[str] = None

# -------------------------------------------------------------
# AUDIT HELPER
# -------------------------------------------------------------
def log_assignment_audit(db: Session, user_id: str, action: str, assignment_id: Optional[str] = None):
    audit = AssignmentAudit(
        id=str(uuid.uuid4()),
        assignmentId=assignment_id,
        userId=user_id,
        action=action,
        ipAddress="127.0.0.1",
        userAgent="Client browser"
    )
    db.add(audit)
    db.commit()

# -------------------------------------------------------------
# CRUD ENDPOINTS
# -------------------------------------------------------------

@router.post("")
def create_assignment(payload: AssignmentCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only master admins or faculty can create assignments.")

    # Validation: due date must be in future
    if payload.dueDate < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Due date must be in the future.")

    assignment = Assignment(
        id=str(uuid.uuid4()),
        academicYearId=payload.academicYearId,
        departmentId=payload.departmentId,
        programId=payload.programId,
        semesterId=payload.semesterId,
        sectionId=payload.sectionId,
        subjectId=payload.subjectId,
        facultyId=current_user.id,
        assignmentType=payload.assignmentType,
        title=payload.title,
        description=payload.description,
        instructions=payload.instructions,
        dueDate=payload.dueDate,
        maxMarks=payload.maxMarks,
        allowedFileTypes=payload.allowedFileTypes,
        maxUploadSizeMb=payload.maxUploadSizeMb,
        status=payload.status
    )
    db.add(assignment)
    db.flush()

    if payload.files:
        for f in payload.files:
            file_record = AssignmentFile(
                id=str(uuid.uuid4()),
                assignmentId=assignment.id,
                fileName=f.fileName,
                fileUrl=f.fileUrl,
                fileSize=f.fileSize
            )
            db.add(file_record)

    db.commit()
    log_assignment_audit(db, current_user.id, "CREATE_ASSIGNMENT", assignment.id)

    return make_response(success=True, message="Assignment created successfully.", data={"id": assignment.id, "title": assignment.title})


@router.get("")
def list_assignments(
    departmentId: Optional[str] = None,
    programId: Optional[str] = None,
    semesterId: Optional[str] = None,
    sectionId: Optional[str] = None,
    subjectId: Optional[str] = None,
    assignmentType: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    sortBy: str = "dueDate",
    order: str = "asc",
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    query = db.query(Assignment)

    # Scoping/Permissions check: Students can only view published assignments mapped to their section
    if current_user.role.name == "STUDENT":
        query = query.filter(Assignment.status == "PUBLISHED")
        # Force filter by student's section/semester if available
        if current_user.sectionId:
            query = query.filter(Assignment.sectionId == current_user.sectionId)
    elif current_user.role.name == "TEACHER":
        # Teachers can only view assignments they created or mapped to sections they teach
        query = query.filter(or_(Assignment.facultyId == current_user.id, Assignment.sectionId == current_user.sectionId))

    # Optional Filters
    if departmentId:
        query = query.filter(Assignment.departmentId == departmentId)
    if programId:
        query = query.filter(Assignment.programId == programId)
    if semesterId:
        query = query.filter(Assignment.semesterId == semesterId)
    if sectionId:
        query = query.filter(Assignment.sectionId == sectionId)
    if subjectId:
        query = query.filter(Assignment.subjectId == subjectId)
    if assignmentType:
        query = query.filter(Assignment.assignmentType == assignmentType)
    if status_filter:
        query = query.filter(Assignment.status == status_filter)

    # Search
    if search:
        query = query.filter(or_(
            Assignment.title.ilike(f"%{search}%"),
            Assignment.description.ilike(f"%{search}%")
        ))

    # Sorting
    sort_column = getattr(Assignment, sortBy, Assignment.dueDate)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Pagination
    offset = (page - 1) * limit
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    data_list = []
    for item in items:
        # Check if current user has submission
        submission_status = "PENDING"
        submitted_at = None
        user_sub = db.query(AssignmentSubmission).filter_by(assignmentId=item.id, studentId=current_user.id).first()
        if user_sub:
            submission_status = user_sub.status
            submitted_at = user_sub.submittedAt

        data_list.append({
            "id": item.id,
            "title": item.title,
            "assignmentType": item.assignmentType,
            "dueDate": item.dueDate,
            "maxMarks": item.maxMarks,
            "status": item.status,
            "subjectName": item.subject.name if item.subject else "",
            "submissionStatus": submission_status,
            "submittedAt": submitted_at
        })

    return make_response(success=True, message="Assignments listed.", data={"assignments": data_list, "total": total, "page": page, "limit": limit})


@router.get("/{id}")
def get_assignment(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter_by(id=id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    # Access control
    if current_user.role.name == "STUDENT" and assignment.status != "PUBLISHED":
        raise HTTPException(status_code=403, detail="Draft assignments are hidden from students.")

    files_list = [{"id": f.id, "fileName": f.fileName, "fileUrl": f.fileUrl, "fileSize": f.fileSize} for f in assignment.files]

    # Student submission state details
    sub_data = None
    sub = db.query(AssignmentSubmission).filter_by(assignmentId=assignment.id, studentId=current_user.id).first()
    if sub:
        attachments = [{"id": a.id, "fileName": a.fileName, "fileUrl": a.fileUrl, "fileSize": a.fileSize} for a in sub.attachments]
        grade_val = sub.grade.marksObtained if (sub.grade and sub.grade.isPublished) else None
        feedback_val = sub.feedback[0].comments if (sub.feedback and sub.grade and sub.grade.isPublished) else None
        sub_data = {
            "id": sub.id,
            "status": sub.status,
            "submittedAt": sub.submittedAt,
            "attachments": attachments,
            "grade": grade_val,
            "feedback": feedback_val
        }

    res_data = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "instructions": assignment.instructions,
        "dueDate": assignment.dueDate,
        "maxMarks": assignment.maxMarks,
        "allowedFileTypes": assignment.allowedFileTypes,
        "maxUploadSizeMb": assignment.maxUploadSizeMb,
        "status": assignment.status,
        "assignmentType": assignment.assignmentType,
        "subjectId": assignment.subjectId,
        "subjectName": assignment.subject.name if assignment.subject else "",
        "sectionId": assignment.sectionId,
        "files": files_list,
        "submission": sub_data
    }
    return make_response(success=True, message="Assignment loaded.", data=res_data)


@router.put("/{id}")
def update_assignment(id: str, payload: AssignmentUpdateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter_by(id=id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Only faculty or admin can update assignments.")

    if current_user.role.name == "TEACHER" and assignment.facultyId != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this assignment.")

    # Update fields
    for field, val in payload.dict(exclude_unset=True).items():
        if field == "files":
            continue
        setattr(assignment, field, val)

    if payload.files is not None:
        # Clear old files
        db.query(AssignmentFile).filter_by(assignmentId=assignment.id).delete()
        for f in payload.files:
            file_record = AssignmentFile(
                id=str(uuid.uuid4()),
                assignmentId=assignment.id,
                fileName=f.fileName,
                fileUrl=f.fileUrl,
                fileSize=f.fileSize
            )
            db.add(file_record)

    db.commit()
    log_assignment_audit(db, current_user.id, f"UPDATE_ASSIGNMENT", assignment.id)

    return make_response(success=True, message="Assignment updated successfully.")


@router.delete("/{id}")
def delete_assignment(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter_by(id=id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Only faculty or admin can delete assignments.")

    if current_user.role.name == "TEACHER" and assignment.facultyId != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this assignment.")

    db.delete(assignment)
    db.commit()
    log_assignment_audit(db, current_user.id, "DELETE_ASSIGNMENT", id)

    return make_response(success=True, message="Assignment deleted successfully.")

# -------------------------------------------------------------
# SUBMISSIONS ENDPOINTS
# -------------------------------------------------------------

@router.post("/{id}/submit")
def submit_assignment(id: str, payload: SubmissionCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can submit assignments.")

    assignment = db.query(Assignment).filter_by(id=id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if assignment.status != "PUBLISHED":
        raise HTTPException(status_code=400, detail="This assignment is not published.")

    # Validation: File checks (Allowed extensions and size limits)
    allowed = [ext.strip().upper() for ext in assignment.allowedFileTypes.split(",")]
    for att in payload.attachments:
        ext = att.fileName.split(".")[-1].upper() if "." in att.fileName else ""
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed. Supported formats: {assignment.allowedFileTypes}")
        
        # Max upload size check
        size_mb = att.fileSize / (1024 * 1024)
        if size_mb > assignment.maxUploadSizeMb:
            raise HTTPException(status_code=400, detail=f"File size exceeds maximum upload limit of {assignment.maxUploadSizeMb} MB.")

    # Create or update submission
    sub = db.query(AssignmentSubmission).filter_by(assignmentId=id, studentId=current_user.id).first()
    is_late = datetime.utcnow() > assignment.dueDate
    sub_status = "LATE" if is_late else "SUBMITTED"

    if sub:
        # Resubmission: replace old attachments
        db.query(SubmissionAttachment).filter_by(submissionId=sub.id).delete()
        sub.status = sub_status
        sub.submittedAt = datetime.utcnow()
    else:
        sub = AssignmentSubmission(
            id=str(uuid.uuid4()),
            assignmentId=id,
            studentId=current_user.id,
            status=sub_status,
            submittedAt=datetime.utcnow()
        )
        db.add(sub)
        db.flush()

    for att in payload.attachments:
        attachment_record = SubmissionAttachment(
            id=str(uuid.uuid4()),
            submissionId=sub.id,
            fileName=att.fileName,
            fileUrl=att.fileUrl,
            fileSize=att.fileSize
        )
        db.add(attachment_record)

    db.commit()
    log_assignment_audit(db, current_user.id, "SUBMIT_ASSIGNMENT", id)

    msg = "Assignment resubmitted successfully." if sub else "Assignment submitted successfully."
    if is_late:
        msg += " Warning: Submitted after the deadline."

    return make_response(success=True, message=msg, data={"id": sub.id, "status": sub.status})


@router.get("/{id}/submissions")
def view_submissions(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter_by(id=id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Only faculty and admin can view submissions.")

    if current_user.role.name == "TEACHER" and assignment.facultyId != current_user.id:
        raise HTTPException(status_code=403, detail="You do not teach this subject section.")

    sub_records = db.query(AssignmentSubmission).filter_by(assignmentId=id).all()
    res_list = []
    for sub in sub_records:
        attachments = [{"fileName": a.fileName, "fileUrl": a.fileUrl, "fileSize": a.fileSize} for a in sub.attachments]
        grade_info = {"marksObtained": sub.grade.marksObtained, "isPublished": sub.grade.isPublished} if sub.grade else None
        feedback_info = {"comments": sub.feedback[0].comments, "annotatedFileUrl": sub.feedback[0].annotatedFileUrl} if sub.feedback else None
        res_list.append({
            "id": sub.id,
            "studentId": sub.studentId,
            "studentName": sub.student.name if sub.student else "",
            "status": sub.status,
            "submittedAt": sub.submittedAt,
            "attachments": attachments,
            "grade": grade_info,
            "feedback": feedback_info
        })

    return make_response(success=True, message="Submissions retrieved.", data=res_list)

# -------------------------------------------------------------
# GRADING & FEEDBACK ENDPOINTS
# -------------------------------------------------------------

@router.post("/submissions/{submission_id}/grade")
def grade_submission(
    submission_id: str,
    payload: GradeCreateSchema,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    sub = db.query(AssignmentSubmission).filter_by(id=submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    assignment = sub.assignment
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Only faculty can grade submissions.")

    if current_user.role.name == "TEACHER" and assignment.facultyId != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to grade this assignment.")

    if payload.marksObtained > assignment.maxMarks or payload.marksObtained < 0:
        raise HTTPException(status_code=400, detail=f"Marks obtained must be between 0 and {assignment.maxMarks}")

    # Grade creation/update
    grade_rec = db.query(AssignmentGrade).filter_by(submissionId=submission_id).first()
    if grade_rec:
        grade_rec.marksObtained = payload.marksObtained
        grade_rec.isPublished = payload.isPublished
        grade_rec.gradedAt = datetime.utcnow()
    else:
        grade_rec = AssignmentGrade(
            id=str(uuid.uuid4()),
            submissionId=submission_id,
            marksObtained=payload.marksObtained,
            isPublished=payload.isPublished
        )
        db.add(grade_rec)

    # Feedback creation/update
    if payload.comments:
        db.query(AssignmentFeedback).filter_by(submissionId=submission_id).delete()
        feedback_rec = AssignmentFeedback(
            id=str(uuid.uuid4()),
            submissionId=submission_id,
            facultyId=current_user.id,
            comments=payload.comments,
            annotatedFileUrl=payload.annotatedFileUrl
        )
        db.add(feedback_rec)

    # Update submission status
    sub.status = "GRADED"
    db.commit()
    log_assignment_audit(db, current_user.id, "GRADE_ASSIGNMENT", assignment.id)

    return make_response(success=True, message="Submission evaluated successfully.")

# -------------------------------------------------------------
# STATISTICS ENDPOINTS
# -------------------------------------------------------------

@router.get("/statistics/summary")
def get_assignment_statistics(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name == "TEACHER":
        total_created = db.query(Assignment).filter_by(facultyId=current_user.id).count()
        published_count = db.query(Assignment).filter_by(facultyId=current_user.id, status="PUBLISHED").count()
        draft_count = db.query(Assignment).filter_by(facultyId=current_user.id, status="DRAFT").count()

        # Pending evaluations (Submissions where status is SUBMITTED or LATE)
        pending_eval = db.query(AssignmentSubmission).join(Assignment).filter(
            Assignment.facultyId == current_user.id,
            AssignmentSubmission.status.in_(["SUBMITTED", "LATE"])
        ).count()

        # Average marks across graded assignments
        graded_marks = db.query(AssignmentGrade.marksObtained).join(AssignmentSubmission).join(Assignment).filter(
            Assignment.facultyId == current_user.id
        ).all()
        avg_marks = 0.0
        if graded_marks:
            avg_marks = sum(m[0] for m in graded_marks) / len(graded_marks)

        late_subs = db.query(AssignmentSubmission).join(Assignment).filter(
            Assignment.facultyId == current_user.id,
            AssignmentSubmission.status == "LATE"
        ).count()

        stats = {
            "totalCreated": total_created,
            "publishedCount": published_count,
            "draftCount": draft_count,
            "pendingEvaluationCount": pending_eval,
            "averageMarks": round(avg_marks, 2),
            "lateSubmissionsCount": late_subs
        }
    else: # Student
        # Enrolled section assignments
        sec_id = current_user.sectionId if current_user.sectionId else ""
        total_assignments = db.query(Assignment).filter_by(sectionId=sec_id, status="PUBLISHED").all()
        total_count = len(total_assignments)

        subs = db.query(AssignmentSubmission).filter_by(studentId=current_user.id).all()
        submitted_count = len(subs)
        pending_count = max(0, total_count - submitted_count)

        upcoming_count = 0
        for item in total_assignments:
            # check if due in future and student hasn't submitted yet
            has_submitted = any(s.assignmentId == item.id for s in subs)
            if item.dueDate > datetime.utcnow() and not has_submitted:
                upcoming_count += 1

        stats = {
            "totalAssignments": total_count,
            "completedAssignments": submitted_count,
            "pendingAssignments": pending_count,
            "upcomingDeadlines": upcoming_count
        }

    return make_response(success=True, message="Biometric / Assignment statistics loaded.", data=stats)
