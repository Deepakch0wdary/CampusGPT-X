import pytest
import uuid
from datetime import datetime, timedelta
from app.models.models import User, Role, UserProfile, StudentAssignment, StudentAttendanceSummary, StudentResult
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
def student_user(db_session):
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    if not role:
        role = Role(id="student-role-uuid", name="STUDENT")
        db_session.add(role)
        db_session.commit()

    hashed = get_password_hash("StudentPassword@123")
    user = User(
        id="student-a-uuid",
        email="student.a@campusgpt.edu",
        username="studenta",
        passwordHash=hashed,
        roleId=role.id,
        name="Student A",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()

    profile = UserProfile(
        id="student-a-profile-uuid",
        userId=user.id,
        usn="USN100A",
        phoneNumber="1234567890",
        emergencyContact="9876543210"
    )
    db_session.add(profile)
    db_session.commit()
    return user

@pytest.fixture
def other_student_user(db_session):
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    hashed = get_password_hash("StudentBPassword@123")
    user = User(
        id="student-b-uuid",
        email="student.b@campusgpt.edu",
        username="studentb",
        passwordHash=hashed,
        roleId=role.id,
        name="Student B",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def admin_user(db_session):
    role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    if not role:
        role = Role(id="admin-role-uuid", name="MASTER_ADMIN")
        db_session.add(role)
        db_session.commit()

    hashed = get_password_hash("AdminPassword@123")
    user = User(
        id="admin-user-uuid",
        email="admin@campusgpt.edu",
        username="admin",
        passwordHash=hashed,
        roleId=role.id,
        name="Admin User",
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

def test_student_dashboard_own_access(client, student_user, db_session):
    headers = get_auth_headers(client, "studenta", "StudentPassword@123")

    res = client.get("/api/v1/student/dashboard", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["student"]["name"] == "Student A"
    assert payload["data"]["student"]["usn"] == "USN100A"

def test_student_cannot_access_other_student_dashboard(client, student_user, other_student_user):
    headers = get_auth_headers(client, "studenta", "StudentPassword@123")

    # Query other student's dashboard
    res = client.get(f"/api/v1/student/dashboard?student_id={other_student_user.id}", headers=headers)
    assert res.status_code == 403
    payload = res.json()
    assert "access denied" in payload["message"].lower()

def test_admin_can_access_any_student_dashboard(client, admin_user, student_user):
    headers = get_auth_headers(client, "admin", "AdminPassword@123")

    res = client.get(f"/api/v1/student/dashboard?student_id={student_user.id}", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["student"]["name"] == "Student A"

def test_student_profile_update(client, student_user):
    headers = get_auth_headers(client, "studenta", "StudentPassword@123")

    payload = {
        "phoneNumber": "9999999999",
        "address": "123 Campus Lane",
        "emergencyContact": "8888888888",
        "bloodGroup": "O+"
    }
    res = client.put("/api/v1/student/profile", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Retrieve profile to verify persistence
    res = client.get("/api/v1/student/profile", headers=headers)
    assert res.status_code == 200
    profile_data = res.json()["data"]
    assert profile_data["phoneNumber"] == "9999999999"
    assert profile_data["address"] == "123 Campus Lane"
    assert profile_data["bloodGroup"] == "O+"
