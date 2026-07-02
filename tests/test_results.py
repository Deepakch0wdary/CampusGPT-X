import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.auth_middleware import get_current_user_no_password_force
from app.main import app
from app.models.models import (
    User, Role, AcademicYear, Department, Program, Semester, Section, Subject,
    Result, ResultDetail, GradeScheme, GradeBoundary, Transcript, RevaluationRequest
)

@pytest.fixture
def seed_result_data(db_session):
    # Setup roles
    admin_role = db_session.query(Role).filter(Role.name == "MASTER_ADMIN").first()
    teacher_role = db_session.query(Role).filter(Role.name == "TEACHER").first()
    student_role = db_session.query(Role).filter(Role.name == "STUDENT").first()

    # Create users
    admin = User(email="admin@test.com", username="admin", passwordHash="hash", name="Admin", roleId=admin_role.id)
    teacher = User(email="teacher@test.com", username="teacher", passwordHash="hash", name="Teacher", roleId=teacher_role.id)
    student = User(email="student@test.com", username="student", passwordHash="hash", name="Student", roleId=student_role.id)
    db_session.add_all([admin, teacher, student])
    db_session.commit()

    # Create basic academic structures
    ay = AcademicYear(name="AY 2026-27", startDate=datetime(2026, 6, 1), endDate=datetime(2027, 5, 31))
    dept = Department(name="Computer Science", code="CS")
    db_session.add_all([ay, dept])
    db_session.commit()

    prog = Program(name="B.Tech CS", code="CS-BTECH", departmentId=dept.id)
    db_session.add(prog)
    db_session.commit()

    sem = Semester(semesterNumber=1, academicYearId=ay.id, programId=prog.id, startDate=datetime(2026, 6, 1), endDate=datetime(2026, 12, 1))
    db_session.add(sem)
    db_session.commit()

    sec = Section(name="Section A", capacity=60, semesterId=sem.id, departmentId=dept.id, programId=prog.id)
    db_session.add(sec)
    db_session.commit()

    # Bind student to section
    student.sectionId = sec.id
    student.departmentId = dept.id
    db_session.commit()

    subj = Subject(code="CS101", name="Intro to CS", credits=4, departmentId=dept.id, semesterId=sem.id, courseId="some-course-id")
    db_session.add(subj)
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

def test_grade_scheme_configuration(db_session, seed_result_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_result_data["admin"]

    payload = {
        "academicYearId": seed_result_data["ay"].id,
        "programId": seed_result_data["prog"].id,
        "gradeScale": "10-POINT",
        "creditSystem": "CHOICE_BASED",
        "passingMarks": 40.0,
        "boundaries": [
            {"letterGrade": "O", "gradePoint": 10.0, "minPercentage": 90.0, "maxPercentage": 100.0},
            {"letterGrade": "A", "gradePoint": 8.0, "minPercentage": 70.0, "maxPercentage": 89.99},
            {"letterGrade": "F", "gradePoint": 0.0, "minPercentage": 0.0, "maxPercentage": 39.99}
        ]
    }

    res = client.post("/api/v1/results/schemes", json=payload)
    assert res.status_code == 201
    assert res.json()["success"] is True

    # List schemes
    res_list = client.get("/api/v1/results/schemes")
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) >= 1

    app.dependency_overrides.clear()

def test_marks_entry_and_calculation(db_session, seed_result_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_result_data["teacher"]

    # 1. Setup grade boundaries first
    scheme = GradeScheme(
        academicYearId=seed_result_data["ay"].id,
        programId=seed_result_data["prog"].id,
        gradeScale="10-POINT",
        passingMarks=40.0
    )
    db_session.add(scheme)
    db_session.flush()

    bounds = [
        GradeBoundary(gradeSchemeId=scheme.id, letterGrade="O", gradePoint=10.0, minPercentage=90.0, maxPercentage=100.0),
        GradeBoundary(gradeSchemeId=scheme.id, letterGrade="A", gradePoint=8.0, minPercentage=70.0, maxPercentage=89.99),
        GradeBoundary(gradeSchemeId=scheme.id, letterGrade="F", gradePoint=0.0, minPercentage=0.0, maxPercentage=39.99)
    ]
    db_session.add_all(bounds)
    db_session.commit()

    # 2. Enter Student Marks
    payload = {
        "studentId": seed_result_data["student"].id,
        "subjectId": seed_result_data["subj"].id,
        "academicYearId": seed_result_data["ay"].id,
        "semesterNumber": 1,
        "internalMarks": 15.0,
        "assignmentMarks": 20.0,
        "labMarks": 10.0,
        "semesterExamMarks": 50.0 # Total: 95.0 -> Grade O
    }

    res = client.post("/api/v1/results/marks", json=payload)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Verify calculated parent Result in DB
    result_card = db_session.query(Result).filter(Result.studentId == seed_result_data["student"].id).first()
    assert result_card is not None
    assert result_card.totalMarks == 95.0
    assert result_card.sgpa == 10.0 # Grade point 10.0 for O

    app.dependency_overrides.clear()

def test_result_publishing_workflow(db_session, seed_result_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_result_data["teacher"]

    # Create dummy Result card in DRAFT
    res_card = Result(
        studentId=seed_result_data["student"].id,
        academicYearId=seed_result_data["ay"].id,
        semesterNumber=1,
        status="DRAFT"
    )
    db_session.add(res_card)
    db_session.commit()

    # Move to DEPT_REVIEW by Faculty (Teacher role)
    res_up = client.post(f"/api/v1/results/{res_card.id}/publish", json={"status": "DEPT_REVIEW"})
    assert res_up.status_code == 200
    assert db_session.query(Result).filter(Result.id == res_card.id).first().status == "DEPT_REVIEW"

    # Attempt to move to PUBLISHED by Faculty -> should fail (Admin only)
    res_fail = client.post(f"/api/v1/results/{res_card.id}/publish", json={"status": "PUBLISHED"})
    assert res_fail.status_code == 403

    # Move to PUBLISHED by Admin -> should succeed
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_result_data["admin"]
    res_pass = client.post(f"/api/v1/results/{res_card.id}/publish", json={"status": "PUBLISHED"})
    assert res_pass.status_code == 200
    assert db_session.query(Result).filter(Result.id == res_card.id).first().status == "PUBLISHED"

    app.dependency_overrides.clear()

def test_revaluation_request_and_review(db_session, seed_result_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_result_data["student"]

    # Create result, detail
    res_card = Result(studentId=seed_result_data["student"].id, academicYearId=seed_result_data["ay"].id, semesterNumber=1, status="PUBLISHED")
    db_session.add(res_card)
    db_session.flush()

    detail = ResultDetail(resultId=res_card.id, subjectId=seed_result_data["subj"].id, totalMarks=45.0, internalMarks=20.0, semesterExamMarks=25.0)
    db_session.add(detail)
    db_session.commit()

    # Student requests revaluation
    payload = {
        "resultDetailId": detail.id,
        "requestType": "REVALUATION",
        "remarks": "Check calculations on question 4"
    }

    res_req = client.post("/api/v1/results/revaluation", json=payload)
    assert res_req.status_code == 200
    req_id = res_req.json()["data"]["id"]

    # Faculty reviews revaluation and updates marks to 55.0 (+10 marks)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_result_data["teacher"]
    res_rev = client.post(f"/api/v1/results/revaluation/{req_id}/review", json={"status": "APPROVED", "updatedMarks": 55.0})
    assert res_rev.status_code == 200

    # Check updated total marks in DB
    db_session.refresh(detail)
    assert detail.semesterExamMarks == 35.0 # +10 marks added
    assert detail.totalMarks == 55.0

    app.dependency_overrides.clear()
