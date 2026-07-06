import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.auth_middleware import get_current_user_no_password_force
from app.main import app
from app.models.models import (
    User, Role, AdmissionApplication, AdmissionStatusHistory, AdmissionDocument, Enrollment
)

@pytest.fixture
def seed_admission_users(db_session):
    admin_role = db_session.query(Role).filter(Role.name == "MASTER_ADMIN").first()
    officer_role = db_session.query(Role).filter(Role.name == "ADMISSION_OFFICE").first()
    if not officer_role:
        officer_role = Role(name="ADMISSION_OFFICE")
        db_session.add(officer_role)
        db_session.flush()
    student_role = db_session.query(Role).filter(Role.name == "STUDENT").first()

    admin = User(email="admin_adm@test.com", username="admin_adm", passwordHash="hash", name="Admin", roleId=admin_role.id)
    officer = User(email="officer@test.com", username="officer_adm", passwordHash="hash", name="Officer", roleId=officer_role.id)
    student = User(email="applicant@test.com", username="applicant_user", passwordHash="hash", name="Applicant", roleId=student_role.id)

    db_session.add_all([admin, officer, student])
    db_session.commit()

    return {
        "admin": admin,
        "officer": officer,
        "student": student
    }

def test_admission_lifecycle(db_session, seed_admission_users):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_admission_users["student"]

    # 1. Create Draft Application
    payload = {
        "academicYearId": "ay-id-123",
        "departmentId": "dept-id-123",
        "programId": "prog-id-123",
        "applicantName": "Applicant",
        "email": "applicant@test.com",
        "phone": "9998887776",
        "dateOfBirth": "1998-05-15T00:00:00",
        "gender": "MALE",
        "nationality": "Indian",
        "category": "OBC",
        "quota": "MERIT"
    }

    res = client.post("/api/v1/admissions", json=payload)
    assert res.status_code == 200
    app_id = res.json()["data"]["id"]

    # 2. Student Submits
    res_sub = client.post(f"/api/v1/admissions/{app_id}/submit")
    assert res_sub.status_code == 200

    # Verify status changed to SUBMITTED
    app_rec = db_session.query(AdmissionApplication).filter(AdmissionApplication.id == app_id).first()
    assert app_rec.status == "SUBMITTED"

    # 3. Officer Reviews & Verifies documents mock checks
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_admission_users["officer"]
    res_rev = client.post(f"/api/v1/admissions/{app_id}/review", json={"action": "VERIFY", "comment": "Documents verified."})
    assert res_rev.status_code == 200
    assert db_session.query(AdmissionApplication).filter(AdmissionApplication.id == app_id).first().status == "VERIFIED"

    # 4. Officer Approves
    res_app = client.post(f"/api/v1/admissions/{app_id}/approve")
    assert res_app.status_code == 200
    assert db_session.query(AdmissionApplication).filter(AdmissionApplication.id == app_id).first().status == "APPROVED"

    app.dependency_overrides.clear()

def test_document_uploads(db_session, seed_admission_users):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_admission_users["student"]

    # Create dummy application
    appl = AdmissionApplication(
        applicationNumber="APP-MOCK-1",
        academicYearId="ay-1",
        departmentId="d-1",
        programId="p-1",
        applicantName="Applicant",
        email="applicant@test.com",
        phone="9998887776",
        dateOfBirth=datetime(1998, 5, 15),
        gender="MALE",
        nationality="Indian",
        category="OBC",
        quota="MERIT",
        status="DRAFT"
    )
    db_session.add(appl)
    db_session.commit()

    # Upload document
    doc_payload = {
        "documentCategory": "10th Marks Card",
        "fileName": "marks_card.pdf",
        "fileUrl": "/media/marks_card.pdf"
    }
    res = client.post(f"/api/v1/admissions/{appl.id}/documents", json=doc_payload)
    assert res.status_code == 200

    # Verify document in DB
    doc = db_session.query(AdmissionDocument).filter(AdmissionDocument.applicationId == appl.id).first()
    assert doc is not None
    assert doc.documentCategory == "10th Marks Card"

    app.dependency_overrides.clear()

def test_enrollment_idempotent(db_session, seed_admission_users):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_admission_users["officer"]

    # Create approved application
    appl = AdmissionApplication(
        applicationNumber="APP-MOCK-2",
        academicYearId="ay-1",
        departmentId="d-1",
        programId="p-1",
        applicantName="Applicant",
        email="applicant@test.com",
        phone="9998887776",
        dateOfBirth=datetime(1998, 5, 15),
        gender="MALE",
        nationality="Indian",
        category="OBC",
        quota="MERIT",
        status="APPROVED"
    )
    db_session.add(appl)
    db_session.commit()

    enroll_payload = {
        "applicationId": appl.id,
        "academicYearId": "ay-1",
        "departmentId": "d-1",
        "programId": "p-1"
    }

    # Enroll First Time
    res1 = client.post("/api/v1/enrollments", json=enroll_payload)
    assert res1.status_code == 200
    enroll_id = res1.json()["data"]["id"]

    # Enroll Second Time (Idempotency)
    res2 = client.post("/api/v1/enrollments", json=enroll_payload)
    assert res2.status_code == 200
    assert res2.json()["data"]["id"] == enroll_id

    app.dependency_overrides.clear()
