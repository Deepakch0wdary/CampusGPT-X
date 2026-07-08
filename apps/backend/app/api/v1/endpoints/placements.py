"""
Enterprise Placement & Career Intelligence System — Day 22
API Endpoints: /api/v1/placements

RBAC:
- MASTER_ADMIN: full access + analytics + audit
- PLACEMENT_OFFICER: company, opportunity, drive, application pipeline, interviews, offers
- STUDENT: own profile, skills, resumes, eligibility, matches, applications, interviews, offers
- TEACHER: read-only scoped student career readiness
- PARENT: read-only linked child placement summary (no private recruiter feedback)

No protected attributes used in scoring.
Intelligence engines are local, deterministic, and explainable.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import (
    User, CareerProfile, SkillCatalog, StudentSkill,
    ResumeProfile, ResumeVersion, Company, RecruiterContact,
    Opportunity, OpportunitySkill, EligibilityRule, EligibilityEvaluation,
    PlacementDrive, DriveRegistration, JobApplication, ApplicationStatusHistory,
    InterviewRound, InterviewFeedback, Offer, PlacementOutcome,
    CareerGoal, SkillGapAnalysis, CareerRecommendation, JobMatchScore,
    PlacementAudit, ParentStudentLink, ParentProfile, FacultyAssignment, Role
)
from app.services.career_matching_service import (
    EligibilityService, CareerMatchingService,
    SkillGapService, PlacementRecommendationService, PlacementAuditService
)
from app.services.notification_service import NotificationService
from app.core.responses import make_response

router = APIRouter()


# ================================================================
# SECURITY UTILITIES
# ================================================================

def require_roles(current_user: User, *allowed_roles: str):
    if current_user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {list(allowed_roles)}"
        )

def require_placement_officer_or_admin(current_user: User):
    require_roles(current_user, "PLACEMENT_OFFICER", "MASTER_ADMIN")

def require_student_self(current_user: User):
    if current_user.role.name not in ("STUDENT", "MASTER_ADMIN"):
        raise HTTPException(status_code=403, detail="Student self-service only.")

def check_parent_child_link_placement(db: Session, parent_user: User, student_id: str):
    if parent_user.role.name == "MASTER_ADMIN":
        return
    if parent_user.role.name != "PARENT":
        raise HTTPException(status_code=403, detail="Parent role required.")
    parent_profile = db.query(ParentProfile).filter_by(userId=parent_user.id).first()
    if not parent_profile:
        raise HTTPException(status_code=403, detail="No parent profile found.")
    link = db.query(ParentStudentLink).filter_by(parentId=parent_profile.id, studentId=student_id).first()
    if not link or link.status != "VERIFIED":
        raise HTTPException(status_code=403, detail="Not linked to this student.")

def check_teacher_student_link_placement(db: Session, teacher_user: User, student_id: str):
    if teacher_user.role.name == "MASTER_ADMIN":
        return
    if teacher_user.role.name != "TEACHER":
        raise HTTPException(status_code=403, detail="Teacher role required.")
    assignments = db.query(FacultyAssignment).filter_by(facultyId=teacher_user.id).all()
    section_ids = {a.sectionId for a in assignments}
    student = db.query(User).filter_by(id=student_id, status="ACTIVE").first()
    if not student or student.sectionId not in section_ids:
        raise HTTPException(status_code=403, detail="Student not in your academic scope.")

def get_student_or_404(db: Session, student_id: str) -> User:
    student = db.query(User).filter_by(id=student_id, status="ACTIVE").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


# ================================================================
# PYDANTIC SCHEMAS
# ================================================================

class CareerProfileCreate(BaseModel):
    graduationYear: int
    biography: Optional[str] = None
    certifications: Optional[str] = None
    projects: Optional[str] = None
    experience: Optional[str] = None
    linkedinUrl: Optional[str] = None
    githubUrl: Optional[str] = None
    portfolioUrl: Optional[str] = None

class CareerProfilePatch(BaseModel):
    graduationYear: Optional[int] = None
    biography: Optional[str] = None
    certifications: Optional[str] = None
    projects: Optional[str] = None
    experience: Optional[str] = None
    linkedinUrl: Optional[str] = None
    githubUrl: Optional[str] = None
    portfolioUrl: Optional[str] = None
    status: Optional[str] = None

class StudentSkillCreate(BaseModel):
    skillName: str
    proficiency: str = "BEGINNER"
    yearsOfExperience: float = 0.0

class StudentSkillPatch(BaseModel):
    proficiency: Optional[str] = None
    yearsOfExperience: Optional[float] = None

class ResumeProfileCreate(BaseModel):
    title: str

class ResumeVersionCreate(BaseModel):
    fileUrl: str
    summary: Optional[str] = None

class CompanyCreate(BaseModel):
    name: str
    industry: str
    website: Optional[str] = None
    description: Optional[str] = None
    hrEmail: Optional[str] = None

class CompanyPatch(BaseModel):
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    hrEmail: Optional[str] = None
    status: Optional[str] = None

class RecruiterCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    designation: Optional[str] = None

class OpportunityCreate(BaseModel):
    companyId: str
    title: str
    description: str
    type: str  # JOB or INTERNSHIP
    roleType: str = "FULL_TIME"
    location: str
    compensation: str
    minCgpa: float = 0.0
    maxBacklogs: int = 999
    graduationYear: Optional[int] = None
    deadline: Optional[datetime] = None
    driveId: Optional[str] = None

class OpportunityPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    compensation: Optional[str] = None
    minCgpa: Optional[float] = None
    maxBacklogs: Optional[int] = None
    status: Optional[str] = None
    deadline: Optional[datetime] = None

class OpportunitySkillAdd(BaseModel):
    skillName: str
    isRequired: bool = True

class EligibilityRuleCreate(BaseModel):
    ruleType: str
    ruleValue: str

class DriveCreate(BaseModel):
    companyId: str
    title: str
    description: Optional[str] = None
    startDate: datetime
    endDate: datetime
    venue: Optional[str] = None

class ApplicationCreate(BaseModel):
    opportunityId: str
    coverLetter: Optional[str] = None
    resumeVersionId: Optional[str] = None

class ApplicationStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class InterviewCreate(BaseModel):
    applicationId: str
    roundNumber: int = 1
    title: str
    type: str
    scheduledAt: Optional[datetime] = None
    location: Optional[str] = None
    interviewerNames: Optional[str] = None
    durationMinutes: int = 60

class InterviewPatch(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None
    scheduledAt: Optional[datetime] = None
    location: Optional[str] = None

class InterviewFeedbackCreate(BaseModel):
    rating: Optional[int] = None
    notes: Optional[str] = None

class OfferCreate(BaseModel):
    applicationId: str
    packageAmount: float
    offerLetterUrl: Optional[str] = None
    joiningDate: Optional[datetime] = None
    deadline: datetime
    notes: Optional[str] = None

class OfferStatusPatch(BaseModel):
    status: str

class CareerGoalCreate(BaseModel):
    title: str
    targetTimeline: Optional[str] = None
    targetRole: Optional[str] = None
    targetIndustry: Optional[str] = None

class CareerGoalPatch(BaseModel):
    title: Optional[str] = None
    targetTimeline: Optional[str] = None
    targetRole: Optional[str] = None
    targetIndustry: Optional[str] = None
    status: Optional[str] = None

class RecommendationStatusPatch(BaseModel):
    status: str  # ACCEPTED, DISMISSED, COMPLETED


# ================================================================
# HELPER: serialize opportunity
# ================================================================

def serialize_opportunity(opp: Opportunity) -> dict:
    return {
        "id": opp.id,
        "companyId": opp.companyId,
        "companyName": opp.company.name if opp.company else None,
        "companyIndustry": opp.company.industry if opp.company else None,
        "driveId": opp.driveId,
        "title": opp.title,
        "description": opp.description,
        "type": opp.type,
        "roleType": opp.roleType,
        "location": opp.location,
        "compensation": opp.compensation,
        "minCgpa": opp.minCgpa,
        "maxBacklogs": opp.maxBacklogs,
        "graduationYear": opp.graduationYear,
        "deadline": opp.deadline.isoformat() if opp.deadline else None,
        "status": opp.status,
        "createdAt": opp.createdAt.isoformat() if opp.createdAt else None
    }


# ================================================================
# CAREER PROFILE ENDPOINTS
# ================================================================

@router.get("/career-profile/me")
def get_my_career_profile(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student reads own career profile."""
    require_student_self(current_user)
    profile = db.query(CareerProfile).filter_by(studentId=current_user.id).first()
    if not profile:
        return make_response(success=True, message="No career profile yet.", data=None)
    return make_response(success=True, message="Career profile.", data={
        "id": profile.id, "studentId": profile.studentId,
        "graduationYear": profile.graduationYear, "status": profile.status,
        "biography": profile.biography, "certifications": profile.certifications,
        "projects": profile.projects, "experience": profile.experience,
        "linkedinUrl": profile.linkedinUrl, "githubUrl": profile.githubUrl,
        "portfolioUrl": profile.portfolioUrl,
        "createdAt": profile.createdAt.isoformat() if profile.createdAt else None,
        "updatedAt": profile.updatedAt.isoformat() if profile.updatedAt else None
    })


@router.post("/career-profile")
def create_career_profile(
    payload: CareerProfileCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student creates career profile (one per student)."""
    require_student_self(current_user)
    existing = db.query(CareerProfile).filter_by(studentId=current_user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Career profile already exists. Use PATCH to update.")
    profile = CareerProfile(
        studentId=current_user.id,
        graduationYear=payload.graduationYear,
        biography=payload.biography,
        certifications=payload.certifications,
        projects=payload.projects,
        experience=payload.experience,
        linkedinUrl=payload.linkedinUrl,
        githubUrl=payload.githubUrl,
        portfolioUrl=payload.portfolioUrl
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return make_response(success=True, message="Career profile created.", data={"id": profile.id})


@router.patch("/career-profile/me")
def update_career_profile(
    payload: CareerProfilePatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student updates own career profile."""
    require_student_self(current_user)
    profile = db.query(CareerProfile).filter_by(studentId=current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Career profile not found. Create one first.")
    for field, val in payload.dict(exclude_none=True).items():
        setattr(profile, field, val)
    db.commit()
    return make_response(success=True, message="Career profile updated.", data={"id": profile.id})


# ================================================================
# SKILLS ENDPOINTS
# ================================================================

@router.get("/skills/catalog")
def get_skill_catalog(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """All users can browse the skill catalog."""
    q = db.query(SkillCatalog)
    if search:
        q = q.filter(SkillCatalog.name.ilike(f"%{search}%"))
    if category:
        q = q.filter(SkillCatalog.category == category.upper())
    skills = q.order_by(SkillCatalog.name).limit(100).all()
    return make_response(success=True, message="Skill catalog.", data=[
        {"id": s.id, "name": s.name, "category": s.category, "description": s.description}
        for s in skills
    ])


@router.get("/skills/me")
def get_my_skills(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student views own skills."""
    require_student_self(current_user)
    skills = db.query(StudentSkill).filter_by(studentId=current_user.id).all()
    return make_response(success=True, message="My skills.", data=[
        {
            "id": ss.id, "skillId": ss.skillId,
            "skillName": ss.skill.name if ss.skill else None,
            "category": ss.skill.category if ss.skill else None,
            "proficiency": ss.proficiency,
            "yearsOfExperience": ss.yearsOfExperience
        } for ss in skills
    ])


@router.post("/skills/me")
def add_my_skill(
    payload: StudentSkillCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student adds a skill from the catalog. Auto-creates catalog entry if missing."""
    require_student_self(current_user)
    skill_cat = db.query(SkillCatalog).filter(
        SkillCatalog.name.ilike(payload.skillName)
    ).first()
    if not skill_cat:
        skill_cat = SkillCatalog(name=payload.skillName, category="TECHNICAL")
        db.add(skill_cat)
        db.flush()

    existing = db.query(StudentSkill).filter_by(
        studentId=current_user.id, skillId=skill_cat.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Skill already added.")

    ss = StudentSkill(
        studentId=current_user.id,
        skillId=skill_cat.id,
        proficiency=payload.proficiency,
        yearsOfExperience=payload.yearsOfExperience
    )
    db.add(ss)
    db.commit()
    db.refresh(ss)
    return make_response(success=True, message="Skill added.", data={"id": ss.id, "skillName": skill_cat.name})


@router.patch("/skills/me/{skill_id}")
def update_my_skill(
    skill_id: str,
    payload: StudentSkillPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student updates proficiency/experience for own skill."""
    require_student_self(current_user)
    ss = db.query(StudentSkill).filter_by(id=skill_id, studentId=current_user.id).first()
    if not ss:
        raise HTTPException(status_code=404, detail="Skill not found.")
    if payload.proficiency:
        ss.proficiency = payload.proficiency
    if payload.yearsOfExperience is not None:
        ss.yearsOfExperience = payload.yearsOfExperience
    db.commit()
    return make_response(success=True, message="Skill updated.", data={"id": ss.id})


@router.delete("/skills/me/{skill_id}")
def remove_my_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student removes own skill."""
    require_student_self(current_user)
    ss = db.query(StudentSkill).filter_by(id=skill_id, studentId=current_user.id).first()
    if not ss:
        raise HTTPException(status_code=404, detail="Skill not found.")
    db.delete(ss)
    db.commit()
    return make_response(success=True, message="Skill removed.")


# ================================================================
# RESUME ENDPOINTS
# ================================================================

@router.get("/resumes/me")
def get_my_resumes(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student views own resumes."""
    require_student_self(current_user)
    profiles = db.query(ResumeProfile).filter_by(studentId=current_user.id).all()
    result = []
    for rp in profiles:
        versions = [
            {
                "id": v.id, "versionNumber": v.versionNumber,
                "fileUrl": v.fileUrl, "status": v.status, "isActive": v.isActive,
                "summary": v.summary,
                "createdAt": v.createdAt.isoformat() if v.createdAt else None
            } for v in rp.versions
        ]
        result.append({"id": rp.id, "title": rp.title, "versions": versions})
    return make_response(success=True, message="My resumes.", data=result)


@router.post("/resumes")
def create_resume_profile(
    payload: ResumeProfileCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student creates a resume profile."""
    require_student_self(current_user)
    rp = ResumeProfile(studentId=current_user.id, title=payload.title)
    db.add(rp)
    db.commit()
    db.refresh(rp)
    return make_response(success=True, message="Resume profile created.", data={"id": rp.id})


@router.post("/resumes/{resume_id}/versions")
def add_resume_version(
    resume_id: str,
    payload: ResumeVersionCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student adds a version to a resume profile."""
    require_student_self(current_user)
    rp = db.query(ResumeProfile).filter_by(id=resume_id, studentId=current_user.id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Resume profile not found.")
    version_num = len(rp.versions) + 1
    v = ResumeVersion(
        resumeProfileId=resume_id,
        versionNumber=version_num,
        fileUrl=payload.fileUrl,
        summary=payload.summary,
        isActive=version_num == 1
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return make_response(success=True, message="Resume version added.", data={"id": v.id, "versionNumber": v.versionNumber})


@router.patch("/resumes/{resume_id}/primary-version")
def set_primary_resume_version(
    resume_id: str,
    version_id: str = Query(...),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student sets a specific resume version as active/primary."""
    require_student_self(current_user)
    rp = db.query(ResumeProfile).filter_by(id=resume_id, studentId=current_user.id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Resume profile not found.")
    for v in rp.versions:
        v.isActive = (v.id == version_id)
    db.commit()
    return make_response(success=True, message="Primary resume version updated.")


# ================================================================
# COMPANY ENDPOINTS
# ================================================================

@router.get("/companies")
def list_companies(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """All authenticated users can view company directory."""
    q = db.query(Company)
    if search:
        q = q.filter(Company.name.ilike(f"%{search}%"))
    companies = q.filter_by(status="ACTIVE").order_by(Company.name).all()
    return make_response(success=True, message="Company directory.", data=[
        {
            "id": c.id, "name": c.name, "industry": c.industry,
            "website": c.website, "logoUrl": c.logoUrl,
            "hrEmail": c.hrEmail if current_user.role.name in ("PLACEMENT_OFFICER", "MASTER_ADMIN") else None
        } for c in companies
    ])


@router.get("/companies/{company_id}")
def get_company(
    company_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """All authenticated users can view company details."""
    c = db.query(Company).filter_by(id=company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found.")
    is_privileged = current_user.role.name in ("PLACEMENT_OFFICER", "MASTER_ADMIN")
    return make_response(success=True, message="Company details.", data={
        "id": c.id, "name": c.name, "industry": c.industry,
        "website": c.website, "description": c.description,
        "logoUrl": c.logoUrl, "status": c.status,
        "hrEmail": c.hrEmail if is_privileged else None,
        "recruiterContacts": [
            {"id": r.id, "name": r.name, "email": r.email if is_privileged else "***", "designation": r.designation}
            for r in c.recruiterContacts
        ] if is_privileged else []
    })


@router.post("/companies")
def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Only Placement Officer or Admin can create companies."""
    require_placement_officer_or_admin(current_user)
    existing = db.query(Company).filter_by(name=payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Company name already exists.")
    c = Company(
        name=payload.name, industry=payload.industry,
        website=payload.website, description=payload.description,
        hrEmail=payload.hrEmail
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    PlacementAuditService.record(db, "CREATE_COMPANY", "Company", actor_id=current_user.id, entity_id=c.id)
    db.commit()
    return make_response(success=True, message="Company created.", data={"id": c.id})


@router.patch("/companies/{company_id}")
def update_company(
    company_id: str,
    payload: CompanyPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement Officer or Admin updates company."""
    require_placement_officer_or_admin(current_user)
    c = db.query(Company).filter_by(id=company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found.")
    for field, val in payload.dict(exclude_none=True).items():
        setattr(c, field, val)
    db.commit()
    return make_response(success=True, message="Company updated.", data={"id": c.id})


@router.post("/companies/{company_id}/recruiters")
def add_recruiter(
    company_id: str,
    payload: RecruiterCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Add recruiter contact to company."""
    require_placement_officer_or_admin(current_user)
    c = db.query(Company).filter_by(id=company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found.")
    existing = db.query(RecruiterContact).filter_by(email=payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Recruiter email already registered.")
    r = RecruiterContact(
        companyId=company_id, name=payload.name, email=payload.email,
        phone=payload.phone, designation=payload.designation
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return make_response(success=True, message="Recruiter added.", data={"id": r.id})


# ================================================================
# OPPORTUNITY ENDPOINTS
# ================================================================

@router.get("/opportunities")
def list_opportunities(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """All authenticated users can browse opportunities."""
    q = db.query(Opportunity)
    if type:
        q = q.filter(Opportunity.type == type.upper())
    if status:
        q = q.filter(Opportunity.status == status.upper())
    else:
        q = q.filter(Opportunity.status == "OPEN")
    if search:
        q = q.filter(Opportunity.title.ilike(f"%{search}%"))
    opps = q.order_by(desc(Opportunity.createdAt)).limit(50).all()
    return make_response(success=True, message="Opportunities.", data=[serialize_opportunity(o) for o in opps])


@router.get("/opportunities/{opp_id}")
def get_opportunity(
    opp_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Get opportunity detail with skills list."""
    opp = db.query(Opportunity).filter_by(id=opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    skills = [
        {"skillName": os.skill.name if os.skill else "?", "isRequired": os.isRequired}
        for os in opp.opportunitySkills
    ]
    data = serialize_opportunity(opp)
    data["skills"] = skills
    return make_response(success=True, message="Opportunity detail.", data=data)


@router.post("/opportunities")
def create_opportunity(
    payload: OpportunityCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement Officer / Admin creates an opportunity."""
    require_placement_officer_or_admin(current_user)
    company = db.query(Company).filter_by(id=payload.companyId).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")
    opp = Opportunity(
        companyId=payload.companyId,
        title=payload.title,
        description=payload.description,
        type=payload.type.upper(),
        roleType=payload.roleType.upper(),
        location=payload.location,
        compensation=payload.compensation,
        minCgpa=payload.minCgpa,
        maxBacklogs=payload.maxBacklogs,
        graduationYear=payload.graduationYear,
        deadline=payload.deadline,
        driveId=payload.driveId
    )
    db.add(opp)
    db.flush()
    # Auto-create eligibility rules from minCgpa and maxBacklogs
    if payload.minCgpa > 0:
        db.add(EligibilityRule(opportunityId=opp.id, ruleType="MIN_CGPA", ruleValue=str(payload.minCgpa)))
    if payload.maxBacklogs < 999:
        db.add(EligibilityRule(opportunityId=opp.id, ruleType="MAX_BACKLOGS", ruleValue=str(payload.maxBacklogs)))
    db.commit()
    PlacementAuditService.record(db, "CREATE_OPPORTUNITY", "Opportunity", actor_id=current_user.id, entity_id=opp.id)
    db.commit()
    return make_response(success=True, message="Opportunity created.", data={"id": opp.id})


@router.patch("/opportunities/{opp_id}")
def update_opportunity(
    opp_id: str,
    payload: OpportunityPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement Officer / Admin updates opportunity."""
    require_placement_officer_or_admin(current_user)
    opp = db.query(Opportunity).filter_by(id=opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    for field, val in payload.dict(exclude_none=True).items():
        setattr(opp, field, val)
    db.commit()
    return make_response(success=True, message="Opportunity updated.", data={"id": opp.id})


@router.post("/opportunities/{opp_id}/skills")
def add_opportunity_skill(
    opp_id: str,
    payload: OpportunitySkillAdd,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Add skill requirement to an opportunity."""
    require_placement_officer_or_admin(current_user)
    opp = db.query(Opportunity).filter_by(id=opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    skill = db.query(SkillCatalog).filter(SkillCatalog.name.ilike(payload.skillName)).first()
    if not skill:
        skill = SkillCatalog(name=payload.skillName, category="TECHNICAL")
        db.add(skill)
        db.flush()
    existing = db.query(OpportunitySkill).filter_by(opportunityId=opp_id, skillId=skill.id).first()
    if existing:
        existing.isRequired = payload.isRequired
    else:
        os_rec = OpportunitySkill(opportunityId=opp_id, skillId=skill.id, isRequired=payload.isRequired)
        db.add(os_rec)
    db.commit()
    return make_response(success=True, message="Skill requirement updated.", data={"skillName": skill.name})


@router.post("/opportunities/{opp_id}/rules")
def add_eligibility_rule(
    opp_id: str,
    payload: EligibilityRuleCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Add custom eligibility rule to an opportunity (Officer/Admin only)."""
    require_placement_officer_or_admin(current_user)
    opp = db.query(Opportunity).filter_by(id=opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    rule = EligibilityRule(opportunityId=opp_id, ruleType=payload.ruleType, ruleValue=payload.ruleValue)
    db.add(rule)
    db.commit()
    return make_response(success=True, message="Eligibility rule added.", data={"id": rule.id})


# ================================================================
# ELIGIBILITY ENDPOINTS
# ================================================================

@router.get("/opportunities/{opp_id}/eligibility/me")
def get_my_eligibility(
    opp_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student checks own eligibility for an opportunity (cached or fresh)."""
    require_student_self(current_user)
    opp = db.query(Opportunity).filter_by(id=opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    eval_rec = db.query(EligibilityEvaluation).filter_by(
        opportunityId=opp_id, studentId=current_user.id
    ).first()
    if eval_rec:
        return make_response(success=True, message="Eligibility (cached).", data={
            "eligible": eval_rec.eligible,
            "reasons": json.loads(eval_rec.reasonsJson),
            "failedRules": json.loads(eval_rec.failedRulesJson),
            "passedRules": json.loads(eval_rec.passedRulesJson),
            "evaluatedAt": eval_rec.evaluatedAt.isoformat() if eval_rec.evaluatedAt else None,
            "engineType": "DETERMINISTIC_ELIGIBILITY_RULES"
        })
    # Fresh evaluate
    result = EligibilityService.evaluate(db, current_user, opp)
    EligibilityService.persist_evaluation(db, current_user.id, opp_id, result)
    db.commit()
    return make_response(success=True, message="Eligibility evaluated.", data=result)


@router.post("/opportunities/{opp_id}/eligibility/evaluate")
def evaluate_eligibility(
    opp_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Force fresh eligibility evaluation for current student."""
    require_student_self(current_user)
    opp = db.query(Opportunity).filter_by(id=opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    result = EligibilityService.evaluate(db, current_user, opp)
    EligibilityService.persist_evaluation(db, current_user.id, opp_id, result)
    db.commit()
    return make_response(success=True, message="Eligibility re-evaluated.", data=result)


@router.post("/admin/eligibility/recalculate")
def bulk_eligibility_recalculate(
    opp_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Admin triggers bulk eligibility recalculation for all students."""
    require_roles(current_user, "MASTER_ADMIN", "PLACEMENT_OFFICER")
    students = db.query(User).join(Role).filter(Role.name == "STUDENT", User.status == "ACTIVE").all()
    opps = db.query(Opportunity).filter_by(status="OPEN").all() if not opp_id else [db.query(Opportunity).filter_by(id=opp_id).first()]
    processed = 0
    for s in students:
        for opp in opps:
            if opp:
                result = EligibilityService.evaluate(db, s, opp)
                EligibilityService.persist_evaluation(db, s.id, opp.id, result)
                processed += 1
    db.commit()
    return make_response(success=True, message=f"Bulk eligibility recalculated.", data={"processed": processed})


# ================================================================
# MATCHING ENDPOINTS
# ================================================================

@router.get("/matches/me")
def get_my_matches(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student sees all precomputed match scores."""
    require_student_self(current_user)
    scores = db.query(JobMatchScore).filter_by(studentId=current_user.id).order_by(
        desc(JobMatchScore.score)
    ).limit(20).all()
    return make_response(success=True, message="My job matches.", data=[
        {
            "id": m.id, "opportunityId": m.opportunityId,
            "opportunityTitle": m.opportunity.title if m.opportunity else None,
            "companyName": m.opportunity.company.name if m.opportunity and m.opportunity.company else None,
            "score": m.score, "engineType": m.engineType,
            "factors": json.loads(m.factorsJson),
            "matchedSkills": json.loads(m.matchedSkillsJson),
            "missingSkills": json.loads(m.missingSkillsJson),
            "eligibilityStatus": m.eligibilityStatus,
            "eligibilityReason": m.eligibilityReason,
            "explanation": m.explanation,
            "generatedAt": m.generatedAt.isoformat() if m.generatedAt else None
        } for m in scores
    ])


@router.get("/matches/me/{opp_id}")
def get_my_match_for_opportunity(
    opp_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student gets detailed match score for a specific opportunity."""
    require_student_self(current_user)
    opp = db.query(Opportunity).filter_by(id=opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    result = CareerMatchingService.compute_match(db, current_user, opp)
    CareerMatchingService.persist_match(db, current_user.id, opp_id, result)
    db.commit()
    return make_response(success=True, message="Match computed.", data=result)


@router.post("/matches/recalculate/me")
def recalculate_my_matches(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student triggers recalculation of all match scores."""
    require_student_self(current_user)
    opps = db.query(Opportunity).filter_by(status="OPEN").limit(20).all()
    computed = 0
    for opp in opps:
        result = CareerMatchingService.compute_match(db, current_user, opp)
        CareerMatchingService.persist_match(db, current_user.id, opp.id, result)
        computed += 1
    db.commit()
    return make_response(success=True, message="Matches recalculated.", data={"computed": computed})


# ================================================================
# APPLICATION ENDPOINTS
# ================================================================

@router.get("/applications/me")
def get_my_applications(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student views own applications."""
    require_student_self(current_user)
    apps = db.query(JobApplication).filter_by(studentId=current_user.id).order_by(
        desc(JobApplication.appliedAt)
    ).all()
    return make_response(success=True, message="My applications.", data=[
        {
            "id": a.id,
            "opportunityId": a.opportunityId,
            "opportunityTitle": a.opportunity.title if a.opportunity else None,
            "companyName": a.opportunity.company.name if a.opportunity and a.opportunity.company else None,
            "status": a.status,
            "appliedAt": a.appliedAt.isoformat() if a.appliedAt else None
        } for a in apps
    ])


@router.post("/applications")
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student applies to an opportunity. Duplicate blocked."""
    require_student_self(current_user)
    opp = db.query(Opportunity).filter_by(id=payload.opportunityId).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    if opp.status != "OPEN":
        raise HTTPException(status_code=409, detail="Opportunity is closed.")
    existing = db.query(JobApplication).filter_by(
        opportunityId=payload.opportunityId, studentId=current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied to this opportunity.")

    app = JobApplication(
        opportunityId=payload.opportunityId,
        studentId=current_user.id,
        resumeVersionId=payload.resumeVersionId,
        coverLetter=payload.coverLetter,
        status="APPLIED"
    )
    db.add(app)
    db.flush()

    # Initial status history entry
    db.add(ApplicationStatusHistory(
        applicationId=app.id,
        status="APPLIED",
        notes="Application submitted by student.",
        changedById=current_user.id
    ))

    db.commit()

    # Notification
    try:
        company_name = opp.company.name if opp.company else "the company"
        NotificationService.create_notification(
            db=db,
            recipient_id=current_user.id,
            title="Application Submitted",
            body=f"Your application for '{opp.title}' at {company_name} has been submitted successfully.",
            type="SUCCESS", priority="MEDIUM", channel="IN_APP", category="CAREER"
        )
        db.commit()
    except Exception:
        pass

    PlacementAuditService.record(db, "SUBMIT_APPLICATION", "JobApplication",
                                  actor_id=current_user.id, student_id=current_user.id, entity_id=app.id)
    db.commit()
    return make_response(success=True, message="Application submitted.", data={"id": app.id})


@router.get("/applications/{app_id}")
def get_application(
    app_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student reads own application detail. Officer/Admin can read any."""
    app = db.query(JobApplication).filter_by(id=app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    is_privileged = current_user.role.name in ("PLACEMENT_OFFICER", "MASTER_ADMIN")
    if not is_privileged and app.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return make_response(success=True, message="Application detail.", data={
        "id": app.id,
        "opportunityId": app.opportunityId,
        "opportunityTitle": app.opportunity.title if app.opportunity else None,
        "studentId": app.studentId,
        "status": app.status,
        "coverLetter": app.coverLetter,
        "appliedAt": app.appliedAt.isoformat() if app.appliedAt else None,
        "statusHistory": [
            {"status": h.status, "notes": h.notes, "changedAt": h.changedAt.isoformat()}
            for h in app.statusHistory
        ]
    })


@router.patch("/applications/{app_id}/status")
def update_application_status(
    app_id: str,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Only Placement Officer or Admin can change application status."""
    require_placement_officer_or_admin(current_user)
    app = db.query(JobApplication).filter_by(id=app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    old_status = app.status
    app.status = payload.status.upper()

    db.add(ApplicationStatusHistory(
        applicationId=app.id,
        status=payload.status.upper(),
        notes=payload.notes,
        changedById=current_user.id
    ))
    db.commit()

    # Notify student
    try:
        NotificationService.create_notification(
            db=db,
            recipient_id=app.studentId,
            title=f"Application Status Updated",
            body=f"Your application for '{app.opportunity.title if app.opportunity else 'an opportunity'}' has been updated to: {payload.status}.",
            type="INFO", priority="HIGH", channel="IN_APP", category="CAREER"
        )
        db.commit()
    except Exception:
        pass

    PlacementAuditService.record(db, "UPDATE_APPLICATION_STATUS", "JobApplication",
                                  actor_id=current_user.id, student_id=app.studentId,
                                  entity_id=app.id, metadata={"from": old_status, "to": payload.status})
    db.commit()
    return make_response(success=True, message="Application status updated.", data={"id": app.id, "status": app.status})


# ================================================================
# PLACEMENT DRIVES
# ================================================================

@router.get("/drives")
def list_drives(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """All authenticated users can see placement drives."""
    drives = db.query(PlacementDrive).order_by(desc(PlacementDrive.startDate)).limit(30).all()
    return make_response(success=True, message="Placement drives.", data=[
        {
            "id": d.id, "companyId": d.companyId,
            "companyName": d.company.name if d.company else None,
            "title": d.title, "startDate": d.startDate.isoformat(),
            "endDate": d.endDate.isoformat(), "status": d.status, "venue": d.venue
        } for d in drives
    ])


@router.post("/drives")
def create_drive(
    payload: DriveCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement Officer / Admin creates a drive."""
    require_placement_officer_or_admin(current_user)
    company = db.query(Company).filter_by(id=payload.companyId).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")
    d = PlacementDrive(
        companyId=payload.companyId,
        title=payload.title,
        description=payload.description,
        startDate=payload.startDate,
        endDate=payload.endDate,
        venue=payload.venue
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    PlacementAuditService.record(db, "CREATE_DRIVE", "PlacementDrive", actor_id=current_user.id, entity_id=d.id)
    db.commit()
    return make_response(success=True, message="Placement drive created.", data={"id": d.id})


@router.get("/drives/{drive_id}")
def get_drive(
    drive_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Get drive details with registration count."""
    d = db.query(PlacementDrive).filter_by(id=drive_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Drive not found.")
    return make_response(success=True, message="Drive details.", data={
        "id": d.id, "title": d.title, "companyName": d.company.name if d.company else None,
        "description": d.description, "startDate": d.startDate.isoformat(),
        "endDate": d.endDate.isoformat(), "status": d.status, "venue": d.venue,
        "registrationCount": len(d.registrations)
    })


@router.post("/drives/{drive_id}/register")
def register_for_drive(
    drive_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student registers for a placement drive. Duplicate blocked."""
    require_student_self(current_user)
    d = db.query(PlacementDrive).filter_by(id=drive_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Drive not found.")
    existing = db.query(DriveRegistration).filter_by(
        driveId=drive_id, studentId=current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already registered for this drive.")
    reg = DriveRegistration(driveId=drive_id, studentId=current_user.id, status="REGISTERED")
    db.add(reg)
    db.commit()
    try:
        NotificationService.create_notification(
            db=db,
            recipient_id=current_user.id,
            title="Drive Registration Confirmed",
            body=f"You have registered for the placement drive: '{d.title}'.",
            type="SUCCESS", priority="MEDIUM", channel="IN_APP", category="CAREER"
        )
        db.commit()
    except Exception:
        pass
    return make_response(success=True, message="Registered for drive.", data={"id": reg.id})


# ================================================================
# INTERVIEW ENDPOINTS
# ================================================================

@router.get("/interviews/me")
def get_my_interviews(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student sees own interview rounds."""
    require_student_self(current_user)
    apps = db.query(JobApplication).filter_by(studentId=current_user.id).all()
    app_ids = [a.id for a in apps]
    rounds = db.query(InterviewRound).filter(
        InterviewRound.applicationId.in_(app_ids)
    ).order_by(InterviewRound.scheduledAt).all()
    return make_response(success=True, message="My interviews.", data=[
        {
            "id": r.id, "applicationId": r.applicationId,
            "opportunityTitle": r.application.opportunity.title if r.application and r.application.opportunity else None,
            "roundNumber": r.roundNumber, "title": r.title, "type": r.type,
            "status": r.status, "result": r.result,
            "scheduledAt": r.scheduledAt.isoformat() if r.scheduledAt else None,
            "location": r.location, "durationMinutes": r.durationMinutes,
            "publicNotes": [f.notes for f in r.feedbacks if f.notes]  # only public notes
        } for r in rounds
    ])


@router.post("/interviews")
def create_interview(
    payload: InterviewCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement Officer creates interview round."""
    require_placement_officer_or_admin(current_user)
    app = db.query(JobApplication).filter_by(id=payload.applicationId).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    ir = InterviewRound(
        applicationId=payload.applicationId,
        roundNumber=payload.roundNumber,
        title=payload.title,
        type=payload.type.upper(),
        scheduledAt=payload.scheduledAt,
        location=payload.location,
        interviewerNames=payload.interviewerNames,
        durationMinutes=payload.durationMinutes
    )
    db.add(ir)
    db.commit()
    # Notify student
    try:
        NotificationService.create_notification(
            db=db,
            recipient_id=app.studentId,
            title="Interview Scheduled",
            body=f"Round {payload.roundNumber} interview ({payload.type}) scheduled. Location: {payload.location or 'TBD'}.",
            type="INFO", priority="HIGH", channel="IN_APP", category="CAREER"
        )
        db.commit()
    except Exception:
        pass
    return make_response(success=True, message="Interview round created.", data={"id": ir.id})


@router.patch("/interviews/{interview_id}")
def update_interview(
    interview_id: str,
    payload: InterviewPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement Officer updates interview status/result."""
    require_placement_officer_or_admin(current_user)
    ir = db.query(InterviewRound).filter_by(id=interview_id).first()
    if not ir:
        raise HTTPException(status_code=404, detail="Interview not found.")
    for field, val in payload.dict(exclude_none=True).items():
        setattr(ir, field, val)
    db.commit()
    return make_response(success=True, message="Interview updated.", data={"id": ir.id})


@router.post("/interviews/{interview_id}/feedback")
def add_interview_feedback(
    interview_id: str,
    payload: InterviewFeedbackCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Add public feedback to interview (Officer/Admin). Private notes stored separately."""
    require_placement_officer_or_admin(current_user)
    ir = db.query(InterviewRound).filter_by(id=interview_id).first()
    if not ir:
        raise HTTPException(status_code=404, detail="Interview not found.")
    fb = InterviewFeedback(
        interviewRoundId=interview_id,
        interviewerId=current_user.id,
        rating=payload.rating,
        notes=payload.notes,
        privateNotes=None  # Private notes only via explicit separate endpoint
    )
    db.add(fb)
    db.commit()
    return make_response(success=True, message="Feedback added.", data={"id": fb.id})


# ================================================================
# OFFER ENDPOINTS
# ================================================================

@router.get("/offers/me")
def get_my_offers(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student views own job offers."""
    require_student_self(current_user)
    offers = db.query(Offer).filter_by(studentId=current_user.id).order_by(desc(Offer.createdAt)).all()
    return make_response(success=True, message="My offers.", data=[
        {
            "id": o.id,
            "opportunityTitle": o.application.opportunity.title if o.application and o.application.opportunity else None,
            "companyName": o.application.opportunity.company.name if o.application and o.application.opportunity and o.application.opportunity.company else None,
            "packageAmount": o.packageAmount,
            "status": o.status,
            "joiningDate": o.joiningDate.isoformat() if o.joiningDate else None,
            "deadline": o.deadline.isoformat() if o.deadline else None,
            "notes": o.notes
        } for o in offers
    ])


@router.post("/offers")
def create_offer(
    payload: OfferCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement Officer creates an offer for a student."""
    require_placement_officer_or_admin(current_user)
    app = db.query(JobApplication).filter_by(id=payload.applicationId).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    offer = Offer(
        applicationId=payload.applicationId,
        studentId=app.studentId,
        packageAmount=payload.packageAmount,
        offerLetterUrl=payload.offerLetterUrl,
        joiningDate=payload.joiningDate,
        deadline=payload.deadline,
        notes=payload.notes
    )
    db.add(offer)
    # Update application status to OFFERED
    app.status = "OFFERED"
    db.flush()
    db.commit()

    # Notify student
    try:
        opp_title = app.opportunity.title if app.opportunity else "an opportunity"
        NotificationService.create_notification(
            db=db,
            recipient_id=app.studentId,
            title="Congratulations! Offer Received",
            body=f"You have received an offer for '{opp_title}'. Package: {payload.packageAmount}. Deadline: {payload.deadline.strftime('%Y-%m-%d')}.",
            type="SUCCESS", priority="CRITICAL", channel="IN_APP", category="CAREER"
        )
        db.commit()
    except Exception:
        pass

    PlacementAuditService.record(db, "CREATE_OFFER", "Offer",
                                  actor_id=current_user.id, student_id=app.studentId, entity_id=offer.id)
    db.commit()
    return make_response(success=True, message="Offer created.", data={"id": offer.id})


@router.patch("/offers/{offer_id}/status")
def update_offer_status(
    offer_id: str,
    payload: OfferStatusPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student accepts/declines offer. Officer/Admin can also update."""
    offer = db.query(Offer).filter_by(id=offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    is_privileged = current_user.role.name in ("PLACEMENT_OFFICER", "MASTER_ADMIN")
    is_own = offer.studentId == current_user.id

    if not is_privileged and not is_own:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Students can only accept/decline, not set arbitrary statuses
    if not is_privileged and payload.status.upper() not in ("ACCEPTED", "DECLINED"):
        raise HTTPException(status_code=403, detail="Students can only ACCEPT or DECLINE offers.")

    offer.status = payload.status.upper()

    # If accepted, create placement outcome
    if offer.status == "ACCEPTED":
        existing_outcome = db.query(PlacementOutcome).filter_by(offerId=offer_id).first()
        if not existing_outcome:
            outcome = PlacementOutcome(
                studentId=offer.studentId,
                offerId=offer_id,
                status="PLACED",
                placedAt=datetime.utcnow()
            )
            db.add(outcome)
            # Update career profile status
            career = db.query(CareerProfile).filter_by(studentId=offer.studentId).first()
            if career:
                career.status = "PLACED"

    db.commit()
    PlacementAuditService.record(db, "UPDATE_OFFER_STATUS", "Offer",
                                  actor_id=current_user.id, student_id=offer.studentId,
                                  entity_id=offer_id, metadata={"status": offer.status})
    db.commit()
    return make_response(success=True, message="Offer status updated.", data={"id": offer.id, "status": offer.status})


# ================================================================
# CAREER GOALS
# ================================================================

@router.get("/career-goals/me")
def get_my_career_goals(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    require_student_self(current_user)
    goals = db.query(CareerGoal).filter_by(studentId=current_user.id).all()
    return make_response(success=True, message="Career goals.", data=[
        {"id": g.id, "title": g.title, "targetTimeline": g.targetTimeline,
         "targetRole": g.targetRole, "targetIndustry": g.targetIndustry, "status": g.status}
        for g in goals
    ])


@router.post("/career-goals")
def create_career_goal(
    payload: CareerGoalCreate,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    require_student_self(current_user)
    g = CareerGoal(
        studentId=current_user.id, title=payload.title,
        targetTimeline=payload.targetTimeline,
        targetRole=payload.targetRole, targetIndustry=payload.targetIndustry
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return make_response(success=True, message="Career goal created.", data={"id": g.id})


@router.patch("/career-goals/{goal_id}")
def update_career_goal(
    goal_id: str,
    payload: CareerGoalPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    require_student_self(current_user)
    g = db.query(CareerGoal).filter_by(id=goal_id, studentId=current_user.id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found.")
    for field, val in payload.dict(exclude_none=True).items():
        setattr(g, field, val)
    db.commit()
    return make_response(success=True, message="Career goal updated.", data={"id": g.id})


# ================================================================
# SKILL GAP ANALYSIS
# ================================================================

@router.get("/skill-gap/me")
def get_my_skill_gap(
    opp_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student views latest skill gap analysis."""
    require_student_self(current_user)
    q = db.query(SkillGapAnalysis).filter_by(studentId=current_user.id)
    if opp_id:
        q = q.filter_by(opportunityId=opp_id)
    analyses = q.order_by(desc(SkillGapAnalysis.calculatedAt)).limit(5).all()
    return make_response(success=True, message="Skill gap analyses.", data=[
        {
            "id": a.id, "goalTitle": a.goalTitle, "opportunityId": a.opportunityId,
            "readinessScore": a.readinessScore,
            "matchedSkills": json.loads(a.matchedSkillsJson),
            "missingCriticalSkills": json.loads(a.missingCriticalSkillsJson),
            "missingOptionalSkills": json.loads(a.missingOptionalSkillsJson),
            "learningActions": json.loads(a.learningActionsJson),
            "engineType": a.engineType,
            "calculatedAt": a.calculatedAt.isoformat() if a.calculatedAt else None
        } for a in analyses
    ])


@router.post("/skill-gap/recalculate/me")
def recalculate_skill_gap(
    opp_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Student triggers skill gap recalculation."""
    require_student_self(current_user)
    opp = db.query(Opportunity).filter_by(id=opp_id).first() if opp_id else None
    result = SkillGapService.analyze(db, current_user, opp)
    analysis = SkillGapAnalysis(
        studentId=current_user.id,
        goalTitle=result["goalTitle"],
        opportunityId=result["opportunityId"],
        readinessScore=result["readinessScore"],
        matchedSkillsJson=json.dumps(result["matchedSkills"]),
        missingCriticalSkillsJson=json.dumps(result["missingCriticalSkills"]),
        missingOptionalSkillsJson=json.dumps(result["missingOptionalSkills"]),
        learningActionsJson=json.dumps(result["learningActions"]),
        engineType=result["engineType"]
    )
    db.add(analysis)
    db.commit()
    return make_response(success=True, message="Skill gap recalculated.", data=result)


# ================================================================
# CAREER RECOMMENDATIONS
# ================================================================

@router.get("/recommendations/me")
def get_my_recommendations(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    require_student_self(current_user)
    recs = db.query(CareerRecommendation).filter_by(
        studentId=current_user.id, status="ACTIVE"
    ).order_by(desc(CareerRecommendation.createdAt)).all()
    if not recs:
        # Auto-generate fresh recommendations
        PlacementRecommendationService.upsert_recommendations(db, current_user.id)
        db.commit()
        recs = db.query(CareerRecommendation).filter_by(
            studentId=current_user.id, status="ACTIVE"
        ).all()
    return make_response(success=True, message="Career recommendations.", data=[
        {
            "id": r.id, "category": r.category, "title": r.title,
            "description": r.description, "priority": r.priority, "status": r.status,
            "reason": r.reason
        } for r in recs
    ])


@router.patch("/recommendations/{rec_id}/status")
def update_recommendation_status(
    rec_id: str,
    payload: RecommendationStatusPatch,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    require_student_self(current_user)
    rec = db.query(CareerRecommendation).filter_by(id=rec_id, studentId=current_user.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found or not yours.")
    rec.status = payload.status.upper()
    db.commit()
    return make_response(success=True, message="Recommendation status updated.", data={"id": rec.id, "status": rec.status})


# ================================================================
# PARENT PORTAL — LINKED CHILD CAREER SUMMARY
# ================================================================

@router.get("/parent/children/{student_id}/career-summary")
def get_child_career_summary(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Parent reads linked child's career summary. No private recruiter feedback exposed."""
    check_parent_child_link_placement(db, current_user, student_id)
    career = db.query(CareerProfile).filter_by(studentId=student_id).first()
    skill_count = db.query(StudentSkill).filter_by(studentId=student_id).count()
    apps_count = db.query(JobApplication).filter_by(studentId=student_id).count()
    active_apps = db.query(JobApplication).filter_by(studentId=student_id).filter(
        JobApplication.status.in_(["APPLIED", "SHORTLISTED"])
    ).count()
    offers = db.query(Offer).filter_by(studentId=student_id).count()
    return make_response(success=True, message="Child career summary.", data={
        "studentId": student_id,
        "careerStatus": career.status if career else "NO_PROFILE",
        "graduationYear": career.graduationYear if career else None,
        "skillCount": skill_count,
        "totalApplications": apps_count,
        "activeApplications": active_apps,
        "totalOffers": offers,
        "note": "Private recruiter feedback and confidential interview notes are not accessible to parents."
    })


# ================================================================
# TEACHER PORTAL — SCOPED STUDENT CAREER READINESS
# ================================================================

@router.get("/teacher/students/{student_id}/career-readiness")
def get_student_career_readiness(
    student_id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Teacher reads scoped student career readiness. No offer mutation. No private notes."""
    check_teacher_student_link_placement(db, current_user, student_id)
    student = get_student_or_404(db, student_id)
    career = db.query(CareerProfile).filter_by(studentId=student_id).first()
    skill_count = db.query(StudentSkill).filter_by(studentId=student_id).count()
    top_match = db.query(JobMatchScore).filter_by(studentId=student_id).order_by(
        desc(JobMatchScore.score)
    ).first()
    return make_response(success=True, message="Student career readiness.", data={
        "studentId": student_id,
        "studentName": student.name,
        "careerStatus": career.status if career else "NO_PROFILE",
        "skillCount": skill_count,
        "topMatchScore": top_match.score if top_match else None,
        "topMatchOpportunity": top_match.opportunity.title if top_match and top_match.opportunity else None,
        "note": "Private recruiter feedback and offer terms are not accessible to teaching staff."
    })


# ================================================================
# ANALYTICS ENDPOINTS
# ================================================================

@router.get("/analytics/overview")
def get_placement_analytics_overview(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Admin/Officer sees aggregate placement analytics."""
    require_placement_officer_or_admin(current_user)
    total_students = db.query(User).join(Role).filter(Role.name == "STUDENT", User.status == "ACTIVE").count()
    total_companies = db.query(Company).filter_by(status="ACTIVE").count()
    total_opps = db.query(Opportunity).filter_by(status="OPEN").count()
    total_apps = db.query(JobApplication).count()
    total_offers = db.query(Offer).count()
    accepted_offers = db.query(Offer).filter_by(status="ACCEPTED").count()
    placed_students = db.query(PlacementOutcome).count()
    placement_rate = round((placed_students / total_students * 100) if total_students > 0 else 0.0, 2)
    return make_response(success=True, message="Placement overview analytics.", data={
        "totalStudents": total_students,
        "totalActiveCompanies": total_companies,
        "totalOpenOpportunities": total_opps,
        "totalApplications": total_apps,
        "totalOffers": total_offers,
        "acceptedOffers": accepted_offers,
        "placedStudents": placed_students,
        "placementRate": placement_rate,
        "engineType": "LOCAL_EXPLAINABLE_CAREER_MATCHING"
    })


@router.get("/analytics/departments")
def get_department_analytics(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Department-level placement breakdown."""
    require_placement_officer_or_admin(current_user)
    from app.models.models import Department
    departments = db.query(Department).all()
    result = []
    for dept in departments:
        students = db.query(User).filter_by(departmentId=dept.id, status="ACTIVE").join(Role).filter(Role.name == "STUDENT").count()
        placed = db.query(PlacementOutcome).join(User, PlacementOutcome.studentId == User.id).filter(
            User.departmentId == dept.id
        ).count()
        result.append({
            "departmentId": dept.id,
            "departmentName": dept.name,
            "totalStudents": students,
            "placedStudents": placed,
            "placementRate": round((placed / students * 100) if students > 0 else 0.0, 2)
        })
    return make_response(success=True, message="Department placement analytics.", data=result)


@router.get("/analytics/opportunities")
def get_opportunity_analytics(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Opportunity-level application funnel analytics."""
    require_placement_officer_or_admin(current_user)
    opps = db.query(Opportunity).filter_by(status="OPEN").limit(20).all()
    result = []
    for opp in opps:
        total = db.query(JobApplication).filter_by(opportunityId=opp.id).count()
        shortlisted = db.query(JobApplication).filter_by(opportunityId=opp.id, status="SHORTLISTED").count()
        offered = db.query(JobApplication).filter_by(opportunityId=opp.id, status="OFFERED").count()
        result.append({
            "opportunityId": opp.id,
            "title": opp.title,
            "companyName": opp.company.name if opp.company else None,
            "totalApplications": total,
            "shortlisted": shortlisted,
            "offered": offered
        })
    return make_response(success=True, message="Opportunity analytics.", data=result)


@router.get("/analytics/outcomes")
def get_outcome_analytics(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Placement outcome analytics — average CTC, placement rate."""
    require_placement_officer_or_admin(current_user)
    outcomes = db.query(PlacementOutcome).all()
    total = len(outcomes)
    packages = []
    for o in outcomes:
        if o.offer and o.offer.packageAmount:
            packages.append(o.offer.packageAmount)
    avg_pkg = round(sum(packages) / len(packages), 2) if packages else 0.0
    return make_response(success=True, message="Outcome analytics.", data={
        "totalPlaced": total,
        "averagePackage": avg_pkg,
        "maxPackage": max(packages) if packages else 0,
        "minPackage": min(packages) if packages else 0
    })


# ================================================================
# AUDIT ENDPOINTS
# ================================================================

@router.get("/audit")
def get_placement_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Only MASTER_ADMIN can read full placement audit log."""
    require_roles(current_user, "MASTER_ADMIN")
    offset = (page - 1) * limit
    audits = db.query(PlacementAudit).order_by(
        desc(PlacementAudit.createdAt)
    ).offset(offset).limit(limit).all()
    total = db.query(PlacementAudit).count()
    return make_response(success=True, message="Placement audit log.", data={
        "total": total, "page": page, "limit": limit,
        "audits": [
            {
                "id": a.id, "action": a.action, "entityType": a.entityType,
                "entityId": a.entityId, "actorId": a.actorId, "studentId": a.studentId,
                "createdAt": a.createdAt.isoformat() if a.createdAt else None
            } for a in audits
        ]
    })


# ================================================================
# STUDENT CAREER DASHBOARD (AGGREGATED)
# ================================================================

@router.get("/dashboard/me")
def get_student_career_dashboard(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Full student career dashboard — aggregated view."""
    require_student_self(current_user)
    career = db.query(CareerProfile).filter_by(studentId=current_user.id).first()
    skill_count = db.query(StudentSkill).filter_by(studentId=current_user.id).count()
    resume_count = db.query(ResumeProfile).filter_by(studentId=current_user.id).count()
    apps = db.query(JobApplication).filter_by(studentId=current_user.id).all()
    active_apps = [a for a in apps if a.status in ("APPLIED", "SHORTLISTED")]
    top_matches = db.query(JobMatchScore).filter_by(studentId=current_user.id).order_by(
        desc(JobMatchScore.score)
    ).limit(5).all()
    pending_offers = db.query(Offer).filter_by(studentId=current_user.id, status="PENDING").count()
    goals = db.query(CareerGoal).filter_by(studentId=current_user.id, status="ACTIVE").count()

    # Completeness score
    completeness = 0
    if career: completeness += 20
    if career and career.biography: completeness += 15
    if career and career.projects: completeness += 15
    if skill_count >= 3: completeness += 20
    if resume_count > 0: completeness += 15
    if goals > 0: completeness += 15

    return make_response(success=True, message="Career dashboard.", data={
        "profileCompleteness": completeness,
        "hasCareerProfile": career is not None,
        "careerStatus": career.status if career else "NO_PROFILE",
        "skillCount": skill_count,
        "resumeCount": resume_count,
        "totalApplications": len(apps),
        "activeApplications": len(active_apps),
        "pendingOffers": pending_offers,
        "activeGoals": goals,
        "topMatches": [
            {
                "opportunityId": m.opportunityId,
                "opportunityTitle": m.opportunity.title if m.opportunity else None,
                "companyName": m.opportunity.company.name if m.opportunity and m.opportunity.company else None,
                "score": m.score,
                "eligibilityStatus": m.eligibilityStatus,
                "engineType": m.engineType
            } for m in top_matches
        ]
    })
