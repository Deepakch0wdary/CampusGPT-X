import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, Department, Section, AcademicYear, Program, Course, Semester, Subject,
    FacultyAssignment, StudentAssignment, StudentResult, AuditLog,
    FacultyProfile, AssignmentDef, FacultyNotes, FacultyQuiz, FacultyLeave, FacultyNotification
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class FacultyProfileUpdateSchema(BaseModel):
    officeHours: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None
    researchArea: Optional[str] = None
    specialization: Optional[str] = None
    officeLocation: Optional[str] = None
    emergencyContact: Optional[str] = None

class AssignmentDefCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    dueDate: datetime
    allowResubmission: Optional[bool] = False
    subjectId: str

class QuizCreateSchema(BaseModel):
    title: str
    subjectId: str
    questionsJson: str
    scheduledAt: Optional[datetime] = None

class NotesCreateSchema(BaseModel):
    title: str
    fileUrl: str
    fileType: str
    subjectId: str

class LeaveCreateSchema(BaseModel):
    leaveType: str # CASUAL, SICK, EARNED
    startDate: datetime
    endDate: datetime
    reason: str

class GradeSubmitSchema(BaseModel):
    studentId: str
    subjectId: str
    semesterNumber: int
    internalMarks: int
    externalMarks: int
    grade: str
    credits: int

class AttendancePrepareSchema(BaseModel):
    departmentId: str
    semesterId: str
    sectionId: str
    subjectId: str
    date: datetime
    period: str

# -------------------------------------------------------------
# HELPER GATES
# -------------------------------------------------------------
def verify_subject_assignment(faculty_id: str, subject_id: str, db: Session):
    """Enforces role-based ownership boundaries. Instructors can only interact with assigned subjects."""
    assigned = db.query(FacultyAssignment).filter_by(facultyId=faculty_id, subjectId=subject_id).first()
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied. You are not assigned to this subject."
        )

# -------------------------------------------------------------
# 1. FACULTY DASHBOARD & WIDGETS
# -------------------------------------------------------------
@router.get("/dashboard")
def get_faculty_dashboard(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "TEACHER":
        raise HTTPException(status_code=403, detail="Only faculty can view the instructor console.")
        
    profile = current_user.facultyProfile
    
    # Fetch assigned subjects and sections
    assignments = db.query(FacultyAssignment).filter_by(facultyId=current_user.id).all()
    assigned_subjects = []
    assigned_sections_count = 0
    subject_ids = []
    for a in assignments:
        subject_ids.append(a.subjectId)
        assigned_subjects.append({
            "subjectId": a.subjectId,
            "subjectName": a.subject.name if a.subject else "Unknown",
            "subjectCode": a.subject.code if a.subject else "N/A",
            "sectionName": a.section.name if a.section else "N/A",
            "semester": a.semester.semesterNumber if a.semester else 1
        })
        assigned_sections_count += 1
        
    # Pending Evaluations
    pending_evals = 0
    if subject_ids:
        pending_evals = db.query(StudentAssignment).filter(
            StudentAssignment.subjectId.in_(subject_ids),
            StudentAssignment.submissionStatus.in_(["SUBMITTED", "LATE"]),
            StudentAssignment.grade == None
        ).count()
        
    # Build dynamic timetable and welcome package
    dashboard_data = {
        "faculty": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "employeeId": profile.employeeId if profile else "EMP-N/A",
            "department": current_user.department.name if current_user.department else "Not Assigned",
            "designation": profile.specialization if profile else "Lecturer"
        },
        "widgets": {
            "assignedSubjectsCount": len(subject_ids),
            "assignedSectionsCount": assigned_sections_count,
            "pendingEvaluations": pending_evals,
            "leaveBalance": 12,
            "weeklyClassesCount": len(subject_ids) * 4
        },
        "subjects": assigned_subjects
    }
    return make_response(success=True, message="Faculty dashboard loaded successfully.", data=dashboard_data, extra_compat=dashboard_data)

# -------------------------------------------------------------
# 2. PROFILE MANAGEMENT
# -------------------------------------------------------------
@router.get("/profile")
def get_faculty_profile(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    profile = current_user.facultyProfile
    data = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "employeeId": profile.employeeId if profile else "EMP-N/A",
        "officeHours": profile.officeHours if profile else "",
        "qualification": profile.qualification if profile else "",
        "experience": profile.experience if profile else "",
        "researchArea": profile.researchArea if profile else "",
        "specialization": profile.specialization if profile else "",
        "officeLocation": profile.officeLocation if profile else "",
        "emergencyContact": profile.emergencyContact if profile else ""
    }
    return make_response(success=True, message="Profile retrieved.", data=data, extra_compat=data)

@router.put("/profile")
def update_faculty_profile(payload: FacultyProfileUpdateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    profile = current_user.facultyProfile
    if not profile:
        profile = FacultyProfile(id=str(uuid.uuid4()), userId=current_user.id, employeeId=f"EMP-{uuid.uuid4().hex[:6].upper()}")
        db.add(profile)
        
    if payload.officeHours is not None: profile.officeHours = payload.officeHours
    if payload.qualification is not None: profile.qualification = payload.qualification
    if payload.experience is not None: profile.experience = payload.experience
    if payload.researchArea is not None: profile.researchArea = payload.researchArea
    if payload.specialization is not None: profile.specialization = payload.specialization
    if payload.officeLocation is not None: profile.officeLocation = payload.officeLocation
    if payload.emergencyContact is not None: profile.emergencyContact = payload.emergencyContact
    
    db.commit()
    return make_response(success=True, message="Faculty profile updated successfully.", data={})

# -------------------------------------------------------------
# 3. CLASS MANAGEMENT
# -------------------------------------------------------------
@router.get("/classes")
def list_assigned_classes(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    assignments = db.query(FacultyAssignment).filter_by(facultyId=current_user.id).all()
    data = []
    for a in assignments:
        # Calculate section strength
        student_count = db.query(User).filter_by(sectionId=a.sectionId).count()
        data.append({
            "id": a.id,
            "subjectId": a.subjectId,
            "subjectName": a.subject.name if a.subject else "Unknown",
            "subjectCode": a.subject.code if a.subject else "N/A",
            "sectionId": a.sectionId,
            "sectionName": a.section.name if a.section else "N/A",
            "semester": a.semester.semesterNumber if a.semester else 1,
            "academicYear": a.academicYear.name if a.academicYear else "N/A",
            "studentCount": student_count
        })
    return make_response(success=True, message="Assigned classes fetched.", data={"classes": data}, extra_compat={"classes": data})

@router.get("/classes/{section_id}/students")
def get_class_students(section_id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    # Verify faculty teaches this section
    is_assigned = db.query(FacultyAssignment).filter_by(facultyId=current_user.id, sectionId=section_id).first()
    if current_user.role.name != "MASTER_ADMIN" and not is_assigned:
        raise HTTPException(status_code=403, detail="Access Denied. You do not teach this class section.")
        
    students = db.query(User).filter_by(sectionId=section_id).all()
    data = [{
        "id": s.id,
        "name": s.name,
        "email": s.email,
        "usn": s.profile.usn if s.profile else None
    } for s in students]
    return make_response(success=True, message="Section students fetched.", data={"students": data}, extra_compat={"students": data})

# -------------------------------------------------------------
# 4. ASSIGNMENT MANAGEMENT
# -------------------------------------------------------------
@router.post("/assignments")
def create_assignment_def(payload: AssignmentDefCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    verify_subject_assignment(current_user.id, payload.subjectId, db)
    
    assign_def = AssignmentDef(
        id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        dueDate=payload.dueDate,
        allowResubmission=payload.allowResubmission,
        subjectId=payload.subjectId,
        facultyId=current_user.id
    )
    db.add(assign_def)
    db.commit()
    
    # Auto-provision StudentAssignment records for all students in the assigned sections of this subject
    fac_assignments = db.query(FacultyAssignment).filter_by(facultyId=current_user.id, subjectId=payload.subjectId).all()
    section_ids = [fa.sectionId for fa in fac_assignments]
    
    students = db.query(User).filter(User.sectionId.in_(section_ids)).all()
    for s in students:
        student_assign = StudentAssignment(
            id=str(uuid.uuid4()),
            userId=s.id,
            subjectId=payload.subjectId,
            title=payload.title,
            description=payload.description,
            dueDate=payload.dueDate,
            submissionStatus="PENDING",
            assignmentDefId=assign_def.id
        )
        db.add(student_assign)
    db.commit()
    
    return make_response(success=True, message="Assignment definition created and pushed to students.", data={"id": assign_def.id})

@router.get("/assignments")
def get_faculty_assignments(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    defs = db.query(AssignmentDef).filter_by(facultyId=current_user.id).all()
    data = [{
        "id": d.id,
        "title": d.title,
        "description": d.description,
        "dueDate": d.dueDate,
        "allowResubmission": d.allowResubmission,
        "subjectName": d.subject.name if d.subject else "Unknown",
        "subjectCode": d.subject.code if d.subject else "N/A"
    } for d in defs]
    return make_response(success=True, message="Faculty assignments retrieved.", data={"assignments": data}, extra_compat={"assignments": data})

@router.delete("/assignments/{id}")
def delete_assignment_def(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    assign_def = db.query(AssignmentDef).filter_by(id=id, facultyId=current_user.id).first()
    if not assign_def:
        raise HTTPException(status_code=404, detail="Assignment not found or unauthorized.")
    db.delete(assign_def)
    db.commit()
    return make_response(success=True, message="Assignment deleted successfully.", data={})

@router.get("/assignments/{id}/submissions")
def get_assignment_submissions(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    assign_def = db.query(AssignmentDef).filter_by(id=id, facultyId=current_user.id).first()
    if not assign_def:
        raise HTTPException(status_code=404, detail="Assignment not found.")
        
    subs = db.query(StudentAssignment).filter_by(assignmentDefId=id).all()
    data = [{
        "id": s.id,
        "studentName": s.user.name,
        "usn": s.user.profile.usn if s.user.profile else None,
        "submissionStatus": s.submissionStatus,
        "submissionUrl": s.submissionUrl,
        "submittedAt": s.submittedAt,
        "grade": s.grade
    } for s in subs]
    return make_response(success=True, message="Submissions fetched.", data={"submissions": data}, extra_compat={"submissions": data})

# -------------------------------------------------------------
# 5. MARKS MANAGEMENT (GRADING)
# -------------------------------------------------------------
@router.post("/marks/grade")
def grade_student(payload: GradeSubmitSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    verify_subject_assignment(current_user.id, payload.subjectId, db)
    
    # Save/Update in StudentResult
    result = db.query(StudentResult).filter_by(userId=payload.studentId, subjectId=payload.subjectId).first()
    if not result:
        result = StudentResult(
            id=str(uuid.uuid4()),
            userId=payload.studentId,
            subjectId=payload.subjectId,
            semesterNumber=payload.semesterNumber,
            internalMarks=payload.internalMarks,
            externalMarks=payload.externalMarks,
            grade=payload.grade,
            credits=payload.credits
        )
        db.add(result)
    else:
        result.internalMarks = payload.internalMarks
        result.externalMarks = payload.externalMarks
        result.grade = payload.grade
        result.credits = payload.credits
        
    db.commit()
    
    # Log audit
    audit = AuditLog(id=str(uuid.uuid4()), userId=current_user.id, action="FACULTY_GRADE_STUDENT", details=f"Faculty graded student {payload.studentId} for subject {payload.subjectId}.")
    db.add(audit)
    db.commit()
    
    return make_response(success=True, message="Student graded successfully.", data={})

# -------------------------------------------------------------
# 6. QUIZ MANAGEMENT
# -------------------------------------------------------------
@router.post("/quizzes")
def create_quiz(payload: QuizCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    verify_subject_assignment(current_user.id, payload.subjectId, db)
    
    quiz = FacultyQuiz(
        id=str(uuid.uuid4()),
        title=payload.title,
        subjectId=payload.subjectId,
        facultyId=current_user.id,
        questionsJson=payload.questionsJson,
        scheduledAt=payload.scheduledAt
    )
    db.add(quiz)
    db.commit()
    return make_response(success=True, message="Quiz created successfully.", data={"id": quiz.id})

@router.get("/quizzes")
def get_faculty_quizzes(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    quizzes = db.query(FacultyQuiz).filter_by(facultyId=current_user.id).all()
    data = [{
        "id": q.id,
        "title": q.title,
        "subjectName": q.subject.name if q.subject else "Unknown",
        "status": q.status,
        "scheduledAt": q.scheduledAt
    } for q in quizzes]
    return make_response(success=True, message="Quizzes fetched.", data={"quizzes": data}, extra_compat={"quizzes": data})

# -------------------------------------------------------------
# 7. NOTES/RESOURCES MANAGEMENT
# -------------------------------------------------------------
@router.post("/notes")
def upload_notes(payload: NotesCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    verify_subject_assignment(current_user.id, payload.subjectId, db)
    
    note = FacultyNotes(
        id=str(uuid.uuid4()),
        title=payload.title,
        fileUrl=payload.fileUrl,
        fileType=payload.fileType,
        subjectId=payload.subjectId,
        facultyId=current_user.id
    )
    db.add(note)
    db.commit()
    return make_response(success=True, message="Lesson notes uploaded.", data={"id": note.id})

@router.get("/notes")
def get_notes(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    notes = db.query(FacultyNotes).filter_by(facultyId=current_user.id).all()
    data = [{
        "id": n.id,
        "title": n.title,
        "fileUrl": n.fileUrl,
        "fileType": n.fileType,
        "subjectName": n.subject.name if n.subject else "Unknown"
    } for n in notes]
    return make_response(success=True, message="Notes fetched.", data={"notes": data}, extra_compat={"notes": data})

# -------------------------------------------------------------
# 8. LEAVE TRACKING
# -------------------------------------------------------------
@router.post("/leaves")
def apply_leave(payload: LeaveCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    leave = FacultyLeave(
        id=str(uuid.uuid4()),
        facultyId=current_user.id,
        leaveType=payload.leaveType,
        startDate=payload.startDate,
        endDate=payload.endDate,
        reason=payload.reason
    )
    db.add(leave)
    db.commit()
    return make_response(success=True, message="Leave application submitted successfully.", data={"id": leave.id})

@router.get("/leaves")
def get_leaves(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    leaves = db.query(FacultyLeave).filter_by(facultyId=current_user.id).all()
    data = [{
        "id": l.id,
        "leaveType": l.leaveType,
        "startDate": l.startDate,
        "endDate": l.endDate,
        "reason": l.reason,
        "status": l.status,
        "requestedAt": l.requestedAt
    } for l in leaves]
    return make_response(success=True, message="Leaves list retrieved.", data={"leaves": data}, extra_compat={"leaves": data})

# -------------------------------------------------------------
# 9. ATTENDANCE SESSION PREPARATION
# -------------------------------------------------------------
@router.post("/attendance/prepare")
def prepare_attendance_session(payload: AttendancePrepareSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    verify_subject_assignment(current_user.id, payload.subjectId, db)
    
    # Audit trail logs the session generation
    audit = AuditLog(
        id=str(uuid.uuid4()),
        userId=current_user.id,
        action="FACULTY_PREPARE_ATTENDANCE_SESSION",
        details=f"Faculty prepared session for section {payload.sectionId}, subject {payload.subjectId}, date {payload.date.date()}."
    )
    db.add(audit)
    db.commit()
    
    return make_response(success=True, message="Attendance preparation session generated successfully.", data={
        "sessionId": str(uuid.uuid4()),
        "status": "READY_TO_MARK"
    })

# -------------------------------------------------------------
# 10. NOTIFICATIONS
# -------------------------------------------------------------
@router.get("/notifications")
def get_faculty_notifications(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    alerts = db.query(FacultyNotification).filter_by(facultyId=current_user.id).all()
    data = [{
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "type": a.type,
        "read": a.read,
        "createdAt": a.createdAt
    } for a in alerts]
    return make_response(success=True, message="Notifications list loaded.", data={"notifications": data}, extra_compat={"notifications": data})
