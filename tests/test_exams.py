import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.auth_middleware import get_current_user_no_password_force
from app.main import app
from app.models.models import (
    User, Role, AcademicYear, Department, Program, Semester, Section, Subject, Room, Building, Exam, ExamSchedule, HallTicket, QuestionPaper
)

@pytest.fixture
def seed_academic_data(db_session):
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
    db_session.commit()

    subj = Subject(code="CS101", name="Intro to CS", credits=4, departmentId=dept.id, semesterId=sem.id, courseId="some-course-id")
    db_session.add(subj)
    db_session.commit()

    # Create Room
    bld = Building(name="Engineering Block", code="EB-1", floors=4)
    db_session.add(bld)
    db_session.commit()

    room = Room(roomNumber="EB-101", capacity=30, buildingId=bld.id, floor=1)
    db_session.add(room)
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
        "subj": subj,
        "room": room
    }

def test_exam_crud(db_session, seed_academic_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_academic_data["admin"]

    # 1. Create Exam
    payload = {
        "examName": "CS101 Mid Exam",
        "examType": "MID",
        "academicYearId": seed_academic_data["ay"].id,
        "departmentId": seed_academic_data["dept"].id,
        "programId": seed_academic_data["prog"].id,
        "semesterId": seed_academic_data["sem"].id,
        "sectionId": seed_academic_data["sec"].id,
        "subjectId": seed_academic_data["subj"].id,
        "examDate": "2026-07-15T00:00:00Z",
        "startTime": "09:30",
        "endTime": "12:30",
        "durationMinutes": 180,
        "maxMarks": 100.0,
        "passingMarks": 40.0,
        "instructions": "No calculators allowed"
    }

    res = client.post("/api/v1/exams", json=payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["examName"] == "CS101 Mid Exam"
    exam_id = data["id"]

    # 2. Get list
    res_list = client.get("/api/v1/exams")
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]["exams"]) >= 1

    # 3. Update exam
    res_up = client.put(f"/api/v1/exams/{exam_id}", json={"examName": "CS101 Mid Term Updated"})
    assert res_up.status_code == 200
    assert res_up.json()["data"]["examName"] == "CS101 Mid Term Updated"

    # Clean up overrides
    app.dependency_overrides.clear()

def test_scheduling_conflicts(db_session, seed_academic_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_academic_data["admin"]

    # Create two exams on same day
    exam1 = Exam(
        examName="Exam 1", examType="MID",
        academicYearId=seed_academic_data["ay"].id, departmentId=seed_academic_data["dept"].id,
        programId=seed_academic_data["prog"].id, semesterId=seed_academic_data["sem"].id,
        sectionId=seed_academic_data["sec"].id, subjectId=seed_academic_data["subj"].id,
        examDate=datetime(2026, 7, 15), startTime="09:00", endTime="12:00",
        durationMinutes=180, maxMarks=100.0, passingMarks=40.0
    )
    exam2 = Exam(
        examName="Exam 2", examType="MID",
        academicYearId=seed_academic_data["ay"].id, departmentId=seed_academic_data["dept"].id,
        programId=seed_academic_data["prog"].id, semesterId=seed_academic_data["sem"].id,
        sectionId=seed_academic_data["sec"].id, subjectId=seed_academic_data["subj"].id,
        examDate=datetime(2026, 7, 15), startTime="10:00", endTime="13:00", # Overlapping!
        durationMinutes=180, maxMarks=100.0, passingMarks=40.0
    )
    db_session.add_all([exam1, exam2])
    db_session.commit()

    # Schedule Exam 1 in Room EB-101
    sched_payload1 = {
        "roomId": seed_academic_data["room"].id,
        "invigilatorId": seed_academic_data["teacher"].id
    }
    res1 = client.post(f"/api/v1/exams/{exam1.id}/schedule", json=sched_payload1)
    assert res1.status_code == 200

    # Try to schedule Exam 2 in the same Room (Overlapping time) -> should fail with 400
    res2 = client.post(f"/api/v1/exams/{exam2.id}/schedule", json=sched_payload1)
    assert res2.status_code == 400
    assert "Room overlap conflict" in res2.json()["message"]

    app.dependency_overrides.clear()

def test_hall_ticket_and_seating(db_session, seed_academic_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_academic_data["admin"]

    # Create exam
    exam = Exam(
        examName="Exam 1", examType="MID",
        academicYearId=seed_academic_data["ay"].id, departmentId=seed_academic_data["dept"].id,
        programId=seed_academic_data["prog"].id, semesterId=seed_academic_data["sem"].id,
        sectionId=seed_academic_data["sec"].id, subjectId=seed_academic_data["subj"].id,
        examDate=datetime(2026, 7, 15), startTime="09:00", endTime="12:00",
        durationMinutes=180, maxMarks=100.0, passingMarks=40.0
    )
    db_session.add(exam)
    db_session.commit()

    # Generate Hall Ticket
    ht_payload = {
        "studentId": seed_academic_data["student"].id,
        "examCenter": "Engineering Block Hall A"
    }
    res_ht = client.post(f"/api/v1/exams/{exam.id}/hallticket", json=ht_payload)
    assert res_ht.status_code == 200
    ticket_id = res_ht.json()["data"]["id"]

    # Duplicate Hall Ticket check -> should fail
    res_dup = client.post(f"/api/v1/exams/{exam.id}/hallticket", json=ht_payload)
    assert res_dup.status_code == 400

    # Allocate Seat
    seat_payload = {
        "blockName": "Block A",
        "roomNumber": "EB-101",
        "benchNumber": 5,
        "seatNumber": "A-5"
    }
    res_seat = client.post(f"/api/v1/exams/halltickets/{ticket_id}/seat-allocation", json=seat_payload)
    assert res_seat.status_code == 200

    # Try allocating same seat to another candidate (mock second ticket)
    student2 = User(email="student2@test.com", username="student2", passwordHash="hash", name="Student 2", roleId=seed_academic_data["student"].roleId)
    db_session.add(student2)
    db_session.commit()

    res_ht2 = client.post(f"/api/v1/exams/{exam.id}/hallticket", json={"studentId": student2.id, "examCenter": "Block B"})
    ticket_id2 = res_ht2.json()["data"]["id"]

    res_seat_dup = client.post(f"/api/v1/exams/halltickets/{ticket_id2}/seat-allocation", json=seat_payload)
    assert res_seat_dup.status_code == 400
    assert "already allocated" in res_seat_dup.json()["message"]

    app.dependency_overrides.clear()

def test_question_paper_workflow(db_session, seed_academic_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_academic_data["teacher"]

    # Create exam
    exam = Exam(
        examName="Exam 1", examType="MID",
        academicYearId=seed_academic_data["ay"].id, departmentId=seed_academic_data["dept"].id,
        programId=seed_academic_data["prog"].id, semesterId=seed_academic_data["sem"].id,
        sectionId=seed_academic_data["sec"].id, subjectId=seed_academic_data["subj"].id,
        examDate=datetime(2026, 7, 15), startTime="09:00", endTime="12:00",
        durationMinutes=180, maxMarks=100.0, passingMarks=40.0
    )
    db_session.add(exam)
    db_session.commit()

    # Upload Question Paper (Teacher)
    qp_payload = {
        "examId": exam.id,
        "fileUrl": "https://s3.amazonaws.com/campusgpt/qp101.pdf",
        "fileName": "qp101.pdf"
    }
    res_qp = client.post("/api/v1/exams/question-papers", json=qp_payload)
    assert res_qp.status_code == 201
    qp_id = res_qp.json()["data"]["id"]
    assert res_qp.json()["data"]["status"] == "PENDING"

    # Try to approve with Teacher role -> should fail (Admin only)
    res_rev_fail = client.post(f"/api/v1/exams/question-papers/{qp_id}/review", json={"status": "APPROVED"})
    assert res_rev_fail.status_code == 403

    # Approve with Admin role -> should pass
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_academic_data["admin"]
    res_rev_pass = client.post(f"/api/v1/exams/question-papers/{qp_id}/review", json={"status": "APPROVED"})
    assert res_rev_pass.status_code == 200
    assert res_rev_pass.json()["data"]["status"] == "APPROVED"

    app.dependency_overrides.clear()
