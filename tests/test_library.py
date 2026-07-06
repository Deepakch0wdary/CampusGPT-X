import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from decimal import Decimal

# Add backend directory to path
backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app
from app.models.models import (
    User, Role, LibraryBranch, Book, BookCopy, LibraryMembership, LibraryPolicy,
    BookLoan, LoanRenewal, BookReservation, LibraryFine
)
from app.core.auth_middleware import get_current_user_no_password_force

@pytest.fixture
def seed_library_test_data(db_session):
    # Setup roles
    admin_role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    student_role = db_session.query(Role).filter_by(name="STUDENT").first()

    # Users
    admin = User(id="admin-u-1", email="admin@library.local", username="admin_lib", name="Librarian Admin", passwordHash="hash", roleId=admin_role.id)
    student1 = User(id="stud-u-1", email="student1@library.local", username="student1", name="Student Samantha", passwordHash="hash", roleId=student_role.id)
    student2 = User(id="stud-u-2", email="student2@library.local", username="student2", name="Student Marcus", passwordHash="hash", roleId=student_role.id)
    db_session.add_all([admin, student1, student2])
    db_session.flush()

    # Library Branch
    branch = LibraryBranch(id="branch-1", name="Central Library", code="CENTRAL")
    db_session.add(branch)
    db_session.flush()

    return {
        "admin": admin,
        "student1": student1,
        "student2": student2,
        "branch": branch
    }

def test_library_catalog_flow(db_session, seed_library_test_data):
    client = TestClient(app)
    data = seed_library_test_data

    # Log in as Admin
    app.dependency_overrides[get_current_user_no_password_force] = lambda: data["admin"]

    # 1. Create a Book
    book_payload = {
        "isbn13": "9780134685991",
        "title": "Effective Java",
        "publicationYear": 2018,
        "language": "English",
        "pageCount": 412,
        "publisherName": "Addison-Wesley",
        "categoryName": "Programming",
        "categoryCode": "PROG",
        "authors": ["Joshua Bloch"],
        "tags": ["Java", "Best Practices"]
    }
    res_book = client.post("/api/v1/library/books", json=book_payload)
    assert res_book.status_code == 200
    book_id = res_book.json()["data"]["id"]

    # 2. Add Book Copy
    copy_payload = {
        "bookId": book_id,
        "branchId": data["branch"].id,
        "accessionNumber": "ACC-EJ-01",
        "barcode": "BARCODE-EJ-01",
        "acquisitionPrice": 450.00
    }
    res_copy = client.post("/api/v1/library/copies", json=copy_payload)
    assert res_copy.status_code == 200

    # 3. Create Student Membership
    memb_payload = {
        "userId": data["student1"].id,
        "membershipNumber": "MEMB-STUD-01",
        "memberType": "STUDENT",
        "branchId": data["branch"].id
    }
    res_memb = client.post("/api/v1/library/memberships", json=memb_payload)
    assert res_memb.status_code == 200

    # Check search
    res_search = client.get("/api/v1/library/books", params={"search": "Effective"})
    assert res_search.status_code == 200
    assert len(res_search.json()["data"]) == 1

def test_book_circulation_and_fines_flow(db_session, seed_library_test_data):
    client = TestClient(app)
    data = seed_library_test_data

    # Log in as Admin
    app.dependency_overrides[get_current_user_no_password_force] = lambda: data["admin"]

    # Seed Book, Copy, and Membership
    book = Book(id="b-1", isbn13="111-222-333", title="Clean Code", publicationYear=2008, language="EN", pageCount=300, publisherId="pub-1", categoryId="cat-1")
    copy = BookCopy(id="c-1", bookId="b-1", branchId=data["branch"].id, accessionNumber="ACC-CC-01", barcode="BAR-CC-01", acquisitionPrice=Decimal("50.00"), status="AVAILABLE", acquisitionDate=datetime.utcnow())
    memb = LibraryMembership(id="m-1", userId=data["student1"].id, membershipNumber="MEM-01", memberType="STUDENT", activatedAt=datetime.utcnow(), expiresAt=datetime.utcnow() + timedelta(days=365))
    policy = LibraryPolicy(id="pol-1", memberType="STUDENT", branchId=data["branch"].id, maxBooks=2, loanDays=7, renewalLimit=1, reservationLimit=1, finePerDay=Decimal("5.00"), graceDays=1, maxFine=Decimal("100.00"))
    
    db_session.add_all([book, copy, memb, policy])
    db_session.commit()

    # 1. Issue Book copy to student
    issue_res = client.post("/api/v1/library/loans/issue", json={
        "membershipNumber": "MEM-01",
        "barcode": "BAR-CC-01"
    })
    assert issue_res.status_code == 200
    loan_id = issue_res.json()["data"]["loanId"]

    # Try duplicate issue of same copy -> Should fail
    dup_res = client.post("/api/v1/library/loans/issue", json={
        "membershipNumber": "MEM-01",
        "barcode": "BAR-CC-01"
    })
    assert dup_res.status_code == 400

    # 2. Renew loan
    renew_res = client.post(f"/api/v1/library/loans/{loan_id}/renew")
    assert renew_res.status_code == 200

    # Second renewal -> Fails (limit is 1)
    renew_res2 = client.post(f"/api/v1/library/loans/{loan_id}/renew")
    assert renew_res2.status_code == 400

    # 3. Return Book (overdue simulation)
    # Simulate overdue loan return
    loan = db_session.query(BookLoan).filter_by(id=loan_id).first()
    loan.dueAt = datetime.utcnow() - timedelta(days=5)
    db_session.commit()

    ret_res = client.post(f"/api/v1/library/loans/{loan_id}/return", json={
        "barcode": "BAR-CC-01"
    })
    assert ret_res.status_code == 200
    assert ret_res.json()["data"]["fineAssessed"] > 0

    # Check fines list
    fines_res = client.get("/api/v1/library/fines")
    assert fines_res.status_code == 200
    assert len(fines_res.json()["data"]) == 1
    fine_id = fines_res.json()["data"][0]["id"]

    # 4. Waive fine as admin -> Success
    waive_res = client.post(f"/api/v1/library/fines/{fine_id}/waive", json={"waiverReason": "Health reasons"})
    assert waive_res.status_code == 200

def test_library_student_idor_restrictions(db_session, seed_library_test_data):
    client = TestClient(app)
    data = seed_library_test_data

    # Log in as Student 1
    app.dependency_overrides[get_current_user_no_password_force] = lambda: data["student1"]

    # 1. Attempt to fetch all library memberships (Admin route) -> Forbidden 403
    res_memb = client.get("/api/v1/library/memberships")
    assert res_memb.status_code == 403

    # 2. Attempt to create a branch -> Forbidden 403
    res_branch = client.post("/api/v1/library/branches", json={"name": "New Branch", "code": "NEW"})
    assert res_branch.status_code == 403
