import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import User, Role
from app.core.security import get_password_hash

def test_login_success(client: TestClient, db_session: Session):
    """Verifies that posting correct credentials issues tokens and reports mustChangePassword status."""
    role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    hashed = get_password_hash("AdminPassword@123")
    
    user = User(
        id=str(uuid.uuid4()),
        email="admin@campusgpt.com",
        username="admin",
        passwordHash=hashed,
        name="Master Admin",
        roleId=role.id,
        mustChangePassword=True
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "admin",
        "password": "AdminPassword@123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["must_change_password"] is True

def test_login_failures_lockout(client: TestClient, db_session: Session):
    """Verifies that 5 consecutive failed login attempts locks the account with HTTP 403."""
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    user = User(
        id=str(uuid.uuid4()),
        email="student@campusgpt.com",
        username="student",
        passwordHash=get_password_hash("password123"),
        name="Test Student",
        roleId=role.id
    )
    db_session.add(user)
    db_session.commit()

    # Fail login 5 times
    for _ in range(5):
        response = client.post("/api/v1/auth/login", json={
            "username_or_email": "student",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    # 6th attempt with correct password should be rejected due to account lock
    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "student",
        "password": "password123"
    })
    assert response.status_code == 403
    assert "locked" in response.json()["error"]["message"].lower()

def test_change_password(client: TestClient, db_session: Session):
    """Verifies that authenticated users can change their password, updating mustChangePassword state."""
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    user = User(
        id=str(uuid.uuid4()),
        email="student2@campusgpt.com",
        username="student2",
        passwordHash=get_password_hash("password123"),
        name="Test Student 2",
        roleId=role.id,
        mustChangePassword=True
    )
    db_session.add(user)
    db_session.commit()

    # Login to get access token
    login_resp = client.post("/api/v1/auth/login", json={
        "username_or_email": "student2",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]

    # Change password
    change_resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "password123", "new_password": "newsecurepassword1"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert change_resp.status_code == 200
    assert change_resp.json()["success"] is True

    # Retrieve user from DB to verify updated values
    db_session.expire_all()
    updated_user = db_session.query(User).filter_by(username="student2").first()
    assert updated_user.mustChangePassword is False
