import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import (
    User, FeeStructure, FeeComponent, StudentFeeAssignment, FeeInvoice,
    InvoiceItem, Payment, Receipt, Scholarship, ScholarshipApplication,
    StudentScholarship, FeeConcession, FeeWaiver, FinePenalty,
    StudentLedgerEntry, FinancialHold, InstallmentPlan, InstallmentSchedule,
    PaymentAllocation, HostelAllocation, TransportSubscription
)

def format_money(val) -> Decimal:
    """Helper to convert to 2 decimal places using ROUND_HALF_UP."""
    if val is None:
        return Decimal("0.00")
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class FinanceService:
    @staticmethod
    def get_student_financial_summary(db: Session, student_id: str):
        """Compiles overall financial statistics for a student."""
        invoices = db.query(FeeInvoice).filter(FeeInvoice.studentId == student_id).all()

        total_billed = Decimal("0.00")
        total_paid = Decimal("0.00")
        total_outstanding = Decimal("0.00")
        overdue_amount = Decimal("0.00")
        now = datetime.utcnow()

        for inv in invoices:
            total_billed += format_money(inv.totalAmount)
            total_paid += format_money(inv.paidAmount)
            bal = format_money(inv.balanceAmount)
            total_outstanding += bal
            if bal > 0 and inv.dueDate < now:
                overdue_amount += bal

        # Check active scholarships
        scholarships = db.query(StudentScholarship).filter(StudentScholarship.studentId == student_id).all()
        active_scholarships_total = sum(format_money(s.amountAwarded) for s in scholarships)

        # Check holds
        holds = db.query(FinancialHold).filter(
            FinancialHold.studentId == student_id,
            FinancialHold.active == True
        ).all()
        has_hold = len(holds) > 0

        # Next due date
        unpaid_invoices = [i for i in invoices if format_money(i.balanceAmount) > 0]
        next_due_date = None
        if unpaid_invoices:
            next_due_date = min(i.dueDate for i in unpaid_invoices).isoformat()

        return {
            "totalBilled": float(total_billed),
            "totalPaid": float(total_paid),
            "outstandingBalance": float(total_outstanding),
            "overdueAmount": float(overdue_amount),
            "activeScholarshipsTotal": float(active_scholarships_total),
            "hasFinancialHold": has_hold,
            "nextDueDate": next_due_date,
            "currency": "INR",
            "calculationMode": "DETERMINISTIC_FINANCIAL_CALCULATION"
        }

    @staticmethod
    def record_ledger_entry(
        db: Session,
        student_id: str,
        amount: Decimal,
        direction: str,  # DEBIT or CREDIT
        entry_type: str,  # INVOICE, PAYMENT, CONCESSION, WAIVER, FINE, REFUND, ADJUSTMENT
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
        actor_id: Optional[str] = None
    ) -> StudentLedgerEntry:
        """Appends a new auditable transaction to the ledger log."""
        entry = StudentLedgerEntry(
            studentId=student_id,
            amount=format_money(amount),
            direction=direction,
            type=entry_type,
            referenceId=reference_id,
            description=description,
            actorId=actor_id,
            createdAt=datetime.utcnow()
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def check_financial_holds(db: Session, student_id: str) -> bool:
        """Determines if a student has any active financial holds."""
        hold = db.query(FinancialHold).filter(
            FinancialHold.studentId == student_id,
            FinancialHold.active == True
        ).first()
        return hold is not None

    @staticmethod
    def get_department_analytics(db: Session):
        """Aggregates revenue collection metrics grouped by student department."""
        # Join User, FeeInvoice to group by department
        invoices = db.query(FeeInvoice, User.departmentId).join(
            User, User.id == FeeInvoice.studentId
        ).all()

        dept_map = {}
        for inv, dept_id in invoices:
            dept_key = dept_id or "UNASSIGNED"
            if dept_key not in dept_map:
                dept_map[dept_key] = {"billed": Decimal("0.00"), "collected": Decimal("0.00")}
            dept_map[dept_key]["billed"] += format_money(inv.totalAmount)
            dept_map[dept_key]["collected"] += format_money(inv.paidAmount)

        result = []
        for dept_id, metrics in dept_map.items():
            billed = metrics["billed"]
            collected = metrics["collected"]
            rate = (collected / billed * 100) if billed > 0 else Decimal("0.00")
            result.append({
                "departmentId": dept_id,
                "billed": float(billed),
                "collected": float(collected),
                "collectionRate": float(rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            })
        return result

    @staticmethod
    def create_installment_plan(
        db: Session,
        invoice_id: str,
        name: str,
        num_installments: int,
        actor_id: str
    ) -> InstallmentPlan:
        """Breaks down an invoice's outstanding balance into installment schedules."""
        invoice = db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id).first()
        if not invoice:
            raise ValueError("Invoice not found.")

        balance = format_money(invoice.balanceAmount)
        if balance <= 0:
            raise ValueError("Invoice is already fully paid.")

        # Check if active plan already exists
        existing_plan = db.query(InstallmentPlan).filter(
            InstallmentPlan.invoiceId == invoice_id,
            InstallmentPlan.status == "ACTIVE"
        ).first()
        if existing_plan:
            raise ValueError("An active installment plan already exists for this invoice.")

        plan = InstallmentPlan(
            invoiceId=invoice_id,
            name=name,
            numberOfInstallments=num_installments,
            totalAmount=balance,
            status="ACTIVE",
            createdAt=datetime.utcnow()
        )
        db.add(plan)
        db.flush()

        # Calculate standard split
        each_amount = (balance / num_installments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cumulative = Decimal("0.00")

        for i in range(1, num_installments + 1):
            if i == num_installments:
                # Adjust rounding differences on final installment
                inst_amount = balance - cumulative
            else:
                inst_amount = each_amount
                cumulative += each_amount

            due_date = datetime.utcnow() + timedelta(days=30 * i)
            schedule = InstallmentSchedule(
                installmentPlanId=plan.id,
                installmentNumber=i,
                dueDate=due_date,
                amount=inst_amount,
                paidAmount=Decimal("0.00"),
                status="UNPAID",
                createdAt=datetime.utcnow()
            )
            db.add(schedule)

        invoice.status = "INSTALLMENT"
        db.flush()
        return plan

    @staticmethod
    def process_payment_allocations(db: Session, payment: Payment):
        """Allocates payment amount across invoice items or installment schedules."""
        invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payment.invoiceId).first()
        if not invoice:
            return

        amount_to_allocate = format_money(payment.amount)

        # 1. Allocate to installments if plan exists
        active_plan = db.query(InstallmentPlan).filter(
            InstallmentPlan.invoiceId == invoice.id,
            InstallmentPlan.status == "ACTIVE"
        ).first()

        if active_plan:
            schedules = db.query(InstallmentSchedule).filter(
                InstallmentSchedule.installmentPlanId == active_plan.id,
                InstallmentSchedule.status != "PAID"
            ).order_by(InstallmentSchedule.installmentNumber).all()

            for sched in schedules:
                if amount_to_allocate <= 0:
                    break
                sched_bal = format_money(sched.amount - sched.paidAmount)
                allocate_to_sched = min(amount_to_allocate, sched_bal)

                sched.paidAmount += allocate_to_sched
                amount_to_allocate -= allocate_to_sched

                if sched.paidAmount >= sched.amount:
                    sched.status = "PAID"
                else:
                    sched.status = "PARTIALLY_PAID"

                # Record allocation record
                db.add(PaymentAllocation(
                    paymentId=payment.id,
                    installmentScheduleId=sched.id,
                    amount=allocate_to_sched
                ))

            # If all installments paid, mark plan completed
            unpaid_scheds = db.query(InstallmentSchedule).filter(
                InstallmentSchedule.installmentPlanId == active_plan.id,
                InstallmentSchedule.status != "PAID"
            ).first()
            if not unpaid_scheds:
                active_plan.status = "COMPLETED"

        # 2. Allocate to line items directly
        else:
            items = db.query(InvoiceItem).filter(InvoiceItem.invoiceId == invoice.id).all()
            # Check how much each line item has been allocated previously
            for item in items:
                if amount_to_allocate <= 0:
                    break
                # Find previous allocations to this item
                prev_allocs = db.query(PaymentAllocation).filter(
                    PaymentAllocation.invoiceItemId == item.id
                ).all()
                allocated_so_far = sum(format_money(a.amount) for a in prev_allocs)
                item_bal = format_money(item.amount - allocated_so_far)

                if item_bal > 0:
                    allocate_to_item = min(amount_to_allocate, item_bal)
                    amount_to_allocate -= allocate_to_item

                    db.add(PaymentAllocation(
                        paymentId=payment.id,
                        invoiceItemId=item.id,
                        amount=allocate_to_item
                    ))

    @staticmethod
    def evaluate_scholarship_eligibility(db: Session, scheme_id: str, student_id: str) -> bool:
        """Determines if a student qualifies for a scholarship scheme."""
        student = db.query(User).filter(User.id == student_id).first()
        scheme = db.query(Scholarship).filter(Scholarship.id == scheme_id).first()
        if not student or not scheme or scheme.status != "ACTIVE":
            return False

        # Parse eligibility rules from scheme metadata
        # Expecting JSON or simple rules key-value inside scheme.eligibility
        # Example format: "MIN_CGPA:8.0;ALLOWED_DEPTS:CS,IS"
        rules = scheme.eligibility or ""
        if not rules:
            return True  # Open schema by default

        try:
            # Deterministic evaluation using standard attributes
            for rule in rules.split(";"):
                if ":" not in rule:
                    continue
                k, v = rule.split(":", 1)
                k = k.strip()
                v = v.strip()

                if k == "MIN_CGPA":
                    # Locate student profile or matching criteria
                    # In Day 22, UserProfile has CGPA or is linked. If not, default check passes.
                    profile = student.profile
                    cgpa = getattr(profile, "cgpa", None)
                    if cgpa is not None and float(cgpa) < float(v):
                        return False
                elif k == "ALLOWED_DEPTS":
                    depts = [d.strip() for d in v.split(",")]
                    if student.departmentId not in depts and (student.department and student.department.code not in depts):
                        return False
            return True
        except Exception:
            return False

    @staticmethod
    def integrate_hostel_and_transport_charges(db: Session, student_id: str) -> List[dict]:
        """Looks up active Hostel allocations and Transport subscriptions to suggest invoice items."""
        items = []

        # 1. Hostel integration
        active_hostel = db.query(HostelAllocation).filter(
            HostelAllocation.studentId == student_id,
            HostelAllocation.status == "ACTIVE"
        ).first()
        if active_hostel:
            items.append({
                "name": "Hostel Accomodation Fee",
                "code": "HSTL-RENT",
                "amount": Decimal("15000.00"),
                "description": f"Hostel Rent for Allocation {active_hostel.id}"
            })

        # 2. Transport integration
        active_transport = db.query(TransportSubscription).filter(
            TransportSubscription.userId == student_id,
            TransportSubscription.status == "ACTIVE"
        ).first()
        if active_transport:
            items.append({
                "name": "Transport Pass Charge",
                "code": "TRNSP-PASS",
                "amount": Decimal("5000.00"),
                "description": f"Bus Route Pass subscription {active_transport.id}"
            })

        return items
