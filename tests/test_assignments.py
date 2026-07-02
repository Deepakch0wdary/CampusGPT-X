import pytest
import json
import uuid
from datetime import datetime, timedelta
from app.models.models import User, Role, Subject, Section, AcademicYear, Department, Program, Semester

def get_auth_headers(client, username, password):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def assignment_setup_data(db_session):
    role_admin = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    role_teacher = db_session.query(Role).filter_by(name="TEACHER").first()
    role_student = db_session.query(Role).filter_by(name="STUDENT").first()
    
    from app.core.security import get_password_hash
    hashed = get_password_hash("AdminPassword@123")
    
    admin = User(id="admin-assign-uuid", email="admin.assign@campusgpt.edu", username="adminassign", passwordHash=hashed, roleId=role_admin.id, name="Admin Assign", mustChangePassword=False)
    teacher = User(id="teacher-assign-uuid", email="teacher.assign@campusgpt.edu", username="teacherassign", passwordHash=hashed, roleId=role_teacher.id, name="Teacher Assign", mustChangePassword=False)
    
    # Context data
    ay = AcademicYear(id="ay-assign", name="2026-2027", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365))
    dept = Department(id="dept-assign", name="Assign Dept", code="ASSGNDPT")
    prog = Program(id="prog-assign", name="Assign Program", code="ASSGNPRG", departmentId=dept.id)
    sem = Semester(id="sem-assign", semesterNumber=1, academicYearId=ay.id, programId=prog.id, startDate=datetime.utcnow(), endDate=datetime.utcnow()+timedelta(days=180))
    sec = Section(id="sec-assign", name="Sec A", capacity=60, semesterId=sem.id, departmentId=dept.id, programId=prog.id)
    subj = Subject(id="subj-assign", code="CS101A", name="Computer Science Intro", credits=4, departmentId=dept.id, semesterId=sem.id, courseId="dummy-course-id-not-exist")
    
    # We need a course if subject cascades onDelete Course
    # Wait, Subject references Course in SQLite during create?
    # Let's check: in models.py, Subject.courseId points to Course.id
    # But since we drop all/create all in SQLite without strict FK constraints (unless enforced by SQLite), let's create a Course anyway to be safe.
    from app.models.models import Course
    course = Course(id="dummy-course-id-not-exist", code="CSE", name="CS Eng", credits=180, duration="4 Years", departmentId=dept.id, programId=prog.id)
    
    student = User(id="student-assign-uuid", email="student.assign@campusgpt.edu", username="studentassign", passwordHash=hashed, roleId=role_student.id, name="Student Assign", sectionId=sec.id, mustChangePassword=False)

    db_session.add_all([admin, teacher, ay, dept, prog, sem, sec, course, subj, student])
    db_session.commit()
    
    return {
        "admin": admin,
        "teacher": teacher,
        "student": student,
        "ay": ay,
        "dept": dept,
        "prog": prog,
        "sem": sem,
        "sec": sec,
        "subj": subj
    }

def test_create_and_publish_assignment(client, assignment_setup_data):
    headers_teacher = get_auth_headers(client, "teacherassign", "AdminPassword@123")
    headers_student = get_auth_headers(client, "studentassign", "AdminPassword@123")

    # 1. Students cannot create assignments
    payload = {
        "academicYearId": assignment_setup_data["ay"].id,
        "departmentId": assignment_setup_data["dept"].id,
        "programId": assignment_setup_data["prog"].id,
        "semesterId": assignment_setup_data["sem"].id,
        "sectionId": assignment_setup_data["sec"].id,
        "subjectId": assignment_setup_data["subj"].id,
        "assignmentType": "HOMEWORK",
        "title": "Introduction to Databases",
        "description": "Learn SQL basics",
        "instructions": "Submit zip file.",
        "dueDate": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        "maxMarks": 100.0,
        "allowedFileTypes": "PDF,ZIP",
        "maxUploadSizeMb": 15.0,
        "status": "PUBLISHED"
    }

    res_stud = client.post("/api/v1/assignments", json=payload, headers=headers_student)
    assert res_stud.status_code == 403

    # 2. Teacher successfully creates assignment
    res_teach = client.post("/api/v1/assignments", json=payload, headers=headers_teacher)
    assert res_teach.status_code == 200
    assign_id = res_teach.json()["data"]["id"]
    assert assign_id is not None

    # 3. Student views assignment details
    res_view = client.get(f"/api/v1/assignments/{assign_id}", headers=headers_student)
    assert res_view.status_code == 200
    assert res_view.json()["data"]["title"] == "Introduction to Databases"

def test_submission_and_evaluation(client, assignment_setup_data, db_session):
    headers_teacher = get_auth_headers(client, "teacherassign", "AdminPassword@123")
    headers_student = get_auth_headers(client, "studentassign", "AdminPassword@123")

    # Create assignment directly
    from app.models.models import Assignment
    assign = Assignment(
        id="a-test-id",
        academicYearId=assignment_setup_data["ay"].id,
        departmentId=assignment_setup_data["dept"].id,
        programId=assignment_setup_data["prog"].id,
        semesterId=assignment_setup_data["sem"].id,
        sectionId=assignment_setup_data["sec"].id,
        subjectId=assignment_setup_data["subj"].id,
        facultyId=assignment_setup_data["teacher"].id,
        assignmentType="HOMEWORK",
        title="Python Basics",
        dueDate=datetime.utcnow() + timedelta(days=2),
        maxMarks=50.0,
        allowedFileTypes="PDF,ZIP",
        maxUploadSizeMb=5.0,
        status="PUBLISHED"
    )
    db_session.add(assign)
    db_session.commit()

    # 1. Student submits assignment with invalid extension
    bad_payload = {
        "attachments": [
            {"fileName": "solution.exe", "fileUrl": "http://storage/solution.exe", "fileSize": 1048576}
        ]
    }
    res_bad = client.post(f"/api/v1/assignments/{assign.id}/submit", json=bad_payload, headers=headers_student)
    assert res_bad.status_code == 400
    assert "allowed" in res_bad.json()["message"].lower()

    # 2. Student submits assignment successfully
    ok_payload = {
        "attachments": [
            {"fileName": "solution.zip", "fileUrl": "http://storage/solution.zip", "fileSize": 1024}
        ]
    }
    res_ok = client.post(f"/api/v1/assignments/{assign.id}/submit", json=ok_payload, headers=headers_student)
    assert res_ok.status_code == 200
    sub_id = res_ok.json()["data"]["id"]

    # 3. Faculty evaluates and grades submission
    grade_payload = {
        "marksObtained": 45.0,
        "isPublished": True
    }
    feedback_payload = {
        "comments": "Excellent organization and code style.",
        "annotatedFileUrl": "http://storage/feedback_solution.zip"
    }
    res_grade = client.post(
        f"/api/v1/assignments/submissions/{sub_id}/grade", 
        json={**grade_payload, **feedback_payload}, 
        headers=headers_teacher
    )
    assert res_grade.status_code == 200

    # 4. Student views their grades and feedback
    res_assign_detail = client.get(f"/api/v1/assignments/{assign.id}", headers=headers_student)
    assert res_assign_detail.status_code == 200
    assert res_assign_detail.json()["data"]["submission"]["grade"] == 45.0
    assert res_assign_detail.json()["data"]["submission"]["feedback"] == "Excellent organization and code style."
