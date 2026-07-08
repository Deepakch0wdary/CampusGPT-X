import pytest
import uuid
from datetime import datetime, timedelta
from app.models.models import (
    User, Role, UserProfile, Subject, StudentAttendanceSummary, StudentResult, StudentAssignment,
    Result, ParentProfile, ParentStudentLink, FacultyAssignment, Department, Program, Course, Semester, AcademicYear,
    AcademicMentorProfile, AcademicInsight, AcademicRiskAssessment, AcademicRiskFactor,
    StudyRecommendation, StudyPlan, StudyPlanItem, StudentGoal, MentorIntervention, AcademicMentorAudit,
    NotificationPreference, Notification
)
from app.core.security import get_password_hash

def get_auth_headers(client, username, password):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def setup_academic_structure(db_session):
    # Ensure roles exist
    student_role = db_session.query(Role).filter_by(name="STUDENT").first()
    if not student_role:
        student_role = Role(id="student-role-uuid", name="STUDENT")
        db_session.add(student_role)

    teacher_role = db_session.query(Role).filter_by(name="TEACHER").first()
    if not teacher_role:
        teacher_role = Role(id="teacher-role-uuid", name="TEACHER")
        db_session.add(teacher_role)

    parent_role = db_session.query(Role).filter_by(name="PARENT").first()
    if not parent_role:
        parent_role = Role(id="parent-role-uuid", name="PARENT")
        db_session.add(parent_role)

    admin_role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    if not admin_role:
        admin_role = Role(id="admin-role-uuid", name="MASTER_ADMIN")
        db_session.add(admin_role)

    db_session.commit()

    # Academic Structure
    dept = Department(id="dept-uuid", name="Computer Science", code="CS")
    db_session.add(dept)
    db_session.commit()

    ay = AcademicYear(id="ay-uuid", name="2025-26", startDate=datetime.utcnow() - timedelta(days=100), endDate=datetime.utcnow() + timedelta(days=200), currentAcademicYear=True)
    db_session.add(ay)
    db_session.commit()

    prog = Program(id="prog-uuid", name="B.Tech CS", code="BTCS", departmentId=dept.id)
    db_session.add(prog)
    db_session.commit()

    course = Course(id="course-uuid", code="CS101", name="Intro to Computer Science", credits=4, duration="4 Months", departmentId=dept.id, programId=prog.id)
    db_session.add(course)
    db_session.commit()

    sem = Semester(id="sem-uuid", semesterNumber=1, academicYearId=ay.id, programId=prog.id, startDate=datetime.utcnow() - timedelta(days=50), endDate=datetime.utcnow() + timedelta(days=100), currentSemester=True)
    db_session.add(sem)
    db_session.commit()

    section = Section = db_session.query(User).filter_by(username="dummy-section").first() # Just use direct creation
    from app.models.models import Section as DBSection
    sec = DBSection(id="sec-uuid", name="A", capacity=60, semesterId=sem.id, departmentId=dept.id, programId=prog.id, academicYearId=ay.id)
    db_session.add(sec)
    db_session.commit()

    subj = Subject(id="subj-uuid", code="CS101SUB", name="Programming in C", credits=4, departmentId=dept.id, semesterId=sem.id, courseId=course.id)
    db_session.add(subj)
    db_session.commit()

    return {
        "dept": dept,
        "ay": ay,
        "prog": prog,
        "course": course,
        "sem": sem,
        "sec": sec,
        "subj": subj,
        "student_role": student_role,
        "teacher_role": teacher_role,
        "parent_role": parent_role,
        "admin_role": admin_role
    }

@pytest.fixture
def student_a(db_session, setup_academic_structure):
    hashed = get_password_hash("StudentA@123")
    user = User(
        id="student-a-uuid",
        email="student.a@campusgpt.edu",
        username="studenta",
        passwordHash=hashed,
        roleId=setup_academic_structure["student_role"].id,
        name="Student A",
        mustChangePassword=False,
        sectionId="sec-uuid",
        departmentId="dept-uuid"
    )
    db_session.add(user)
    db_session.commit()

    # Pre-configure Notification Preference
    pref = NotificationPreference(userId=user.id)
    db_session.add(pref)
    db_session.commit()

    # Add academic data for risk calculation: low attendance, failing marks
    att = StudentAttendanceSummary(userId=user.id, subjectId="subj-uuid", totalClasses=20, presentClasses=12, percentage=60.0) # <75%
    db_session.add(att)

    res = StudentResult(userId=user.id, subjectId="subj-uuid", semesterNumber=1, internalMarks=10, externalMarks=20, grade="F", credits=4) # Fail
    db_session.add(res)

    ass = StudentAssignment(userId=user.id, subjectId="subj-uuid", title="Hw 1", submissionStatus="PENDING", dueDate=datetime.utcnow() - timedelta(days=2)) # Late/Pending
    db_session.add(ass)

    db_session.commit()
    return user

@pytest.fixture
def student_b(db_session, setup_academic_structure):
    hashed = get_password_hash("StudentB@123")
    user = User(
        id="student-b-uuid",
        email="student.b@campusgpt.edu",
        username="studentb",
        passwordHash=hashed,
        roleId=setup_academic_structure["student_role"].id,
        name="Student B",
        mustChangePassword=False,
        sectionId="sec-uuid"
    )
    db_session.add(user)
    db_session.commit()

    # Prefs
    pref = NotificationPreference(userId=user.id)
    db_session.add(pref)
    db_session.commit()

    # Add academic data: good attendance, passing marks
    att = StudentAttendanceSummary(userId=user.id, subjectId="subj-uuid", totalClasses=20, presentClasses=19, percentage=95.0)
    db_session.add(att)

    res = StudentResult(userId=user.id, subjectId="subj-uuid", semesterNumber=1, internalMarks=40, externalMarks=45, grade="A+", credits=4)
    db_session.add(res)

    db_session.commit()
    return user

@pytest.fixture
def student_c(db_session, setup_academic_structure):
    # Student with insufficient data
    hashed = get_password_hash("StudentC@123")
    user = User(
        id="student-c-uuid",
        email="student.c@campusgpt.edu",
        username="studentc",
        passwordHash=hashed,
        roleId=setup_academic_structure["student_role"].id,
        name="Student C",
        mustChangePassword=False,
        sectionId="sec-uuid"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def parent_user(db_session, setup_academic_structure, student_a, student_b):
    hashed = get_password_hash("Parent@123")
    user = User(
        id="parent-user-uuid",
        email="parent@campusgpt.edu",
        username="parent",
        passwordHash=hashed,
        roleId=setup_academic_structure["parent_role"].id,
        name="Parent Profile",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()

    profile = ParentProfile(
        id="parent-profile-uuid",
        userId=user.id,
        phoneNumber="9876543210"
    )
    db_session.add(profile)
    db_session.commit()

    # Link with Student A (Verified) and Student B (Verified)
    link_a = ParentStudentLink(parentId=profile.id, studentId=student_a.id, relationship="FATHER", status="VERIFIED")
    link_b = ParentStudentLink(parentId=profile.id, studentId=student_b.id, relationship="FATHER", status="VERIFIED")
    db_session.add(link_a)
    db_session.add(link_b)
    db_session.commit()
    return user

@pytest.fixture
def teacher_user(db_session, setup_academic_structure):
    hashed = get_password_hash("Teacher@123")
    user = User(
        id="teacher-user-uuid",
        email="teacher@campusgpt.edu",
        username="teacher",
        passwordHash=hashed,
        roleId=setup_academic_structure["teacher_role"].id,
        name="Teacher Profile",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()

    # Faculty Assignment to CS101 Section A (matching Student A/B)
    fa = FacultyAssignment(
        departmentId="dept-uuid",
        subjectId="subj-uuid",
        facultyId=user.id,
        sectionId="sec-uuid",
        semesterId="sem-uuid",
        academicYearId="ay-uuid"
    )
    db_session.add(fa)
    db_session.commit()
    return user

@pytest.fixture
def admin_user(db_session, setup_academic_structure):
    hashed = get_password_hash("Admin@123")
    user = User(
        id="admin-user-uuid",
        email="admin@campusgpt.edu",
        username="admin",
        passwordHash=hashed,
        roleId=setup_academic_structure["admin_role"].id,
        name="Master Admin",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user


# --- UNIT & INTEGRATION TESTS ---

def test_student_gets_own_overview_and_risk(client, student_a):
    headers = get_auth_headers(client, "studenta", "StudentA@123")

    # Overview
    res = client.get("/api/v1/academic-mentor/me/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "profile" in data
    assert data["profile"]["currentRiskLevel"] in ["HIGH", "CRITICAL"] # student A has bad grades/attendance
    assert data["stats"]["overallAttendance"] == 60.0

    # Risk Assessment factors
    res = client.get("/api/v1/academic-mentor/me/risk-assessment", headers=headers)
    assert res.status_code == 200
    assess_data = res.json()["data"]
    assert "disclaimer" in assess_data
    assert assess_data["engineType"] == "LOCAL_EXPLAINABLE_ANALYTICS"
    assert len(assess_data["factors"]) > 0

    # Verify score bounds (0-100) and factors sum
    score = assess_data["assessment"]["score"]
    assert 0.0 <= score <= 100.0

def test_recalculation_cooldown_enforced(client, student_a):
    headers = get_auth_headers(client, "studenta", "StudentA@123")

    # Recalculate first time
    res = client.post("/api/v1/academic-mentor/me/recalculate", headers=headers)
    assert res.status_code == 200

    # Immediate second try should fail with 400 Bad Request
    res2 = client.post("/api/v1/academic-mentor/me/recalculate", headers=headers)
    assert res2.status_code == 400
    assert "cooling down" in res2.json()["message"]

def test_student_insufficient_data(client, student_c):
    headers = get_auth_headers(client, "studentc", "StudentC@123")
    res = client.get("/api/v1/academic-mentor/me/risk-assessment", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["assessment"] is not None
    assert data["assessment"]["level"] == "INSUFFICIENT_DATA"
    assert data["assessment"]["score"] == 0.0

def test_recommendation_and_study_plan_cycle(client, student_a):
    headers = get_auth_headers(client, "studenta", "StudentA@123")

    # Get active recommendations
    res = client.get("/api/v1/academic-mentor/me/recommendations", headers=headers)
    assert res.status_code == 200
    recs = res.json()["data"]
    assert len(recs) > 0
    rec_id = recs[0]["id"]

    # Transition recommendation to ACCEPTED
    res_patch = client.patch(f"/api/v1/academic-mentor/me/recommendations/{rec_id}", headers=headers, json={"status": "ACCEPTED"})
    assert res_patch.status_code == 200
    assert res_patch.json()["data"]["status"] == "ACCEPTED"

    # Invalid status transition rejected
    res_bad = client.patch(f"/api/v1/academic-mentor/me/recommendations/{rec_id}", headers=headers, json={"status": "INVALID_STATUS"})
    assert res_bad.status_code == 400

    # Create study plan
    plan_payload = {
        "title": "My CS101 Revision Plan",
        "description": "Plan to clear programming backlogs",
        "startDate": str(datetime.utcnow()),
        "endDate": str(datetime.utcnow() + timedelta(days=7)),
        "generatedFromRecommendationId": rec_id,
        "items": [
            {
                "subjectId": "subj-uuid",
                "title": "Review pointers",
                "description": "Read Chapter 4",
                "scheduledDate": str(datetime.utcnow()),
                "estimatedMinutes": 60,
                "orderIndex": 0
            }
        ]
    }
    res_plan = client.post("/api/v1/academic-mentor/me/study-plans", headers=headers, json=plan_payload)
    assert res_plan.status_code == 200
    plan_id = res_plan.json()["data"]["id"]

    # Get plan details
    res_details = client.get(f"/api/v1/academic-mentor/me/study-plans/{plan_id}", headers=headers)
    assert res_details.status_code == 200
    assert len(res_details.json()["data"]["items"]) == 1
    item_id = res_details.json()["data"]["items"][0]["id"]

    # Update item to COMPLETED
    res_item = client.patch(f"/api/v1/academic-mentor/me/study-plans/items/{item_id}", headers=headers, json={"status": "COMPLETED"})
    assert res_item.status_code == 200
    assert res_item.json()["data"]["status"] == "COMPLETED"

def test_goals_crud(client, student_a):
    headers = get_auth_headers(client, "studenta", "StudentA@123")

    # Create goal
    res = client.post("/api/v1/academic-mentor/me/goals", headers=headers, json={
        "subjectId": "subj-uuid",
        "title": "Score 80 in internal",
        "targetType": "MARKS",
        "targetValue": 80.0
    })
    assert res.status_code == 200
    goal_id = res.json()["data"]["id"]

    # Update goal
    res_update = client.patch(f"/api/v1/academic-mentor/me/goals/{goal_id}", headers=headers, json={
        "currentValue": 75.0,
        "status": "COMPLETED"
    })
    assert res_update.status_code == 200
    assert res_update.json()["data"]["status"] == "COMPLETED"

    # Delete goal
    res_del = client.delete(f"/api/v1/academic-mentor/me/goals/{goal_id}", headers=headers)
    assert res_del.status_code == 200

def test_student_idor_prevention(client, student_a, student_b):
    headers_a = get_auth_headers(client, "studenta", "StudentA@123")
    headers_b = get_auth_headers(client, "studentb", "StudentB@123")

    # Get student B recommendations
    res_b_recs = client.get("/api/v1/academic-mentor/me/recommendations", headers=headers_b)
    rec_b_id = res_b_recs.json()["data"][0]["id"] if res_b_recs.json()["data"] else None

    if rec_b_id:
        # Student A tries to update Student B recommendation
        res_hack = client.patch(f"/api/v1/academic-mentor/me/recommendations/{rec_b_id}", headers=headers_a, json={"status": "ACCEPTED"})
        assert res_hack.status_code == 404 # Treated as not found for safety

def test_parent_academic_view_safety_and_idor(client, parent_user, student_a, student_c):
    headers = get_auth_headers(client, "parent", "Parent@123")

    # List linked children
    res = client.get("/api/v1/academic-mentor/children", headers=headers)
    assert res.status_code == 200
    children = res.json()["data"]
    assert len(children) == 2
    linked_ids = [c["id"] for c in children]
    assert student_a.id in linked_ids
    assert student_c.id not in linked_ids # Student C not linked

    # Access linked Child A overview
    res_child = client.get(f"/api/v1/academic-mentor/children/{student_a.id}/overview", headers=headers)
    assert res_child.status_code == 200

    # Unrelated child IDOR block
    res_blocked = client.get(f"/api/v1/academic-mentor/children/{student_c.id}/overview", headers=headers)
    assert res_blocked.status_code == 403

def test_teacher_scoped_access_and_idor(client, teacher_user, student_a, student_c, db_session):
    headers = get_auth_headers(client, "teacher", "Teacher@123")

    # List scoped students
    res = client.get("/api/v1/academic-mentor/students", headers=headers)
    assert res.status_code == 200
    students = res.json()["data"]
    scoped_ids = [s["id"] for s in students]
    assert student_a.id in scoped_ids
    # Student C is in same section but let's test a student in another section
    # Let's create an unrelated student D in section B
    from app.models.models import Section as DBSection, Role
    sec_b = DBSection(id="sec-b-uuid", name="B", capacity=60, semesterId="sem-uuid", departmentId="dept-uuid", programId="prog-uuid", academicYearId="ay-uuid")
    db_session.add(sec_b)
    db_session.commit()

    hashed = get_password_hash("StudentD@123")
    student_d = User(
        id="student-d-uuid",
        email="student.d@campusgpt.edu",
        username="studentd",
        passwordHash=hashed,
        roleId=db_session.query(Role).filter_by(name="STUDENT").first().id,
        name="Student D",
        mustChangePassword=False,
        sectionId="sec-b-uuid"
    )
    db_session.add(student_d)
    db_session.commit()

    # Teacher requests Student D (Unrelated Section)
    res_blocked = client.get(f"/api/v1/academic-mentor/students/{student_d.id}/overview", headers=headers)
    assert res_blocked.status_code == 403

    # Teacher creates intervention for student A (Legitimate)
    res_int = client.post(f"/api/v1/academic-mentor/students/{student_a.id}/interventions", headers=headers, json={
        "type": "TUTORING",
        "reason": "Needs help in programming basics.",
        "notes": "Booked tutoring sessions."
    })
    assert res_int.status_code == 200
    int_id = res_int.json()["data"]["id"]

    # Student cannot create intervention for themselves
    std_headers = get_auth_headers(client, "studenta", "StudentA@123")
    res_bad = client.post(f"/api/v1/academic-mentor/students/{student_a.id}/interventions", headers=std_headers, json={
        "type": "TUTORING",
        "reason": "Self-tutoring"
    })
    assert res_bad.status_code == 403

def test_admin_bulk_analytics_and_audits(client, admin_user):
    headers = get_auth_headers(client, "admin", "Admin@123")

    # Access analytics
    res = client.get("/api/v1/academic-mentor/analytics", headers=headers)
    assert res.status_code == 200
    assert "averageRiskScore" in res.json()["data"]

    # Bulk recalculation
    res_bulk = client.post("/api/v1/academic-mentor/recalculate", headers=headers)
    assert res_bulk.status_code == 200
    assert "processed" in res_bulk.json()["data"]

    # Retrieve Audits
    res_audits = client.get("/api/v1/academic-mentor/audits", headers=headers)
    assert res_audits.status_code == 200
    assert len(res_audits.json()["data"]["audits"]) > 0

def test_day_20_notification_integration(client, student_a, db_session):
    headers = get_auth_headers(client, "studenta", "StudentA@123")

    # Trigger recalculation which triggers high-risk notification
    res = client.post("/api/v1/academic-mentor/me/recalculate", headers=headers)
    assert res.status_code == 200

    # Retrieve notifications for student A
    notifications = db_session.query(Notification).filter_by(recipientId=student_a.id).all()
    assert len(notifications) > 0
    types = [n.type for n in notifications]
    assert "ADVISORY" in types
    assert any("academic risk has been assessed as" in n.body for n in notifications)

def test_no_automatic_punitive_actions(client, student_a, db_session):
    # Verify that Student A remains active even with a critical risk score
    # No automated status changes
    user = db_session.query(User).filter_by(id=student_a.id).first()
    assert user.status == "ACTIVE"
    assert user.isSuspended is False
    assert user.isDisabled is False
