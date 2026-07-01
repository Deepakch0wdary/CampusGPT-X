import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import User, Role
from app.core.security import get_password_hash

def test_prevent_master_admin_duplication(client: TestClient, db_session: Session):
    """Verifies that attempts to provision an additional MASTER_ADMIN account are blocked with HTTP 400."""
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

    # Login to retrieve token
    login_resp = client.post("/api/v1/auth/login", json={
        "username_or_email": "admin",
        "password": "AdminPassword@123"
    })
    token = login_resp.json()["access_token"]

    # Attempt user creation with MASTER_ADMIN role
    response = client.post(
        "/api/v1/users",
        json={
            "email": "admin2@campusgpt.com",
            "name": "Admin Two",
            "role_name": "MASTER_ADMIN"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "MASTER_ADMIN" in response.json()["error"]["message"]

def test_force_change_password_block(client: TestClient, db_session: Session):
    """Verifies that users flagged with mustChangePassword=True are blocked from using general system routers."""
    role = db_session.query(Role).filter_by(name="TEACHER").first()
    user = User(
        id=str(uuid.uuid4()),
        email="teacher@campusgpt.com",
        username="teacher",
        passwordHash=get_password_hash("password123"),
        name="Professor",
        roleId=role.id,
        mustChangePassword=True
    )
    db_session.add(user)
    db_session.commit()

    # Login to retrieve token
    login_resp = client.post("/api/v1/auth/login", json={
        "username_or_email": "teacher",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]

    # Attempt to hit the user listings endpoint
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "password change is required" in response.json()["error"]["message"].lower()
