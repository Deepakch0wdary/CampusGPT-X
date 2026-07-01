import pytest
import json
import uuid
from datetime import datetime, timedelta
from app.models.models import User, Role, FaceProfile, FaceEmbedding, AttendanceSession, AttendanceRecord

def get_auth_headers(client, username, password):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_users_face(db_session):
    role_admin = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    role_student = db_session.query(Role).filter_by(name="STUDENT").first()
    
    from app.core.security import get_password_hash
    hashed = get_password_hash("AdminPassword@123")
    
    admin = User(id="admin-face-uuid", email="admin.face@campusgpt.edu", username="adminface", passwordHash=hashed, roleId=role_admin.id, name="Admin Face", mustChangePassword=False)
    student = User(id="student-face-uuid", email="student.face@campusgpt.edu", username="studentface", passwordHash=hashed, roleId=role_student.id, name="Student Face", mustChangePassword=False)
    
    db_session.add_all([admin, student])
    db_session.commit()
    return {"admin": admin, "student": student}

def test_face_registration_and_validation(client, test_users_face):
    headers = get_auth_headers(client, "studentface", "AdminPassword@123")
    
    # 1. Reject registration if missing angles
    payload_bad = {
        "embeddings": [
            {"angle": "FRONT", "embeddingJson": json.dumps([0.1]*512)}
        ]
    }
    res_bad = client.post("/api/v1/face/register", json=payload_bad, headers=headers)
    assert res_bad.status_code == 400
    assert "angles" in res_bad.json()["message"].lower()
    
    # 2. Reject if dimension is not 512
    payload_dim = {
        "embeddings": [
            {"angle": "FRONT", "embeddingJson": json.dumps([0.1]*128)},
            {"angle": "LEFT", "embeddingJson": json.dumps([0.1]*512)},
            {"angle": "RIGHT", "embeddingJson": json.dumps([0.1]*512)},
            {"angle": "UP", "embeddingJson": json.dumps([0.1]*512)},
            {"angle": "DOWN", "embeddingJson": json.dumps([0.1]*512)}
        ]
    }
    res_dim = client.post("/api/v1/face/register", json=payload_dim, headers=headers)
    assert res_dim.status_code == 400
    assert "dimension" in res_dim.json()["message"].lower()

    # 3. Success registration (all 5 angles, 512 dim each)
    payload_ok = {
        "embeddings": [
            {"angle": "FRONT", "embeddingJson": json.dumps([0.1]*512)},
            {"angle": "LEFT", "embeddingJson": json.dumps([0.1]*512)},
            {"angle": "RIGHT", "embeddingJson": json.dumps([0.1]*512)},
            {"angle": "UP", "embeddingJson": json.dumps([0.1]*512)},
            {"angle": "DOWN", "embeddingJson": json.dumps([0.1]*512)}
        ]
    }
    res_ok = client.post("/api/v1/face/register", json=payload_ok, headers=headers)
    assert res_ok.status_code == 200
    assert "awaiting" in res_ok.json()["message"].lower()

def test_admin_review_and_face_login(client, test_users_face, db_session):
    headers_student = get_auth_headers(client, "studentface", "AdminPassword@123")
    headers_admin = get_auth_headers(client, "adminface", "AdminPassword@123")
    
    # Create Face Profile in pending state
    profile = FaceProfile(id="fp-test", userId=test_users_face["student"].id, status="PENDING")
    front = FaceEmbedding(id="fe-front", faceProfileId=profile.id, angle="FRONT", embeddingJson=json.dumps([0.1]*512))
    db_session.add_all([profile, front])
    db_session.commit()
    
    # 1. Admin reviews and approves profile
    res_app = client.post(f"/api/v1/face/registrations/{profile.id}/review", json={
        "status": "APPROVED"
    }, headers=headers_admin)
    assert res_app.status_code == 200
    
    # 2. Try Face Login - spoofing attempt (should be rejected)
    payload_spoof = {
        "username_or_email": "studentface",
        "queryEmbeddingJson": json.dumps([0.1]*512),
        "liveness": {"blinkCount": 3, "smileDetected": True, "headRotationDegrees": 5.0},
        "spoofing": {"spoofProbability": 0.85, "spoofCategory": "PHONE_SCREEN"}
    }
    res_spoof = client.post("/api/v1/face/login", json=payload_spoof)
    assert res_spoof.status_code == 400
    assert "spoofing" in res_spoof.json()["message"].lower()

    # 3. Try Face Login - liveness failure (should be rejected)
    payload_live = {
        "username_or_email": "studentface",
        "queryEmbeddingJson": json.dumps([0.1]*512),
        "liveness": {"blinkCount": 0, "smileDetected": False, "headRotationDegrees": 0.0},
        "spoofing": {"spoofProbability": 0.05, "spoofCategory": "NONE"}
    }
    res_live = client.post("/api/v1/face/login", json=payload_live)
    assert res_live.status_code == 400
    assert "liveness" in res_live.json()["message"].lower()

    # 4. Try Face Login - success (valid embeddings match and checks passed)
    # Norm of A = sqrt(512 * 0.1 * 0.1) = sqrt(5.12)
    # Cosine similarity for matching vectors will be 1.0 (since they are identical)
    payload_success = {
        "username_or_email": "studentface",
        "queryEmbeddingJson": json.dumps([0.1]*512),
        "liveness": {"blinkCount": 2, "smileDetected": True, "headRotationDegrees": 4.5},
        "spoofing": {"spoofProbability": 0.02, "spoofCategory": "NONE"}
    }
    res_login = client.post("/api/v1/face/login", json=payload_success)
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()["data"]
