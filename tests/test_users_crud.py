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
