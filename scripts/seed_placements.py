import sys
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to path
backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.models import (
    Base, Role, User, Department, CareerProfile, SkillCatalog, StudentSkill,
    ResumeProfile, ResumeVersion, Company, RecruiterContact, Opportunity,
    OpportunitySkill, EligibilityRule, PlacementDrive, DriveRegistration,
    JobApplication, ApplicationStatusHistory, InterviewRound, InterviewFeedback,
    Offer, PlacementOutcome, CareerGoal, SkillGapAnalysis, CareerRecommendation,
    JobMatchScore, Result, AcademicYear
)
from app.services.career_matching_service import EligibilityService, CareerMatchingService, SkillGapService, PlacementRecommendationService

def run_placement_seeder():
    print("Connecting to database at:", settings.DATABASE_URL)
    try:
        engine = create_engine(settings.DATABASE_URL)
        conn = engine.connect()
        conn.close()
    except Exception as e:
        print("\n[DB CONNECTION ERROR] Could not connect to database.")
        print("Reason:", str(e))
        return

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("Starting Placement & Career Intelligence seeding transaction...")

        # 1. Check or Create Roles
        roles = {}
        for role_name in ["MASTER_ADMIN", "PLACEMENT_OFFICER", "STUDENT", "PARENT", "TEACHER"]:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} role")
                db.add(role)
                db.flush()
            roles[role_name] = role

        # 2. Check/Get existing department
        dept = db.query(Department).first()
        if not dept:
            dept = Department(name="Computer Science and Engineering", code="CSE")
            db.add(dept)
            db.flush()

        # 3. Create/Retrieve Demo Users (Student A, Student B, Student C, Officer)
        # Student A (Demo Student)
        student_a = db.query(User).filter(User.email == "student.demo@campusgpt.local").first()
        if not student_a:
            student_a = User(
                email="student.demo@campusgpt.local",
                username="student_demo",
                passwordHash=get_password_hash("password"),
                name="Demo Student A",
                roleId=roles["STUDENT"].id,
                departmentId=dept.id,
                status="ACTIVE",
                mustChangePassword=False
            )
            db.add(student_a)
            db.flush()
        else:
            student_a.departmentId = dept.id
            db.add(student_a)
            db.flush()

        # Student B
        student_b = db.query(User).filter(User.email == "student_b@campusgpt.local").first()
        if not student_b:
            student_b = User(
                email="student_b@campusgpt.local",
                username="student_b",
                passwordHash=get_password_hash("password"),
                name="Student B (Partial Match)",
                roleId=roles["STUDENT"].id,
                departmentId=dept.id,
                status="ACTIVE",
                mustChangePassword=False
            )
            db.add(student_b)
            db.flush()

        # Student C
        student_c = db.query(User).filter(User.email == "student_c@campusgpt.local").first()
        if not student_c:
            student_c = User(
                email="student_c@campusgpt.local",
                username="student_c",
                passwordHash=get_password_hash("password"),
                name="Student C (Insufficient Profile)",
                roleId=roles["STUDENT"].id,
                departmentId=dept.id,
                status="ACTIVE",
                mustChangePassword=False
            )
            db.add(student_c)
            db.flush()

        # Placement Officer
        officer = db.query(User).filter(User.email == "officer.demo@campusgpt.local").first()
        if not officer:
            officer = User(
                email="officer.demo@campusgpt.local",
                username="officer_demo",
                passwordHash=get_password_hash("password"),
                name="Demo Placement Officer",
                roleId=roles["PLACEMENT_OFFICER"].id,
                status="ACTIVE",
                mustChangePassword=False
            )
            db.add(officer)
            db.flush()

        # Get or create AcademicYear
        ay = db.query(AcademicYear).filter(AcademicYear.name == "2026-2027").first()
        if not ay:
            ay = AcademicYear(name="2026-2027", startDate=datetime(2026, 6, 1), endDate=datetime(2027, 5, 31), status="ACTIVE")
            db.add(ay)
            db.flush()

        # Seed results for CGPA calculations
        for student, cgpa in [(student_a, 9.2), (student_b, 7.1), (student_c, 5.2)]:
            res = db.query(Result).filter_by(studentId=student.id).first()
            if not res:
                res = Result(
                    studentId=student.id,
                    academicYearId=ay.id,
                    semesterNumber=6,
                    sgpa=cgpa,
                    cgpa=cgpa,
                    creditsEarned=100,
                    status="PUBLISHED"
                )
                db.add(res)
                db.flush()

        # 4. Seed Skill Catalog
        skills = {}
        skill_list = [
            ("Python", "TECHNICAL", "Python Programming"),
            ("React", "TECHNICAL", "Frontend UI Library"),
            ("SQL", "TECHNICAL", "Relational Database Query Language"),
            ("Java", "TECHNICAL", "Backend Object Oriented Language"),
            ("TypeScript", "TECHNICAL", "Typed JS"),
            ("Communication", "SOFT_SKILL", "Verbal/Written Skills")
        ]
        for name, category, desc in skill_list:
            sk = db.query(SkillCatalog).filter(SkillCatalog.name == name).first()
            if not sk:
                sk = SkillCatalog(name=name, category=category, description=desc)
                db.add(sk)
                db.flush()
            skills[name] = sk

        # 5. Career Profiles
        # Student A (Strong Profile)
        prof_a = db.query(CareerProfile).filter_by(studentId=student_a.id).first()
        if not prof_a:
            prof_a = CareerProfile(
                studentId=student_a.id,
                graduationYear=2026,
                status="ACTIVE",
                biography="Ambitious software engineer focusing on full-stack systems and cloud computing.",
                certifications="AWS Certified Cloud Practitioner, Oracle Certified Java Associate",
                projects="CampusGPT X: An enterprise university web platform with advanced intelligence modules.",
                experience="Intern at TechCorp for 3 months developing REST APIs.",
                linkedinUrl="https://linkedin.com/in/studenta",
                githubUrl="https://github.com/studenta",
                portfolioUrl="https://studenta.dev"
            )
            db.add(prof_a)
            db.flush()

        # Student B (Moderate Profile)
        prof_b = db.query(CareerProfile).filter_by(studentId=student_b.id).first()
        if not prof_b:
            prof_b = CareerProfile(
                studentId=student_b.id,
                graduationYear=2026,
                status="ACTIVE",
                biography="Computer science student with core knowledge in Java and databases.",
                projects="Simple DBMS: A basic terminal-based database engine in Java.",
                linkedinUrl="https://linkedin.com/in/studentb"
            )
            db.add(prof_b)
            db.flush()

        # Student C (Empty Profile)
        prof_c = db.query(CareerProfile).filter_by(studentId=student_c.id).first()
        if not prof_c:
            prof_c = CareerProfile(
                studentId=student_c.id,
                graduationYear=2026,
                status="ACTIVE"
            )
            db.add(prof_c)
            db.flush()

        # 6. Student Skills
        # Student A
        for sk_name, prof, exp in [("Python", "EXPERT", 3.0), ("React", "ADVANCED", 2.0), ("SQL", "INTERMEDIATE", 1.5)]:
            existing = db.query(StudentSkill).filter_by(studentId=student_a.id, skillId=skills[sk_name].id).first()
            if not existing:
                db.add(StudentSkill(studentId=student_a.id, skillId=skills[sk_name].id, proficiency=prof, yearsOfExperience=exp))
        # Student B
        for sk_name, prof, exp in [("Java", "INTERMEDIATE", 1.5), ("SQL", "BEGINNER", 0.5)]:
            existing = db.query(StudentSkill).filter_by(studentId=student_b.id, skillId=skills[sk_name].id).first()
            if not existing:
                db.add(StudentSkill(studentId=student_b.id, skillId=skills[sk_name].id, proficiency=prof, yearsOfExperience=exp))

        # 7. Resume Profiles & Versions
        for student in [student_a, student_b]:
            rp = db.query(ResumeProfile).filter_by(studentId=student.id).first()
            if not rp:
                rp = ResumeProfile(studentId=student.id, title="Main Resume")
                db.add(rp)
                db.flush()
                v = ResumeVersion(
                    resumeProfileId=rp.id,
                    versionNumber=1,
                    fileUrl=f"https://storage.campusgpt.local/resumes/{student.username}_v1.pdf",
                    status="ACTIVE",
                    isActive=True,
                    summary="Full-stack software developer resume."
                )
                db.add(v)
                db.flush()

        # 8. Companies & Recruiter Contacts
        google = db.query(Company).filter_by(name="Google").first()
        if not google:
            google = Company(name="Google", industry="TECHNOLOGY", website="https://google.com", description="Search & AI technology leader.", hrEmail="hr@google.com")
            db.add(google)
            db.flush()
            rec = RecruiterContact(companyId=google.id, name="Sarah Jenkins", email="sjenkins@google.com", designation="University Recruiter")
            db.add(rec)
            db.flush()

        startup = db.query(Company).filter_by(name="Startup Corp").first()
        if not startup:
            startup = Company(name="Startup Corp", industry="FINTECH", website="https://startupcorp.io", description="Fast-growing payment provider.", hrEmail="recruiter@startupcorp.io")
            db.add(startup)
            db.flush()

        # 9. Placement Drives
        drive = db.query(PlacementDrive).filter_by(title="Google Summer Placement Drive").first()
        if not drive:
            drive = PlacementDrive(
                companyId=google.id,
                title="Google Summer Placement Drive",
                description="Google hiring event for SWE & Intern roles.",
                startDate=datetime.utcnow() + timedelta(days=5),
                endDate=datetime.utcnow() + timedelta(days=10),
                status="UPCOMING",
                venue="Main Campus Seminar Hall"
            )
            db.add(drive)
            db.flush()

        # 10. Opportunities
        opp_google = db.query(Opportunity).filter_by(title="Software Engineer - Python/React").first()
        if not opp_google:
            opp_google = Opportunity(
                companyId=google.id,
                driveId=drive.id,
                title="Software Engineer - Python/React",
                description="Join Google engineering team to build scalable cloud features using Python and React.",
                type="JOB",
                roleType="FULL_TIME",
                location="Bangalore",
                compensation="22 LPA",
                minCgpa=8.0,
                maxBacklogs=0,
                status="OPEN",
                deadline=datetime.utcnow() + timedelta(days=4)
            )
            db.add(opp_google)
            db.flush()
            # Rules & Skills
            db.add(EligibilityRule(opportunityId=opp_google.id, ruleType="MIN_CGPA", ruleValue="8.0"))
            db.add(EligibilityRule(opportunityId=opp_google.id, ruleType="MAX_BACKLOGS", ruleValue="0"))
            db.add(OpportunitySkill(opportunityId=opp_google.id, skillId=skills["Python"].id, isRequired=True))
            db.add(OpportunitySkill(opportunityId=opp_google.id, skillId=skills["React"].id, isRequired=True))
            db.add(OpportunitySkill(opportunityId=opp_google.id, skillId=skills["SQL"].id, isRequired=False))

        opp_startup = db.query(Opportunity).filter_by(title="Junior Developer - Java").first()
        if not opp_startup:
            opp_startup = Opportunity(
                companyId=startup.id,
                title="Junior Developer - Java",
                description="Entry level developers needed for Java payment gateway team.",
                type="JOB",
                roleType="FULL_TIME",
                location="Hyderabad",
                compensation="8 LPA",
                minCgpa=6.0,
                maxBacklogs=2,
                status="OPEN",
                deadline=datetime.utcnow() + timedelta(days=6)
            )
            db.add(opp_startup)
            db.flush()
            db.add(EligibilityRule(opportunityId=opp_startup.id, ruleType="MIN_CGPA", ruleValue="6.0"))
            db.add(OpportunitySkill(opportunityId=opp_startup.id, skillId=skills["Java"].id, isRequired=True))

        # 11. Evaluate and Persist Matches for all students & opportunities
        for student in [student_a, student_b, student_c]:
            for opp in [opp_google, opp_startup]:
                elig = EligibilityService.evaluate(db, student, opp)
                EligibilityService.persist_evaluation(db, student.id, opp.id, elig)

                match = CareerMatchingService.compute_match(db, student, opp)
                CareerMatchingService.persist_match(db, student.id, opp.id, match)

                SkillGapService.analyze(db, student, opp)

        # 12. Create applications, interview rounds, offers
        # Student A applying to Google
        app_google = db.query(JobApplication).filter_by(opportunityId=opp_google.id, studentId=student_a.id).first()
        if not app_google:
            res_v = db.query(ResumeVersion).join(ResumeProfile).filter(ResumeProfile.studentId == student_a.id).first()
            app_google = JobApplication(
                opportunityId=opp_google.id,
                studentId=student_a.id,
                resumeVersionId=res_v.id if res_v else None,
                status="SHORTLISTED",
                coverLetter="I am highly passionate about cloud systems."
            )
            db.add(app_google)
            db.flush()
            db.add(ApplicationStatusHistory(applicationId=app_google.id, status="APPLIED", notes="Initial application", changedById=student_a.id))
            db.add(ApplicationStatusHistory(applicationId=app_google.id, status="SHORTLISTED", notes="Resume selected", changedById=officer.id))
            db.flush()

            # Interview round
            ir = InterviewRound(
                applicationId=app_google.id,
                roundNumber=1,
                title="Technical Coding Round",
                type="CODING",
                status="SCHEDULED",
                result="PENDING",
                scheduledAt=datetime.utcnow() + timedelta(days=2),
                location="Google Meet",
                interviewerNames="John Doe"
            )
            db.add(ir)
            db.flush()

        # Student B applying to Startup Corp
        app_startup = db.query(JobApplication).filter_by(opportunityId=opp_startup.id, studentId=student_b.id).first()
        if not app_startup:
            res_v = db.query(ResumeVersion).join(ResumeProfile).filter(ResumeProfile.studentId == student_b.id).first()
            app_startup = JobApplication(
                opportunityId=opp_startup.id,
                studentId=student_b.id,
                resumeVersionId=res_v.id if res_v else None,
                status="APPLIED"
            )
            db.add(app_startup)
            db.flush()
            db.add(ApplicationStatusHistory(applicationId=app_startup.id, status="APPLIED", notes="Initial application", changedById=student_b.id))
            db.flush()

        # Seed recommendations
        for student in [student_a, student_b, student_c]:
            PlacementRecommendationService.upsert_recommendations(db, student.id)

        db.commit()
        print("Placement & Career Intelligence seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print("\n[SEED ERROR] Transaction rolled back.")
        print("Reason:", str(e))
    finally:
        db.close()

if __name__ == "__main__":
    run_placement_seeder()
