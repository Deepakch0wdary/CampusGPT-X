import pytest
import uuid
from datetime import datetime, timedelta
from app.models.models import User, Role, Subject, Department, Course, Semester, AcademicYear, Program, Section, Room, TimeSlot, Timetable, TimetableEntry

def get_auth_headers(client, username, password):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def master_admin(db_session):
    role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    from app.core.security import get_password_hash
    hashed = get_password_hash("AdminPassword@123")
    user = User(
        id="admin-timetable-uuid",
        email="admin.timetable@campusgpt.edu",
        username="admintimetable",
        passwordHash=hashed,
        roleId=role.id,
        name="Admin Timetable",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_setup(db_session, master_admin):
    dept = Department(id="dept-tt", name="Information Science", code="IS")
    prog = Program(id="prog-tt", name="B.Tech", code="BTECH", departmentId=dept.id)
    course = Course(id="course-tt", name="IS Basics", code="IS101", credits=4, duration="4 Months", departmentId=dept.id, programId=prog.id)
    ay = AcademicYear(id="ay-tt", name="2026-27-TT", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365))
    sem = Semester(id="sem-tt", semesterNumber=1, academicYearId=ay.id, programId=prog.id, startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=120))
    subj1 = Subject(id="subj-tt-1", code="IS101-SUBJ1", name="Software Eng", credits=4, departmentId=dept.id, semesterId=sem.id, courseId=course.id)
    subj2 = Subject(id="subj-tt-2", code="IS101-SUBJ2", name="Database Sys", credits=4, departmentId=dept.id, semesterId=sem.id, courseId=course.id)
    sect = Section(id="sect-tt", name="Section IS-A", capacity=60, semesterId=sem.id, departmentId=dept.id, programId=prog.id, academicYearId=ay.id)
    room1 = Room(id="room-tt-1", roomNumber="LH-301", capacity=60, floor=3, buildingId="b-1" if db_session.query(Room).first() else "b-default")
    
    db_session.add_all([dept, prog, course, ay, sem, subj1, subj2, sect, room1])
    db_session.commit()
    return {
        "ay": ay,
        "sem": sem,
        "sect": sect,
        "subj1": subj1,
        "subj2": subj2,
        "room1": room1
    }

def test_create_academic_calendar(client, master_admin, test_setup):
    headers = get_auth_headers(client, "admintimetable", "AdminPassword@123")
    payload = {
        "academicYearId": test_setup["ay"].id,
        "workingDays": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    }
    res = client.post("/api/v1/timetable/calendar", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

def test_time_slot_overlap_validation(client, master_admin):
    headers = get_auth_headers(client, "admintimetable", "AdminPassword@123")
    
    # 1. Create slot 1
    payload1 = {
        "name": "Period 1",
        "startTime": "09:00",
        "endTime": "09:50",
        "type": "CLASS"
    }
    res1 = client.post("/api/v1/timetable/slots", json=payload1, headers=headers)
    assert res1.status_code == 200
    
    # 2. Try creating overlapping slot 2
    payload2 = {
        "name": "Period 2 Overlap",
        "startTime": "09:30",
        "endTime": "10:20",
        "type": "CLASS"
    }
    res2 = client.post("/api/v1/timetable/slots", json=payload2, headers=headers)
    assert res2.status_code == 400
    assert "overlap" in res2.json()["message"].lower()

def test_smart_conflict_clash_detection(client, master_admin, test_setup, db_session):
    headers = get_auth_headers(client, "admintimetable", "AdminPassword@123")
    
    # Setup standard slots
    slot1 = TimeSlot(id="s-tt-1", name="P1", startTime="10:00", endTime="10:50", type="CLASS")
    db_session.add(slot1)
    db_session.commit()
    
    # 1. Create a published Timetable
    tt1 = Timetable(id="tt-grid-1", name="TT 1", academicYearId=test_setup["ay"].id, semesterId=test_setup["sem"].id, sectionId=test_setup["sect"].id, status="PUBLISHED")
    db_session.add(tt1)
    db_session.commit()
    
    # 2. Save a TimetableEntry mapping Room LH-301 to Subject 1
    entry1 = TimetableEntry(
        id="tt-entry-1",
        timetableId=tt1.id,
        dayOfWeek="MONDAY",
        timeSlotId=slot1.id,
        subjectId=test_setup["subj1"].id,
        roomId=test_setup["room1"].id
    )
    db_session.add(entry1)
    db_session.commit()
    
    # 3. Request conflict check validation route for LH-301 at MONDAY slot1
    payload = {
        "timetableId": tt1.id,
        "dayOfWeek": "MONDAY",
        "timeSlotId": slot1.id,
        "roomId": test_setup["room1"].id
    }
    res = client.post("/api/v1/timetable/validate", json=payload, headers=headers)
    assert res.status_code == 200
    # Conflicts detected because Room LH-301 is already booked
    assert res.json()["success"] is False
    assert len(res.json()["data"]["conflicts"]) > 0

def test_timetable_approval_workflow(client, master_admin, test_setup, db_session):
    headers = get_auth_headers(client, "admintimetable", "AdminPassword@123")
    tt = Timetable(id="tt-grid-2", name="TT 2 Draft", academicYearId=test_setup["ay"].id, semesterId=test_setup["sem"].id, sectionId=test_setup["sect"].id, status="DRAFT")
    db_session.add(tt)
    db_session.commit()
    
    payload = {
        "timetableId": tt.id,
        "stage": "MASTER_ADMIN",
        "status": "APPROVED",
        "remarks": "Approved by chief administrator."
    }
    res = client.post("/api/v1/timetable/approval", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True
    
    # Status should transition to PUBLISHED
    db_session.refresh(tt)
    assert tt.status == "PUBLISHED"
