import uuid
from io import BytesIO
import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import User, Role
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

def test_export_users_xlsx(client: TestClient, admin_auth_headers):
    """Verifies that export route compiles database directories into standard Excel streams."""
    response = client.get("/api/v1/users/export/xlsx", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]
    assert "spreadsheet" in response.headers["Content-Type"]

def test_import_users_xlsx(client: TestClient, db_session: Session, admin_auth_headers):
    """Verifies that import route parses Excel uploads, validates inputs, and bulk registers users."""
    # 1. Create a dummy spreadsheet in memory
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Name", "Email", "Role"])
    ws.append(["Alice Doe", "alicedoe@gmail.com", "STUDENT"])
    ws.append(["Bob Staff", "bobstaff@gmail.com", "TEACHER"])
    
    output = BytesIO()
    wb.save(output)
    file_bytes = output.getvalue()

    # 2. Post file streams to import endpoints
    response = client.post(
        "/api/v1/users/import",
        files={"file": ("import.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["imported"] == 2
    assert len(data["errors"]) == 0

    # 3. Assert database listings are created
    db_session.expire_all()
    user_alice = db_session.query(User).filter_by(email="alicedoe@gmail.com").first()
    assert user_alice is not None
    assert user_alice.name == "Alice Doe"
    assert user_alice.role.name == "STUDENT"

    user_bob = db_session.query(User).filter_by(email="bobstaff@gmail.com").first()
    assert user_bob is not None
    assert user_bob.name == "Bob Staff"
    assert user_bob.role.name == "TEACHER"
