import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from decimal import Decimal

from app.core.auth_middleware import get_current_user_no_password_force
from app.main import app
from app.models.models import (
    User, Role, FeeStructure, FeeComponent, StudentFeeAssignment,
    FeeInvoice, Payment, Receipt, Scholarship, ScholarshipApplication, StudentScholarship
)

@pytest.fixture
def seed_fee_users(db_session):
    admin_role = db_session.query(Role).filter(Role.name == "MASTER_ADMIN").first()
    finance_role = db_session.query(Role).filter(Role.name == "FINANCE_OFFICE").first()
    if not finance_role:
        finance_role = Role(name="FINANCE_OFFICE")
        db_session.add(finance_role)
        db_session.flush()
    student_role = db_session.query(Role).filter(Role.name == "STUDENT").first()

    admin = User(email="admin_fee@test.com", username="admin_fee", passwordHash="hash", name="Admin", roleId=admin_role.id)
    finance = User(email="finance@test.com", username="finance_user", passwordHash="hash", name="Finance", roleId=finance_role.id)
    student = User(email="student_fee@test.com", username="student_fee_user", passwordHash="hash", name="Student", roleId=student_role.id)

    db_session.add_all([admin, finance, student])
    db_session.commit()

    return {
        "admin": admin,
        "finance": finance,
        "student": student
    }

def test_fee_structure_and_invoice(db_session, seed_fee_users):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_fee_users["finance"]

    # 1. Create Fee Structure
    struct_payload = {
        "academicYearId": "ay-2026",
        "programId": "prog-cs",
        "category": "GENERAL",
        "quota": "MERIT",
        "currency": "INR",
        "components": [
            {"name": "Tuition Fee", "code": "TUI", "amount": 50000.00, "dueDate": "2026-12-31T00:00:00"},
            {"name": "Lab Fee", "code": "LAB", "amount": 10000.00, "dueDate": "2026-12-31T00:00:00"}
        ]
    }

    res_struct = client.post("/api/v1/fee-structures", json=struct_payload)
    assert res_struct.status_code == 200
    struct_id = res_struct.json()["data"]["id"]

    # 2. Generate Invoice
    inv_payload = {
        "studentId": seed_fee_users["student"].id,
        "dueDate": "2026-12-31T00:00:00"
    }

    res_inv = client.post("/api/v1/invoices", json=inv_payload)
    assert res_inv.status_code == 200
    inv_id = res_inv.json()["data"]["id"]

    # Verify balanceAmount = 60000.00
    invoice = db_session.query(FeeInvoice).filter(FeeInvoice.id == inv_id).first()
    assert invoice is not None
    assert invoice.totalAmount == Decimal("60000.00")
    assert invoice.balanceAmount == Decimal("60000.00")

    app.dependency_overrides.clear()

def test_payment_and_overpayment_rejection(db_session, seed_fee_users):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_fee_users["student"]

    # Setup invoice
    invoice = FeeInvoice(
        invoiceNumber="INV-MOCK-1",
        studentId=seed_fee_users["student"].id,
        subtotal=Decimal("20000.00"),
        scholarshipAmount=Decimal("0.00"),
        discountAmount=Decimal("0.00"),
        adjustmentAmount=Decimal("0.00"),
        taxAmount=Decimal("0.00"),
        totalAmount=Decimal("20000.00"),
        paidAmount=Decimal("0.00"),
        balanceAmount=Decimal("20000.00"),
        dueDate=datetime(2026, 12, 31),
        status="ISSUED"
    )
    db_session.add(invoice)
    db_session.commit()

    # Overpayment amount: 25000.00 -> should fail
    pay_payload_invalid = {
        "invoiceId": invoice.id,
        "amount": 25000.00,
        "method": "UPI",
        "idempotencyKey": "idem-key-1"
    }
    res_inv = client.post("/api/v1/payments", json=pay_payload_invalid)
    assert res_inv.status_code == 400

    # Correct payment: 10000.00 -> success
    pay_payload_valid = {
        "invoiceId": invoice.id,
        "amount": 10000.00,
        "method": "UPI",
        "idempotencyKey": "idem-key-2"
    }
    res_valid = client.post("/api/v1/payments", json=pay_payload_valid)
    assert res_valid.status_code == 200
    pay_id = res_valid.json()["data"]["id"]

    # Confirm Payment
    res_conf = client.post(f"/api/v1/payments/{pay_id}/confirm")
    assert res_conf.status_code == 200

    db_session.refresh(invoice)
    assert invoice.paidAmount == Decimal("10000.00")
    assert invoice.balanceAmount == Decimal("10000.00")
    assert invoice.status == "PARTIALLY_PAID"

    app.dependency_overrides.clear()

def test_scholarships(db_session, seed_fee_users):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_fee_users["finance"]

    # Create scholarship
    sch_payload = {
        "name": "Merit Waiver",
        "type": "Merit Scholarship",
        "fixedAmount": 15000.00,
        "validFrom": "2026-06-01T00:00:00",
        "validTo": "2027-05-31T00:00:00"
    }
    res_sch = client.post("/api/v1/scholarships", json=sch_payload)
    assert res_sch.status_code == 200
    sch_id = res_sch.json()["data"]["id"]

    # Student applies
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_fee_users["student"]
    res_app = client.post("/api/v1/scholarship-applications", json={"scholarshipId": sch_id})
    assert res_app.status_code == 200
    app_id = res_app.json()["data"]["id"]

    # Finance approves
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_fee_users["finance"]
    res_rev = client.post(f"/api/v1/scholarship-applications/{app_id}/review", json={"status": "APPROVED", "remarks": "Approved"})
    assert res_rev.status_code == 200

    # Verify awarded
    award = db_session.query(StudentScholarship).filter(StudentScholarship.studentId == seed_fee_users["student"].id).first()
    assert award is not None
    assert award.amountAwarded == Decimal("15000.00")

    app.dependency_overrides.clear()
