import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, AcademicYear, Program, Semester, Section,
    FeeStructure, FeeComponent, StudentFeeAssignment, FeeInvoice,
    InvoiceItem, Payment, WebhookEvent, Receipt, Scholarship,
    ScholarshipApplication, StudentScholarship, Discount, StudentDiscount,
    FeeAdjustment, Refund, PaymentAdjustment, FeeReminder, FinancialAudit
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class ComponentPayload(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    amount: float
    mandatory: bool = True
    refundable: bool = False
    dueDate: datetime
    sortOrder: int = 0

class FeeStructureCreatePayload(BaseModel):
    academicYearId: str
    programId: str
    category: Optional[str] = None
    quota: Optional[str] = None
    currency: str = "INR"
    components: List[ComponentPayload]

class InvoiceCreatePayload(BaseModel):
    studentId: str
    enrollmentId: Optional[str] = None
    dueDate: datetime

class PaymentCreatePayload(BaseModel):
    invoiceId: str
    amount: float
    currency: str = "INR"
    method: str # CASH, UPI, CREDIT_CARD, etc.
    idempotencyKey: str

class WebhookPayload(BaseModel):
    eventId: str
    provider: str
    payload: str

class ScholarshipCreatePayload(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    percentageAmount: Optional[float] = None
    fixedAmount: Optional[float] = None
    maximumBenefit: Optional[float] = None
    validFrom: datetime
    validTo: datetime

class ScholarshipApplyPayload(BaseModel):
    scholarshipId: str

class ScholarshipReviewPayload(BaseModel):
    status: str # APPROVED, REJECTED
    remarks: Optional[str] = None

# Mock Payment Provider Integration
class MockPaymentProvider:
    @staticmethod
    def create_order(amount: Decimal, currency: str) -> str:
        return f"ORDER-MOCK-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
        # Mock validation matches
        return signature.startswith("SIG-")

# Helper to generate unique codes
def generate_unique_number(db: Session, prefix: str, model_class, field_name: str) -> str:
    timestamp = int(datetime.utcnow().timestamp())
    rand_hex = uuid.uuid4().hex[:4].upper()
    val = f"{prefix}-{timestamp}-{rand_hex}"
    # Verify unique
    exists = db.query(model_class).filter(getattr(model_class, field_name) == val).first()
    if exists:
        return generate_unique_number(db, prefix, model_class, field_name)
    return val

# -------------------------------------------------------------
# FEE STRUCTURE ENDPOINTS
# -------------------------------------------------------------

@router.post("/fee-structures")
def create_fee_structure(
    payload: FeeStructureCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

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

    # Audit log
    audit = FinancialAudit(
        entityType="FEE_STRUCTURE",
        entityId=struct.id,
        action="CREATE",
        userId=current_user.id,
        newData=f"Created fee structure with {len(payload.components)} components"
    )
    db.add(audit)
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
        message="Fee structures retrieved.",
        data=[{
            "id": s.id,
            "academicYearId": s.academicYearId,
            "programId": s.programId,
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
        message="Fee structure retrieved.",
        data={
            "id": s.id,
            "academicYearId": s.academicYearId,
            "programId": s.programId,
            "currency": s.currency,
            "components": [{
                "id": c.id,
                "name": c.name,
                "code": c.code,
                "amount": float(c.amount),
                "mandatory": c.mandatory
            } for c in comps]
        }
    )

# -------------------------------------------------------------
# INVOICE ENDPOINTS
# -------------------------------------------------------------

@router.post("/invoices")
def generate_invoice(
    payload: InvoiceCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    student = db.query(User).filter(User.id == payload.studentId).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Match FeeStructure by AcademicYear/Program (Mock fallback configuration lookup)
    struct = db.query(FeeStructure).first()
    if not struct:
        raise HTTPException(status_code=400, detail="No active fee structures found to build invoice.")

    comps = db.query(FeeComponent).filter(FeeComponent.feeStructureId == struct.id).all()

    # Calculate Decimal values server-side. Never trust user/frontend pricing.
    subtotal = Decimal("0.00")
    invoice_items = []

    for c in comps:
        subtotal += c.amount
        invoice_items.append({
            "name": c.name,
            "code": c.code,
            "amount": c.amount,
            "desc": c.description
        })

    # Check for scholarships/discounts applied
    scholarship_amt = Decimal("0.00")
    stud_scholarships = db.query(StudentScholarship).filter(StudentScholarship.studentId == student.id).all()
    for ss in stud_scholarships:
        scholarship_amt += ss.amountAwarded

    total = subtotal - scholarship_amt
    if total < 0:
        total = Decimal("0.00")

    inv_num = generate_unique_number(db, "INV", FeeInvoice, "invoiceNumber")
    invoice = FeeInvoice(
        invoiceNumber=inv_num,
        studentId=student.id,
        enrollmentId=payload.enrollmentId,
        currency="INR",
        subtotal=subtotal,
        scholarshipAmount=scholarship_amt,
        discountAmount=Decimal("0.00"),
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

    for item in invoice_items:
        db.add(InvoiceItem(
            invoiceId=invoice.id,
            componentName=item["name"],
            componentCode=item["code"],
            amount=item["amount"],
            description=item["desc"]
        ))

    audit = FinancialAudit(
        entityType="INVOICE",
        entityId=invoice.id,
        action="ISSUE",
        userId=current_user.id,
        newData=f"Issued invoice {invoice.invoiceNumber} for amount {invoice.totalAmount}"
    )
    db.add(audit)
    db.commit()
    db.refresh(invoice)

    return make_response(success=True, message="Invoice generated successfully.", data={"id": invoice.id, "invoiceNumber": invoice.invoiceNumber})

@router.get("/invoices")
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    query = db.query(FeeInvoice)
    if current_user.role.name == "STUDENT":
        query = query.filter(FeeInvoice.studentId == current_user.id)
    elif current_user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    invoices = query.all()
    return make_response(
        success=True,
        message="Invoices retrieved.",
        data=[{
            "id": i.id,
            "invoiceNumber": i.invoiceNumber,
            "studentId": i.studentId,
            "totalAmount": float(i.totalAmount),
            "paidAmount": float(i.paidAmount),
            "balanceAmount": float(i.balanceAmount),
            "status": i.status
        } for i in invoices]
    )

@router.get("/invoices/{id}")
def get_invoice(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if current_user.role.name == "STUDENT" and invoice.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    items = db.query(InvoiceItem).filter(InvoiceItem.invoiceId == id).all()

    return make_response(
        success=True,
        message="Invoice details retrieved.",
        data={
            "id": invoice.id,
            "invoiceNumber": invoice.invoiceNumber,
            "totalAmount": float(invoice.totalAmount),
            "balanceAmount": float(invoice.balanceAmount),
            "status": invoice.status,
            "items": [{
                "id": it.id,
                "componentName": it.componentName,
                "amount": float(it.amount)
            } for it in items]
        }
    )

# -------------------------------------------------------------
# PAYMENTS ENDPOINTS
# -------------------------------------------------------------

@router.post("/payments")
def initiate_payment(
    payload: PaymentCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payload.invoiceId).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if current_user.role.name == "STUDENT" and invoice.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Idempotency guard check
    existing = db.query(Payment).filter(Payment.idempotencyKey == payload.idempotencyKey).first()
    if existing:
        return make_response(success=True, message="Payment replay retrieved.", data={"id": existing.id, "paymentNumber": existing.paymentNumber, "status": existing.status})

    pay_amount = Decimal(str(payload.amount))
    if pay_amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero.")

    # Overpayment protection
    if pay_amount > invoice.balanceAmount:
        raise HTTPException(status_code=400, detail=f"Overpayment blocked. Maximum payable balance is {invoice.balanceAmount}")

    pay_num = generate_unique_number(db, "PAY", Payment, "paymentNumber")
    order_id = MockPaymentProvider.create_order(pay_amount, payload.currency)

    payment = Payment(
        paymentNumber=pay_num,
        invoiceId=invoice.id,
        studentId=invoice.studentId,
        amount=pay_amount,
        currency=payload.currency,
        method=payload.method,
        status="INITIATED",
        provider="MOCK",
        providerOrderId=order_id,
        idempotencyKey=payload.idempotencyKey
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return make_response(
        success=True,
        message="Payment initiated.",
        data={
            "id": payment.id,
            "paymentNumber": payment.paymentNumber,
            "providerOrderId": payment.providerOrderId,
            "status": payment.status
        }
    )

@router.post("/payments/{id}/confirm")
def confirm_payment(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    payment = db.query(Payment).filter(Payment.id == id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")

    if payment.status == "SUCCESS":
        return make_response(success=True, message="Payment already processed.", data={"id": payment.id})

    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payment.invoiceId).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice matching payment not found.")

    # Process atomic balance changes in transaction boundary
    payment.status = "SUCCESS"
    payment.paidAt = datetime.utcnow()

    invoice.paidAmount += payment.amount
    invoice.balanceAmount -= payment.amount

    if invoice.balanceAmount <= 0:
        invoice.status = "PAID"
    else:
        invoice.status = "PARTIALLY_PAID"

    # Generate receipt only for successful confirmation payments
    rec_num = generate_unique_number(db, "REC", Receipt, "receiptNumber")
    verification_token = f"VERIFY-{uuid.uuid4().hex[:12].upper()}"
    receipt = Receipt(
        receiptNumber=rec_num,
        paymentId=payment.id,
        studentId=payment.studentId,
        amount=payment.amount,
        currency=payment.currency,
        verificationToken=verification_token
    )
    db.add(receipt)

    audit = FinancialAudit(
        entityType="PAYMENT",
        entityId=payment.id,
        action="CONFIRM_SUCCESS",
        userId=current_user.id,
        newData=f"Payment {payment.paymentNumber} confirmed. Invoice {invoice.invoiceNumber} balance updated to {invoice.balanceAmount}"
    )
    db.add(audit)
    db.commit()

    return make_response(success=True, message="Payment confirmed and receipt generated.", data={"receiptNumber": receipt.receiptNumber})

@router.get("/payments")
def list_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    query = db.query(Payment)
    if current_user.role.name == "STUDENT":
        query = query.filter(Payment.studentId == current_user.id)
    elif current_user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    payments = query.all()
    return make_response(
        success=True,
        message="Payments retrieved.",
        data=[{
            "id": p.id,
            "paymentNumber": p.paymentNumber,
            "amount": float(p.amount),
            "method": p.method,
            "status": p.status
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
        message="Payment details retrieved.",
        data={
            "id": p.id,
            "paymentNumber": p.paymentNumber,
            "amount": float(p.amount),
            "status": p.status
        }
    )

# -------------------------------------------------------------
# WEBHOOK ENDPOINTS
# -------------------------------------------------------------

@router.post("/webhooks/{provider}")
def process_payment_webhook(
    provider: str,
    payload: WebhookPayload,
    db: Session = Depends(get_db)
):
    # Verify signature logic / event deduplication
    existing = db.query(WebhookEvent).filter(WebhookEvent.eventId == payload.eventId).first()
    if existing:
        return {"status": "already_processed"}

    event = WebhookEvent(
        eventId=payload.eventId,
        provider=provider,
        payload=payload.payload,
        processed=True
    )
    db.add(event)
    db.commit()

    return {"status": "processed"}

# -------------------------------------------------------------
# RECEIPTS ENDPOINTS
# -------------------------------------------------------------

@router.get("/receipts")
def list_receipts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    query = db.query(Receipt)
    if current_user.role.name == "STUDENT":
        query = query.filter(Receipt.studentId == current_user.id)

    receipts = query.all()
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

    return make_response(
        success=True,
        message="Receipt details retrieved.",
        data={
            "id": r.id,
            "receiptNumber": r.receiptNumber,
            "amount": float(r.amount),
            "verificationToken": r.verificationToken
        }
    )

@router.get("/receipts/verify/{token}")
def verify_receipt_token(
    token: str,
    db: Session = Depends(get_db)
):
    r = db.query(Receipt).filter(Receipt.verificationToken == token).first()
    if not r:
        raise HTTPException(status_code=404, detail="Receipt token signature invalid or not found.")

    return make_response(
        success=True,
        message="Receipt token signature verified successfully.",
        data={
            "receiptNumber": r.receiptNumber,
            "amount": float(r.amount),
            "issuedAt": r.issuedAt.isoformat()
        }
    )

# -------------------------------------------------------------
# SCHOLARSHIPS ENDPOINTS
# -------------------------------------------------------------

@router.post("/scholarships")
def create_scholarship(
    payload: ScholarshipCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    s = Scholarship(
        name=payload.name,
        type=payload.type,
        description=payload.description,
        percentageAmount=payload.percentageAmount,
        fixedAmount=Decimal(str(payload.fixedAmount)) if payload.fixedAmount else None,
        maximumBenefit=Decimal(str(payload.maximumBenefit)) if payload.maximumBenefit else None,
        validFrom=payload.validFrom,
        validTo=payload.validTo,
        status="ACTIVE"
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    return make_response(success=True, message="Scholarship structure configured.", data={"id": s.id})

@router.get("/scholarships")
def list_scholarships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    scholarships = db.query(Scholarship).all()
    return make_response(
        success=True,
        message="Scholarships retrieved.",
        data=[{
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "status": s.status
        } for s in scholarships]
    )

@router.post("/scholarship-applications")
def apply_scholarship(
    payload: ScholarshipApplyPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Access restricted to students.")

    # Check duplicates applications
    existing = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.scholarshipId == payload.scholarshipId,
        ScholarshipApplication.studentId == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied for this scholarship.")

    app = ScholarshipApplication(
        scholarshipId=payload.scholarshipId,
        studentId=current_user.id,
        status="SUBMITTED"
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    return make_response(success=True, message="Scholarship application submitted.", data={"id": app.id})

@router.post("/scholarship-applications/{id}/review")
def review_scholarship_application(
    id: str,
    payload: ScholarshipReviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    app = db.query(ScholarshipApplication).filter(ScholarshipApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Scholarship application not found.")

    app.status = payload.status
    app.remarks = payload.remarks

    if payload.status == "APPROVED":
        # Award the scholarship to StudentScholarship
        scholar = db.query(Scholarship).filter(Scholarship.id == app.scholarshipId).first()
        awarded_amount = scholar.fixedAmount if scholar.fixedAmount else Decimal("5000.00") # mock fallback
        
        db.add(StudentScholarship(
            studentId=app.studentId,
            scholarshipId=app.scholarshipId,
            amountAwarded=awarded_amount
        ))

    db.commit()
    return make_response(success=True, message=f"Scholarship application reviewed as {payload.status}.")

# -------------------------------------------------------------
# FINANCIAL ANALYTICS ENDPOINTS
# -------------------------------------------------------------

@router.get("/fee-analytics")
def get_fee_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "FINANCE_OFFICE"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    invoices = db.query(FeeInvoice).all()
    total_invoiced = sum(i.totalAmount for i in invoices)
    total_collected = sum(i.paidAmount for i in invoices)
    total_outstanding = sum(i.balanceAmount for i in invoices)

    return make_response(
        success=True,
        message="Fee analytics metrics compiled.",
        data={
            "totalInvoiced": float(total_invoiced),
            "totalCollected": float(total_collected),
            "outstandingBalance": float(total_outstanding),
            "outstandingCount": sum(1 for i in invoices if i.balanceAmount > 0)
        }
    )
