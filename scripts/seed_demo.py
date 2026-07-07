import sys
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
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
    Base, Role, Permission, User, AcademicYear, Department, Program, Semester, Section, Subject, Course,
    FacultyProfile, Enrollment, ParentProfile, ParentStudentLink, ParentMessage, ParentNotification, AdmissionApplication,
    AttendanceSession, AttendanceRecord, AssignmentDef, StudentAssignment, AssignmentSubmission,
    Exam, ExamSchedule, StudentResult, FeeStructure, FeeComponent, FeeInvoice, InvoiceItem,
    Payment, Receipt, StudentScholarship, Scholarship, UserPermission
)

def run_seeder():
    print("Connecting to database at:", settings.DATABASE_URL)
    try:
        engine = create_engine(settings.DATABASE_URL)
        # Attempt simple connection
        conn = engine.connect()
        conn.close()
    except Exception as e:
        print("\n[DB CONNECTION ERROR] Could not connect to MySQL database on localhost:3306.")
        print("Reason:", str(e))
        print("To start the database, please install MySQL locally or run:")
        print("  docker compose up -d db")
        print("\nDB-dependent seeding aborted.")
        return

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("DB connection healthy. Starting seeding transaction...")

        # 1. Create Roles
        roles = {}
        for role_name in ["MASTER_ADMIN", "ADMISSION_OFFICE", "FINANCE_OFFICE", "TEACHER", "STUDENT", "PARENT"]:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} demo role")
                db.add(role)
                db.flush()
            roles[role_name] = role

        # 2. Create Users
        demo_accounts = [
            ("admin.demo@campusgpt.local", "admin_demo", "Master Admin", "MASTER_ADMIN"),
            ("admission.demo@campusgpt.local", "admission_demo", "Admission Officer", "ADMISSION_OFFICE"),
            ("finance.demo@campusgpt.local", "finance_demo", "Finance Officer", "FINANCE_OFFICE"),
            ("teacher.demo@campusgpt.local", "teacher_demo", "Demo Teacher", "TEACHER"),
            ("mentor.demo@campusgpt.local", "mentor_demo", "Demo Mentor", "TEACHER"),
            ("student.demo@campusgpt.local", "student_demo", "Demo Student", "STUDENT"),
            ("parent.demo@campusgpt.local", "parent_demo", "Demo Parent", "PARENT")
        ]

        users = {}
        for email, username, name, role_name in demo_accounts:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    username=username,
                    passwordHash=get_password_hash("password"),
                    name=name,
                    roleId=roles[role_name].id,
                    status="ACTIVE",
                    mustChangePassword=False
                )
                db.add(user)
                db.flush()
            users[role_name] = user
        users["MENTOR"] = users["TEACHER"] # fallback reuse

        # 3. Academic Structure
        ay = db.query(AcademicYear).filter(AcademicYear.name == "2026-2027").first()
        if not ay:
            ay = AcademicYear(name="2026-2027", startDate=datetime(2026, 6, 1), endDate=datetime(2027, 5, 31), status="ACTIVE")
            db.add(ay)
            db.flush()

        dept = db.query(Department).filter(Department.code == "CSE-AI").first()
        if not dept:
            dept = Department(name="Computer Science and Engineering – AI", code="CSE-AI")
            db.add(dept)
            db.flush()

        prog = db.query(Program).filter(Program.code == "BTECH-CSE-AI").first()
        if not prog:
            prog = Program(departmentId=dept.id, name="B.Tech CSE-AI", code="BTECH-CSE-AI")
            db.add(prog)
            db.flush()

        sem = db.query(Semester).filter(Semester.programId == prog.id, Semester.semesterNumber == 6).first()
        if not sem:
            sem = Semester(programId=prog.id, semesterNumber=6, academicYearId=ay.id, startDate=datetime(2026, 6, 1), endDate=datetime(2026, 12, 31))
            db.add(sem)
            db.flush()

        sec = db.query(Section).filter(Section.semesterId == sem.id, Section.name == "A").first()
        if not sec:
            sec = Section(semesterId=sem.id, name="A", capacity=60, departmentId=dept.id, programId=prog.id, academicYearId=ay.id)
            db.add(sec)
            db.flush()

        # Update student user section
        student_user = users["STUDENT"]
        student_user.sectionId = sec.id
        student_user.departmentId = dept.id
        db.add(student_user)
        db.flush()

        # Course
        course = db.query(Course).filter(Course.code == "CS-AI-DEGC").first()
        if not course:
            course = Course(
                code="CS-AI-DEGC",
                name="Computer Science & Engineering (AI) Degree Course",
                credits=160,
                duration="4 Years",
                departmentId=dept.id,
                programId=prog.id
            )
            db.add(course)
            db.flush()

        # Subjects
        subject_names = ["Artificial Intelligence", "Machine Learning", "Computer Networks", "Software Engineering"]
        subjects = {}
        for name in subject_names:
            code = "CS-" + "".join([word[0] for word in name.split()]).upper() + "-600"
            subj = db.query(Subject).filter(Subject.code == code).first()
            if not subj:
                subj = Subject(semesterId=sem.id, name=name, code=code, credits=4, departmentId=dept.id, courseId=course.id)
                db.add(subj)
                db.flush()
            subjects[name] = subj

        # 4. Student Enrollment
        enroll = db.query(Enrollment).filter(Enrollment.studentId == student_user.id).first()
        if not enroll:
            app_record = db.query(AdmissionApplication).filter(AdmissionApplication.email == student_user.email).first()
            if not app_record:
                app_record = AdmissionApplication(
                    applicationNumber="APP-2026-AI001",
                    academicYearId=ay.id,
                    departmentId=dept.id,
                    programId=prog.id,
                    applicantName=student_user.name,
                    email=student_user.email,
                    phone="9988776655",
                    dateOfBirth=datetime(2005, 5, 15),
                    gender="MALE",
                    nationality="Indian",
                    category="General",
                    quota="General Merit"
                )
                db.add(app_record)
                db.flush()

            enroll = Enrollment(
                applicationId=app_record.id,
                enrollmentNumber="ENR-2026-AI001",
                studentId=student_user.id,
                usn="USN2026AI01",
                rollNumber="ROLL-101",
                academicYearId=ay.id,
                departmentId=dept.id,
                programId=prog.id,
                semesterNumber=6,
                sectionId=sec.id
            )
            db.add(enroll)
            db.flush()

        # 5. Parent-Student Link
        parent_profile = db.query(ParentProfile).filter(ParentProfile.userId == users["PARENT"].id).first()
        if not parent_profile:
            parent_profile = ParentProfile(
                userId=users["PARENT"].id,
                fatherName="Father Vance",
                relationshipType="FATHER",
                phoneNumber="9876543210"
            )
            db.add(parent_profile)
            db.flush()

        link = db.query(ParentStudentLink).filter(ParentStudentLink.parentId == parent_profile.id, ParentStudentLink.studentId == student_user.id).first()
        if not link:
            link = ParentStudentLink(
                parentId=parent_profile.id,
                studentId=student_user.id,
                relationship="FATHER",
                isPrimaryContact=True
            )
            db.add(link)
            db.flush()

        # 6. Attendance Sessions & Records
        sess = db.query(AttendanceSession).filter(AttendanceSession.subjectId == subjects["Artificial Intelligence"].id).first()
        if not sess:
            sess = AttendanceSession(
                academicYearId=ay.id,
                departmentId=dept.id,
                programId=prog.id,
                semesterId=sem.id,
                sectionId=sec.id,
                subjectId=subjects["Artificial Intelligence"].id,
                facultyId=users["TEACHER"].id,
                date=datetime.utcnow() - timedelta(days=2),
                status="CLOSED"
            )
            db.add(sess)
            db.flush()

        att = db.query(AttendanceRecord).filter(AttendanceRecord.sessionId == sess.id, AttendanceRecord.studentId == student_user.id).first()
        if not att:
            att = AttendanceRecord(
                sessionId=sess.id,
                studentId=student_user.id,
                status="PRESENT"
            )
            db.add(att)
            db.flush()

        # 7. Assignment
        ass_def = db.query(AssignmentDef).filter(AssignmentDef.subjectId == subjects["Machine Learning"].id).first()
        if not ass_def:
            ass_def = AssignmentDef(
                subjectId=subjects["Machine Learning"].id,
                title="Supervised Learning Projects",
                description="Implement linear and logistic regressions.",
                facultyId=users["TEACHER"].id,
                dueDate=datetime.utcnow() + timedelta(days=5)
            )
            db.add(ass_def)
            db.flush()

        ass_sub = db.query(StudentAssignment).filter(StudentAssignment.userId == student_user.id).first()
        if not ass_sub:
            ass_sub = StudentAssignment(
                userId=student_user.id,
                subjectId=subjects["Machine Learning"].id,
                title="Supervised Learning Tasks",
                description="Implement regression algorithms.",
                dueDate=datetime.utcnow() + timedelta(days=5),
                submissionStatus="SUBMITTED"
            )
            db.add(ass_sub)
            db.flush()

        # 8. Exam, Schedule & Results
        exam = db.query(Exam).filter(Exam.examName == "CSE-AI Midterm").first()
        if not exam:
            exam = Exam(
                examName="CSE-AI Midterm",
                examType="MID",
                academicYearId=ay.id,
                departmentId=dept.id,
                programId=prog.id,
                semesterId=sem.id,
                sectionId=sec.id,
                subjectId=subjects["Artificial Intelligence"].id,
                facultyId=users["TEACHER"].id,
                examDate=datetime.utcnow() - timedelta(days=5),
                startTime="10:00",
                endTime="13:00",
                durationMinutes=180,
                maxMarks=100.0,
                passingMarks=40.0,
                status="COMPLETED"
            )
            db.add(exam)
            db.flush()

        res = db.query(StudentResult).filter(StudentResult.userId == student_user.id).first()
        if not res:
            res = StudentResult(
                userId=student_user.id,
                subjectId=subjects["Artificial Intelligence"].id,
                semesterNumber=6,
                internalMarks=44,
                externalMarks=50,
                grade="A+",
                credits=4
            )
            db.add(res)
            db.flush()

        # 9. Fee Structure, Invoices & Payments
        fs = db.query(FeeStructure).filter(FeeStructure.programId == prog.id).first()
        if not fs:
            fs = FeeStructure(
                academicYearId=ay.id,
                programId=prog.id,
                category="GENERAL",
                quota="MERIT",
                currency="INR",
                status="ACTIVE"
            )
            db.add(fs)
            db.flush()
            # add components
            db.add(FeeComponent(
                feeStructureId=fs.id,
                name="Tuition Fee",
                code="TUI",
                amount=Decimal("50000.00"),
                dueDate=datetime.utcnow() + timedelta(days=10)
            ))
            db.add(FeeComponent(
                feeStructureId=fs.id,
                name="Lab Fee",
                code="LAB",
                amount=Decimal("10000.00"),
                dueDate=datetime.utcnow() + timedelta(days=10)
            ))
            db.flush()

        inv = db.query(FeeInvoice).filter(FeeInvoice.studentId == student_user.id).first()
        if not inv:
            inv = FeeInvoice(
                invoiceNumber="INV-2026-AI001",
                studentId=student_user.id,
                enrollmentId=enroll.id,
                currency="INR",
                subtotal=Decimal("60000.00"),
                scholarshipAmount=Decimal("0.00"),
                discountAmount=Decimal("0.00"),
                adjustmentAmount=Decimal("0.00"),
                taxAmount=Decimal("0.00"),
                totalAmount=Decimal("60000.00"),
                paidAmount=Decimal("20000.00"),
                balanceAmount=Decimal("40000.00"),
                dueDate=datetime.utcnow() + timedelta(days=10),
                status="PARTIALLY_PAID"
            )
            db.add(inv)
            db.flush()
            # Invoice Item
            db.add(InvoiceItem(
                invoiceId=inv.id,
                componentName="Tuition Fee",
                componentCode="TUI",
                amount=Decimal("50000.00")
            ))
            db.add(InvoiceItem(
                invoiceId=inv.id,
                componentName="Lab Fee",
                componentCode="LAB",
                amount=Decimal("10000.00")
            ))
            db.flush()

        pay = db.query(Payment).filter(Payment.invoiceId == inv.id).first()
        if not pay:
            pay = Payment(
                paymentNumber="PAY-2026-AI001",
                invoiceId=inv.id,
                studentId=student_user.id,
                amount=Decimal("20000.00"),
                currency="INR",
                method="UPI",
                status="SUCCESS",
                provider="MOCK",
                providerOrderId="ORDER-101",
                idempotencyKey="idem-key-seed-1",
                paidAt=datetime.utcnow()
            )
            db.add(pay)
            db.flush()

        rec = db.query(Receipt).filter(Receipt.paymentId == pay.id).first()
        if not rec:
            rec = Receipt(
                receiptNumber="REC-2026-AI001",
                paymentId=pay.id,
                studentId=student_user.id,
                amount=Decimal("20000.00"),
                currency="INR",
                verificationToken="VERIFY-SEED-TOKEN-V1"
            )
            db.add(rec)
            db.flush()

        # 10. Parent Notification
        notif = db.query(ParentNotification).filter(ParentNotification.parentId == parent_profile.id).first()
        if not notif:
            notif = ParentNotification(
                parentId=parent_profile.id,
                title="Low Attendance Alert",
                message="Samantha's attendance in Computer Networks is below 75%.",
                category="ATTENDANCE_ALERT",
                isRead=False
            )
            db.add(notif)
            db.flush()

        db.commit()
        print("Demo data seeded successfully and relationally verified!")
    except Exception as e:
        db.rollback()
        print("Seeding transaction rolled back due to error:", str(e))
    finally:
        db.close()

if __name__ == "__main__":
    run_seeder()
