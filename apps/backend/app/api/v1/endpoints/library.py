from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import (
    User, LibraryBranch, Author, Publisher, BookCategory, Book, BookAuthor, BookTag,
    BookCopy, LibraryMembership, LibraryPolicy, BookLoan, LoanRenewal, BookReservation,
    LibraryFine, LibraryInventoryEvent, DigitalResource, LibraryVendor, BookAcquisitionRequest,
    BookAcquisitionItem, InventoryAudit, InventoryAuditItem, LibraryAudit
)
from app.core.responses import make_response

router = APIRouter()

# ----------------------------------------------------
# Pydantic Schemas
# ----------------------------------------------------
class BranchCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    location: Optional[str] = None
    contactEmail: Optional[str] = None
    contactPhone: Optional[str] = None
    openingTime: Optional[str] = None
    closingTime: Optional[str] = None

class BookCreate(BaseModel):
    isbn10: Optional[str] = None
    isbn13: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    edition: Optional[str] = None
    publicationYear: int
    language: str
    pageCount: int
    coverImageUrl: Optional[str] = None
    publisherName: str
    categoryName: str
    categoryCode: str
    authors: List[str]
    tags: Optional[List[str]] = []

class CopyCreate(BaseModel):
    bookId: str
    branchId: str
    accessionNumber: str
    barcode: str
    shelfLocation: Optional[str] = None
    rackNumber: Optional[str] = None
    acquisitionPrice: Decimal
    source: Optional[str] = None

class MembershipCreate(BaseModel):
    userId: str
    membershipNumber: str
    memberType: str # STUDENT, FACULTY, STAFF, ALUMNI, OTHER
    branchId: Optional[str] = None

class IssueRequest(BaseModel):
    membershipNumber: str
    barcode: str

class ReturnRequest(BaseModel):
    barcode: str
    condition: Optional[str] = "GOOD"
    isLost: Optional[bool] = False

class RenewRequest(BaseModel):
    loanId: str

class ReserveRequest(BaseModel):
    bookId: str
    membershipNumber: str

class FineWaiveRequest(BaseModel):
    waiverReason: str

# Helper to check permissions
def verify_role(user: User, allowed_roles: List[str]):
    if user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation restricted by access privileges."
        )

# Helper for Library Audit logging
def log_library_action(db: Session, user_id: str, action: str, details: str, request: Request = None):
    ip_addr = request.client.host if (request and request.client) else None
    audit = LibraryAudit(
        id=str(uuid.uuid4()),
        userId=user_id,
        action=action,
        details=details,
        ipAddress=ip_addr
    )
    db.add(audit)
    db.commit()

# ----------------------------------------------------
# 1. Branch Endpoints
# ----------------------------------------------------
@router.post("/branches")
def create_branch(payload: BranchCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN"])
    
    existing = db.query(LibraryBranch).filter_by(code=payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Branch code already registered.")

    branch = LibraryBranch(
        id=str(uuid.uuid4()),
        name=payload.name,
        code=payload.code,
        description=payload.description,
        location=payload.location,
        contactEmail=payload.contactEmail,
        contactPhone=payload.contactPhone,
        openingTime=payload.openingTime,
        closingTime=payload.closingTime
    )
    db.add(branch)
    db.commit()
    return make_response(success=True, message="Library branch created successfully.", data={"id": branch.id})

@router.get("/branches")
def list_branches(db: Session = Depends(get_db)):
    branches = db.query(LibraryBranch).all()
    data = [{"id": b.id, "name": b.name, "code": b.code, "location": b.location, "active": b.active} for b in branches]
    return make_response(success=True, message="Branches list fetched.", data=data)

# ----------------------------------------------------
# 2. Book Catalog Endpoints
# ----------------------------------------------------
@router.post("/books")
def create_book(payload: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN", "LIBRARIAN"])
    
    existing = db.query(Book).filter_by(isbn13=payload.isbn13).first()
    if existing:
        raise HTTPException(status_code=400, detail="Book with this ISBN-13 already cataloged.")

    # Find or create Publisher
    pub = db.query(Publisher).filter_by(name=payload.publisherName).first()
    if not pub:
        pub = Publisher(id=str(uuid.uuid4()), name=payload.publisherName)
        db.add(pub)
        db.flush()

    # Find or create Category
    cat = db.query(BookCategory).filter_by(code=payload.categoryCode).first()
    if not cat:
        cat = BookCategory(id=str(uuid.uuid4()), name=payload.categoryName, code=payload.categoryCode)
        db.add(cat)
        db.flush()

    # Create Book
    book = Book(
        id=str(uuid.uuid4()),
        isbn10=payload.isbn10,
        isbn13=payload.isbn13,
        title=payload.title,
        subtitle=payload.subtitle,
        description=payload.description,
        edition=payload.edition,
        publicationYear=payload.publicationYear,
        language=payload.language,
        pageCount=payload.pageCount,
        coverImageUrl=payload.coverImageUrl,
        publisherId=pub.id,
        categoryId=cat.id
    )
    db.add(book)
    db.flush()

    # Handle Authors
    for aut_name in payload.authors:
        aut = db.query(Author).filter_by(name=aut_name).first()
        if not aut:
            aut = Author(id=str(uuid.uuid4()), name=aut_name)
            db.add(aut)
            db.flush()
        db.add(BookAuthor(id=str(uuid.uuid4()), bookId=book.id, authorId=aut.id))

    # Handle Tags
    if payload.tags:
        for t_name in payload.tags:
            db.add(BookTag(id=str(uuid.uuid4()), bookId=book.id, name=t_name))

    db.commit()
    return make_response(success=True, message="Book cataloged successfully.", data={"id": book.id})

@router.get("/books")
def list_books(search: Optional[str] = None, categoryCode: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Book)
    if categoryCode:
        query = query.join(BookCategory).filter(BookCategory.code == categoryCode)
    if search:
        query = query.filter((Book.title.like(f"%{search}%")) | (Book.isbn13 == search))
    
    books = query.all()
    data = []
    for b in books:
        data.append({
            "id": b.id,
            "title": b.title,
            "isbn13": b.isbn13,
            "publisher": b.publisher.name,
            "category": b.category.name,
            "authors": [ba.author.name for ba in b.bookAuthors]
        })
    return make_response(success=True, message="Books fetched.", data=data)

# ----------------------------------------------------
# 3. Book Copy Endpoints
# ----------------------------------------------------
@router.post("/copies")
def create_copy(payload: CopyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN", "LIBRARIAN"])
    
    # Check duplicate accession/barcode
    if db.query(BookCopy).filter((BookCopy.accessionNumber == payload.accessionNumber) | (BookCopy.barcode == payload.barcode)).first():
        raise HTTPException(status_code=400, detail="Accession number or barcode already registered.")

    copy = BookCopy(
        id=str(uuid.uuid4()),
        bookId=payload.bookId,
        branchId=payload.branchId,
        accessionNumber=payload.accessionNumber,
        barcode=payload.barcode,
        shelfLocation=payload.shelfLocation,
        rackNumber=payload.rackNumber,
        acquisitionDate=datetime.utcnow(),
        acquisitionPrice=payload.acquisitionPrice,
        source=payload.source
    )
    db.add(copy)
    db.commit()
    return make_response(success=True, message="Book copy registered successfully.", data={"id": copy.id})

@router.get("/copies")
def list_copies(bookId: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(BookCopy)
    if bookId:
        query = query.filter_by(bookId=bookId)
    copies = query.all()
    data = [{
        "id": c.id,
        "accessionNumber": c.accessionNumber,
        "barcode": c.barcode,
        "status": c.status,
        "condition": c.condition,
        "title": c.book.title
    } for c in copies]
    return make_response(success=True, message="Book copies list fetched.", data=data)

# ----------------------------------------------------
# 4. Library Membership Endpoints
# ----------------------------------------------------
@router.post("/memberships")
def create_membership(payload: MembershipCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN", "LIBRARIAN"])
    
    existing = db.query(LibraryMembership).filter_by(userId=payload.userId).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already holds a library membership.")

    memb = LibraryMembership(
        id=str(uuid.uuid4()),
        userId=payload.userId,
        membershipNumber=payload.membershipNumber,
        memberType=payload.memberType,
        branchId=payload.branchId,
        activatedAt=datetime.utcnow(),
        expiresAt=datetime.utcnow() + timedelta(days=365)
    )
    db.add(memb)
    db.commit()
    return make_response(success=True, message="Library membership activated successfully.", data={"id": memb.id})

@router.get("/memberships")
def list_memberships(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN", "LIBRARIAN"])
    m = db.query(LibraryMembership).all()
    data = [{"id": r.id, "membershipNumber": r.membershipNumber, "studentName": r.user.name, "memberType": r.memberType, "status": r.status} for r in m]
    return make_response(success=True, message="Memberships list fetched.", data=data)

# ----------------------------------------------------
# 5. Circulation: Book Issue Endpoint
# ----------------------------------------------------
@router.post("/loans/issue")
def issue_book(payload: IssueRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN", "LIBRARIAN"])
    
    # Resolve membership
    member = db.query(LibraryMembership).filter_by(membershipNumber=payload.membershipNumber, status="ACTIVE").first()
    if not member:
        raise HTTPException(status_code=400, detail="Active library membership not found.")

    # Resolve book copy
    copy = db.query(BookCopy).filter_by(barcode=payload.barcode, status="AVAILABLE").first()
    if not copy:
        raise HTTPException(status_code=400, detail="Target book copy is currently unavailable.")

    # Get library policy configuration
    policy = db.query(LibraryPolicy).filter_by(memberType=member.memberType, branchId=copy.branchId).first()
    if not policy:
        # Default policies if not configured
        policy = LibraryPolicy(
            id="temp-policy",
            memberType=member.memberType,
            branchId=copy.branchId,
            maxBooks=5,
            loanDays=14,
            renewalLimit=2,
            reservationLimit=3,
            finePerDay=Decimal("10.00"),
            graceDays=3,
            maxFine=Decimal("500.00")
        )

    # Check active loans count limit
    active_loans = db.query(BookLoan).filter_by(membershipId=member.id, status="ACTIVE").count()
    if active_loans >= policy.maxBooks:
        raise HTTPException(status_code=400, detail="Borrowing quota limit reached under active policy.")

    # Check for blocking unpaid fines
    unpaid_fines = db.query(LibraryFine).filter_by(membershipId=member.id, status="PENDING").first()
    if unpaid_fines:
        raise HTTPException(status_code=400, detail="Borrowing blocked due to pending unpaid library fines.")

    # Create BookLoan
    loan = BookLoan(
        id=str(uuid.uuid4()),
        copyId=copy.id,
        membershipId=member.id,
        issuedBy=current_user.id,
        issuedAt=datetime.utcnow(),
        dueAt=datetime.utcnow() + timedelta(days=policy.loanDays),
        status="ACTIVE"
    )
    copy.status = "ISSUED"
    db.add(loan)
    
    # Audit log entry
    log_library_action(db, current_user.id, "BOOK_ISSUE", f"Book copy {copy.barcode} issued to member {member.membershipNumber}", request)
    
    db.commit()
    return make_response(success=True, message="Book copy issued successfully.", data={"loanId": loan.id, "dueAt": loan.dueAt})

# ----------------------------------------------------
# 6. Circulation: Book Return Endpoint
# ----------------------------------------------------
@router.post("/loans/{id}/return")
def return_book(id: str, payload: ReturnRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN", "LIBRARIAN"])
    
    loan = db.query(BookLoan).filter_by(id=id, status="ACTIVE").first()
    if not loan:
        raise HTTPException(status_code=404, detail="Active loan record not found.")

    copy = loan.copy
    member = loan.membership

    # Get policy rules
    policy = db.query(LibraryPolicy).filter_by(memberType=member.memberType, branchId=copy.branchId).first()
    fine_per_day = policy.finePerDay if policy else Decimal("10.00")
    grace_days = policy.graceDays if policy else 3
    max_fine = policy.maxFine if policy else Decimal("500.00")

    # Mark Return details
    loan.returnedAt = datetime.utcnow()
    
    # Overdue fine calculation
    overdue_days = (loan.returnedAt.date() - loan.dueAt.date()).days
    fine_amount = Decimal("0.00")
    if overdue_days > grace_days:
        fine_amount = Decimal(overdue_days) * fine_per_day
        if fine_amount > max_fine:
            fine_amount = max_fine

    # Lost/Damaged declaration overrides
    if payload.isLost:
        loan.status = "LOST"
        copy.status = "LOST"
        # Assess lost book recovery fee
        fine_amount += copy.acquisitionPrice
        db.add(LibraryFine(
            id=str(uuid.uuid4()),
            loanId=loan.id,
            membershipId=member.id,
            amount=copy.acquisitionPrice,
            reason="LOST",
            status="PENDING"
        ))
    elif payload.condition == "DAMAGED" or loan.status == "DAMAGED":
        loan.status = "DAMAGED"
        copy.status = "DAMAGED"
        damage_fee = copy.acquisitionPrice / Decimal("2.00")
        fine_amount += damage_fee
        db.add(LibraryFine(
            id=str(uuid.uuid4()),
            loanId=loan.id,
            membershipId=member.id,
            amount=damage_fee,
            reason="DAMAGED",
            status="PENDING"
        ))
    else:
        loan.status = "RETURNED"
        # Check if book is reserved by someone
        res = db.query(BookReservation).filter_by(bookId=copy.bookId, status="WAITING").order_by(BookReservation.reservedAt.asc()).first()
        if res:
            copy.status = "RESERVED"
            res.status = "READY_FOR_PICKUP"
            res.pickupDeadline = datetime.utcnow() + timedelta(days=2)
        else:
            copy.status = "AVAILABLE"

    # Add overdue fine if calculated
    if fine_amount > 0 and not payload.isLost and payload.condition != "DAMAGED":
        db.add(LibraryFine(
            id=str(uuid.uuid4()),
            loanId=loan.id,
            membershipId=member.id,
            amount=fine_amount,
            reason="OVERDUE",
            status="PENDING"
        ))

    log_library_action(db, current_user.id, "BOOK_RETURN", f"Book copy {copy.barcode} returned by member {member.membershipNumber}", request)
    
    db.commit()
    return make_response(success=True, message="Book copy returned successfully.", data={"fineAssessed": float(fine_amount)})

# ----------------------------------------------------
# 7. Circulation: Book Renewal Endpoint
# ----------------------------------------------------
@router.post("/loans/{id}/renew")
def renew_book(id: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    # Can be renewed by Librarian OR Student self-renewal
    loan = db.query(BookLoan).filter_by(id=id, status="ACTIVE").first()
    if not loan:
        raise HTTPException(status_code=404, detail="Active loan record not found.")

    member = loan.membership
    copy = loan.copy

    # Verify ownership for students
    if current_user.role.name == "STUDENT" and member.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized self-renewal attempt.")

    # Check policy
    policy = db.query(LibraryPolicy).filter_by(memberType=member.memberType, branchId=copy.branchId).first()
    renewal_limit = policy.renewalLimit if policy else 2
    loan_days = policy.loanDays if policy else 14

    if loan.renewalCount >= renewal_limit:
        raise HTTPException(status_code=400, detail="Maximum renewal count limit reached for this loan.")

    # Check reservation conflicts
    res = db.query(BookReservation).filter_by(bookId=copy.bookId, status="WAITING").first()
    if res:
        raise HTTPException(status_code=400, detail="Cannot renew: book copy contains pending student reservations.")

    # Save original due date and apply extension
    orig_due = loan.dueAt
    loan.dueAt = loan.dueAt + timedelta(days=loan_days)
    loan.renewalCount += 1

    # Record renewal history
    renewal = LoanRenewal(
        id=str(uuid.uuid4()),
        loanId=loan.id,
        renewedBy=current_user.id,
        originalDueAt=orig_due,
        newDueAt=loan.dueAt
    )
    db.add(renewal)
    
    log_library_action(db, current_user.id, "BOOK_RENEWAL", f"Loan {loan.id} renewed. Extension to {loan.dueAt}", request)
    db.commit()
    return make_response(success=True, message="Book loan renewed successfully.", data={"newDueAt": loan.dueAt})

# ----------------------------------------------------
# 8. Reservations Endpoints
# ----------------------------------------------------
@router.post("/reservations")
def create_reservation(payload: ReserveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    # Verify membership
    member = db.query(LibraryMembership).filter_by(membershipNumber=payload.membershipNumber, status="ACTIVE").first()
    if not member:
        raise HTTPException(status_code=400, detail="Active library membership not found.")

    # Verify ownership for students
    if current_user.role.name == "STUDENT" and member.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized reservation request.")

    # Check duplicate active reservation
    existing = db.query(BookReservation).filter_by(
        bookId=payload.bookId,
        membershipId=member.id
    ).filter(BookReservation.status.in_(["WAITING", "READY_FOR_PICKUP"])).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Duplicate active reservation found for this book title.")

    # Create BookReservation
    res = BookReservation(
        id=str(uuid.uuid4()),
        bookId=payload.bookId,
        membershipId=member.id,
        status="WAITING"
    )
    db.add(res)
    db.commit()
    return make_response(success=True, message="Book title reserved successfully.", data={"reservationId": res.id})

@router.get("/reservations")
def list_reservations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    query = db.query(BookReservation)
    if current_user.role.name == "STUDENT":
        # IDOR prevention check
        member = db.query(LibraryMembership).filter_by(userId=current_user.id).first()
        if not member:
            return make_response(success=True, message="No memberships active.", data=[])
        query = query.filter_by(membershipId=member.id)

    res_list = query.all()
    data = [{
        "id": r.id,
        "title": r.book.title,
        "membershipNumber": r.membership.membershipNumber,
        "status": r.status,
        "reservedAt": r.reservedAt
    } for r in res_list]
    return make_response(success=True, message="Reservations list fetched.", data=data)

@router.post("/reservations/{id}/cancel")
def cancel_reservation(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    res = db.query(BookReservation).filter_by(id=id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found.")

    # IDOR check
    if current_user.role.name == "STUDENT" and res.membership.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized cancellation request.")

    res.status = "CANCELLED"
    db.commit()
    return make_response(success=True, message="Reservation cancelled.", data={})

# ----------------------------------------------------
# 9. Fines Endpoints
# ----------------------------------------------------
@router.get("/fines")
def list_fines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    query = db.query(LibraryFine)
    if current_user.role.name == "STUDENT":
        member = db.query(LibraryMembership).filter_by(userId=current_user.id).first()
        if not member:
            return make_response(success=True, message="No active library membership.", data=[])
        query = query.filter_by(membershipId=member.id)
    
    fines = query.all()
    data = [{
        "id": f.id,
        "amount": float(f.amount),
        "reason": f.reason,
        "status": f.status,
        "assessedAt": f.assessedAt,
        "membershipNumber": f.membership.membershipNumber
    } for f in fines]
    return make_response(success=True, message="Fines records retrieved.", data=data)

@router.post("/fines/{id}/pay")
def pay_fine(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    fine = db.query(LibraryFine).filter_by(id=id, status="PENDING").first()
    if not fine:
        raise HTTPException(status_code=404, detail="Pending fine invoice not resolved.")

    # Mark paid
    fine.status = "PAID"
    fine.paidAt = datetime.utcnow()
    db.commit()
    return make_response(success=True, message="Fine fee paid successfully.", data={})

@router.post("/fines/{id}/waive")
def waive_fine(id: str, payload: FineWaiveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN"])
    
    fine = db.query(LibraryFine).filter_by(id=id, status="PENDING").first()
    if not fine:
        raise HTTPException(status_code=404, detail="Pending fine invoice not resolved.")

    fine.status = "WAIVED"
    fine.waivedAt = datetime.utcnow()
    fine.waivedBy = current_user.id
    fine.waiverReason = payload.waiverReason
    db.commit()
    return make_response(success=True, message="Fine waived successfully.", data={})

# ----------------------------------------------------
# 10. Analytics Endpoint
# ----------------------------------------------------
@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    verify_role(current_user, ["MASTER_ADMIN", "LIBRARIAN"])
    
    total_titles = db.query(Book).count()
    total_copies = db.query(BookCopy).count()
    issued_copies = db.query(BookCopy).filter_by(status="ISSUED").count()
    active_loans = db.query(BookLoan).filter_by(status="ACTIVE").count()
    overdue_loans = db.query(BookLoan).filter_by(status="OVERDUE").count()
    total_fines = db.query(func.sum(LibraryFine.amount)).filter_by(status="PENDING").scalar() or 0.0

    stats = {
        "totalTitles": total_titles,
        "totalCopies": total_copies,
        "issuedCopies": issued_copies,
        "activeLoans": active_loans,
        "overdueLoans": overdue_loans,
        "pendingFinesAmount": float(total_fines)
    }
    return make_response(success=True, message="Library analytics statistics compiled.", data=stats)
