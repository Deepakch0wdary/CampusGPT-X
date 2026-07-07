import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.models import (
    User, Role, ParentProfile, ParentStudentLink, ParentTeacherMeeting,
    ParentConsent, ParentNotificationPreference, ParentAudit,
    AttendanceRecord, AttendanceSession, Subject, Assignment,
    AssignmentSubmission, Exam, ExamSchedule, Result, ResultDetail,
    FeeInvoice, BookLoan, BookCopy, Book
)
from app.core.security import get_password_hash

@pytest.fixture
def parent_role(db_session: Session) -> Role:
    role = db_session.query(Role).filter_by(name="PARENT").first()
    if not role:
        role = Role(id=str(uuid.uuid4()), name="PARENT", description="Parent role")
        db_session.add(role)
        db_session.commit()
    return role

@pytest.fixture
def student_role(db_session: Session) -> Role:
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    if not role:
        role = Role(id=str(uuid.uuid4()), name="STUDENT", description="Student role")
        db_session.add(role)
        db_session.commit()
    return role

@pytest.fixture
def parent_user(db_session: Session, parent_role: Role) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="parent_test@campusgpt.com",
        username="parent_test",
        passwordHash=get_password_hash("password"),
        name="Parent Test",
        roleId=parent_role.id,
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def student_user_a(db_session: Session, student_role: Role) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="student_a@campusgpt.com",
        username="student_a",
        passwordHash=get_password_hash("password"),
        name="Student A",
        roleId=student_role.id,
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def student_user_b(db_session: Session, student_role: Role) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="student_b@campusgpt.com",
        username="student_b",
        passwordHash=get_password_hash("password"),
        name="Student B",
        roleId=student_role.id,
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def parent_headers(client: TestClient, parent_user: User) -> dict:
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "parent_test",
        "password": "password"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def student_headers(client: TestClient, student_user_a: User) -> dict:
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "student_a",
        "password": "password"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def linked_parent_profile(db_session: Session, parent_user: User, student_user_a: User) -> ParentProfile:
    profile = ParentProfile(
        id=str(uuid.uuid4()),
        userId=parent_user.id,
        phoneNumber="9998887776",
        guardianName="Parent Test"
    )
    db_session.add(profile)
    db_session.commit()

    link = ParentStudentLink(
        parentId=profile.id,
        studentId=student_user_a.id,
        relationship="FATHER",
        isPrimaryContact=True,
        status="VERIFIED"
    )
    db_session.add(link)
    db_session.commit()
    return profile


def test_parent_child_linking_scopes(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a, student_user_b):
    # 1. Accessing linked Child A details (Success 200)
    res_a = client.get(f"/api/v1/parent/children/{student_user_a.id}/overview", headers=parent_headers)
    assert res_a.status_code == 200
    assert res_a.json()["studentId"] == student_user_a.id

    # 2. Accessing unrelated Child B details (Forbidden 403)
    res_b = client.get(f"/api/v1/parent/children/{student_user_b.id}/overview", headers=parent_headers)
    assert res_b.status_code == 403


def test_pending_and_revoked_link_rejection(client: TestClient, db_session: Session, parent_role, student_role):
    # Create parent with revoked link
    p_user = User(
        id=str(uuid.uuid4()), email="parent_revoked@campusgpt.com", username="parent_revoked",
        passwordHash=get_password_hash("password"), name="Parent Revoked", roleId=parent_role.id, mustChangePassword=False
    )
    s_user = User(
        id=str(uuid.uuid4()), email="student_revoked@campusgpt.com", username="student_revoked",
        passwordHash=get_password_hash("password"), name="Student Revoked", roleId=student_role.id, mustChangePassword=False
    )
    db_session.add_all([p_user, s_user])
    db_session.commit()

    prof = ParentProfile(id=str(uuid.uuid4()), userId=p_user.id, phoneNumber="123")
    db_session.add(prof)
    db_session.commit()

    link = ParentStudentLink(
        parentId=prof.id, studentId=s_user.id, relationship="MOTHER", status="REVOKED"
    )
    db_session.add(link)
    db_session.commit()

    # Login revoked parent
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "parent_revoked", "password": "password"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Attempt overview read (must return 403 Forbidden)
    res = client.get(f"/api/v1/parent/children/{s_user.id}/overview", headers=headers)
    assert res.status_code == 403
def test_results_draft_versus_published(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    from app.models.models import AcademicYear, Department, Program, Semester, Course

    dept = Department(name="Science", code="SCI-1")
    db_session.add(dept)
    db_session.commit()

    prog = Program(name="Physics Bachelor", code="PHY-B", departmentId=dept.id)
    db_session.add(prog)
    db_session.commit()

    course = Course(
        name="Introductory Physics",
        code="PHYS-101",
        credits=4,
        duration="4 Years",
        departmentId=dept.id,
        programId=prog.id
    )
    db_session.add(course)
    db_session.commit()

    ay = AcademicYear(name="2025-2026", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365))
    db_session.add(ay)
    db_session.commit()

    sem = Semester(
        semesterNumber=1,
        academicYearId=ay.id,
        programId=prog.id,
        startDate=datetime.utcnow(),
        endDate=datetime.utcnow() + timedelta(days=180)
    )
    db_session.add(sem)
    db_session.commit()

    subject = Subject(name="Physics", code="PHY-101", credits=4, departmentId=dept.id, semesterId=sem.id, courseId=course.id)
    db_session.add(subject)
    db_session.commit()

    # Published Result
    pub_res = Result(
        studentId=student_user_a.id,
        academicYearId=ay.id,
        semesterNumber=1,
        sgpa=8.0,
        cgpa=8.0,
        totalMarks=85.0,
        percentage=85.0,
        creditsEarned=4,
        status="PUBLISHED"
    )
    db_session.add(pub_res)
    db_session.commit()

    pub_detail = ResultDetail(
        resultId=pub_res.id,
        subjectId=subject.id,
        totalMarks=85.0,
        grade="A"
    )
    db_session.add(pub_detail)

    # Draft Result
    draft_res = Result(
        studentId=student_user_a.id,
        academicYearId=ay.id,
        semesterNumber=2,
        sgpa=9.5,
        cgpa=9.5,
        totalMarks=95.0,
        percentage=95.0,
        creditsEarned=4,
        status="DRAFT"
    )
    db_session.add(draft_res)
    db_session.commit()

    draft_detail = ResultDetail(
        resultId=draft_res.id,
        subjectId=subject.id,
        totalMarks=95.0,
        grade="O"
    )
    db_session.add(draft_detail)
    db_session.commit()

    # Retrieve grades via Parent endpoint
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/results", headers=parent_headers)
    assert res.status_code == 200
    data = res.json()

    # Must only display PUBLISHED score (Physic: 85), must hide DRAFT score
    assert len(data) == 1
    assert data[0]["marksObtained"] == 85.0


def test_fees_read_only_boundaries(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    # Create Invoice
    invoice = FeeInvoice(
        invoiceNumber="INV-PARENT-111",
        studentId=student_user_a.id,
        subtotal=50000.0,
        totalAmount=50000.0,
        paidAmount=10000.0,
        balanceAmount=40000.0,
        dueDate=datetime.utcnow() + timedelta(days=30),
        status="PARTIALLY_PAID"
    )
    db_session.add(invoice)
    db_session.commit()

    # 1. Read fees (allowed)
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/fees", headers=parent_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 2. Modify invoice (denied / not existing endpoint)
    # Re-verify that parent cannot submit mock payment triggers on endpoints directly
    res_mod = client.post(f"/api/v1/parent/children/{student_user_a.id}/fees", json={"amount": 0}, headers=parent_headers)
    assert res_mod.status_code in [404, 405]


def test_parent_ptm_meetings_workflow(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    # Create a teacher user
    role_teacher = db_session.query(Role).filter_by(name="TEACHER").first()
    teacher_user = User(
        id=str(uuid.uuid4()), email="teacher_test@campusgpt.com", username="teacher_test",
        passwordHash="hash", name="Teacher Test", roleId=role_teacher.id, mustChangePassword=False
    )
    db_session.add(teacher_user)
    db_session.commit()

    # Request PTM meeting
    meeting_payload = {
        "studentId": student_user_a.id,
        "teacherUserId": teacher_user.id,
        "scheduledAt": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        "meetingMode": "ONLINE",
        "agenda": "Discuss physics grades performance"
    }

    req_res = client.post("/api/v1/parent/meetings", json=meeting_payload, headers=parent_headers)
    assert req_res.status_code == 200
    meeting_id = req_res.json()["id"]

    # Verify meeting list
    list_res = client.get("/api/v1/parent/meetings", headers=parent_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == meeting_id


def test_consents_management_responses(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a, parent_user):
    consent = ParentConsent(
        parentUserId=parent_user.id,
        studentId=student_user_a.id,
        consentType="FIELD_TRIP",
        title="Physics Lab Trip",
        description="Visit to national lab",
        status="PENDING",
        expiresAt=datetime.utcnow() + timedelta(days=5)
    )
    db_session.add(consent)
    db_session.commit()

    # Respond Approve
    resp_res = client.post(f"/api/v1/parent/consents/{consent.id}/respond", json={"status": "APPROVED"}, headers=parent_headers)
    assert resp_res.status_code == 200
    assert resp_res.json()["status"] == "APPROVED"


def test_parent_rbac_restrictions(client: TestClient, student_headers, student_user_a):
    # Student account blocked from accessing parent endpoints
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/overview", headers=student_headers)
    assert res.status_code == 403


def test_master_admin_bypass_access(client: TestClient, db_session: Session, linked_parent_profile, student_user_a):
    """MASTER_ADMIN should be able to view any student's overview without a parent link."""
    admin_role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    admin = User(
        id=str(uuid.uuid4()), email="admin_parent_test@campusgpt.com", username="admin_parent_test",
        passwordHash=get_password_hash("password"), name="Admin Test", roleId=admin_role.id, mustChangePassword=False
    )
    db_session.add(admin)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin_parent_test", "password": "password"})
    assert login_res.status_code == 200
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/overview", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["studentId"] == student_user_a.id


def test_child_switching(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a, student_user_b):
    """Parent can switch between linked Child A and Child B, and IDOR to Child C is denied."""
    # Link parent to Child B as well
    link_b = ParentStudentLink(
        parentId=linked_parent_profile.id,
        studentId=student_user_b.id,
        relationship="FATHER",
        isPrimaryContact=False,
        status="VERIFIED"
    )
    db_session.add(link_b)
    db_session.commit()

    # Child A overview works
    res_a = client.get(f"/api/v1/parent/children/{student_user_a.id}/overview", headers=parent_headers)
    assert res_a.status_code == 200
    assert res_a.json()["studentId"] == student_user_a.id

    # Child B overview works
    res_b = client.get(f"/api/v1/parent/children/{student_user_b.id}/overview", headers=parent_headers)
    assert res_b.status_code == 200
    assert res_b.json()["studentId"] == student_user_b.id

    # Child C (unlinked) overview is denied
    from app.models.models import Role as RoleModel
    student_role = db_session.query(RoleModel).filter_by(name="STUDENT").first()
    child_c = User(
        id=str(uuid.uuid4()), email="student_c@campusgpt.com", username="student_c",
        passwordHash=get_password_hash("password"), name="Student C",
        roleId=student_role.id, mustChangePassword=False
    )
    db_session.add(child_c)
    db_session.commit()

    res_c = client.get(f"/api/v1/parent/children/{child_c.id}/overview", headers=parent_headers)
    assert res_c.status_code == 403


def test_notification_preferences_crud(client: TestClient, db_session: Session, parent_headers, linked_parent_profile):
    """Parent can read and update notification preferences."""
    # GET
    res = client.get("/api/v1/parent/notification-preferences", headers=parent_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["attendanceAlerts"] is True

    # PUT - toggle attendance alerts off
    res_put = client.put("/api/v1/parent/notification-preferences", json={"attendanceAlerts": False}, headers=parent_headers)
    assert res_put.status_code == 200
    assert res_put.json()["attendanceAlerts"] is False

    # Verify persistence
    res2 = client.get("/api/v1/parent/notification-preferences", headers=parent_headers)
    assert res2.status_code == 200
    assert res2.json()["attendanceAlerts"] is False


def test_attendance_endpoint(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can read child's attendance records."""
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/attendance", headers=parent_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_academics_endpoint(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can read child's academic profile."""
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/academics", headers=parent_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["studentId"] == student_user_a.id
    assert "studentName" in data


def test_alerts_endpoint(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can retrieve rule-based risk alerts for a child."""
    res = client.get(f"/api/v1/parent/alerts?studentId={student_user_a.id}", headers=parent_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_expired_consent_rejection(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a, parent_user):
    """Responding to an expired consent should return 400."""
    consent = ParentConsent(
        parentUserId=parent_user.id,
        studentId=student_user_a.id,
        consentType="EVENT",
        title="Expired Event Consent",
        description="This consent has already expired.",
        status="PENDING",
        expiresAt=datetime.utcnow() - timedelta(days=1)  # Already expired
    )
    db_session.add(consent)
    db_session.commit()

    res = client.post(f"/api/v1/parent/consents/{consent.id}/respond", json={"status": "APPROVED"}, headers=parent_headers)
    assert res.status_code == 400
    assert "expired" in res.json()["message"].lower()


def test_meeting_notes_workflow(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can create a meeting, add notes, and retrieve them."""
    from app.models.models import ParentTeacherMeeting as PTM

    # Create teacher
    teacher_role = db_session.query(Role).filter_by(name="TEACHER").first()
    teacher = User(
        id=str(uuid.uuid4()), email="teacher_notes@campusgpt.com", username="teacher_notes",
        passwordHash=get_password_hash("password"), name="Teacher Notes", roleId=teacher_role.id, mustChangePassword=False
    )
    db_session.add(teacher)
    db_session.commit()

    # Create meeting
    meeting_payload = {
        "studentId": student_user_a.id,
        "teacherUserId": teacher.id,
        "scheduledAt": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        "meetingMode": "ONLINE",
        "agenda": "Discuss lab performance"
    }
    m_res = client.post("/api/v1/parent/meetings", json=meeting_payload, headers=parent_headers)
    assert m_res.status_code == 200
    meeting_id = m_res.json()["id"]

    # Add note
    note_payload = {"noteText": "Parent requested extra attention on practicals.", "visibleToParent": True}
    n_res = client.post(f"/api/v1/parent/meetings/{meeting_id}/notes", json=note_payload, headers=parent_headers)
    assert n_res.status_code == 200
    assert n_res.json()["noteText"] == note_payload["noteText"]

    # Verify note appears in meeting list
    list_res = client.get("/api/v1/parent/meetings", headers=parent_headers)
    assert list_res.status_code == 200
    meeting_data = [m for m in list_res.json() if m["id"] == meeting_id][0]
    assert len(meeting_data["notes"]) == 1


def test_children_list_endpoint(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can retrieve the list of linked children."""
    res = client.get("/api/v1/parent/children", headers=parent_headers)
    assert res.status_code == 200
    children = res.json()
    assert len(children) >= 1
    student_ids = [c["id"] for c in children]
    assert student_user_a.id in student_ids
    # Verify expected fields
    assert "name" in children[0]
    assert "relationship" in children[0]
    assert "status" in children[0]


def test_library_endpoint(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can access child library data."""
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/library", headers=parent_headers)
    assert res.status_code == 200
    data = res.json()
    assert "activeLoans" in data
    assert "pendingFines" in data


def test_hostel_endpoint(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can access child hostel data."""
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/hostel", headers=parent_headers)
    assert res.status_code == 200
    data = res.json()
    assert "allocated" in data
    assert "leaves" in data
    assert "complaints" in data


def test_transport_endpoint(client: TestClient, db_session: Session, parent_headers, linked_parent_profile, student_user_a):
    """Parent can access child transport data."""
    res = client.get(f"/api/v1/parent/children/{student_user_a.id}/transport", headers=parent_headers)
    assert res.status_code == 200
    data = res.json()
    assert "assigned" in data
