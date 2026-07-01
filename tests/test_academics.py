import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import User, Role, Department, Course, Subject, FacultyAssignment

@pytest.fixture
def admin_auth_headers(client: TestClient, db_session: Session):
    """Provisions an admin account and logs in to get auth headers."""
    # Note: conftest.py already seeds MASTER_ADMIN, TEACHER, STUDENT roles.
    role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    
    # We create a random user with username "admin_test"
    from app.core.security import get_password_hash
    hashed = get_password_hash("AdminPassword@123")
    admin = User(
        id="test-admin-uuid",
        email="admin_test@campusgpt.com",
        username="admin_test",
        passwordHash=hashed,
        name="Test Admin",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add(admin)
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "admin_test",
        "password": "AdminPassword@123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_academic_year_crud(client: TestClient, admin_auth_headers):
    # Create Academic Year
    response = client.post("/api/v1/academic-years", json={
        "name": "2026-2027",
        "startDate": "2026-06-01",
        "endDate": "2027-05-31",
        "status": "ACTIVE",
        "currentAcademicYear": True
    }, headers=admin_auth_headers)
    assert response.status_code == 200
    ay_id = response.json()["data"]["id"]

    # List Academic Years
    response = client.get("/api/v1/academic-years", headers=admin_auth_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]["academic_years"]) >= 1

    # Get Academic Year
    response = client.get(f"/api/v1/academic-years/{ay_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "2026-2027"

def test_department_crud_and_validation(client: TestClient, admin_auth_headers):
    # Create Department
    response = client.post("/api/v1/departments", json={
        "name": "Computer Science",
        "code": "CSE",
        "deanHod": "Dr. John Doe",
        "email": "cse@campusgpt.com"
    }, headers=admin_auth_headers)
    assert response.status_code == 200
    dept_id = response.json()["data"]["id"]

    # Duplicate Check
    response = client.post("/api/v1/departments", json={
        "name": "Computer Science Secondary",
        "code": "CSE",
        "deanHod": "Dr. Smith"
    }, headers=admin_auth_headers)
    assert response.status_code == 400

    # Get Department
    response = client.get(f"/api/v1/departments/{dept_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["code"] == "CSE"

def test_program_and_course(client: TestClient, admin_auth_headers, db_session: Session):
    # Provision Department
    dept = Department(id="dept-1", name="Electrical Eng", code="EE")
    db_session.add(dept)
    db_session.commit()

    # Create Program
    response = client.post("/api/v1/programs", json={
        "name": "B.Tech Electrical",
        "code": "BTECH-EE",
        "departmentId": "dept-1"
    }, headers=admin_auth_headers)
    assert response.status_code == 200
    prog_id = response.json()["data"]["id"]

    # Create Course
    response = client.post("/api/v1/courses", json={
        "code": "EE101",
        "name": "Basic Electrical Engineering",
        "credits": 4,
        "duration": "4 Years",
        "departmentId": "dept-1",
        "programId": prog_id
    }, headers=admin_auth_headers)
    assert response.status_code == 200

    # Active Course delete check
    response = client.delete("/api/v1/departments/dept-1", headers=admin_auth_headers)
    assert response.status_code == 400
    assert "active courses" in response.json()["message"]

def test_faculty_assignment(client: TestClient, admin_auth_headers, db_session: Session):
    # Provision models directly
    from app.models.models import AcademicYear, Program, Semester, Subject, Section, Role, User
    
    ay = AcademicYear(id="ay-1", name="2026-AY", startDate=pytest.approx(0), endDate=pytest.approx(0)) # Note: db_session transactional
    # Use dates instead
    from datetime import datetime
    ay = AcademicYear(id="ay-1", name="2026-AY", startDate=datetime.now(), endDate=datetime.now())
    db_session.add(ay)
    
    dept = Department(id="dept-2", name="Mechanical Eng", code="ME")
    db_session.add(dept)
    
    prog = Program(id="prog-1", name="B.Tech Mech", code="BTECH-ME", departmentId="dept-2")
    db_session.add(prog)
    
    course = Course(id="course-1", name="Dynamics", code="ME102", credits=3, duration="1 Semester", departmentId="dept-2", programId="prog-1")
    db_session.add(course)
    
    sem = Semester(id="sem-1", semesterNumber=1, academicYearId="ay-1", programId="prog-1", startDate=datetime.now(), endDate=datetime.now())
    db_session.add(sem)
    
    sub = Subject(id="sub-1", code="ME102-S", name="Dynamics Subject", credits=3, departmentId="dept-2", semesterId="sem-1", courseId="course-1")
    db_session.add(sub)
    
    # Provision Teacher user
    teacher_role = db_session.query(Role).filter_by(name="TEACHER").first()
    teacher = User(id="teacher-1", email="teacher@campusgpt.com", username="teacher1", passwordHash="hash", name="Teacher One", roleId=teacher_role.id)
    db_session.add(teacher)
    
    sect = Section(id="sect-1", name="Section A", capacity=60, semesterId="sem-1", departmentId="dept-2", programId="prog-1")
    db_session.add(sect)
    db_session.commit()
    
    # Perform Faculty Assignment
    response = client.post("/api/v1/faculty-assignments", json={
        "departmentId": "dept-2",
        "subjectId": "sub-1",
        "facultyId": "teacher-1",
        "sectionId": "sect-1",
        "semesterId": "sem-1",
        "academicYearId": "ay-1"
    }, headers=admin_auth_headers)
    assert response.status_code == 200
    
    # Duplicate Assignment Check
    response = client.post("/api/v1/faculty-assignments", json={
        "departmentId": "dept-2",
        "subjectId": "sub-1",
        "facultyId": "teacher-1",
        "sectionId": "sect-1",
        "semesterId": "sem-1",
        "academicYearId": "ay-1"
    }, headers=admin_auth_headers)
    assert response.status_code == 400
