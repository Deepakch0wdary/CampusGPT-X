import pytest
import uuid
from datetime import datetime, timedelta
from app.models.models import User, Role, FacultyAssignment, Subject, Department, Course, Semester, AcademicYear, Program, Section

def get_auth_headers(client, username, password):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def faculty_user(db_session):
    role = db_session.query(Role).filter_by(name="TEACHER").first()
    if not role:
        role = Role(id="teacher-role-uuid", name="TEACHER")
        db_session.add(role)
        db_session.commit()

    from app.core.security import get_password_hash
    hashed = get_password_hash("TeacherPassword@123")
    user = User(
        id="teacher-a-uuid",
        email="teacher.a@campusgpt.edu",
        username="teachera",
        passwordHash=hashed,
        roleId=role.id,
        name="Teacher A",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def assigned_subject(db_session, faculty_user):
    dept = Department(id="dept-1", name="Computer Science", code="CS")
    prog = Program(id="prog-1", name="B.Tech", code="BTECH", departmentId=dept.id)
    course = Course(id="course-1", name="Intro to CS", code="CS101", credits=4, duration="4 Months", departmentId=dept.id, programId=prog.id)
    ay = AcademicYear(id="ay-1", name="2026-27", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365))
    sem = Semester(id="sem-1", semesterNumber=1, academicYearId=ay.id, programId=prog.id, startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=120))
    subj = Subject(id="subj-1", code="CS101-SUBJ", name="Data Structures", credits=4, departmentId=dept.id, semesterId=sem.id, courseId=course.id)
    sect = Section(id="sect-1", name="Section A", capacity=60, semesterId=sem.id, departmentId=dept.id, programId=prog.id, academicYearId=ay.id, facultyAdvisorId=faculty_user.id)
    
    db_session.add_all([dept, prog, course, ay, sem, subj, sect])
    db_session.commit()

    # Create faculty assignment map
    assignment = FacultyAssignment(
        id="fa-1",
        departmentId=dept.id,
        subjectId=subj.id,
        facultyId=faculty_user.id,
        sectionId=sect.id,
        semesterId=sem.id,
        academicYearId=ay.id
    )
    db_session.add(assignment)
    db_session.commit()
    return subj

def test_faculty_dashboard_assigned_details(client, faculty_user, assigned_subject):
    headers = get_auth_headers(client, "teachera", "TeacherPassword@123")
    res = client.get("/api/v1/faculty/dashboard", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["faculty"]["name"] == "Teacher A"
    assert len(payload["data"]["subjects"]) == 1
    assert payload["data"]["subjects"][0]["subjectCode"] == "CS101-SUBJ"

def test_faculty_restricted_subject_access(client, faculty_user, db_session):
    headers = get_auth_headers(client, "teachera", "TeacherPassword@123")
    
    # Try uploading notes for a non-existent/unassigned subject ID
    payload = {
        "title": "Invalid Notes File",
        "fileUrl": "http://invalid.url/doc.pdf",
        "fileType": "PDF",
        "subjectId": "unassigned-subject-uuid"
    }
    res = client.post("/api/v1/faculty/notes", json=payload, headers=headers)
    assert res.status_code == 403
    assert "access denied" in res.json()["message"].lower()

def test_faculty_create_assignment_def(client, faculty_user, assigned_subject):
    headers = get_auth_headers(client, "teachera", "TeacherPassword@123")
    payload = {
        "title": "Data Structures Assignment 1",
        "description": "Analyze Big O notation complexities",
        "dueDate": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
        "allowResubmission": True,
        "subjectId": assigned_subject.id
    }
    res = client.post("/api/v1/faculty/assignments", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

def test_faculty_apply_leave(client, faculty_user):
    headers = get_auth_headers(client, "teachera", "TeacherPassword@123")
    payload = {
        "leaveType": "CASUAL",
        "startDate": (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z",
        "endDate": (datetime.utcnow() + timedelta(days=4)).isoformat() + "Z",
        "reason": "Family gathering."
    }
    res = client.post("/api/v1/faculty/leaves", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True
