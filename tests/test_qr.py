import pytest
import uuid
from datetime import datetime, timedelta
from app.models.models import User, Role, Subject, Department, Course, Semester, AcademicYear, Program, Section, AttendanceSession, QRSession, QRCode, DeviceValidation, QRScanLog

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
    role_student1 = db_session.query(Role).filter_by(name="STUDENT").first()
    role_student2 = db_session.query(Role).filter_by(name="STUDENT").first()
    
    from app.core.security import get_password_hash
    hashed = get_password_hash("AdminPassword@123")
    
    admin = User(id="admin-qr-uuid", email="admin.qr@campusgpt.edu", username="adminqr", passwordHash=hashed, roleId=role_admin.id, name="Admin Qr", mustChangePassword=False)
    teacher = User(id="teacher-qr-uuid", email="teacher.qr@campusgpt.edu", username="teacherqr", passwordHash=hashed, roleId=role_teacher.id, name="Teacher Qr", mustChangePassword=False)
    student1 = User(id="student-qr-1", email="student.qr1@campusgpt.edu", username="studentqr1", passwordHash=hashed, roleId=role_student1.id, name="Student Qr1", mustChangePassword=False)
    student2 = User(id="student-qr-2", email="student.qr2@campusgpt.edu", username="studentqr2", passwordHash=hashed, roleId=role_student2.id, name="Student Qr2", mustChangePassword=False)
    
    db_session.add_all([admin, teacher, student1, student2])
    db_session.commit()
    return {"admin": admin, "teacher": teacher, "student1": student1, "student2": student2}

@pytest.fixture
def test_qr_setup(db_session, test_users):
    dept = Department(id="dept-qr", name="Aerospace Eng", code="AERO")
    prog = Program(id="prog-qr", name="B.Tech", code="BTECH-AE", departmentId=dept.id)
    course = Course(id="course-qr", name="Aerospace Intro", code="AE", credits=120, duration="4 Years", departmentId=dept.id, programId=prog.id)
    ay = AcademicYear(id="ay-qr", name="2026-27-QR", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365))
    sem = Semester(id="sem-qr", semesterNumber=1, academicYearId=ay.id, programId=prog.id, startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=120))
    subj = Subject(id="subj-qr", code="AE101", name="Flight Dynamics", credits=4, departmentId=dept.id, semesterId=sem.id, courseId=course.id)
    sect = Section(id="sect-qr", name="AE-Section A", capacity=60, semesterId=sem.id, departmentId=dept.id, programId=prog.id, academicYearId=ay.id)
    
    # Assign students to section
    s1 = db_session.query(User).filter_by(id=test_users["student1"].id).first()
    s1.sectionId = sect.id
    s2 = db_session.query(User).filter_by(id=test_users["student2"].id).first()
    s2.sectionId = sect.id
    
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

def test_start_qr_session(client, test_users, test_qr_setup):
    headers = get_auth_headers(client, "teacherqr", "AdminPassword@123")
    payload = {
        "academicYearId": test_qr_setup["ay"].id,
        "departmentId": test_qr_setup["dept"].id,
        "programId": test_qr_setup["prog"].id,
        "semesterId": test_qr_setup["sem"].id,
        "sectionId": test_qr_setup["sect"].id,
        "subjectId": test_qr_setup["subj"].id,
        "date": datetime.utcnow().isoformat(),
        "latitude": 12.9716,
        "longitude": 77.5946,
        "allowedRadius": 100.0,
        "intervalSeconds": 30
    }
    res = client.post("/api/v1/qr-attendance/session", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "id" in res.json()["data"]

def test_qr_rotation_expiration(client, test_users, test_qr_setup, db_session):
    headers = get_auth_headers(client, "teacherqr", "AdminPassword@123")
    
    # Setup QRSession
    att = AttendanceSession(id="as-rot", academicYearId=test_qr_setup["ay"].id, departmentId=test_qr_setup["dept"].id, programId=test_qr_setup["prog"].id, semesterId=test_qr_setup["sem"].id, sectionId=test_qr_setup["sect"].id, subjectId=test_qr_setup["subj"].id, date=datetime.utcnow(), status="ACTIVE", facultyId=test_users["teacher"].id)
    qr = QRSession(id="qs-rot", attendanceSessionId=att.id, latitude=12.9716, longitude=77.5946, allowedRadius=100.0, intervalSeconds=30)
    db_session.add_all([att, qr])
    db_session.commit()
    
    # 1. Fetch code 1
    res1 = client.get(f"/api/v1/qr-attendance/session/{qr.id}/code", headers=headers)
    assert res1.status_code == 200
    code1 = res1.json()["data"]["code"]
    
    # 2. Simulate code expiration in database
    expired_code = db_session.query(QRCode).filter_by(codeValue=code1).first()
    expired_code.expiresAt = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()
    
    # 3. Fetch code 2 (triggers rotation)
    res2 = client.get(f"/api/v1/qr-attendance/session/{qr.id}/code", headers=headers)
    assert res2.status_code == 200
    code2 = res2.json()["data"]["code"]
    assert code1 != code2

def test_scan_geofencing_and_device_duplicates(client, test_users, test_qr_setup, db_session):
    headers_teach = get_auth_headers(client, "teacherqr", "AdminPassword@123")
    headers_s1 = get_auth_headers(client, "studentqr1", "AdminPassword@123")
    headers_s2 = get_auth_headers(client, "studentqr2", "AdminPassword@123")
    
    # Setup QRSession with active code
    att = AttendanceSession(id="as-scan", academicYearId=test_qr_setup["ay"].id, departmentId=test_qr_setup["dept"].id, programId=test_qr_setup["prog"].id, semesterId=test_qr_setup["sem"].id, sectionId=test_qr_setup["sect"].id, subjectId=test_qr_setup["subj"].id, date=datetime.utcnow(), status="ACTIVE", facultyId=test_users["teacher"].id)
    qr = QRSession(id="qs-scan", attendanceSessionId=att.id, latitude=12.9716, longitude=77.5946, allowedRadius=100.0, intervalSeconds=30)
    code = QRCode(id="code-scan", qrSessionId=qr.id, codeValue="valid-token", expiresAt=datetime.utcnow() + timedelta(seconds=30))
    db_session.add_all([att, qr, code])
    db_session.commit()
    
    # 1. Scan from outside geofence (coordinates set far away: e.g. Mumbai coordinates)
    payload_far = {
        "qrSessionId": qr.id,
        "scannedToken": "valid-token",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "deviceId": "device-s1"
    }
    res_far = client.post("/api/v1/qr-attendance/scan", json=payload_far, headers=headers_s1)
    assert res_far.status_code == 400
    assert "bounds" in res_far.json()["message"].lower()
    
    # 2. Scan from inside geofence (success)
    payload_success = {
        "qrSessionId": qr.id,
        "scannedToken": "valid-token",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "deviceId": "device-s1"
    }
    res_success = client.post("/api/v1/qr-attendance/scan", json=payload_success, headers=headers_s1)
    assert res_success.status_code == 200
    
    # 3. Proxy Scan (S2 scans with the same Device ID "device-s1" -> returns 400)
    payload_proxy = {
        "qrSessionId": qr.id,
        "scannedToken": "valid-token",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "deviceId": "device-s1"
    }
    res_proxy = client.post("/api/v1/qr-attendance/scan", json=payload_proxy, headers=headers_s2)
    assert res_proxy.status_code == 400
    assert "device" in res_proxy.json()["message"].lower()
