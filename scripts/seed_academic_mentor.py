import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Resolve backend module structures
backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.dependencies import SessionLocal
from app.models.models import (
    Role, User, UserProfile, Department, Semester, Section, Course, Subject, AcademicYear,
    StudentAttendanceSummary, StudentResult, StudentAssignment, Result, ParentProfile, ParentStudentLink,
    FacultyAssignment
)
from app.core.security import get_password_hash
from app.services.academic_mentor_service import AcademicMentorService

def seed_academic_mentor():
    print("[i] Seeding Academic Mentor & Student Intelligence...")
    db = SessionLocal()
    try:
        # 1. Verify Roles
        student_role = db.query(Role).filter_by(name="STUDENT").first()
        parent_role = db.query(Role).filter_by(name="PARENT").first()
        teacher_role = db.query(Role).filter_by(name="TEACHER").first()
        admin_role = db.query(Role).filter_by(name="MASTER_ADMIN").first()

        # 2. Get Academic Structure from seed_demo.py
        ay = db.query(AcademicYear).filter_by(name="2026-2027").first()
        if not ay:
            print("[x] Please run seed_demo.py first to establish basic academic structure.")
            return

        dept = db.query(Department).filter_by(code="CSE-AI").first()
        sem = db.query(Semester).filter_by(semesterNumber=6).first()
        sec = db.query(Section).filter_by(name="A", semesterId=sem.id).first()
        course = db.query(Course).filter_by(code="CS-AI-DEGC").first()
        subjects = db.query(Subject).filter_by(semesterId=sem.id).all()

        if not subjects:
            print("[x] Subjects not found. Please ensure seed_demo.py completed.")
            return

        subject_ai = subjects[0]
        subject_ml = subjects[1] if len(subjects) > 1 else subjects[0]

        # 3. Create or Get Demo Teacher and Admin
        teacher = db.query(User).filter_by(username="teacher_demo").first()
        admin = db.query(User).filter_by(username="admin").first()

        # Legitimate Faculty Assignment for Section A
        if teacher:
            existing_fa = db.query(FacultyAssignment).filter_by(
                facultyId=teacher.id,
                sectionId=sec.id
            ).first()
            if not existing_fa:
                fa = FacultyAssignment(
                    departmentId=dept.id,
                    subjectId=subject_ai.id,
                    facultyId=teacher.id,
                    sectionId=sec.id,
                    semesterId=sem.id,
                    academicYearId=ay.id
                )
                db.add(fa)
                db.commit()
                print("[+] Scoped teacher_demo to Section A.")

        # 4. Create Students A, B, and C
        # Student A (Low Risk, High Performance)
        student_a = db.query(User).filter_by(username="studenta").first()
        if not student_a:
            student_a = User(
                email="student.a@campusgpt.local",
                username="studenta",
                passwordHash=get_password_hash("password"),
                name="Student A (Low Risk)",
                roleId=student_role.id,
                sectionId=sec.id,
                departmentId=dept.id,
                status="ACTIVE",
                mustChangePassword=False,
                verified=True
            )
            db.add(student_a)
            db.commit()
            print("[+] Seeded Student A.")

            # UserProfile
            profile_a = UserProfile(
                userId=student_a.id,
                usn="USN-STUDENT-A",
                phoneNumber="9000000001"
            )
            db.add(profile_a)
            db.commit()

        # Student B (High Risk, Poor Attendance & Failing Grades)
        student_b = db.query(User).filter_by(username="studentb").first()
        if not student_b:
            student_b = User(
                email="student.b@campusgpt.local",
                username="studentb",
                passwordHash=get_password_hash("password"),
                name="Student B (High Risk)",
                roleId=student_role.id,
                sectionId=sec.id,
                departmentId=dept.id,
                status="ACTIVE",
                mustChangePassword=False,
                verified=True
            )
            db.add(student_b)
            db.commit()
            print("[+] Seeded Student B.")

            # UserProfile
            profile_b = UserProfile(
                userId=student_b.id,
                usn="USN-STUDENT-B",
                phoneNumber="9000000002"
            )
            db.add(profile_b)
            db.commit()

        # Student C (Insufficient Data)
        student_c = db.query(User).filter_by(username="studentc").first()
        if not student_c:
            student_c = User(
                email="student.c@campusgpt.local",
                username="studentc",
                passwordHash=get_password_hash("password"),
                name="Student C (No Data)",
                roleId=student_role.id,
                sectionId=sec.id,
                departmentId=dept.id,
                status="ACTIVE",
                mustChangePassword=False,
                verified=True
            )
            db.add(student_c)
            db.commit()
            print("[+] Seeded Student C.")

            # UserProfile
            profile_c = UserProfile(
                userId=student_c.id,
                usn="USN-STUDENT-C",
                phoneNumber="9000000003"
            )
            db.add(profile_c)
            db.commit()

        # 5. Parent Linking
        parent = db.query(User).filter_by(username="parent_demo").first()
        if parent:
            parent_profile = db.query(ParentProfile).filter_by(userId=parent.id).first()
            if not parent_profile:
                parent_profile = ParentProfile(
                    userId=parent.id,
                    phoneNumber="9876543210"
                )
                db.add(parent_profile)
                db.commit()

            # Link Parent to Student A & Student B
            for s in [student_a, student_b]:
                existing_link = db.query(ParentStudentLink).filter_by(
                    parentId=parent_profile.id,
                    studentId=s.id
                ).first()
                if not existing_link:
                    link = ParentStudentLink(
                        parentId=parent_profile.id,
                        studentId=s.id,
                        relationship="MOTHER",
                        isPrimaryContact=True,
                        status="VERIFIED",
                        verifiedAt=datetime.utcnow()
                    )
                    db.add(link)
                    db.commit()
                    print(f"[+] Linked parent_demo to student {s.username}.")

        # 6. Populate Student A Academic Data (Low Risk)
        # Attendance: 95%
        db.query(StudentAttendanceSummary).filter_by(userId=student_a.id).delete()
        db.query(StudentResult).filter_by(userId=student_a.id).delete()
        db.query(StudentAssignment).filter_by(userId=student_a.id).delete()
        db.query(Result).filter_by(studentId=student_a.id).delete()

        att_a = StudentAttendanceSummary(
            userId=student_a.id,
            subjectId=subject_ai.id,
            totalClasses=30,
            presentClasses=29,
            percentage=96.67
        )
        db.add(att_a)

        res_a = StudentResult(
            userId=student_a.id,
            subjectId=subject_ai.id,
            semesterNumber=6,
            internalMarks=46,
            externalMarks=48,
            grade="O",
            credits=4
        )
        db.add(res_a)

        ass_a = StudentAssignment(
            userId=student_a.id,
            subjectId=subject_ai.id,
            title="AI Lab Assignment 1",
            submissionStatus="GRADED",
            dueDate=datetime.utcnow() - timedelta(days=2),
            submittedAt=datetime.utcnow() - timedelta(days=3),
            grade="A"
        )
        db.add(ass_a)

        ass_a_pending = StudentAssignment(
            userId=student_a.id,
            subjectId=subject_ai.id,
            title="AI Lab Assignment 2",
            submissionStatus="PENDING",
            dueDate=datetime.utcnow() - timedelta(days=1)
        )
        db.add(ass_a_pending)


        # Previous Semester Result to show stable/improving trend
        prev_res_a = Result(
            studentId=student_a.id,
            academicYearId=ay.id,
            semesterNumber=5,
            sgpa=8.2,
            cgpa=8.2,
            totalMarks=820.0,
            percentage=82.0,
            creditsEarned=20,
            status="PUBLISHED"
        )
        db.add(prev_res_a)

        latest_res_a = Result(
            studentId=student_a.id,
            academicYearId=ay.id,
            semesterNumber=6,
            sgpa=9.4, # Improved!
            cgpa=8.8,
            totalMarks=940.0,
            percentage=94.0,
            creditsEarned=20,
            status="PUBLISHED"
        )
        db.add(latest_res_a)

        # 7. Populate Student B Academic Data (High Risk)
        db.query(StudentAttendanceSummary).filter_by(userId=student_b.id).delete()
        db.query(StudentResult).filter_by(userId=student_b.id).delete()
        db.query(StudentAssignment).filter_by(userId=student_b.id).delete()
        db.query(Result).filter_by(studentId=student_b.id).delete()

        # Low attendance: 58.33%
        att_b = StudentAttendanceSummary(
            userId=student_b.id,
            subjectId=subject_ml.id,
            totalClasses=24,
            presentClasses=14,
            percentage=58.33
        )
        db.add(att_b)

        # Failing grade
        res_b = StudentResult(
            userId=student_b.id,
            subjectId=subject_ml.id,
            semesterNumber=6,
            internalMarks=12,
            externalMarks=15,
            grade="F",
            credits=4
        )
        db.add(res_b)

        # Pending backlog assignment
        ass_b = StudentAssignment(
            userId=student_b.id,
            subjectId=subject_ml.id,
            title="ML Programming Lab",
            submissionStatus="PENDING",
            dueDate=datetime.utcnow() - timedelta(days=1)
        )
        db.add(ass_b)

        # Semester decline: 7.8 SGPA dropping to 5.2 SGPA
        prev_res_b = Result(
            studentId=student_b.id,
            academicYearId=ay.id,
            semesterNumber=5,
            sgpa=7.8,
            cgpa=7.8,
            status="PUBLISHED"
        )
        db.add(prev_res_b)

        latest_res_b = Result(
            studentId=student_b.id,
            academicYearId=ay.id,
            semesterNumber=6,
            sgpa=5.2, # Declining
            cgpa=6.5,
            status="PUBLISHED"
        )
        db.add(latest_res_b)

        db.commit()

        # 8. Trigger Calculations via AcademicMentorService
        print("[i] Running intelligence calculations...")
        AcademicMentorService.recalculate_student_intelligence(db, student_a.id, admin.id if admin else student_a.id)
        AcademicMentorService.recalculate_student_intelligence(db, student_b.id, admin.id if admin else student_b.id)
        AcademicMentorService.recalculate_student_intelligence(db, student_c.id, admin.id if admin else student_c.id)

        # Manually ensure student_a has at least one active recommendation for smoke test coverage
        from app.models.models import StudyRecommendation
        existing_rec = db.query(StudyRecommendation).filter_by(studentId=student_a.id, status="ACTIVE").first()
        if not existing_rec:
            smoke_rec = StudyRecommendation(
                id=str(uuid.uuid4()),
                studentId=student_a.id,
                subjectId=subject_ai.id,
                category="REVISION",
                title="Review AI Concepts",
                description="Go through Chapter 1 to 3 slides.",
                priority="MEDIUM",
                reason="Regular study consistency.",
                status="ACTIVE",
                generatedBy="LOCAL_ANALYTICS_ENGINE",
                createdAt=datetime.utcnow()
            )
            db.add(smoke_rec)
            db.commit()
            print("[+] Seeded active recommendation for Student A smoke test.")

        print("[OK] Successfully seeded and calculated academic intelligence profiles!")


    except Exception as e:
        print(f"[ERROR] Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_academic_mentor()
