import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, AcademicYear, Program, Department,
    FeeCategory, FeeStructure, FeeComponent, StudentFeeAssignment,
    FeeInvoice, InvoiceItem, Payment, Receipt, Scholarship,
    ScholarshipApplication, StudentScholarship, FeeConcession, FeeWaiver,
    FinePenalty, StudentLedgerEntry, FinancialHold, InstallmentPlan,
    InstallmentSchedule, PaymentAllocation, ParentStudentLink, ParentProfile, FinancialAudit, Refund
)
from app.services.finance_service import FinanceService, format_money
from app.services.notification_service import NotificationService

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class FeeCategoryPayload(BaseModel):
    name: str
    description: Optional[str] = None

class FeeCategoryUpdatePayload(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ComponentPayload(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    amount: float
    mandatory: bool = True
    refundable: bool = False
    dueDate: datetime
    sortOrder: int = 0

class FeeStructurePayload(BaseModel):
    academicYearId: str
    programId: str
    category: Optional[str] = None
    quota: Optional[str] = None
    currency: str = "INR"
    components: List[ComponentPayload]

class StudentAssignmentPayload(BaseModel):
    studentId: str
    feeStructureId: str

class InvoiceGeneratePayload(BaseModel):
    studentId: str
    enrollmentId: Optional[str] = None
    dueDate: datetime

class InstallmentPlanPayload(BaseModel):
    invoiceId: str
    name: str
    numberOfInstallments: int

class DemoPaymentPayload(BaseModel):
    invoiceId: str
    amount: float
    currency: str = "INR"
    method: str  # CASH, UPI, CREDIT_CARD, DEBIT_CARD
    idempotencyKey: str

class ScholarshipPayload(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    percentageAmount: Optional[float] = None
    fixedAmount: Optional[float] = None
    maximumBenefit: Optional[float] = None
    eligibility: Optional[str] = None
    validFrom: datetime
    validTo: datetime

class ReviewApplicationPayload(BaseModel):
    status: str  # APPROVED, REJECTED
    remarks: Optional[str] = None

class ConcessionPayload(BaseModel):
    studentId: str
    category: str
    amount: float
    description: Optional[str] = None

class WaiverPayload(BaseModel):
    invoiceId: str
    amount: float
    reason: str

class FinePayload(BaseModel):
    studentId: str
    invoiceId: Optional[str] = None
    amount: float
    reason: str

class RefundRequestPayload(BaseModel):
    paymentId: str
    amount: float
    reason: str

class RefundReviewPayload(BaseModel):
    status: str  # APPROVED, REJECTED
    remarks: Optional[str] = None

class HoldPayload(BaseModel):
    studentId: str
    reason: str

class ReleaseHoldPayload(BaseModel):
    releaseReason: str

# Helper to generate unique codes
def generate_unique_code(db: Session, prefix: str, model_class, field_name: str) -> str:
    timestamp = int(datetime.utcnow().timestamp())
    rand_hex = uuid.uuid4().hex[:4].upper()
    val = f"{prefix}-{timestamp}-{rand_hex}"
    exists = db.query(model_class).filter(getattr(model_class, field_name) == val).first()
    if exists:
        return generate_unique_code(db, prefix, model_class, field_name)
    return val

# Helper to verify auth role
def check_finance_auth(user: User):
    if user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied. Authorized finance access only.")

# Helper to check hold status block
def enforce_not_held(db: Session, student_id: str):
    if FinanceService.check_financial_holds(db, student_id):
        raise HTTPException(status_code=403, detail="Action blocked due to active financial hold.")

# -------------------------------------------------------------
# FEE CATEGORIES
# -------------------------------------------------------------
@router.get("/fee-categories")
def list_fee_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    categories = db.query(FeeCategory).all()
    return make_response(
        success=True,
        message="Fee categories retrieved successfully.",
        data=[{"id": c.id, "name": c.name, "description": c.description} for c in categories]
    )

@router.post("/fee-categories")
def create_fee_category(
    payload: FeeCategoryPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    # Check uniqueness
    existing = db.query(FeeCategory).filter(FeeCategory.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Fee category name already exists.")

    cat = FeeCategory(name=payload.name, description=payload.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return make_response(
        success=True,
        message="Fee category created successfully.",
        data={"id": cat.id, "name": cat.name}
    )

@router.patch("/fee-categories/{id}")
def update_fee_category(
    id: str,
    payload: FeeCategoryUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    cat = db.query(FeeCategory).filter(FeeCategory.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Fee category not found.")

    if payload.name:
        existing = db.query(FeeCategory).filter(FeeCategory.name == payload.name, FeeCategory.id != id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Fee category name already exists.")
        cat.name = payload.name
    if payload.description is not None:
        cat.description = payload.description

    db.commit()
    return make_response(success=True, message="Fee category updated successfully.")

# -------------------------------------------------------------
# FEE STRUCTURES
# -------------------------------------------------------------
@router.post("/fee-structures")
def create_fee_structure(
    payload: FeeStructurePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    struct = FeeStructure(
        academicYearId=payload.academicYearId,
        programId=payload.programId,
        category=payload.category,
        quota=payload.quota,
        currency=payload.currency,
        status="ACTIVE"
    )
    db.add(struct)
    db.flush()

    for comp in payload.components:
        db.add(FeeComponent(
            feeStructureId=struct.id,
            name=comp.name,
            code=comp.code,
            description=comp.description,
            amount=Decimal(str(comp.amount)),
            mandatory=comp.mandatory,
            refundable=comp.refundable,
            dueDate=comp.dueDate,
            sortOrder=comp.sortOrder
        ))

    db.add(FinancialAudit(
        entityType="FEE_STRUCTURE",
        entityId=struct.id,
        action="CREATE",
        userId=current_user.id,
        newData=f"Configured structure for academic year {payload.academicYearId} program {payload.programId}"
    ))
    db.commit()
    db.refresh(struct)
    return make_response(success=True, message="Fee structure configured successfully.", data={"id": struct.id})

@router.get("/fee-structures")
def list_fee_structures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    structs = db.query(FeeStructure).all()
    return make_response(
        success=True,
        message="Fee structures list retrieved.",
        data=[{
            "id": s.id,
            "academicYearId": s.academicYearId,
            "programId": s.programId,
            "category": s.category,
            "quota": s.quota,
            "currency": s.currency,
            "status": s.status
        } for s in structs]
    )

@router.get("/fee-structures/{id}")
def get_fee_structure(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    s = db.query(FeeStructure).filter(FeeStructure.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Fee structure not found.")

    comps = db.query(FeeComponent).filter(FeeComponent.feeStructureId == id).all()
    return make_response(
        success=True,
        message="Fee structure detail retrieved.",
        data={
            "id": s.id,
            "academicYearId": s.academicYearId,
            "programId": s.programId,
            "category": s.category,
            "quota": s.quota,
            "currency": s.currency,
            "status": s.status,
            "components": [{
                "id": c.id,
                "name": c.name,
                "code": c.code,
                "amount": float(c.amount),
                "mandatory": c.mandatory,
                "refundable": c.refundable,
                "dueDate": c.dueDate.isoformat()
            } for c in comps]
        }
    )

# -------------------------------------------------------------
# STUDENT ASSIGNMENTS
# -------------------------------------------------------------
@router.post("/assignments")
def assign_student_fee(
    payload: StudentAssignmentPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    student = db.query(User).filter(User.id == payload.studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    struct = db.query(FeeStructure).filter(FeeStructure.id == payload.feeStructureId).first()
    if not struct:
        raise HTTPException(status_code=404, detail="Fee structure not found.")

    # Calculate total net payable
    comps = db.query(FeeComponent).filter(FeeComponent.feeStructureId == struct.id).all()
    net = sum(c.amount for c in comps)

    assign = StudentFeeAssignment(
        studentId=payload.studentId,
        feeStructureId=payload.feeStructureId,
        netPayable=net
    )
    db.add(assign)
    db.commit()
    db.refresh(assign)
    return make_response(
        success=True,
        message="Fee structure assigned to student successfully.",
        data={"id": assign.id, "netPayable": float(assign.netPayable)}
    )

@router.get("/assignments/me")
def get_own_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    assigns = db.query(StudentFeeAssignment).filter(StudentFeeAssignment.studentId == current_user.id).all()
    return make_response(
        success=True,
        message="Student assignments retrieved.",
        data=[{
            "id": a.id,
            "feeStructureId": a.feeStructureId,
            "netPayable": float(a.netPayable),
            "createdAt": a.createdAt.isoformat()
        } for a in assigns]
    )

@router.get("/assignments/{id}")
def get_assignment(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    assign = db.query(StudentFeeAssignment).filter(StudentFeeAssignment.id == id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if current_user.role.name == "STUDENT" and assign.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return make_response(
        success=True,
        message="Assignment retrieved.",
        data={
            "id": assign.id,
            "studentId": assign.studentId,
            "feeStructureId": assign.feeStructureId,
            "netPayable": float(assign.netPayable)
        }
    )

# -------------------------------------------------------------
# INVOICES
# -------------------------------------------------------------
@router.post("/invoices")
def generate_invoice(
    payload: InvoiceGeneratePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    student = db.query(User).filter(User.id == payload.studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Enforce Holds check
    enforce_not_held(db, student.id)

    # Resolve structure from assignments or default fallback
    assign = db.query(StudentFeeAssignment).filter(StudentFeeAssignment.studentId == student.id).first()
    struct = None
    if assign:
        struct = db.query(FeeStructure).filter(FeeStructure.id == assign.feeStructureId).first()
    if not struct:
        struct = db.query(FeeStructure).first()

    if not struct:
        raise HTTPException(status_code=400, detail="No active fee structure available for this student.")

    comps = db.query(FeeComponent).filter(FeeComponent.feeStructureId == struct.id).all()
    subtotal = sum(c.amount for c in comps)

    # 1. Scholarship reductions
    scholarship_amt = Decimal("0.00")
    awards = db.query(StudentScholarship).filter(StudentScholarship.studentId == student.id).all()
    for aw in awards:
        scholarship_amt += aw.amountAwarded

    # 2. Concession reductions
    concession_amt = Decimal("0.00")
    concessions = db.query(FeeConcession).filter(FeeConcession.studentId == student.id, FeeConcession.status == "APPROVED").all()
    for con in concessions:
        concession_amt += con.amount

    # 3. Fine penalties additions
    fine_amt = Decimal("0.00")
    fines = db.query(FinePenalty).filter(FinePenalty.studentId == student.id, FinePenalty.status == "UNPAID", FinePenalty.invoiceId == None).all()
    for fn in fines:
        fine_amt += fn.amount

    # 4. Integrations additions (Hostel / Transport Rent)
    integration_items = FinanceService.integrate_hostel_and_transport_charges(db, student.id)
    integration_subtotal = sum(item["amount"] for item in integration_items)

    subtotal += integration_subtotal
    total = subtotal - scholarship_amt - concession_amt + fine_amt
    if total < 0:
        total = Decimal("0.00")

    inv_num = generate_unique_code(db, "INV", FeeInvoice, "invoiceNumber")
    invoice = FeeInvoice(
        invoiceNumber=inv_num,
        studentId=student.id,
        enrollmentId=payload.enrollmentId,
        currency="INR",
        subtotal=subtotal,
        scholarshipAmount=scholarship_amt,
        discountAmount=concession_amt,  # Concession mapped as discount
        adjustmentAmount=Decimal("0.00"),
        taxAmount=Decimal("0.00"),
        totalAmount=total,
        paidAmount=Decimal("0.00"),
        balanceAmount=total,
        dueDate=payload.dueDate,
        status="ISSUED",
        issuedAt=datetime.utcnow()
    )
    db.add(invoice)
    db.flush()

    # Create line items
    for c in comps:
        db.add(InvoiceItem(
            invoiceId=invoice.id,
            componentName=c.name,
            componentCode=c.code,
            amount=c.amount,
            description=c.description
        ))

    # Create integration items
    for it in integration_items:
        db.add(InvoiceItem(
            invoiceId=invoice.id,
            componentName=it["name"],
            componentCode=it["code"],
            amount=it["amount"],
            description=it["description"]
        ))

    # Link unlinked fines to this invoice
    for fn in fines:
        fn.invoiceId = invoice.id

    # Ledger entry debiting invoice total
    FinanceService.record_ledger_entry(
        db=db,
        student_id=student.id,
        amount=invoice.totalAmount,
        direction="DEBIT",
        entry_type="INVOICE",
        reference_id=invoice.id,
        description=f"Generated invoice {invoice.invoiceNumber}",
        actor_id=current_user.id
    )

    # Audited Log
    db.add(FinancialAudit(
        entityType="INVOICE",
        entityId=invoice.id,
        action="ISSUE",
        userId=current_user.id,
        newData=f"Issued invoice {invoice.invoiceNumber} for amount {invoice.totalAmount}"
    ))

    # Send Notification
    NotificationService.create_notification(
        db=db,
        recipient_id=student.id,
        title="Fee Invoice Generated",
        body=f"Your invoice {invoice.invoiceNumber} of INR {invoice.totalAmount} has been generated. Due date: {invoice.dueDate.strftime('%Y-%m-%d')}.",
        category="FEES"
    )

    db.commit()
    db.refresh(invoice)
    return make_response(success=True, message="Invoice generated successfully.", data={"id": invoice.id, "invoiceNumber": invoice.invoiceNumber})

@router.get("/invoices/me")
def get_own_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    invoices = db.query(FeeInvoice).filter(FeeInvoice.studentId == current_user.id).order_by(desc(FeeInvoice.createdAt)).all()
    return make_response(
        success=True,
        message="Invoices retrieved.",
        data=[{
            "id": i.id,
            "invoiceNumber": i.invoiceNumber,
            "totalAmount": float(i.totalAmount),
            "paidAmount": float(i.paidAmount),
            "balanceAmount": float(i.balanceAmount),
            "dueDate": i.dueDate.isoformat(),
            "status": i.status
        } for i in invoices]
    )

@router.get("/invoices/{id}")
def get_invoice_details(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    inv = db.query(FeeInvoice).filter(FeeInvoice.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    # Enforce Student privacy check
    if current_user.role.name == "STUDENT" and inv.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    # Enforce Parent privacy check
    elif current_user.role.name == "PARENT":
        profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=403, detail="Parent profile not found.")
        link = db.query(ParentStudentLink).filter(
            ParentStudentLink.parentId == profile.id,
            ParentStudentLink.studentId == inv.studentId,
            ParentStudentLink.canViewFees == True
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Access restricted to linked child only.")

    items = db.query(InvoiceItem).filter(InvoiceItem.invoiceId == id).all()
    plans = db.query(InstallmentPlan).filter(InstallmentPlan.invoiceId == id).all()

    return make_response(
        success=True,
        message="Invoice detail retrieved.",
        data={
            "id": inv.id,
            "invoiceNumber": inv.invoiceNumber,
            "studentId": inv.studentId,
            "subtotal": float(inv.subtotal),
            "scholarshipAmount": float(inv.scholarshipAmount),
            "discountAmount": float(inv.discountAmount),
            "totalAmount": float(inv.totalAmount),
            "paidAmount": float(inv.paidAmount),
            "balanceAmount": float(inv.balanceAmount),
            "dueDate": inv.dueDate.isoformat(),
            "status": inv.status,
            "items": [{
                "id": it.id,
                "componentName": it.componentName,
                "componentCode": it.componentCode,
                "amount": float(it.amount),
                "description": it.description
            } for it in items],
            "installmentPlans": [{
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "total": float(p.totalAmount)
            } for p in plans]
        }
    )

# -------------------------------------------------------------
# INSTALLMENTS
# -------------------------------------------------------------
@router.post("/installment-plans")
def setup_installment_plan(
    payload: InstallmentPlanPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    try:
        plan = FinanceService.create_installment_plan(
            db=db,
            invoice_id=payload.invoiceId,
            name=payload.name,
            num_installments=payload.numberOfInstallments,
            actor_id=current_user.id
        )
        db.commit()
        return make_response(success=True, message="Installment plan setup successfully.", data={"id": plan.id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/installments/me")
def get_own_installments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    plans = db.query(InstallmentPlan).join(FeeInvoice).filter(FeeInvoice.studentId == current_user.id).all()
    res_plans = []
    for p in plans:
        schedules = db.query(InstallmentSchedule).filter(InstallmentSchedule.installmentPlanId == p.id).all()
        res_plans.append({
            "id": p.id,
            "name": p.name,
            "totalAmount": float(p.totalAmount),
            "status": p.status,
            "schedules": [{
                "id": s.id,
                "installmentNumber": s.installmentNumber,
                "amount": float(s.amount),
                "paidAmount": float(s.paidAmount),
                "dueDate": s.dueDate.isoformat(),
                "status": s.status
            } for s in schedules]
        })
    return make_response(success=True, message="Installment plans retrieved.", data=res_plans)

# -------------------------------------------------------------
# PAYMENTS
# -------------------------------------------------------------
@router.post("/payments/demo")
def process_demo_payment(
    payload: DemoPaymentPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    # Reject raw card details if sent in headers/body to maintain PCI-DSS compliance
    req_body_raw = str(payload)
    if "card" in req_body_raw.lower() or "cvv" in req_body_raw.lower() or "pin" in req_body_raw.lower():
        raise HTTPException(status_code=400, detail="Storage of raw card numbers, PINs, or CVVs is prohibited.")

    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payload.invoiceId).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if current_user.role.name == "STUDENT" and invoice.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Idempotency safety guard
    existing_pay = db.query(Payment).filter(Payment.idempotencyKey == payload.idempotencyKey).first()
    if existing_pay:
        return make_response(
            success=True,
            message="Payment replay completed successfully.",
            data={
                "id": existing_pay.id,
                "paymentNumber": existing_pay.paymentNumber,
                "status": existing_pay.status,
                "providerMode": "SIMULATED_DEMO_PAYMENT_PROVIDER",
                "realMoneyMoved": False
            }
        )

    pay_amt = Decimal(str(payload.amount))
    if pay_amt <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive.")

    # Balance overflow safety guard
    if pay_amt > invoice.balanceAmount:
        raise HTTPException(status_code=400, detail=f"Overpayment blocked. Outstanding invoice balance is {invoice.balanceAmount}")

    pay_num = generate_unique_code(db, "PAY", Payment, "paymentNumber")
    payment = Payment(
        paymentNumber=pay_num,
        invoiceId=invoice.id,
        studentId=invoice.studentId,
        amount=pay_amt,
        currency=payload.currency,
        method=payload.method,
        status="SUCCESS",  # Autoprocess success in demo simulation
        provider="SIMULATED_DEMO_PAYMENT_PROVIDER",
        providerOrderId=f"ORD-SIM-{uuid.uuid4().hex[:6].upper()}",
        providerPaymentId=f"TXN-SIM-{uuid.uuid4().hex[:8].upper()}",
        idempotencyKey=payload.idempotencyKey,
        paidAt=datetime.utcnow()
    )
    db.add(payment)
    db.flush()

    # Update invoice balances
    invoice.paidAmount += pay_amt
    invoice.balanceAmount -= pay_amt
    if invoice.balanceAmount <= 0:
        invoice.status = "PAID"
    else:
        invoice.status = "PARTIALLY_PAID"

    # Process allocations
    FinanceService.process_payment_allocations(db, payment)

    # Post credit ledger entry
    FinanceService.record_ledger_entry(
        db=db,
        student_id=invoice.studentId,
        amount=pay_amt,
        direction="CREDIT",
        entry_type="PAYMENT",
        reference_id=payment.id,
        description=f"Recorded payment {payment.paymentNumber} via {payment.method}",
        actor_id=current_user.id
    )

    # Generate unique receipt
    rec_num = generate_unique_code(db, "REC", Receipt, "receiptNumber")
    token = f"VERIFY-{uuid.uuid4().hex[:12].upper()}"
    receipt = Receipt(
        receiptNumber=rec_num,
        paymentId=payment.id,
        studentId=invoice.studentId,
        amount=pay_amt,
        currency=payment.currency,
        verificationToken=token,
        issuedAt=datetime.utcnow()
    )
    db.add(receipt)

    # Audited log
    db.add(FinancialAudit(
        entityType="PAYMENT",
        entityId=payment.id,
        action="CONFIRM_SUCCESS",
        userId=current_user.id,
        newData=f"Recorded simulated payment {payment.paymentNumber} of amount {payment.amount}"
    ))

    # Send Notification
    NotificationService.create_notification(
        db=db,
        recipient_id=invoice.studentId,
        title="Fee Payment Recorded",
        body=f"Your payment of INR {payment.amount} for invoice {invoice.invoiceNumber} was successfully processed.",
        category="FEES"
    )

    db.commit()
    db.refresh(payment)

    return make_response(
        success=True,
        message="Demo payment processed successfully. Labeled as simulated.",
        data={
            "id": payment.id,
            "paymentNumber": payment.paymentNumber,
            "status": payment.status,
            "providerMode": "SIMULATED_DEMO_PAYMENT_PROVIDER",
            "settlementStatus": "SIMULATED",
            "realMoneyMoved": False
        }
    )

@router.get("/payments/me")
def get_own_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    payments = db.query(Payment).filter(Payment.studentId == current_user.id).order_by(desc(Payment.createdAt)).all()
    return make_response(
        success=True,
        message="Payments retrieved.",
        data=[{
            "id": p.id,
            "paymentNumber": p.paymentNumber,
            "amount": float(p.amount),
            "method": p.method,
            "status": p.status,
            "paidAt": p.paidAt.isoformat() if p.paidAt else None
        } for p in payments]
    )

@router.get("/payments/{id}")
def get_payment(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    p = db.query(Payment).filter(Payment.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")

    if current_user.role.name == "STUDENT" and p.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return make_response(
        success=True,
        message="Payment detail retrieved.",
        data={
            "id": p.id,
            "paymentNumber": p.paymentNumber,
            "amount": float(p.amount),
            "status": p.status,
            "provider": p.provider
        }
    )

# -------------------------------------------------------------
# RECEIPTS
# -------------------------------------------------------------
@router.get("/receipts/me")
def get_own_receipts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    receipts = db.query(Receipt).filter(Receipt.studentId == current_user.id).order_by(desc(Receipt.issuedAt)).all()
    return make_response(
        success=True,
        message="Receipts list retrieved.",
        data=[{
            "id": r.id,
            "receiptNumber": r.receiptNumber,
            "amount": float(r.amount),
            "issuedAt": r.issuedAt.isoformat()
        } for r in receipts]
    )

@router.get("/receipts/{id}")
def get_receipt(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    r = db.query(Receipt).filter(Receipt.id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found.")

    if current_user.role.name == "STUDENT" and r.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    elif current_user.role.name == "PARENT":
        profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=403, detail="Parent profile not found.")
        link = db.query(ParentStudentLink).filter(
            ParentStudentLink.parentId == profile.id,
            ParentStudentLink.studentId == r.studentId,
            ParentStudentLink.canViewFees == True
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Access restricted to linked child only.")

    return make_response(
        success=True,
        message="Receipt detail retrieved.",
        data={
            "id": r.id,
            "receiptNumber": r.receiptNumber,
            "amount": float(r.amount),
            "verificationToken": r.verificationToken,
            "issuedAt": r.issuedAt.isoformat()
        }
    )

# -------------------------------------------------------------
# SCHOLARSHIPS
# -------------------------------------------------------------
@router.post("/scholarships")
def create_scholarship(
    payload: ScholarshipPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    sch = Scholarship(
        name=payload.name,
        type=payload.type,
        description=payload.description,
        percentageAmount=payload.percentageAmount,
        fixedAmount=Decimal(str(payload.fixedAmount)) if payload.fixedAmount else None,
        maximumBenefit=Decimal(str(payload.maximumBenefit)) if payload.maximumBenefit else None,
        eligibility=payload.eligibility,
        validFrom=payload.validFrom,
        validTo=payload.validTo,
        status="ACTIVE"
    )
    db.add(sch)
    db.commit()
    db.refresh(sch)
    return make_response(success=True, message="Scholarship created successfully.", data={"id": sch.id})

@router.get("/scholarships")
def list_scholarships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    scholarships = db.query(Scholarship).filter(Scholarship.status == "ACTIVE").all()
    return make_response(
        success=True,
        message="Active scholarships list retrieved.",
        data=[{
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "eligibility": s.eligibility
        } for s in scholarships]
    )

@router.post("/scholarships/{id}/apply")
def apply_scholarship(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    # Check duplicate application safety guard
    existing = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.scholarshipId == id,
        ScholarshipApplication.studentId == current_user.id,
        ScholarshipApplication.status != "REJECTED"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active/submitted application for this scholarship.")

    # Check eligibility rules
    eligible = FinanceService.evaluate_scholarship_eligibility(db, id, current_user.id)
    if not eligible:
        raise HTTPException(status_code=400, detail="Student does not meet the eligibility requirements for this scholarship.")

    app = ScholarshipApplication(
        scholarshipId=id,
        studentId=current_user.id,
        status="SUBMITTED",
        createdAt=datetime.utcnow()
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return make_response(success=True, message="Scholarship application submitted.", data={"id": app.id})

@router.get("/scholarship-applications/me")
def get_own_scholarship_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    apps = db.query(ScholarshipApplication).filter(ScholarshipApplication.studentId == current_user.id).all()
    return make_response(
        success=True,
        message="Applications retrieved.",
        data=[{
            "id": a.id,
            "scholarshipId": a.scholarshipId,
            "status": a.status,
            "remarks": a.remarks,
            "createdAt": a.createdAt.isoformat()
        } for a in apps]
    )

@router.patch("/scholarship-applications/{id}/status")
def review_scholarship_application(
    id: str,
    payload: ReviewApplicationPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    app = db.query(ScholarshipApplication).filter(ScholarshipApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Scholarship application not found.")

    app.status = payload.status
    app.remarks = payload.remarks

    if payload.status == "APPROVED":
        scholar = db.query(Scholarship).filter(Scholarship.id == app.scholarshipId).first()
        amt = scholar.fixedAmount if scholar.fixedAmount else Decimal("5000.00")

        db.add(StudentScholarship(
            studentId=app.studentId,
            scholarshipId=app.scholarshipId,
            amountAwarded=amt,
            awardedAt=datetime.utcnow()
        ))

        # Credit the student ledger for transparency
        FinanceService.record_ledger_entry(
            db=db,
            student_id=app.studentId,
            amount=amt,
            direction="CREDIT",
            entry_type="CONCESSION",
            reference_id=app.id,
            description=f"Awarded scholarship: {scholar.name}",
            actor_id=current_user.id
        )

    # Trigger Notification
    NotificationService.create_notification(
        db=db,
        recipient_id=app.studentId,
        title="Scholarship Application Reviewed",
        body=f"Your scholarship application was {payload.status}. Remarks: {payload.remarks or 'None'}.",
        category="FEES"
    )

    db.commit()
    return make_response(success=True, message=f"Scholarship application reviewed as {payload.status}.")

# -------------------------------------------------------------
# CONCESSIONS
# -------------------------------------------------------------
@router.post("/concessions")
def create_concession(
    payload: ConcessionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    student = db.query(User).filter(User.id == payload.studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    con = FeeConcession(
        studentId=payload.studentId,
        category=payload.category,
        amount=Decimal(str(payload.amount)),
        description=payload.description,
        status="APPROVED",  # Directly pre-approved by finance officer
        createdAt=datetime.utcnow()
    )
    db.add(con)

    # Ledger credit
    FinanceService.record_ledger_entry(
        db=db,
        student_id=payload.studentId,
        amount=con.amount,
        direction="CREDIT",
        entry_type="CONCESSION",
        reference_id=con.id,
        description=f"Granted fee concession: {con.category}",
        actor_id=current_user.id
    )

    db.commit()
    return make_response(success=True, message="Concession granted successfully.", data={"id": con.id})

# -------------------------------------------------------------
# WAIVERS
# -------------------------------------------------------------
@router.post("/waivers")
def create_waiver(
    payload: WaiverPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payload.invoiceId).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    waiver_amt = Decimal(str(payload.amount))
    if waiver_amt > invoice.balanceAmount:
        raise HTTPException(status_code=400, detail=f"Waiver amount exceeds outstanding invoice balance of {invoice.balanceAmount}")

    waiver = FeeWaiver(
        invoiceId=payload.invoiceId,
        amount=waiver_amt,
        reason=payload.reason,
        approvedBy=current_user.id,
        createdAt=datetime.utcnow()
    )
    db.add(waiver)

    # Adjust invoice balance
    invoice.discountAmount += waiver_amt
    invoice.balanceAmount -= waiver_amt
    if invoice.balanceAmount <= 0:
        invoice.status = "PAID"
    else:
        invoice.status = "PARTIALLY_PAID"

    # Ledger entry credit
    FinanceService.record_ledger_entry(
        db=db,
        student_id=invoice.studentId,
        amount=waiver_amt,
        direction="CREDIT",
        entry_type="WAIVER",
        reference_id=waiver.id,
        description=f"Approved waiver for invoice {invoice.invoiceNumber}. Reason: {payload.reason}",
        actor_id=current_user.id
    )

    db.commit()
    return make_response(success=True, message="Fee waiver posted successfully.", data={"id": waiver.id})

# -------------------------------------------------------------
# FINES
# -------------------------------------------------------------
@router.post("/fines")
def create_fine(
    payload: FinePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    student = db.query(User).filter(User.id == payload.studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    fine = FinePenalty(
        studentId=payload.studentId,
        invoiceId=payload.invoiceId,
        amount=Decimal(str(payload.amount)),
        reason=payload.reason,
        status="UNPAID",
        createdAt=datetime.utcnow()
    )
    db.add(fine)

    if payload.invoiceId:
        invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payload.invoiceId).first()
        if invoice:
            invoice.totalAmount += fine.amount
            invoice.balanceAmount += fine.amount

    # Ledger entry debiting fine
    FinanceService.record_ledger_entry(
        db=db,
        student_id=payload.studentId,
        amount=fine.amount,
        direction="DEBIT",
        entry_type="FINE",
        reference_id=fine.id,
        description=f"Assessed fine penalty: {payload.reason}",
        actor_id=current_user.id
    )

    db.commit()
    return make_response(success=True, message="Fine registered successfully.", data={"id": fine.id})

# -------------------------------------------------------------
# REFUNDS
# -------------------------------------------------------------
@router.post("/refunds")
def request_refund(
    payload: RefundRequestPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    payment = db.query(Payment).filter(Payment.id == payload.paymentId).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")

    if current_user.role.name == "STUDENT" and payment.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    ref_amt = Decimal(str(payload.amount))
    if ref_amt <= 0:
        raise HTTPException(status_code=400, detail="Refund amount must be positive.")

    # Check that total refunds do not exceed successful payment amount
    prev_refunds = db.query(Refund).filter(Refund.paymentId == payment.id, Refund.status != "REJECTED").all()
    refunded_so_far = sum(r.amount for r in prev_refunds)

    if (refunded_so_far + ref_amt) > payment.amount:
        raise HTTPException(status_code=400, detail=f"Refund request exceeds refundable paid amount. Limit remaining: {payment.amount - refunded_so_far}")

    ref = Refund(
        paymentId=payload.paymentId,
        amount=ref_amt,
        reason=payload.reason,
        status="REQUESTED",
        createdAt=datetime.utcnow()
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return make_response(success=True, message="Refund request submitted for review.", data={"id": ref.id})

@router.get("/refunds/me")
def get_own_refunds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    refunds = db.query(Refund).join(Payment).filter(Payment.studentId == current_user.id).all()
    return make_response(
        success=True,
        message="Refund requests retrieved.",
        data=[{
            "id": r.id,
            "paymentId": r.paymentId,
            "amount": float(r.amount),
            "reason": r.reason,
            "status": r.status,
            "createdAt": r.createdAt.isoformat()
        } for r in refunds]
    )

@router.patch("/refunds/{id}/status")
def review_refund_request(
    id: str,
    payload: RefundReviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    ref = db.query(Refund).filter(Refund.id == id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Refund request not found.")

    payment = db.query(Payment).filter(Payment.id == ref.paymentId).first()
    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payment.invoiceId).first()

    ref.status = payload.status

    if payload.status == "APPROVED" or payload.status == "SIMULATED_PROCESSED":
        # Deduct from ledger history
        FinanceService.record_ledger_entry(
            db=db,
            student_id=payment.studentId,
            amount=ref.amount,
            direction="DEBIT",  # Debit to offset the credit
            entry_type="REFUND",
            reference_id=ref.id,
            description=f"Processed simulated refund for payment {payment.paymentNumber}. Reason: {ref.reason}",
            actor_id=current_user.id
        )

        # Notify Refund Changed
        NotificationService.create_notification(
            db=db,
            recipient_id=payment.studentId,
            title="Refund Request Processed",
            body=f"Your refund request of INR {ref.amount} was approved and processed in SIMULATED mode.",
            category="FEES"
        )

    db.commit()
    return make_response(success=True, message=f"Refund request updated to status: {payload.status}.")

# -------------------------------------------------------------
# LEDGER
# -------------------------------------------------------------
@router.get("/ledger/me")
def get_own_ledger(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    entries = db.query(StudentLedgerEntry).filter(StudentLedgerEntry.studentId == current_user.id).order_by(desc(StudentLedgerEntry.createdAt)).all()
    return make_response(
        success=True,
        message="Student ledger entries retrieved.",
        data=[{
            "id": e.id,
            "amount": float(e.amount),
            "direction": e.direction,
            "type": e.type,
            "description": e.description,
            "createdAt": e.createdAt.isoformat()
        } for e in entries]
    )

@router.get("/ledger/student/{student_id}")
def get_student_ledger(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    entries = db.query(StudentLedgerEntry).filter(StudentLedgerEntry.studentId == student_id).order_by(desc(StudentLedgerEntry.createdAt)).all()
    return make_response(
        success=True,
        message="Student ledger retrieved.",
        data=[{
            "id": e.id,
            "amount": float(e.amount),
            "direction": e.direction,
            "type": e.type,
            "description": e.description,
            "createdAt": e.createdAt.isoformat()
        } for e in entries]
    )

# -------------------------------------------------------------
# HOLDS
# -------------------------------------------------------------
@router.get("/holds/me")
def get_own_holds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to students.")

    holds = db.query(FinancialHold).filter(FinancialHold.studentId == current_user.id, FinancialHold.active == True).all()
    return make_response(
        success=True,
        message="Holds retrieved.",
        data=[{
            "id": h.id,
            "reason": h.reason,
            "placedAt": h.placedAt.isoformat()
        } for h in holds]
    )

@router.post("/holds")
def place_financial_hold(
    payload: HoldPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    student = db.query(User).filter(User.id == payload.studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Check existing active hold
    existing = db.query(FinancialHold).filter(
        FinancialHold.studentId == payload.studentId,
        FinancialHold.active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already has an active financial hold.")

    hold = FinancialHold(
        studentId=payload.studentId,
        reason=payload.reason,
        active=True,
        placedBy=current_user.id,
        placedAt=datetime.utcnow()
    )
    db.add(hold)
    db.flush()

    # Audit Financial Holds
    db.add(FinancialAudit(
        entityType="HOLD",
        entityId=hold.id,
        action="PLACE_HOLD",
        userId=current_user.id,
        newData=f"Placed financial hold on student {payload.studentId}. Reason: {payload.reason}"
    ))

    # Send Notification
    NotificationService.create_notification(
        db=db,
        recipient_id=payload.studentId,
        title="Financial Hold Placed",
        body=f"An active financial hold has been placed on your account due to: {payload.reason}. Actions are restricted.",
        category="FEES"
    )

    db.commit()
    return make_response(success=True, message="Financial hold placed successfully.", data={"id": hold.id})

@router.patch("/holds/{id}")
def release_financial_hold(
    id: str,
    payload: ReleaseHoldPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    hold = db.query(FinancialHold).filter(FinancialHold.id == id).first()
    if not hold:
        raise HTTPException(status_code=404, detail="Financial hold not found.")

    if not hold.active:
        raise HTTPException(status_code=400, detail="Financial hold is already inactive.")

    hold.active = False
    hold.releasedBy = current_user.id
    hold.releasedAt = datetime.utcnow()
    hold.releaseReason = payload.releaseReason

    # Audit Financial Holds
    db.add(FinancialAudit(
        entityType="HOLD",
        entityId=hold.id,
        action="RELEASE_HOLD",
        userId=current_user.id,
        newData=f"Released financial hold {id}. Reason: {payload.releaseReason}"
    ))

    # Send Notification
    NotificationService.create_notification(
        db=db,
        recipient_id=hold.studentId,
        title="Financial Hold Released",
        body="Your financial hold has been released successfully. Full portal access is restored.",
        category="FEES"
    )

    db.commit()
    return make_response(success=True, message="Financial hold released successfully.")

# -------------------------------------------------------------
# PARENT PORTAL FEEDS
# -------------------------------------------------------------
@router.get("/parent/children")
def list_parent_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "PARENT":
        raise HTTPException(status_code=403, detail="Endpoint restricted to Parent Portal access.")

    profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Parent profile details not found.")

    links = db.query(ParentStudentLink).filter(ParentStudentLink.parentId == profile.id).all()
    children = []
    for lnk in links:
        child = db.query(User).filter(User.id == lnk.studentId).first()
        if child:
            children.append({
                "id": child.id,
                "name": child.name,
                "email": child.email,
                "relationship": lnk.relationship
            })
    return make_response(success=True, message="Linked children retrieved successfully.", data=children)

@router.get("/parent/children/{student_id}/summary")
def get_parent_child_summary(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "PARENT":
        raise HTTPException(status_code=403, detail="Access denied.")

    profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.parentId == profile.id,
        ParentStudentLink.studentId == student_id,
        ParentStudentLink.canViewFees == True
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Parent not authorized or child link mismatch.")

    summary = FinanceService.get_student_financial_summary(db, student_id)
    return make_response(success=True, message="Child financial summary compiled.", data=summary)

@router.get("/parent/children/{student_id}/invoices")
def get_parent_child_invoices(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "PARENT":
        raise HTTPException(status_code=403, detail="Access denied.")

    profile = db.query(ParentProfile).filter(ParentProfile.userId == current_user.id).first()
    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.parentId == profile.id,
        ParentStudentLink.studentId == student_id,
        ParentStudentLink.canViewFees == True
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Parent not authorized or child link mismatch.")

    invoices = db.query(FeeInvoice).filter(FeeInvoice.studentId == student_id).order_by(desc(FeeInvoice.createdAt)).all()
    return make_response(
        success=True,
        message="Child invoices retrieved.",
        data=[{
            "id": i.id,
            "invoiceNumber": i.invoiceNumber,
            "totalAmount": float(i.totalAmount),
            "paidAmount": float(i.paidAmount),
            "balanceAmount": float(i.balanceAmount),
            "dueDate": i.dueDate.isoformat(),
            "status": i.status
        } for i in invoices]
    )

# -------------------------------------------------------------
# ANALYTICS
# -------------------------------------------------------------
@router.get("/analytics/overview")
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    invoices = db.query(FeeInvoice).all()
    total_billed = sum(format_money(i.totalAmount) for i in invoices)
    total_collected = sum(format_money(i.paidAmount) for i in invoices)
    total_outstanding = sum(format_money(i.balanceAmount) for i in invoices)

    refunds = db.query(Refund).filter(Refund.status == "APPROVED").all()
    total_refunded = sum(format_money(r.amount) for r in refunds)

    holds = db.query(FinancialHold).filter(FinancialHold.active == True).count()

    rate = (total_collected / total_billed * 100) if total_billed > 0 else Decimal("0.00")
    rate_formatted = float(rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return make_response(
        success=True,
        message="Overview compiled.",
        data={
            "totalBilled": float(total_billed),
            "totalCollected": float(total_collected),
            "totalOutstanding": float(total_outstanding),
            "totalRefunded": float(total_refunded),
            "activeHoldsCount": holds,
            "collectionRate": rate_formatted
        }
    )

@router.get("/analytics/collections")
def get_collection_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    # Return collection metrics over time (grouped by payment month)
    payments = db.query(Payment).filter(Payment.status == "SUCCESS").all()
    monthly_map = {}
    for p in payments:
        if p.paidAt:
            m_key = p.paidAt.strftime("%Y-%m")
            if m_key not in monthly_map:
                monthly_map[m_key] = Decimal("0.00")
            monthly_map[m_key] += format_money(p.amount)

    result = [{"month": k, "amount": float(v)} for k, v in sorted(monthly_map.items())]
    return make_response(success=True, message="Collection analytics compiled.", data=result)

@router.get("/analytics/outstanding")
def get_outstanding_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    # Return list of students with balance > 0
    invoices = db.query(FeeInvoice).filter(FeeInvoice.balanceAmount > 0).all()
    students_map = {}
    for inv in invoices:
        if inv.studentId not in students_map:
            students_map[inv.studentId] = Decimal("0.00")
        students_map[inv.studentId] += format_money(inv.balanceAmount)

    result = []
    for s_id, bal in students_map.items():
        student = db.query(User).filter(User.id == s_id).first()
        if student:
            result.append({
                "studentId": s_id,
                "studentName": student.name,
                "outstandingBalance": float(bal)
            })
    return make_response(success=True, message="Outstanding balance list compiled.", data=result)

@router.get("/analytics/departments")
def get_dept_collection_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    data = FinanceService.get_department_analytics(db)
    # Populate names of departments if codes exist
    for item in data:
        dept = db.query(Department).filter(Department.id == item["departmentId"]).first()
        item["departmentName"] = dept.name if dept else "Unassigned / General"
    return make_response(success=True, message="Department analytics retrieved.", data=data)

# -------------------------------------------------------------
# AUDIT TRAIL
# -------------------------------------------------------------
@router.get("/audit")
def get_audit_trail(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    check_finance_auth(current_user)
    audits = db.query(FinancialAudit).order_by(desc(FinancialAudit.createdAt)).limit(100).all()
    return make_response(
        success=True,
        message="Financial audits retrieved.",
        data=[{
            "id": a.id,
            "entityType": a.entityType,
            "entityId": a.entityId,
            "action": a.action,
            "userId": a.userId,
            "newData": a.newData,
            "createdAt": a.createdAt.isoformat()
        } for a in audits]
    )
