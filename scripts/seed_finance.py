import sys
from pathlib import Path
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

# Resolve backend module structures
backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.dependencies import SessionLocal
from app.models.models import (
    Role, User, ParentProfile, ParentStudentLink, AcademicYear, Program, Department,
    FeeCategory, FeeStructure, FeeComponent, StudentFeeAssignment, FeeInvoice,
    InvoiceItem, Payment, Receipt, Scholarship, ScholarshipApplication,
    StudentScholarship, FeeConcession, FinePenalty, StudentLedgerEntry, FinancialHold
)
from app.core.security import get_password_hash
from app.services.finance_service import FinanceService

CATEGORIES = ["Tuition", "Examination", "Hostel", "Transport", "Library Fine"]

def seed():
    print("[i] Seeding Finance system data...")
    db = SessionLocal()
    try:
        # 1. Resolve roles
        student_role = db.query(Role).filter_by(name="STUDENT").first()
        parent_role = db.query(Role).filter_by(name="PARENT").first()
        finance_role = db.query(Role).filter_by(name="FINANCE_OFFICE").first()
        if not finance_role:
            finance_role = Role(id=str(uuid.uuid4()), name="FINANCE_OFFICE", description="Finance Office role")
            db.add(finance_role)
            db.flush()

        # 2. Seed Fee Categories
        for cat_name in CATEGORIES:
            existing = db.query(FeeCategory).filter_by(name=cat_name).first()
            if not existing:
                db.add(FeeCategory(name=cat_name, description=f"{cat_name} fee category"))
        db.flush()

        # 3. Create Finance User
        pwd_hash = get_password_hash("FinancePassword@123")
        fin_user = db.query(User).filter_by(email="finance_fee@campusgpt.com").first()
        if not fin_user:
            fin_user = User(
                email="finance_fee@campusgpt.com",
                username="finance_fee",
                passwordHash=pwd_hash,
                name="Finance Officer",
                roleId=finance_role.id,
                mustChangePassword=False,
                verified=True
            )
            db.add(fin_user)
            db.flush()

        # 4. Create Students A, B, C and Parent
        student_pwd = get_password_hash("StudentPassword@123")

        # Student A (Partially paid)
        student_a = db.query(User).filter_by(email="student_fee_a@campusgpt.com").first()
        if not student_a:
            student_a = User(
                email="student_fee_a@campusgpt.com",
                username="student_fee_a",
                passwordHash=student_pwd,
                name="Student A (Partially Paid)",
                roleId=student_role.id,
                mustChangePassword=False,
                verified=True
            )
            db.add(student_a)
            db.flush()

        # Student B (Scholarship recipient)
        student_b = db.query(User).filter_by(email="student_fee_b@campusgpt.com").first()
        if not student_b:
            student_b = User(
                email="student_fee_b@campusgpt.com",
                username="student_fee_b",
                passwordHash=student_pwd,
                name="Student B (Scholarship)",
                roleId=student_role.id,
                mustChangePassword=False,
                verified=True
            )
            db.add(student_b)
            db.flush()

        # Student C (Overdue + Hold)
        student_c = db.query(User).filter_by(email="student_fee_c@campusgpt.com").first()
        if not student_c:
            student_c = User(
                email="student_fee_c@campusgpt.com",
                username="student_fee_c",
                passwordHash=student_pwd,
                name="Student C (Overdue)",
                roleId=student_role.id,
                mustChangePassword=False,
                verified=True
            )
            db.add(student_c)
            db.flush()

        # Parent Profile and Link
        parent_user = db.query(User).filter_by(email="parent_fee@campusgpt.com").first()
        if not parent_user:
            parent_user = User(
                email="parent_fee@campusgpt.com",
                username="parent_fee",
                passwordHash=get_password_hash("ParentPassword@123"),
                name="Parent User",
                roleId=parent_role.id,
                mustChangePassword=False,
                verified=True
            )
            db.add(parent_user)
            db.flush()

            parent_prof = ParentProfile(userId=parent_user.id, phoneNumber="9876543210")
            db.add(parent_prof)
            db.flush()

            parent_link = ParentStudentLink(
                parentId=parent_prof.id,
                studentId=student_a.id,
                relationship="MOTHER",
                canViewFees=True,
                status="VERIFIED"
            )
            db.add(parent_link)
            db.flush()

        # 5. Setup Academic Year and Program
        ay = db.query(AcademicYear).filter_by(name="AY-2026").first()
        if not ay:
            ay = AcademicYear(name="AY-2026", startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=365), status="ACTIVE")
            db.add(ay)
            db.flush()

        prog = db.query(Program).filter_by(code="CSE").first()
        if not prog:
            # Query first department or seed default
            dept = db.query(Department).first()
            dept_id = dept.id if dept else "dept-cse-1"
            if not dept:
                dept = Department(id=dept_id, name="Computer Science Dept", code="CS")
                db.add(dept)
                db.flush()
            prog = Program(name="B.Tech Computer Science", code="CSE", departmentId=dept_id)
            db.add(prog)
            db.flush()

        # 6. Configure Fee Structure
        struct = db.query(FeeStructure).filter_by(academicYearId=ay.id, programId=prog.id).first()
        if not struct:
            struct = FeeStructure(
                academicYearId=ay.id,
                programId=prog.id,
                category="REGULAR",
                quota="MERIT",
                currency="INR",
                status="ACTIVE"
            )
            db.add(struct)
            db.flush()

            db.add(FeeComponent(feeStructureId=struct.id, name="Tuition Fee", code="TUI", amount=Decimal("50000.00"), dueDate=datetime.utcnow() + timedelta(days=60)))
            db.add(FeeComponent(feeStructureId=struct.id, name="Examination Fee", code="EXM", amount=Decimal("10000.00"), dueDate=datetime.utcnow() + timedelta(days=60)))
            db.flush()

        # 7. Student Assignments
        for std in [student_a, student_b, student_c]:
            assign = db.query(StudentFeeAssignment).filter_by(studentId=std.id, feeStructureId=struct.id).first()
            if not assign:
                db.add(StudentFeeAssignment(studentId=std.id, feeStructureId=struct.id, netPayable=Decimal("60000.00")))
        db.flush()

        # 8. Create Invoices and payments idempotently
        # A. Partially Paid Invoice
        inv_a = db.query(FeeInvoice).filter_by(invoiceNumber="INV-DEMO-A").first()
        if not inv_a:
            inv_a = FeeInvoice(
                invoiceNumber="INV-DEMO-A",
                studentId=student_a.id,
                currency="INR",
                subtotal=Decimal("60000.00"),
                totalAmount=Decimal("60000.00"),
                paidAmount=Decimal("20000.00"),
                balanceAmount=Decimal("40000.00"),
                dueDate=datetime.utcnow() + timedelta(days=30),
                status="PARTIALLY_PAID",
                issuedAt=datetime.utcnow()
            )
            db.add(inv_a)
            db.flush()

            db.add(InvoiceItem(invoiceId=inv_a.id, componentName="Tuition Fee", componentCode="TUI", amount=Decimal("50000.00")))
            db.add(InvoiceItem(invoiceId=inv_a.id, componentName="Examination Fee", componentCode="EXM", amount=Decimal("10000.00")))
            db.flush()

            # Record Payment of 20000
            payment = Payment(
                paymentNumber="PAY-DEMO-A1",
                invoiceId=inv_a.id,
                studentId=student_a.id,
                amount=Decimal("20000.00"),
                currency="INR",
                method="UPI",
                status="SUCCESS",
                provider="SIMULATED_DEMO_PAYMENT_PROVIDER",
                idempotencyKey="idem-demo-a1",
                paidAt=datetime.utcnow()
            )
            db.add(payment)
            db.flush()

            # Generate Receipt
            db.add(Receipt(
                receiptNumber="REC-DEMO-A1",
                paymentId=payment.id,
                studentId=student_a.id,
                amount=Decimal("20000.00"),
                currency="INR",
                verificationToken="VERIFY-DEMO-A1"
            ))

            # Post Ledger entries
            FinanceService.record_ledger_entry(db, student_a.id, Decimal("60000.00"), "DEBIT", "INVOICE", inv_a.id, "Invoice billing TUI+EXM", fin_user.id)
            FinanceService.record_ledger_entry(db, student_a.id, Decimal("20000.00"), "CREDIT", "PAYMENT", payment.id, "Demo Payment recorded", fin_user.id)

        # B. Scholarship Recipient Student B
        inv_b = db.query(FeeInvoice).filter_by(invoiceNumber="INV-DEMO-B").first()
        if not inv_b:
            # Create scholarship scheme
            scholar = db.query(Scholarship).filter_by(name="Academic Excellence").first()
            if not scholar:
                scholar = Scholarship(
                    name="Academic Excellence",
                    type="Merit Scholarship",
                    fixedAmount=Decimal("15000.00"),
                    validFrom=datetime.utcnow(),
                    validTo=datetime.utcnow() + timedelta(days=365),
                    status="ACTIVE"
                )
                db.add(scholar)
                db.flush()

            # Apply and Award
            app = ScholarshipApplication(scholarshipId=scholar.id, studentId=student_b.id, status="APPROVED", remarks="Approved Merit Waiver")
            db.add(app)
            db.flush()

            db.add(StudentScholarship(studentId=student_b.id, scholarshipId=scholar.id, amountAwarded=Decimal("15000.00")))
            db.flush()

            # Bill Invoice B: 60k - 15k scholarship = 45k
            inv_b = FeeInvoice(
                invoiceNumber="INV-DEMO-B",
                studentId=student_b.id,
                currency="INR",
                subtotal=Decimal("60000.00"),
                scholarshipAmount=Decimal("15000.00"),
                totalAmount=Decimal("45000.00"),
                paidAmount=Decimal("0.00"),
                balanceAmount=Decimal("45000.00"),
                dueDate=datetime.utcnow() + timedelta(days=30),
                status="ISSUED",
                issuedAt=datetime.utcnow()
            )
            db.add(inv_b)
            db.flush()

            db.add(InvoiceItem(invoiceId=inv_b.id, componentName="Tuition Fee", componentCode="TUI", amount=Decimal("50000.00")))
            db.add(InvoiceItem(invoiceId=inv_b.id, componentName="Examination Fee", componentCode="EXM", amount=Decimal("10000.00")))
            db.flush()

            # Post Ledger entries
            FinanceService.record_ledger_entry(db, student_b.id, Decimal("45000.00"), "DEBIT", "INVOICE", inv_b.id, "Invoice billing with scholarship offset", fin_user.id)

        # C. Overdue Invoice and Hold Student C
        inv_c = db.query(FeeInvoice).filter_by(invoiceNumber="INV-DEMO-C").first()
        if not inv_c:
            inv_c = FeeInvoice(
                invoiceNumber="INV-DEMO-C",
                studentId=student_c.id,
                currency="INR",
                subtotal=Decimal("60000.00"),
                totalAmount=Decimal("60000.00"),
                paidAmount=Decimal("0.00"),
                balanceAmount=Decimal("60000.00"),
                dueDate=datetime.utcnow() - timedelta(days=5),  # 5 days ago
                status="ISSUED",
                issuedAt=datetime.utcnow() - timedelta(days=35)
            )
            db.add(inv_c)
            db.flush()

            db.add(InvoiceItem(invoiceId=inv_c.id, componentName="Tuition Fee", componentCode="TUI", amount=Decimal("50000.00")))
            db.add(InvoiceItem(invoiceId=inv_c.id, componentName="Examination Fee", componentCode="EXM", amount=Decimal("10000.00")))
            db.flush()

            # Place Hold due to overdue
            db.add(FinancialHold(
                studentId=student_c.id,
                reason="Overdue tuition fee billing limit exceeded",
                active=True,
                placedBy=fin_user.id,
                placedAt=datetime.utcnow()
            ))

            # Post Ledger debit
            FinanceService.record_ledger_entry(db, student_c.id, Decimal("60000.00"), "DEBIT", "INVOICE", inv_c.id, "Invoice billing overdue", fin_user.id)

        db.commit()
        print("[SUCCESS] Seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
