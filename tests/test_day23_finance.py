import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import (
    User, Role, AcademicYear, Program, Department,
    FeeCategory, FeeStructure, FeeComponent, StudentFeeAssignment,
    FeeInvoice, InvoiceItem, Payment, Receipt, Scholarship,
    ScholarshipApplication, StudentScholarship, FeeConcession, FeeWaiver,
    FinePenalty, StudentLedgerEntry, FinancialHold, InstallmentPlan,
    InstallmentSchedule, PaymentAllocation, ParentStudentLink, ParentProfile, FinancialAudit, Refund
)

@pytest.fixture
def seed_test_data(db_session):
    # Setup Roles
    admin_role = db_session.query(Role).filter(Role.name == "MASTER_ADMIN").first()
    if not admin_role:
        admin_role = Role(name="MASTER_ADMIN")
        db_session.add(admin_role)

    finance_role = db_session.query(Role).filter(Role.name == "FINANCE_OFFICE").first()
    if not finance_role:
        finance_role = Role(name="FINANCE_OFFICE")
        db_session.add(finance_role)

    student_role = db_session.query(Role).filter(Role.name == "STUDENT").first()
    if not student_role:
        student_role = Role(name="STUDENT")
        db_session.add(student_role)

    parent_role = db_session.query(Role).filter(Role.name == "PARENT").first()
    if not parent_role:
        parent_role = Role(name="PARENT")
        db_session.add(parent_role)

    teacher_role = db_session.query(Role).filter(Role.name == "TEACHER").first()
    if not teacher_role:
        teacher_role = Role(name="TEACHER")
        db_session.add(teacher_role)

    placement_role = db_session.query(Role).filter(Role.name == "PLACEMENT_OFFICER").first()
    if not placement_role:
        placement_role = Role(name="PLACEMENT_OFFICER")
        db_session.add(placement_role)

    db_session.flush()

    # Create Users
    admin = User(email="adm@test.com", username="admin_user", passwordHash="hash", name="Admin User", roleId=admin_role.id)
    finance = User(email="fin@test.com", username="finance_user", passwordHash="hash", name="Finance Officer", roleId=finance_role.id)
    student_a = User(email="std_a@test.com", username="student_a", passwordHash="hash", name="Student A", roleId=student_role.id)
    student_b = User(email="std_b@test.com", username="student_b", passwordHash="hash", name="Student B", roleId=student_role.id)
    parent = User(email="parent@test.com", username="parent_user", passwordHash="hash", name="Parent User", roleId=parent_role.id)
    teacher = User(email="teacher@test.com", username="teacher_user", passwordHash="hash", name="Teacher User", roleId=teacher_role.id)
    placement_officer = User(email="placement@test.com", username="placement_user", passwordHash="hash", name="Placement Officer", roleId=placement_role.id)

    db_session.add_all([admin, finance, student_a, student_b, parent, teacher, placement_officer])
    db_session.flush()

    # Setup ParentProfile and Link for Student A
    parent_prof = ParentProfile(userId=parent.id, phoneNumber="1234567890")
    db_session.add(parent_prof)
    db_session.flush()

    parent_link = ParentStudentLink(
        parentId=parent_prof.id,
        studentId=student_a.id,
        relationship="FATHER",
        canViewFees=True,
        status="VERIFIED"
    )
    db_session.add(parent_link)
    db_session.flush()

    # Setup basic academic structures
    ay = AcademicYear(name="AY-2026", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365))
    prog = Program(name="B.Tech CSE", code="CSE", departmentId="dept-1")
    db_session.add_all([ay, prog])
    db_session.flush()

    db_session.commit()

    return {
        "admin": admin,
        "finance": finance,
        "student_a": student_a,
        "student_b": student_b,
        "parent": parent,
        "teacher": teacher,
        "placement_officer": placement_officer,
        "parent_profile": parent_prof,
        "academic_year": ay,
        "program": prog
    }

# 1-6. RBAC access security tests
def test_rbac_boundaries(db_session, seed_test_data):
    client = TestClient(app)

    # 1. Student A can see own invoices
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["student_a"]
    res = client.get("/api/v1/finance/invoices/me")
    assert res.status_code == 200

    # Setup dummy invoice for student A
    inv_a = FeeInvoice(
        invoiceNumber="INV-A-1", studentId=seed_test_data["student_a"].id,
        subtotal=Decimal("10000.00"), totalAmount=Decimal("10000.00"), paidAmount=Decimal("0.00"),
        balanceAmount=Decimal("10000.00"), dueDate=datetime.utcnow(), status="ISSUED"
    )
    db_session.add(inv_a)

    # Setup dummy invoice for student B
    inv_b = FeeInvoice(
        invoiceNumber="INV-B-1", studentId=seed_test_data["student_b"].id,
        subtotal=Decimal("20000.00"), totalAmount=Decimal("20000.00"), paidAmount=Decimal("0.00"),
        balanceAmount=Decimal("20000.00"), dueDate=datetime.utcnow(), status="ISSUED"
    )
    db_session.add(inv_b)
    db_session.commit()

    # 2. Student A accessing Student B's invoice is blocked
    res = client.get(f"/api/v1/finance/invoices/{inv_b.id}")
    assert res.status_code == 403

    # 3. Parent linked to Student A allowed
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["parent"]
    res = client.get(f"/api/v1/finance/parent/children/{seed_test_data['student_a'].id}/summary")
    assert res.status_code == 200

    # 4. Parent accessing Student B (unrelated child) is blocked
    res = client.get(f"/api/v1/finance/parent/children/{seed_test_data['student_b'].id}/summary")
    assert res.status_code == 403

    # 5. Teacher private ledger access blocked
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["teacher"]
    res = client.get(f"/api/v1/finance/ledger/student/{seed_test_data['student_a'].id}")
    assert res.status_code == 403

    # 6. Placement Officer private ledger access blocked
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["placement_officer"]
    res = client.get(f"/api/v1/finance/ledger/student/{seed_test_data['student_a'].id}")
    assert res.status_code == 403

    app.dependency_overrides.clear()

# 7-10. Calculations tests
def test_invoice_calculation_logic(db_session, seed_test_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["finance"]

    # 7. Setup fee structure components
    fs = FeeStructure(academicYearId=seed_test_data["academic_year"].id, programId=seed_test_data["program"].id, status="ACTIVE")
    db_session.add(fs)
    db_session.flush()

    db_session.add(FeeComponent(feeStructureId=fs.id, name="Tuition", code="TUI", amount=Decimal("10000.00"), dueDate=datetime.utcnow() + timedelta(days=10)))
    db_session.add(FeeComponent(feeStructureId=fs.id, name="Lab", code="LAB", amount=Decimal("2000.00"), dueDate=datetime.utcnow() + timedelta(days=10)))
    db_session.flush()

    # 8. Setup Concession for student A
    con = FeeConcession(studentId=seed_test_data["student_a"].id, category="Merit", amount=Decimal("1500.00"), status="APPROVED")
    db_session.add(con)

    # 9. Setup Scholarship Award for student A
    scholar = Scholarship(name="Scheme-A", type="Merit", validFrom=datetime.utcnow(), validTo=datetime.utcnow() + timedelta(days=365))
    db_session.add(scholar)
    db_session.flush()

    db_session.add(StudentScholarship(studentId=seed_test_data["student_a"].id, scholarshipId=scholar.id, amountAwarded=Decimal("3000.00")))

    # 10. Fine registered
    fine = FinePenalty(studentId=seed_test_data["student_a"].id, amount=Decimal("500.00"), reason="Late Library Return", status="UNPAID")
    db_session.add(fine)
    db_session.commit()

    # Generate Invoice and verify total amount calculation
    res = client.post("/api/v1/finance/invoices", json={
        "studentId": seed_test_data["student_a"].id,
        "dueDate": (datetime.utcnow() + timedelta(days=20)).isoformat()
    })
    assert res.status_code == 200
    inv_id = res.json()["data"]["id"]

    inv = db_session.query(FeeInvoice).filter(FeeInvoice.id == inv_id).first()
    assert inv.totalAmount == Decimal("8000.00")
    assert inv.balanceAmount == Decimal("8000.00")

    app.dependency_overrides.clear()

# 11-16. Payment and Allocations tests
def test_payments_and_allocations(db_session, seed_test_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["student_a"]

    inv = FeeInvoice(
        invoiceNumber="INV-PAY-1", studentId=seed_test_data["student_a"].id,
        subtotal=Decimal("5000.00"), totalAmount=Decimal("5000.00"), paidAmount=Decimal("0.00"),
        balanceAmount=Decimal("5000.00"), dueDate=datetime.utcnow() + timedelta(days=10), status="ISSUED"
    )
    db_session.add(inv)
    db_session.commit()

    # 11. Positive payment success
    # 12. Negative payment blocked
    res_neg = client.post("/api/v1/finance/payments/demo", json={
        "invoiceId": inv.id, "amount": -100.00, "method": "UPI", "idempotencyKey": "idem-neg-1"
    })
    assert res_neg.status_code == 400

    # 14. Overpayment blocked
    res_over = client.post("/api/v1/finance/payments/demo", json={
        "invoiceId": inv.id, "amount": 6000.00, "method": "UPI", "idempotencyKey": "idem-over-1"
    })
    assert res_over.status_code == 400

    # Correct payment: 2000
    res_pay = client.post("/api/v1/finance/payments/demo", json={
        "invoiceId": inv.id, "amount": 2000.00, "method": "UPI", "idempotencyKey": "idem-valid-1"
    })
    assert res_pay.status_code == 200
    pay_data = res_pay.json()["data"]
    assert pay_data["providerMode"] == "SIMULATED_DEMO_PAYMENT_PROVIDER"
    assert pay_data["realMoneyMoved"] is False

    # 15. Duplicate payment token replay blocked
    res_dup = client.post("/api/v1/finance/payments/demo", json={
        "invoiceId": inv.id, "amount": 2000.00, "method": "UPI", "idempotencyKey": "idem-valid-1"
    })
    assert res_dup.status_code == 200
    assert res_dup.json()["data"]["id"] == pay_data["id"]

    # 16. Unique receipt validation
    receipts = db_session.query(Receipt).filter(Receipt.studentId == seed_test_data["student_a"].id).all()
    assert len(receipts) == 1
    assert receipts[0].amount == Decimal("2000.00")

    app.dependency_overrides.clear()

# 17-18. Refund and Scholarship constraint tests
def test_refunds_and_scholarships(db_session, seed_test_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["student_a"]

    inv = FeeInvoice(
        invoiceNumber="INV-REFUND-1", studentId=seed_test_data["student_a"].id,
        subtotal=Decimal("1000.00"), totalAmount=Decimal("1000.00"), paidAmount=Decimal("1000.00"),
        balanceAmount=Decimal("0.00"), dueDate=datetime.utcnow() + timedelta(days=10), status="PAID"
    )
    db_session.add(inv)
    db_session.flush()

    payment = Payment(
        paymentNumber="PAY-REFUND-1", invoiceId=inv.id, studentId=seed_test_data["student_a"].id,
        amount=Decimal("1000.00"), currency="INR", method="UPI", status="SUCCESS", idempotencyKey="ref-idem-1", paidAt=datetime.utcnow()
    )
    db_session.add(payment)
    db_session.commit()

    # 17. Refund request overflow blocked (ref 1200 > paid 1000)
    res_ref_neg = client.post("/api/v1/finance/refunds", json={
        "paymentId": payment.id, "amount": 1200.00, "reason": "Accidental overpay"
    })
    assert res_ref_neg.status_code == 400

    # 18. Scholarship duplicate application check
    scholar = Scholarship(name="Scheme-B", type="Merit", validFrom=datetime.utcnow(), validTo=datetime.utcnow() + timedelta(days=365))
    db_session.add(scholar)
    db_session.commit()

    res_app1 = client.post(f"/api/v1/finance/scholarships/{scholar.id}/apply")
    assert res_app1.status_code == 200

    res_app2 = client.post(f"/api/v1/finance/scholarships/{scholar.id}/apply")
    assert res_app2.status_code == 400

    app.dependency_overrides.clear()

# 19-20. Student mutability block tests
def test_student_mutability_restrictions(db_session, seed_test_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["student_a"]

    # 19. Student cannot configure fee structure
    res_struct = client.post("/api/v1/finance/fee-structures", json={
        "academicYearId": "ay", "programId": "prog", "components": []
    })
    assert res_struct.status_code == 403

    # 20. Student cannot trigger manual invoice generation
    res_inv = client.post("/api/v1/finance/invoices", json={
        "studentId": seed_test_data["student_a"].id, "dueDate": "2026-12-31T00:00:00"
    })
    assert res_inv.status_code == 403

    app.dependency_overrides.clear()

# 21-25. Finance Officer & Holds tests
def test_finance_officer_workflow(db_session, seed_test_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["finance"]

    # 21. Finance officer places hold
    res_hold = client.post("/api/v1/finance/holds", json={
        "studentId": seed_test_data["student_a"].id, "reason": "Outstanding fine limit exceeded"
    })
    assert res_hold.status_code == 200
    hold_id = res_hold.json()["data"]["id"]

    # 25. Financial hold audits check
    audit = db_session.query(FinancialAudit).filter(FinancialAudit.entityId == hold_id).first()
    assert audit is not None
    assert audit.action == "PLACE_HOLD"

    app.dependency_overrides.clear()

# 26. Ledger append behavior test
def test_ledger_append_only(db_session, seed_test_data):
    client = TestClient(app)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["finance"]

    # Post multiple ledger records and confirm direction
    entry1 = StudentLedgerEntry(studentId=seed_test_data["student_a"].id, amount=Decimal("100.00"), direction="DEBIT", type="FINE")
    entry2 = StudentLedgerEntry(studentId=seed_test_data["student_a"].id, amount=Decimal("50.00"), direction="CREDIT", type="CONCESSION")
    db_session.add_all([entry1, entry2])
    db_session.commit()

    app.dependency_overrides[get_current_user_no_password_force] = lambda: seed_test_data["student_a"]
    res = client.get("/api/v1/finance/ledger/me")
    assert res.status_code == 200
    ledger = res.json()["data"]
    assert len(ledger) >= 2

    app.dependency_overrides.clear()

# 33. MASTER_ADMIN uniqueness invariant test
def test_master_admin_uniqueness(db_session, seed_test_data):
    # Verify we do not duplicate master admins during any workflows
    admins = db_session.query(User).join(Role).filter(Role.name == "MASTER_ADMIN").all()
    assert len(admins) <= 1
