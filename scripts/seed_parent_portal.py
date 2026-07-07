import os
import sys
from datetime import datetime, timedelta
import uuid

# Set up backend path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import (
    User, Role, ParentProfile, ParentStudentLink, ParentTeacherMeeting,
    ParentConsent, ParentNotificationPreference, Subject, AcademicYear, Semester, Course, Result, ResultDetail, Department, Program
)
from app.core.security import get_password_hash

def seed():
    database_url = "sqlite:///c:/Users/DELL/OneDrive/Desktop/CampusGPT/apps/backend/campusgpt.db"
    print(f"Connecting to database at: {database_url}")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Fetch Roles
        parent_role = db.query(Role).filter_by(name="PARENT").first()
        student_role = db.query(Role).filter_by(name="STUDENT").first()
        teacher_role = db.query(Role).filter_by(name="TEACHER").first()

        if not parent_role or not student_role or not teacher_role:
            print("ERROR: Basic roles (PARENT/STUDENT/TEACHER) not found. Run init_sqlite.py first.")
            return

        # 2. Get or create a teacher user for meeting scheduler reference
        teacher_user = db.query(User).filter_by(username="teacher_demo").first()
        if not teacher_user:
            teacher_user = User(
                id=str(uuid.uuid4()),
                email="teacher_demo@campusgpt.com",
                username="teacher_demo",
                passwordHash=get_password_hash("Password123"),
                name="Prof. Sarah Jenkins",
                roleId=teacher_role.id,
                mustChangePassword=False
            )
            db.add(teacher_user)
            db.commit()
            print(f"Created teacher: {teacher_user.username}")

        # 3. Find some existing student to link
        student = db.query(User).filter_by(roleId=student_role.id).first()
        if not student:
            # Create a mock student if none exist
            student = User(
                id=str(uuid.uuid4()),
                email="student_demo@campusgpt.com",
                username="student_demo",
                passwordHash=get_password_hash("Password123"),
                name="Alex Cooper",
                roleId=student_role.id,
                mustChangePassword=False
            )
            db.add(student)
            db.commit()
            print(f"Created student: {student.username}")

        # 4. Create Parent User
        parent = db.query(User).filter_by(username="parent_demo").first()
        if not parent:
            parent = User(
                id=str(uuid.uuid4()),
                email="parent@campusgpt.com",
                username="parent_demo",
                passwordHash=get_password_hash("Password123"),
                name="Richard Cooper",
                roleId=parent_role.id,
                mustChangePassword=False
            )
            db.add(parent)
            db.commit()
            print(f"Created parent user: {parent.username}")

        # 5. Create ParentProfile
        profile = db.query(ParentProfile).filter_by(userId=parent.id).first()
        if not profile:
            profile = ParentProfile(
                id=str(uuid.uuid4()),
                userId=parent.id,
                phoneNumber="9876543210",
                guardianName="Richard Cooper"
            )
            db.add(profile)
            db.commit()
            print("Created parent profile.")

        # 6. Link Parent to Student
        link = db.query(ParentStudentLink).filter_by(parentId=profile.id, studentId=student.id).first()
        if not link:
            link = ParentStudentLink(
                parentId=profile.id,
                studentId=student.id,
                relationship="FATHER",
                isPrimaryContact=True,
                status="VERIFIED"
            )
            db.add(link)
            db.commit()
            print(f"Linked parent {parent.name} with student {student.name}")

        # 7. Create preferences if missing
        pref = db.query(ParentNotificationPreference).filter_by(parentProfileId=profile.id).first()
        if not pref:
            pref = ParentNotificationPreference(
                parentProfileId=profile.id,
                attendanceAlerts=True,
                assignmentAlerts=True,
                examAlerts=True,
                resultAlerts=True,
                feeAlerts=True,
                emergencyAlerts=True
            )
            db.add(pref)
            db.commit()
            print("Seeded parent notification preferences.")

        # 8. Seed some mock meetings
        meeting = db.query(ParentTeacherMeeting).filter_by(parentUserId=parent.id).first()
        if not meeting:
            meeting_1 = ParentTeacherMeeting(
                parentUserId=parent.id,
                studentId=student.id,
                teacherUserId=teacher_user.id,
                scheduledAt=datetime.utcnow() + timedelta(days=2),
                durationMinutes=30,
                meetingMode="ONLINE",
                agenda="Discuss mathematics performance review",
                status="APPROVED",
                requestedBy="PARENT"
            )
            meeting_2 = ParentTeacherMeeting(
                parentUserId=parent.id,
                studentId=student.id,
                teacherUserId=teacher_user.id,
                scheduledAt=datetime.utcnow() + timedelta(days=5),
                durationMinutes=30,
                meetingMode="IN_PERSON",
                agenda="Final grade consultation discussion",
                status="REQUESTED",
                requestedBy="PARENT"
            )
            db.add_all([meeting_1, meeting_2])
            db.commit()
            print("Seeded mock PTM meetings.")

        # 9. Seed some mock consents
        consent = db.query(ParentConsent).filter_by(parentUserId=parent.id).first()
        if not consent:
            consent_1 = ParentConsent(
                parentUserId=parent.id,
                studentId=student.id,
                consentType="FIELD_TRIP",
                title="Industrial Visit to Tech Park",
                description="Permission for industrial field trip next month.",
                status="PENDING",
                expiresAt=datetime.utcnow() + timedelta(days=10)
            )
            consent_2 = ParentConsent(
                parentUserId=parent.id,
                studentId=student.id,
                consentType="SPORTS_EVENT",
                title="Annual Track and Field Meet Participation",
                description="Permission to participate in track events.",
                status="APPROVED",
                respondedAt=datetime.utcnow()
            )
            db.add_all([consent_1, consent_2])
            db.commit()
            print("Seeded mock consents.")

        # 10. Seed some mock results if missing
        res_check = db.query(Result).filter_by(studentId=student.id).first()
        if not res_check:
            # Get an academic year
            ay = db.query(AcademicYear).first()
            dept = db.query(Department).first()
            prog = db.query(Program).first()
            sem = db.query(Semester).first()
            course = db.query(Course).first()
            subject = db.query(Subject).first()

            if ay and dept and prog and sem and course and subject:
                # Create a published result
                result = Result(
                    studentId=student.id,
                    academicYearId=ay.id,
                    semesterNumber=sem.semesterNumber,
                    sgpa=8.5,
                    cgpa=8.5,
                    totalMarks=85.0,
                    percentage=85.0,
                    creditsEarned=4,
                    status="PUBLISHED"
                )
                db.add(result)
                db.commit()

                detail = ResultDetail(
                    resultId=result.id,
                    subjectId=subject.id,
                    totalMarks=85.0,
                    grade="A"
                )
                db.add(detail)
                db.commit()
                print("Seeded published academic result card.")

        print("Parent Portal database seeding completed successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
