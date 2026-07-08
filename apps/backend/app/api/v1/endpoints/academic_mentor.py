from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.rbac_middleware import RoleChecker
from app.models.models import (
    User, Subject, StudentAttendanceSummary, StudentResult, StudentAssignment, Result,
    AcademicMentorProfile, AcademicInsight, AcademicRiskAssessment, AcademicRiskFactor,
    StudyRecommendation, StudyPlan, StudyPlanItem, StudentGoal, MentorIntervention,
    AcademicMentorAudit, ParentStudentLink, ParentProfile, FacultyAssignment, Role
)
from app.services.academic_mentor_service import AcademicMentorService
from app.services.notification_service import NotificationService
from app.core.responses import make_response

router = APIRouter()

# --- SECURITY UTILITIES ---

def check_student_self(current_user: User):
    """Enforces that the user is a STUDENT."""
    if current_user.role.name != "STUDENT" and current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Student self-service only."
        )

def check_parent_child_link(db: Session, parent_user: User, student_id: str) -> ParentStudentLink:
    """Verifies that parent has verified access to the requested student."""
    if parent_user.role.name == "MASTER_ADMIN":
        link = db.query(ParentStudentLink).filter_by(studentId=student_id).first()
        if not link:
            return ParentStudentLink(studentId=student_id, relationship="ADMIN_OVERWRITE", status="VERIFIED")
        return link

    if parent_user.role.name != "PARENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User role must be PARENT."
        )

    parent_profile = db.query(ParentProfile).filter_by(userId=parent_user.id).first()
    if not parent_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Active parent profile not found."
        )

    link = db.query(ParentStudentLink).filter_by(parentId=parent_profile.id, studentId=student_id).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Parent is not linked to this student."
        )

    if link.status != "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Parent-student link is {link.status}."
        )

    return link

def check_teacher_student_link(db: Session, teacher_user: User, student_id: str) -> User:
    """Verifies that teacher has legitimate academic relationship with student."""
    student = db.query(User).filter_by(id=student_id, status="ACTIVE").first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    if teacher_user.role.name == "MASTER_ADMIN":
        return student

    if teacher_user.role.name != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User role must be TEACHER."
        )

    # Check if teacher has FacultyAssignment in student's section
    if not student.sectionId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Student is not assigned to any section."
        )

    is_assigned = db.query(FacultyAssignment).filter_by(
        facultyId=teacher_user.id,
        sectionId=student.sectionId
    ).first()

    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not assigned to teach this student's section."
        )

    return student


# --- SCHEMAS ---

class StudyPlanItemCreate(BaseModel):
    subjectId: Optional[str] = None
    title: str
    description: Optional[str] = None
    scheduledDate: datetime
    estimatedMinutes: Optional[int] = 30
    orderIndex: Optional[int] = 0

class StudyPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    startDate: datetime
    endDate: datetime
    generatedFromRecommendationId: Optional[str] = None
    items: List[StudyPlanItemCreate]

class StudyPlanPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None

class StudyPlanItemPatch(BaseModel):
    status: Optional[str] = None

class StudentGoalCreate(BaseModel):
    subjectId: Optional[str] = None
    title: str
    targetType: str
    targetValue: float
    deadline: Optional[datetime] = None

class StudentGoalPatch(BaseModel):
    title: Optional[str] = None
    targetValue: Optional[float] = None
    currentValue: Optional[float] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None

class InterventionCreate(BaseModel):
    type: str
    reason: str
    assignedToId: Optional[str] = None
    notes: Optional[str] = None
    dueAt: Optional[datetime] = None

class InterventionPatch(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    resolvedAt: Optional[datetime] = None

class RecommendationPatch(BaseModel):
    status: str


# --- STUDENT ENDPOINTS ---

@router.get("/me/overview")
def get_my_overview(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Returns overview statistics and current risk assessment for authenticated student."""
    check_student_self(current_user)

    # Recalculate implicitly to keep dashboard fresh
    AcademicMentorService.recalculate_student_intelligence(db, current_user.id, current_user.id)

    profile = db.query(AcademicMentorProfile).filter_by(studentId=current_user.id).first()
    latest_assessment = db.query(AcademicRiskAssessment).filter_by(studentId=current_user.id).order_by(desc(AcademicRiskAssessment.assessedAt)).first()

    # Build statistics
    att_summaries = db.query(StudentAttendanceSummary).filter_by(userId=current_user.id).all()
    overall_att = sum(s.percentage for s in att_summaries) / len(att_summaries) if att_summaries else 100.0

    assignments = db.query(StudentAssignment).filter_by(userId=current_user.id).all()
    pending_ass = sum(1 for a in assignments if a.submissionStatus == "PENDING")

    results = db.query(Result).filter_by(studentId=current_user.id).order_by(desc(Result.semesterNumber)).first()
    latest_gpa = results.sgpa if results else 0.0

    return make_response(
        success=True,
        message="My Academic Mentor Overview.",
        data={
            "profile": {
                "id": profile.id if profile else None,
                "currentRiskLevel": profile.currentRiskLevel if profile else "INSUFFICIENT_DATA",
                "currentRiskScore": profile.currentRiskScore if profile else 0.0,
                "dataCompleteness": profile.dataCompleteness if profile else 0.0,
                "lastCalculatedAt": profile.lastCalculatedAt if profile else None
            },
            "stats": {
                "overallAttendance": round(overall_att, 2),
                "pendingAssignments": pending_ass,
                "latestSGPA": latest_gpa
            },
            "assessment": latest_assessment
        }
    )

@router.get("/me/insights")
def get_my_insights(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieves generated explainable insights for authenticated student."""
    check_student_self(current_user)
    insights = db.query(AcademicInsight).filter_by(studentId=current_user.id).all()
    return make_response(
        success=True,
        message="My Academic Insights.",
        data=insights
    )

@router.get("/me/risk-assessment")
def get_my_risk_assessment(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieves full versioned explanation with risk factors for student."""
    check_student_self(current_user)
    assessment = db.query(AcademicRiskAssessment).filter_by(studentId=current_user.id).order_by(desc(AcademicRiskAssessment.version)).first()
    if not assessment:
        AcademicMentorService.recalculate_student_intelligence(db, current_user.id, current_user.id)
        assessment = db.query(AcademicRiskAssessment).filter_by(studentId=current_user.id).order_by(desc(AcademicRiskAssessment.version)).first()

    factors = []
    if assessment:
        factors = db.query(AcademicRiskFactor).filter_by(assessmentId=assessment.id).all()

    return make_response(
        success=True,
        message="My latest Academic Risk Assessment.",
        data={
            "assessment": {
                "id": assessment.id if assessment else None,
                "studentId": assessment.studentId if assessment else None,
                "score": assessment.score if assessment else 0.0,
                "level": assessment.level if assessment else "INSUFFICIENT_DATA",
                "dataCompleteness": assessment.dataCompleteness if assessment else 0.0,
                "engineType": assessment.engineType if assessment else "LOCAL_EXPLAINABLE_ANALYTICS",
                "explanation": assessment.explanation if assessment else "No assessment record found.",
                "assessedAt": assessment.assessedAt.isoformat() if (assessment and assessment.assessedAt) else None
            } if assessment else None,
            "factors": [
                {
                    "id": f.id,
                    "assessmentId": f.assessmentId,
                    "factorCode": f.factorCode,
                    "factorName": f.factorName,
                    "observedValue": f.observedValue,
                    "normalizedValue": f.normalizedValue,
                    "weight": f.weight,
                    "contribution": f.contribution,
                    "direction": f.direction,
                    "explanation": f.explanation,
                    "sourceType": f.sourceType
                } for f in factors
            ],
            "engineType": "LOCAL_EXPLAINABLE_ANALYTICS",
            "disclaimer": "Academic insights are advisory and generated from available academic records. They do not make automated grading, disciplinary, admission, or other high-stakes decisions."
        }
    )

@router.get("/me/recommendations")
def get_my_recommendations(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieves study recommendations for authenticated student."""
    check_student_self(current_user)
    profile = db.query(AcademicMentorProfile).filter_by(studentId=current_user.id).first()
    if not profile:
        AcademicMentorService.recalculate_student_intelligence(db, current_user.id, current_user.id)
    recs = db.query(StudyRecommendation).filter_by(studentId=current_user.id).all()

    recs_serialized = [
        {
            "id": r.id,
            "studentId": r.studentId,
            "subjectId": r.subjectId,
            "category": r.category,
            "title": r.title,
            "description": r.description,
            "priority": r.priority,
            "reason": r.reason,
            "status": r.status,
            "generatedBy": r.generatedBy,
            "createdAt": r.createdAt.isoformat() if r.createdAt else None
        } for r in recs
    ]

    return make_response(
        success=True,
        message="My Study Recommendations.",
        data=recs_serialized
    )

@router.patch("/me/recommendations/{id}")
def update_my_recommendation(
    id: str,
    payload: RecommendationPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Updates recommendation status (e.g., ACCEPTED, DISMISSED, COMPLETED). Enforces IDOR check."""
    check_student_self(current_user)
    rec = db.query(StudyRecommendation).filter_by(id=id, studentId=current_user.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    allowed_transitions = ["ACCEPTED", "DISMISSED", "COMPLETED", "ACTIVE"]
    if payload.status not in allowed_transitions:
        raise HTTPException(status_code=400, detail=f"Invalid transition status: {payload.status}")

    rec.status = payload.status
    if payload.status == "ACCEPTED":
        rec.acceptedAt = datetime.utcnow()
    elif payload.status == "DISMISSED":
        rec.dismissedAt = datetime.utcnow()
    elif payload.status == "COMPLETED":
        rec.completedAt = datetime.utcnow()

    db.commit()
    db.refresh(rec)

    # Audit action
    AcademicMentorService.record_mentor_audit(
        db=db,
        action="UPDATE_RECOMMENDATION",
        entity_type="StudyRecommendation",
        entity_id=rec.id,
        actor_id=current_user.id,
        student_id=current_user.id,
        metadata={"status": payload.status}
    )

    return make_response(
        success=True,
        message="Recommendation updated successfully.",
        data={
            "id": rec.id,
            "studentId": rec.studentId,
            "subjectId": rec.subjectId,
            "category": rec.category,
            "title": rec.title,
            "description": rec.description,
            "priority": rec.priority,
            "reason": rec.reason,
            "status": rec.status,
            "generatedBy": rec.generatedBy,
            "createdAt": rec.createdAt.isoformat() if rec.createdAt else None,
            "acceptedAt": rec.acceptedAt.isoformat() if rec.acceptedAt else None,
            "dismissedAt": rec.dismissedAt.isoformat() if rec.dismissedAt else None,
            "completedAt": rec.completedAt.isoformat() if rec.completedAt else None
        }
    )

@router.get("/me/study-plans")
def list_my_study_plans(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Lists study plans for authenticated student."""
    check_student_self(current_user)
    plans = db.query(StudyPlan).filter_by(studentId=current_user.id).all()
    return make_response(
        success=True,
        message="My Study Plans.",
        data=plans
    )

@router.post("/me/study-plans")
def create_my_study_plan(
    payload: StudyPlanCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Creates a new study plan with concrete tasks for student."""
    check_student_self(current_user)

    plan = StudyPlan(
        studentId=current_user.id,
        title=payload.title,
        description=payload.description,
        startDate=payload.startDate,
        endDate=payload.endDate,
        status="ACTIVE",
        generatedFromRecommendationId=payload.generatedFromRecommendationId,
        createdAt=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    for i, item_data in enumerate(payload.items):
        item = StudyPlanItem(
            studyPlanId=plan.id,
            subjectId=item_data.subjectId,
            title=item_data.title,
            description=item_data.description,
            scheduledDate=item_data.scheduledDate,
            estimatedMinutes=item_data.estimatedMinutes or 30,
            status="PENDING",
            orderIndex=item_data.orderIndex or i
        )
        db.add(item)

    db.commit()
    db.refresh(plan)

    # Audit action
    AcademicMentorService.record_mentor_audit(
        db=db,
        action="CREATE_STUDY_PLAN",
        entity_type="StudyPlan",
        entity_id=plan.id,
        actor_id=current_user.id,
        student_id=current_user.id
    )

    return make_response(
        success=True,
        message="Study plan created successfully.",
        data={
            "id": plan.id,
            "studentId": plan.studentId,
            "title": plan.title,
            "description": plan.description,
            "startDate": plan.startDate.isoformat() if plan.startDate else None,
            "endDate": plan.endDate.isoformat() if plan.endDate else None,
            "status": plan.status,
            "generatedFromRecommendationId": plan.generatedFromRecommendationId,
            "createdAt": plan.createdAt.isoformat() if plan.createdAt else None
        }
    )

@router.get("/me/study-plans/{id}")
def get_my_study_plan_details(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieves details of a specific study plan and its items. Enforces IDOR protection."""
    check_student_self(current_user)
    plan = db.query(StudyPlan).filter_by(id=id, studentId=current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found.")

    items = db.query(StudyPlanItem).filter_by(studyPlanId=plan.id).order_by(StudyPlanItem.orderIndex.asc()).all()

    items_serialized = [
        {
            "id": item.id,
            "studyPlanId": item.studyPlanId,
            "subjectId": item.subjectId,
            "title": item.title,
            "description": item.description,
            "scheduledDate": item.scheduledDate.isoformat() if item.scheduledDate else None,
            "estimatedMinutes": item.estimatedMinutes,
            "status": item.status,
            "completedAt": item.completedAt.isoformat() if item.completedAt else None,
            "orderIndex": item.orderIndex
        } for item in items
    ]

    return make_response(
        success=True,
        message="Study plan details.",
        data={
            "plan": {
                "id": plan.id,
                "studentId": plan.studentId,
                "title": plan.title,
                "description": plan.description,
                "startDate": plan.startDate.isoformat() if plan.startDate else None,
                "endDate": plan.endDate.isoformat() if plan.endDate else None,
                "status": plan.status,
                "generatedFromRecommendationId": plan.generatedFromRecommendationId,
                "createdAt": plan.createdAt.isoformat() if plan.createdAt else None
            },
            "items": items_serialized
        }
    )

@router.patch("/me/study-plans/{id}")
def patch_my_study_plan(
    id: str,
    payload: StudyPlanPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Updates general metadata of a study plan."""
    check_student_self(current_user)
    plan = db.query(StudyPlan).filter_by(id=id, studentId=current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found.")

    if payload.title is not None:
        plan.title = payload.title
    if payload.description is not None:
        plan.description = payload.description
    if payload.startDate is not None:
        plan.startDate = payload.startDate
    if payload.endDate is not None:
        plan.endDate = payload.endDate
    if payload.status is not None:
        plan.status = payload.status

    db.commit()
    db.refresh(plan)

    return make_response(
        success=True,
        message="Study plan updated successfully.",
        data={
            "id": plan.id,
            "studentId": plan.studentId,
            "title": plan.title,
            "description": plan.description,
            "startDate": plan.startDate.isoformat() if plan.startDate else None,
            "endDate": plan.endDate.isoformat() if plan.endDate else None,
            "status": plan.status
        }
    )

@router.patch("/me/study-plans/items/{item_id}")
def patch_my_study_plan_item(
    item_id: str,
    payload: StudyPlanItemPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Updates completion status of a study task."""
    check_student_self(current_user)
    item = db.query(StudyPlanItem).join(StudyPlan).filter(
        StudyPlanItem.id == item_id,
        StudyPlan.studentId == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Study plan item not found.")

    if payload.status is not None:
        item.status = payload.status
        if payload.status == "COMPLETED":
            item.completedAt = datetime.utcnow()
        else:
            item.completedAt = None

    db.commit()
    db.refresh(item)

    return make_response(
        success=True,
        message="Study plan task updated.",
        data={
            "id": item.id,
            "studyPlanId": item.studyPlanId,
            "subjectId": item.subjectId,
            "title": item.title,
            "description": item.description,
            "scheduledDate": item.scheduledDate.isoformat() if item.scheduledDate else None,
            "estimatedMinutes": item.estimatedMinutes,
            "status": item.status,
            "completedAt": item.completedAt.isoformat() if item.completedAt else None,
            "orderIndex": item.orderIndex
        }
    )

@router.post("/me/recalculate")
def student_request_recalculation(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student triggers a recalculation of their academic risk. Enforces a 30s cooldown constraint."""
    check_student_self(current_user)
    profile = db.query(AcademicMentorProfile).filter_by(studentId=current_user.id).first()

    # Recalculation Cooldown Enforced (30 seconds)
    if profile and profile.lastCalculatedAt:
        elapsed = datetime.utcnow() - profile.lastCalculatedAt
        if elapsed < timedelta(seconds=30):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recalculation cooling down. Please wait {int(30 - elapsed.total_seconds())}s."
            )

    result = AcademicMentorService.recalculate_student_intelligence(db, current_user.id, current_user.id)
    return make_response(
        success=True,
        message="Academic mentor recalculation finished.",
        data=result
    )

# --- GOAL ENDPOINTS ---

@router.get("/me/goals")
def list_my_goals(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Lists academic goals defined by student."""
    check_student_self(current_user)
    goals = db.query(StudentGoal).filter_by(studentId=current_user.id).all()
    return make_response(
        success=True,
        message="My Academic Goals.",
        data=goals
    )

@router.post("/me/goals")
def create_my_goal(
    payload: StudentGoalCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Allows student to configure a new academic goal."""
    check_student_self(current_user)

    goal = StudentGoal(
        studentId=current_user.id,
        subjectId=payload.subjectId,
        title=payload.title,
        targetType=payload.targetType,
        targetValue=payload.targetValue,
        status="ACTIVE",
        deadline=payload.deadline,
        createdAt=datetime.utcnow()
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return make_response(
        success=True,
        message="Goal set successfully.",
        data=goal
    )

@router.patch("/me/goals/{id}")
def update_my_goal(
    id: str,
    payload: StudentGoalPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Modifies a goal description, target, or completion status."""
    check_student_self(current_user)
    goal = db.query(StudentGoal).filter_by(id=id, studentId=current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    if payload.title is not None:
        goal.title = payload.title
    if payload.targetValue is not None:
        goal.targetValue = payload.targetValue
    if payload.currentValue is not None:
        goal.currentValue = payload.currentValue
    if payload.deadline is not None:
        goal.deadline = payload.deadline
    if payload.status is not None:
        goal.status = payload.status

    db.commit()
    db.refresh(goal)

    return make_response(
        success=True,
        message="Goal updated.",
        data=goal
    )

@router.delete("/me/goals/{id}")
def delete_my_goal(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Deletes an academic goal."""
    check_student_self(current_user)
    goal = db.query(StudentGoal).filter_by(id=id, studentId=current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    db.delete(goal)
    db.commit()

    return make_response(
        success=True,
        message="Goal deleted."
    )


# --- PARENT ENDPOINTS ---

@router.get("/children")
def list_my_linked_children(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Returns only children linked through existing verified parent-student relation."""
    if current_user.role.name == "MASTER_ADMIN":
        links = db.query(ParentStudentLink).all()
    else:
        parent_profile = db.query(ParentProfile).filter_by(userId=current_user.id).first()
        if not parent_profile:
            return make_response(success=True, message="No linked children.", data=[])
        links = db.query(ParentStudentLink).filter_by(parentId=parent_profile.id, status="VERIFIED").all()

    children = []
    for l in links:
        student = db.query(User).filter_by(id=l.studentId, status="ACTIVE").first()
        if student:
            children.append({
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "relationship": l.relationship,
                "canViewAcademics": l.canViewAcademics
            })

    return make_response(
        success=True,
        message="My Linked Children.",
        data=children
    )

@router.get("/children/{student_id}/overview")
def get_child_overview(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Allows parents to read child's academic health indicators."""
    check_parent_child_link(db, current_user, student_id)

    # Recalculate to keep parent overview current
    AcademicMentorService.recalculate_student_intelligence(db, student_id, current_user.id)

    profile = db.query(AcademicMentorProfile).filter_by(studentId=student_id).first()
    latest_assessment = db.query(AcademicRiskAssessment).filter_by(studentId=student_id).order_by(desc(AcademicRiskAssessment.assessedAt)).first()

    att_summaries = db.query(StudentAttendanceSummary).filter_by(userId=student_id).all()
    overall_att = sum(s.percentage for s in att_summaries) / len(att_summaries) if att_summaries else 100.0

    assignments = db.query(StudentAssignment).filter_by(userId=student_id).all()
    pending_ass = sum(1 for a in assignments if a.submissionStatus == "PENDING")

    results = db.query(Result).filter_by(studentId=student_id).order_by(desc(Result.semesterNumber)).first()
    latest_gpa = results.sgpa if results else 0.0

    return make_response(
        success=True,
        message="Child Academic Overview.",
        data={
            "profile": {
                "id": profile.id if profile else None,
                "currentRiskLevel": profile.currentRiskLevel if profile else "INSUFFICIENT_DATA",
                "currentRiskScore": profile.currentRiskScore if profile else 0.0,
                "dataCompleteness": profile.dataCompleteness if profile else 0.0
            },
            "stats": {
                "overallAttendance": round(overall_att, 2),
                "pendingAssignments": pending_ass,
                "latestSGPA": latest_gpa
            },
            "assessment": latest_assessment
        }
    )

@router.get("/children/{student_id}/insights")
def get_child_insights(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Allows parents to see generated strengths and weaknesses."""
    check_parent_child_link(db, current_user, student_id)
    insights = db.query(AcademicInsight).filter_by(studentId=student_id).all()
    return make_response(
        success=True,
        message="Child Academic Insights.",
        data=insights
    )

@router.get("/children/{student_id}/recommendations")
def get_child_recommendations(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Allows parents to see child's active suggestions."""
    check_parent_child_link(db, current_user, student_id)
    profile = db.query(AcademicMentorProfile).filter_by(studentId=student_id).first()
    if not profile:
        AcademicMentorService.recalculate_student_intelligence(db, student_id, current_user.id)
    recs = db.query(StudyRecommendation).filter_by(studentId=student_id).all()

    recs_serialized = [
        {
            "id": r.id,
            "studentId": r.studentId,
            "subjectId": r.subjectId,
            "category": r.category,
            "title": r.title,
            "description": r.description,
            "priority": r.priority,
            "reason": r.reason,
            "status": r.status,
            "generatedBy": r.generatedBy,
            "createdAt": r.createdAt.isoformat() if r.createdAt else None
        } for r in recs
    ]

    return make_response(
        success=True,
        message="Child Study Recommendations.",
        data=recs_serialized
    )


# --- TEACHER / MENTOR ENDPOINTS ---

@router.get("/students")
def list_my_scoped_students(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Returns only students within teacher's academic scope."""
    if current_user.role.name == "MASTER_ADMIN":
        students = db.query(User).filter_by(roleId=db.query(User).filter_by(roleId="STUDENT").first().roleId if db.query(User).filter_by(roleId="STUDENT").first() else "STUDENT").all()
        # Fallback to direct role.name checks
        students = db.query(User).join(User.role).filter(User.role.name == "STUDENT", User.status == "ACTIVE").all()
    else:
        if current_user.role.name != "TEACHER":
            raise HTTPException(status_code=403, detail="Teacher or Admin role required.")

        # Get section assignments for this teacher
        assignments = db.query(FacultyAssignment).filter_by(facultyId=current_user.id).all()
        section_ids = {a.sectionId for a in assignments}

        students = db.query(User).filter(
            User.sectionId.in_(section_ids),
            User.status == "ACTIVE"
        ).all()

    student_list = []
    for s in students:
        profile = db.query(AcademicMentorProfile).filter_by(studentId=s.id).first()
        student_list.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "sectionId": s.sectionId,
            "riskLevel": profile.currentRiskLevel if profile else "INSUFFICIENT_DATA",
            "riskScore": profile.currentRiskScore if profile else 0.0,
            "dataCompleteness": profile.dataCompleteness if profile else 0.0
        })

    return make_response(
        success=True,
        message="Teacher Scoped Student Directory.",
        data=student_list
    )

@router.get("/students/{student_id}/overview")
def get_scoped_student_overview(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Teacher fetches scoped student profile detail."""
    student = check_teacher_student_link(db, current_user, student_id)

    AcademicMentorService.recalculate_student_intelligence(db, student_id, current_user.id)
    profile = db.query(AcademicMentorProfile).filter_by(studentId=student_id).first()

    att_summaries = db.query(StudentAttendanceSummary).filter_by(userId=student_id).all()
    overall_att = sum(s.percentage for s in att_summaries) / len(att_summaries) if att_summaries else 100.0

    assignments = db.query(StudentAssignment).filter_by(userId=student_id).all()
    pending_ass = sum(1 for a in assignments if a.submissionStatus == "PENDING")

    results = db.query(Result).filter_by(studentId=student_id).order_by(desc(Result.semesterNumber)).first()
    latest_gpa = results.sgpa if results else 0.0

    return make_response(
        success=True,
        message="Student Academic Overview.",
        data={
            "student": {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "sectionId": student.sectionId
            },
            "profile": {
                "id": profile.id if profile else None,
                "currentRiskLevel": profile.currentRiskLevel if profile else "INSUFFICIENT_DATA",
                "currentRiskScore": profile.currentRiskScore if profile else 0.0,
                "dataCompleteness": profile.dataCompleteness if profile else 0.0,
                "lastCalculatedAt": profile.lastCalculatedAt if profile else None
            },
            "stats": {
                "overallAttendance": round(overall_att, 2),
                "pendingAssignments": pending_ass,
                "latestSGPA": latest_gpa
            }
        }
    )

@router.get("/students/{student_id}/risk-assessment")
def get_scoped_student_risk(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Teacher reads scoped student risk score factors."""
    check_teacher_student_link(db, current_user, student_id)

    assessment = db.query(AcademicRiskAssessment).filter_by(studentId=student_id).order_by(desc(AcademicRiskAssessment.version)).first()
    if not assessment:
        AcademicMentorService.recalculate_student_intelligence(db, student_id, current_user.id)
        assessment = db.query(AcademicRiskAssessment).filter_by(studentId=student_id).order_by(desc(AcademicRiskAssessment.version)).first()

    factors = []
    if assessment:
        factors = db.query(AcademicRiskFactor).filter_by(assessmentId=assessment.id).all()

    return make_response(
        success=True,
        message="Student Risk Assessment.",
        data={
            "assessment": {
                "id": assessment.id if assessment else None,
                "studentId": assessment.studentId if assessment else None,
                "score": assessment.score if assessment else 0.0,
                "level": assessment.level if assessment else "INSUFFICIENT_DATA",
                "dataCompleteness": assessment.dataCompleteness if assessment else 0.0,
                "engineType": assessment.engineType if assessment else "LOCAL_EXPLAINABLE_ANALYTICS",
                "explanation": assessment.explanation if assessment else "No assessment record found.",
                "assessedAt": assessment.assessedAt.isoformat() if (assessment and assessment.assessedAt) else None
            } if assessment else None,
            "factors": [
                {
                    "id": f.id,
                    "assessmentId": f.assessmentId,
                    "factorCode": f.factorCode,
                    "factorName": f.factorName,
                    "observedValue": f.observedValue,
                    "normalizedValue": f.normalizedValue,
                    "weight": f.weight,
                    "contribution": f.contribution,
                    "direction": f.direction,
                    "explanation": f.explanation,
                    "sourceType": f.sourceType
                } for f in factors
            ]
        }
    )

@router.get("/students/{student_id}/recommendations")
def get_scoped_student_recommendations(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Teacher lists student suggestions."""
    check_teacher_student_link(db, current_user, student_id)
    profile = db.query(AcademicMentorProfile).filter_by(studentId=student_id).first()
    if not profile:
        AcademicMentorService.recalculate_student_intelligence(db, student_id, current_user.id)
    recs = db.query(StudyRecommendation).filter_by(studentId=student_id).all()

    recs_serialized = [
        {
            "id": r.id,
            "studentId": r.studentId,
            "subjectId": r.subjectId,
            "category": r.category,
            "title": r.title,
            "description": r.description,
            "priority": r.priority,
            "reason": r.reason,
            "status": r.status,
            "generatedBy": r.generatedBy,
            "createdAt": r.createdAt.isoformat() if r.createdAt else None
        } for r in recs
    ]

    return make_response(
        success=True,
        message="Student Study Recommendations.",
        data=recs_serialized
    )

@router.post("/students/{student_id}/interventions")
def create_student_intervention(
    student_id: str,
    payload: InterventionCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Enables teacher to initiate a mentor intervention card."""
    check_teacher_student_link(db, current_user, student_id)

    intervention = MentorIntervention(
        studentId=student_id,
        initiatedById=current_user.id,
        assignedToId=payload.assignedToId,
        type=payload.type,
        reason=payload.reason,
        status="OPEN",
        notes=payload.notes,
        dueAt=payload.dueAt,
        createdAt=datetime.utcnow()
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)

    # Send Notification to Student (Advisory Language)
    NotificationService.create_notification(
        db=db,
        recipient_id=student_id,
        title="New Mentor Academic Support Program",
        body=f"A new tutoring or academic support intervention ({payload.type}) has been scheduled for you. Advisory review suggested.",
        type="INFO",
        priority="MEDIUM",
        channel="IN_APP",
        category="ACADEMIC"
    )

    # Audit action
    AcademicMentorService.record_mentor_audit(
        db=db,
        action="CREATE_INTERVENTION",
        entity_type="MentorIntervention",
        entity_id=intervention.id,
        actor_id=current_user.id,
        student_id=student_id
    )

    return make_response(
        success=True,
        message="Academic intervention workflow successfully registered.",
        data={
            "id": intervention.id,
            "studentId": intervention.studentId,
            "initiatedById": intervention.initiatedById,
            "assignedToId": intervention.assignedToId,
            "type": intervention.type,
            "reason": intervention.reason,
            "status": intervention.status,
            "notes": intervention.notes,
            "dueAt": intervention.dueAt.isoformat() if intervention.dueAt else None,
            "createdAt": intervention.createdAt.isoformat() if intervention.createdAt else None
        }
    )

@router.patch("/interventions/{id}")
def update_intervention(
    id: str,
    payload: InterventionPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Enables teacher or assignee to update intervention notes/status."""
    intervention = db.query(MentorIntervention).filter_by(id=id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found.")

    # Enforce role bounds (Must be admin, teacher initiator, or assignee teacher)
    if current_user.role.name != "MASTER_ADMIN" and intervention.initiatedById != current_user.id and intervention.assignedToId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to manage this intervention."
        )

    if payload.status is not None:
        intervention.status = payload.status
        if payload.status in ["RESOLVED", "CANCELLED"]:
            intervention.resolvedAt = datetime.utcnow()
    if payload.notes is not None:
        intervention.notes = payload.notes

    db.commit()
    db.refresh(intervention)

    # Audit action
    AcademicMentorService.record_mentor_audit(
        db=db,
        action="UPDATE_INTERVENTION",
        entity_type="MentorIntervention",
        entity_id=intervention.id,
        actor_id=current_user.id,
        student_id=intervention.studentId,
        metadata={"status": payload.status}
    )

    return make_response(
        success=True,
        message="Intervention updated successfully.",
        data={
            "id": intervention.id,
            "studentId": intervention.studentId,
            "initiatedById": intervention.initiatedById,
            "assignedToId": intervention.assignedToId,
            "type": intervention.type,
            "reason": intervention.reason,
            "status": intervention.status,
            "notes": intervention.notes,
            "dueAt": intervention.dueAt.isoformat() if intervention.dueAt else None,
            "resolvedAt": intervention.resolvedAt.isoformat() if intervention.resolvedAt else None,
            "createdAt": intervention.createdAt.isoformat() if intervention.createdAt else None,
            "updatedAt": intervention.updatedAt.isoformat() if intervention.updatedAt else None
        }
    )


# --- ADMIN ANALYTICS ---

@router.get("/analytics")
def get_aggregate_analytics(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Master admin aggregate statistics on school risk level distributions."""
    # RBAC limit
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    profiles = db.query(AcademicMentorProfile).all()

    levels = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0, "INSUFFICIENT_DATA": 0}
    total = len(profiles)

    score_sum = 0.0
    valid_count = 0

    for p in profiles:
        levels[p.currentRiskLevel] = levels.get(p.currentRiskLevel, 0) + 1
        if p.currentRiskLevel != "INSUFFICIENT_DATA":
            score_sum += p.currentRiskScore
            valid_count += 1

    avg_score = (score_sum / valid_count) if valid_count > 0 else 0.0

    return make_response(
        success=True,
        message="Academic Mentor Admin Aggregate Analytics.",
        data={
            "totalEvaluated": total,
            "averageRiskScore": round(avg_score, 2),
            "distribution": levels,
            "engineType": "LOCAL_EXPLAINABLE_ANALYTICS"
        }
    )

@router.post("/recalculate")
def admin_bulk_recalculate(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Triggers bulk academic intelligence recalculation for all active students."""
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    # Fetch all students
    students = db.query(User).join(Role).filter(Role.name == "STUDENT", User.status == "ACTIVE").all()

    processed = 0
    failed = 0

    for s in students:
        try:
            AcademicMentorService.recalculate_student_intelligence(db, s.id, current_user.id)
            processed += 1
        except Exception:
            failed += 1

    # Audit action
    AcademicMentorService.record_mentor_audit(
        db=db,
        action="BULK_RECALCULATE",
        entity_type="System",
        actor_id=current_user.id,
        metadata={"processed": processed, "failed": failed}
    )

    return make_response(
        success=True,
        message="Bulk risk calculation processed.",
        data={
            "processed": processed,
            "failed": failed
        }
    )

@router.get("/audits")
def get_mentor_audits(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Lists recent privileged recalculation and intervention audits."""
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    # Pagination maximum enforced (limit cap)
    offset = (page - 1) * limit
    audits = db.query(AcademicMentorAudit).order_by(desc(AcademicMentorAudit.createdAt)).offset(offset).limit(limit).all()
    total = db.query(AcademicMentorAudit).count()

    return make_response(
        success=True,
        message="Audit logs.",
        data={
            "total": total,
            "page": page,
            "limit": limit,
            "audits": audits
        }
    )
