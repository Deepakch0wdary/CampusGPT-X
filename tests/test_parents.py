import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.auth_middleware import get_current_user_no_password_force
from app.main import app
from app.models.models import (
    User, Role, ParentProfile, ParentStudentLink, ParentMessage, ParentNotification,
    AttendanceRecord, StudentResult, StudentAssignment, FeeInvoice, AttendanceSession
)

@pytest.fixture
def seed_parent_test_data(db_session):
    admin_role = db_session.query(Role).filter(Role.name == "MASTER_ADMIN").first()
    parent_role = db_session.query(Role).filter(Role.name == "PARENT").first()
    if not parent_role:
        parent_role = Role(name="PARENT")
        db_session.add(parent_role)
        db_session.flush()
    student_role = db_session.query(Role).filter(Role.name == "STUDENT").first()

    # Users
    admin = User(email="admin_parent@test.com", username="admin_parent", passwordHash="hash", name="Admin", roleId=admin_role.id)
    parent_user = User(email="parent@test.com", username="parent_user", passwordHash="hash", name="Parent Person", roleId=parent_role.id)
    student1 = User(email="stud1@test.com", username="student_one", passwordHash="hash", name="Student One", roleId=student_role.id)
    student2 = User(email="stud2@test.com", username="student_two", passwordHash="hash", name="Student Two", roleId=student_role.id)
    unlinked_stud = User(email="stud3@test.com", username="student_three", passwordHash="hash", name="Student Three", roleId=student_role.id)

    db_session.add_all([admin, parent_user, student1, student2, unlinked_stud])
    db_session.commit()

    # Profiles
    parent_profile = ParentProfile(
        userId=parent_user.id,
        fatherName="Father Name",
        phoneNumber="9876543210"
    )
    db_session.add(parent_profile)
    db_session.flush()

    # Links (parent links to student1 and student2)
    link1 = ParentStudentLink(parentId=parent_profile.id, studentId=student1.id, relationship="FATHER")
    link2 = ParentStudentLink(parentId=parent_profile.id, studentId=student2.id, relationship="FATHER")
    db_session.add_all([link1, link2])
    db_session.commit()

    return {
        "admin": admin,
        "parent_user": parent_user,
        "parent_profile": parent_profile,
        "student1": student1,
        "student2": student2,
        "unlinked_stud": unlinked_stud
    }

def test_parent_linking_and_idor_protection(db_session, seed_parent_test_data):
    client = TestClient(app)
    data = seed_parent_test_data

    # Log in as parent
    app.dependency_overrides[get_current_user_no_password_force] = lambda: data["parent_user"]

    # 1. Fetch linked students list
    res_list = client.get("/api/v1/parents/students")
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) == 2

    # 2. Add some mock attendance for student1
    sess = AttendanceSession(
        id="sess-mock-1",
        academicYearId="ay-1",
        departmentId="d-1",
        programId="p-1",
        semesterId="s-1",
        sectionId="sec-1",
        subjectId="subj-1",
        facultyId="fac-1",
        status="CLOSED",
        date=datetime.utcnow()
    )
    db_session.add(sess)
    db_session.flush()

    att = AttendanceRecord(sessionId=sess.id, studentId=data["student1"].id, status="PRESENT")
    db_session.add(att)
    db_session.commit()

    # 3. Parent inspects student1 attendance -> Allowed (200 OK)
    res_att1 = client.get(f"/api/v1/parents/students/{data['student1'].id}/attendance")
    assert res_att1.status_code == 200
    assert res_att1.json()["data"]["attendancePercentage"] == 100.0

    # 4. Parent inspects unlinked student attendance -> Forbidden (403 IDOR blocked)
    res_att_unlinked = client.get(f"/api/v1/parents/students/{data['unlinked_stud'].id}/attendance")
    assert res_att_unlinked.status_code == 403

    app.dependency_overrides.clear()

def test_parent_direct_messaging(db_session, seed_parent_test_data):
    client = TestClient(app)
    data = seed_parent_test_data

    # Send message from Parent to Admin
    app.dependency_overrides[get_current_user_no_password_force] = lambda: data["parent_user"]
    msg_payload = {
        "receiverId": data["admin"].id,
        "content": "Hello Administrator, how is my child doing?"
    }

    res_send = client.post("/api/v1/parents/messages", json=msg_payload)
    assert res_send.status_code == 200
    msg_id = res_send.json()["data"]["id"]

    # Fetch messages
    res_history = client.get("/api/v1/parents/messages")
    assert res_history.status_code == 200
    assert len(res_history.json()["data"]) == 1
    assert res_history.json()["data"][0]["content"] == "Hello Administrator, how is my child doing?"

    app.dependency_overrides.clear()

def test_parent_notification_reads(db_session, seed_parent_test_data):
    client = TestClient(app)
    data = seed_parent_test_data

    # Add mock notification
    notif = ParentNotification(
        parentId=data["parent_profile"].id,
        title="Fee Alert",
        message="Upcoming due date is tomorrow.",
        category="FEE_REMINDER"
    )
    db_session.add(notif)
    db_session.commit()

    app.dependency_overrides[get_current_user_no_password_force] = lambda: data["parent_user"]

    # Fetch parent notifications
    res_notif = client.get("/api/v1/parents/notifications")
    assert res_notif.status_code == 200
    assert len(res_notif.json()["data"]) == 1
    assert res_notif.json()["data"][0]["isRead"] is False

    # Mark as read
    notif_id = res_notif.json()["data"][0]["id"]
    res_read = client.post(f"/api/v1/parents/notifications/{notif_id}/read")
    assert res_read.status_code == 200

    db_session.refresh(notif)
    assert notif.isRead is True

    app.dependency_overrides.clear()
