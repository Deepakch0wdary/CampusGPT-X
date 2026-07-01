import pytest
import uuid
from datetime import datetime, timedelta
from app.models.models import User, Role, Subject, Department, Course, Semester, AcademicYear, Program, Section, AttendanceSession, AttendanceRecord, AttendanceCorrection, StudentAttendanceSummary, DefaulterList

def get_auth_headers(client, username, password):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_users(db_session):
    role_admin = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    role_teacher = db_session.query(Role).filter_by(name="TEACHER").first()
    role_student = db_session.query(Role).filter_by(name="STUDENT").first()
    
    from app.core.security import get_password_hash
    hashed = get_password_hash("AdminPassword@123")
    
    admin = User(
        id="admin-att-uuid",
        email="admin.att@campusgpt.edu",
        username="adminatt",
        passwordHash=hashed,
        roleId=role_admin.id,
        name="Admin Att",
        mustChangePassword=False
    )
    teacher = User(
        id="teacher-att-uuid",
        email="teacher.att@campusgpt.edu",
        username="teacheratt",
        passwordHash=hashed,
        roleId=role_teacher.id,
        name="Teacher Att",
        mustChangePassword=False
    )
    student = User(
        id="student-att-uuid",
        email="student.att@campusgpt.edu",
        username="studentatt",
        passwordHash=hashed,
        roleId=role_student.id,
        name="Student Att",
        mustChangePassword=False
    )
    
    db_session.add_all([admin, teacher, student])
    db_session.commit()
    return {"admin": admin, "teacher": teacher, "student": student}

@pytest.fixture
def test_roster_setup(db_session, test_users):
    dept = Department(id="dept-att", name="Mechanical Eng", code="MECH")
    prog = Program(id="prog-att", name="B.Tech", code="BTECH-ME", departmentId=dept.id)
    course = Course(id="course-att", name="Mech Eng", code="ME", credits=120, duration="4 Years", departmentId=dept.id, programId=prog.id)
    ay = AcademicYear(id="ay-att", name="2026-27-ATT", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365))
    sem = Semester(id="sem-att", semesterNumber=1, academicYearId=ay.id, programId=prog.id, startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=120))
    subj = Subject(id="subj-att", code="ME101", name="Thermodynamics", credits=4, departmentId=dept.id, semesterId=sem.id, courseId=course.id)
    sect = Section(id="sect-att", name="ME-Section A", capacity=60, semesterId=sem.id, departmentId=dept.id, programId=prog.id, academicYearId=ay.id)
    
    # Assign student to section
    student = db_session.query(User).filter_by(id=test_users["student"].id).first()
    student.sectionId = sect.id
    
    db_session.add_all([dept, prog, course, ay, sem, subj, sect])
    db_session.commit()
    return {
        "ay": ay,
        "dept": dept,
        "prog": prog,
        "sem": sem,
        "subj": subj,
        "sect": sect
    }

def test_attendance_session_creation(client, test_users, test_roster_setup):
    headers = get_auth_headers(client, "teacheratt", "AdminPassword@123")
    payload = {
        "academicYearId": test_roster_setup["ay"].id,
        "departmentId": test_roster_setup["dept"].id,
        "programId": test_roster_setup["prog"].id,
        "semesterId": test_roster_setup["sem"].id,
        "sectionId": test_roster_setup["sect"].id,
        "subjectId": test_roster_setup["subj"].id,
        "date": datetime.utcnow().isoformat()
    }
    res = client.post("/api/v1/attendance/session", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

def test_marking_attendance_and_defaulter_calculation(client, test_users, test_roster_setup, db_session):
    headers = get_auth_headers(client, "teacheratt", "AdminPassword@123")
    
    # 1. Create session
    sess = AttendanceSession(
        id="att-sess-1",
        academicYearId=test_roster_setup["ay"].id,
        departmentId=test_roster_setup["dept"].id,
        programId=test_roster_setup["prog"].id,
        semesterId=test_roster_setup["sem"].id,
        sectionId=test_roster_setup["sect"].id,
        subjectId=test_roster_setup["subj"].id,
        date=datetime.utcnow(),
        status="ACTIVE",
        facultyId=test_users["teacher"].id
    )
    db_session.add(sess)
    db_session.commit()
    
    # 2. Batch mark student absent to trigger defaulter logic (< 75%)
    payload = {
        "records": [
            {"studentId": test_users["student"].id, "status": "ABSENT"}
        ],
        "finalize": True,
        "reason": "Cold and flu."
    }
    res = client.post(f"/api/v1/attendance/session/{sess.id}/records", json=payload, headers=headers)
    assert res.status_code == 200
    
    # 3. Verify StudentAttendanceSummary has 0%
    summary = db_session.query(StudentAttendanceSummary).filter_by(userId=test_users["student"].id, subjectId=test_roster_setup["subj"].id).first()
    assert summary is not None
    assert summary.percentage == 0.0
    
    # 4. Verify Student is added to DefaulterList
    defaulter = db_session.query(DefaulterList).filter_by(studentId=test_users["student"].id, subjectId=test_roster_setup["subj"].id).first()
    assert defaulter is not None
    assert defaulter.category == "BELOW_50"

def test_attendance_correction_workflow(client, test_users, test_roster_setup, db_session):
    # Setup record
    sess = AttendanceSession(id="att-sess-2", academicYearId=test_roster_setup["ay"].id, departmentId=test_roster_setup["dept"].id, programId=test_roster_setup["prog"].id, semesterId=test_roster_setup["sem"].id, sectionId=test_roster_setup["sect"].id, subjectId=test_roster_setup["subj"].id, date=datetime.utcnow(), status="CLOSED", facultyId=test_users["teacher"].id)
    rec = AttendanceRecord(id="att-rec-2", sessionId=sess.id, studentId=test_users["student"].id, status="ABSENT")
    db_session.add_all([sess, rec])
    db_session.commit()
    
    # 1. Student requests correction
    headers_stud = get_auth_headers(client, "studentatt", "AdminPassword@123")
    payload_corr = {
        "recordId": rec.id,
        "requestedStatus": "PRESENT",
        "reason": "Was present but marked absent by mistake."
    }
    res_corr = client.post("/api/v1/attendance/corrections", json=payload_corr, headers=headers_stud)
    assert res_corr.status_code == 200
    
    corr_req = db_session.query(AttendanceCorrection).filter_by(recordId=rec.id).first()
    assert corr_req is not None
    
    # 2. Teacher reviews and approves correction
    headers_teach = get_auth_headers(client, "teacheratt", "AdminPassword@123")
    payload_rev = {
        "status": "APPROVED",
        "comments": "Correction verified and resolved."
    }
    res_rev = client.post(f"/api/v1/attendance/corrections/{corr_req.id}/review", json=payload_rev, headers=headers_teach)
    assert res_rev.status_code == 200
    
    # 3. Verify record status is updated to PRESENT
    db_session.refresh(rec)
    assert rec.status == "PRESENT"
    
    # 4. Verify summary is updated to 100%
    summary = db_session.query(StudentAttendanceSummary).filter_by(userId=test_users["student"].id, subjectId=test_roster_setup["subj"].id).first()
    assert summary.percentage == 100.0
    
    # 5. Verify student is removed from DefaulterList
    defaulter = db_session.query(DefaulterList).filter_by(studentId=test_users["student"].id, subjectId=test_roster_setup["subj"].id).first()
    assert defaulter is None
