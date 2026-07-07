import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import User, Role, Department
from app.core.security import get_password_hash

@pytest.fixture
def admin_auth_headers(client: TestClient, db_session: Session):
    """Provisions a Master Admin account and returns bearer authorization headers."""
    role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    hashed = get_password_hash("AdminPassword@123")

    admin = User(
        id=str(uuid.uuid4()),
        email="admin@campusgpt.com",
        username="admin",
        passwordHash=hashed,
        name="Master Admin",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add(admin)
    db_session.commit()

    # Authenticate to extract JWT
    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "admin",
        "password": "AdminPassword@123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_users_pagination_sorting(client: TestClient, db_session: Session, admin_auth_headers):
    """Verifies that listing user directories handles sort columns, page bounds, and search filters."""
    role = db_session.query(Role).filter_by(name="STUDENT").first()

    # Insert 15 student records
    for i in range(15):
        student = User(
            id=str(uuid.uuid4()),
            email=f"student{i}@campusgpt.com",
            username=f"student{i}",
            passwordHash="hash",
            name=f"Student {i:02d}",
            roleId=role.id
        )
        db_session.add(student)
    db_session.commit()

    # Query first page, sorting name alphabetically
    response = client.get("/api/v1/users?page=1&limit=10&sort_by=name&sort_order=asc", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 10
    assert data["total"] == 16  # 15 students + 1 master admin
    assert data["users"][0]["name"] == "Master Admin"  # M comes before S

    # Query search parameters
    search_response = client.get("/api/v1/users?search=Student 05", headers=admin_auth_headers)
    assert len(search_response.json()["users"]) == 1
    assert search_response.json()["users"][0]["email"] == "student5@campusgpt.com"

def test_master_admin_purging_protection(client: TestClient, db_session: Session, admin_auth_headers):
    """Ensures service-level validations deny delete calls targeting the Master Admin account."""
    admin = db_session.query(User).filter_by(username="admin").first()

    # Attempt account deletion
    response = client.delete(f"/api/v1/users/{admin.id}", headers=admin_auth_headers)
    assert response.status_code == 403
    assert "cannot be deleted" in response.json()["error"]["message"].lower()

def test_update_user_profiles(client: TestClient, db_session: Session, admin_auth_headers):
    """Verifies that users:update endpoint applies parameter modifications."""
    role = db_session.query(Role).filter_by(name="TEACHER").first()
    user = User(
        id=str(uuid.uuid4()),
        email="teacher1@campusgpt.com",
        username="teacher1",
        passwordHash="hash",
        name="Old Name",
        roleId=role.id
    )
    db_session.add(user)
    db_session.commit()

    # Perform updates
    response = client.put(
        f"/api/v1/users/{user.id}",
        json={
            "name": "Updated Name",
            "email": "teacher1@campusgpt.com",
            "phone_number": "123456789"
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Retrieve from DB to check parameters updates
    db_session.expire_all()
    updated_user = db_session.query(User).filter_by(id=user.id).first()
    assert updated_user.name == "Updated Name"
    assert updated_user.profile.phoneNumber == "123456789"

def test_roles_endpoint(client: TestClient, admin_auth_headers):
    """Verifies that the /api/v1/users/roles endpoint returns the system roles list."""
    response = client.get("/api/v1/users/roles", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "roles" in data
    assert any(r["name"] == "STUDENT" for r in data["roles"])
    assert any(r["name"] == "TEACHER" for r in data["roles"])

def test_master_admin_modification_protection(client: TestClient, db_session: Session, admin_auth_headers):
    """Verifies that other users cannot modify the MASTER_ADMIN profile."""
    # Find master admin
    admin = db_session.query(User).filter_by(username="admin").first()

    # Create another staff user with users:update permissions
    role = db_session.query(Role).filter_by(name="TEACHER").first()
    staff_id = str(uuid.uuid4())
    staff = User(
        id=staff_id,
        email="staff@campusgpt.com",
        username="staff_user",
        passwordHash=get_password_hash("password"),
        name="Staff User",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add(staff)

    # Grant permissions to this staff user
    from app.models.models import UserPermission, Permission
    perm = db_session.query(Permission).filter_by(name="users:update").first()
    if not perm:
        perm = Permission(id=str(uuid.uuid4()), name="users:update", description="update users")
        db_session.add(perm)
        db_session.commit()
    user_perm = UserPermission(id=str(uuid.uuid4()), userId=staff_id, permissionId=perm.id)
    db_session.add(user_perm)
    db_session.commit()

    # Log in as the staff user
    login_resp = client.post("/api/v1/auth/login", json={
        "username_or_email": "staff_user",
        "password": "password"
    })
    assert login_resp.status_code == 200
    staff_token = login_resp.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # Attempt to modify MASTER_ADMIN profile using staff account
    resp = client.put(
        f"/api/v1/users/{admin.id}",
        json={
            "name": "Modified Name",
            "email": "admin@campusgpt.com"
        },
        headers=staff_headers
    )
    assert resp.status_code == 403
    assert "cannot be modified by another user" in resp.json()["error"]["message"].lower()

def test_create_duplicate_master_admin_rejected(client: TestClient, admin_auth_headers):
    """Verifies that creating a second MASTER_ADMIN user is rejected."""
    resp = client.post(
        "/api/v1/users",
        json={
            "email": "another.admin@campusgpt.com",
            "name": "Another Master Admin",
            "role_name": "MASTER_ADMIN"
        },
        headers=admin_auth_headers
    )
    assert resp.status_code == 400
    assert "duplicate master_admin" in resp.json()["error"]["message"].lower()
