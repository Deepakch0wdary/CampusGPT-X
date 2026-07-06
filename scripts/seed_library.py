# scripts/seed_library.py
import sys
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add backend directory to path
backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.models import (
    User, LibraryBranch, Book, BookCopy, LibraryMembership, LibraryPolicy,
    Author, Publisher, BookCategory, BookAuthor, BookTag, BookLoan, LibraryFine
)

def run_seeder():
    print("Connecting to database at:", settings.DATABASE_URL)
    try:
        engine = create_engine(settings.DATABASE_URL)
        conn = engine.connect()
        conn.close()
    except Exception as e:
        print("\n[DB CONNECTION ERROR] Could not connect to MySQL database on localhost:3306.")
        print("Reason:", str(e))
        print("Seeding aborted. (This is expected if the local MySQL port is offline.)")
        return

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("Database connected. Starting library seeding transaction...")

        # 1. Library Branch
        branch = db.query(LibraryBranch).filter_by(code="CENTRAL").first()
        if not branch:
            branch = LibraryBranch(
                id=str(uuid.uuid4()),
                name="Central Library",
                code="CENTRAL",
                description="Main campus smart library branch.",
                location="Block B, Ground Floor"
            )
            db.add(branch)
            db.flush()

        # 2. Categories
        categories = {}
        cat_data = [
            ("Artificial Intelligence", "AI"),
            ("Machine Learning", "ML"),
            ("Computer Networks", "CN"),
            ("Software Engineering", "SE")
        ]
        for name, code in cat_data:
            cat = db.query(BookCategory).filter_by(code=code).first()
            if not cat:
                cat = BookCategory(id=str(uuid.uuid4()), name=name, code=code)
                db.add(cat)
                db.flush()
            categories[code] = cat

        # 3. Publisher
        pub = db.query(Publisher).filter_by(name="Pearson Education").first()
        if not pub:
            pub = Publisher(id=str(uuid.uuid4()), name="Pearson Education")
            db.add(pub)
            db.flush()

        # 4. Books Catalog
        books_data = [
            ("9780136086208", "Artificial Intelligence: A Modern Approach", "AI"),
            ("9781492032649", "Hands-On Machine Learning", "ML"),
            ("9780133594140", "Computer Networking: A Top-Down Approach", "CN"),
            ("9780132350884", "Clean Code", "SE")
        ]

        books = {}
        for isbn, title, cat_code in books_data:
            book = db.query(Book).filter_by(isbn13=isbn).first()
            if not book:
                book = Book(
                    id=str(uuid.uuid4()),
                    isbn13=isbn,
                    title=title,
                    publicationYear=2020,
                    language="English",
                    pageCount=500,
                    publisherId=pub.id,
                    categoryId=categories[cat_code].id
                )
                db.add(book)
                db.flush()
            books[title] = book

        # 5. Book Copies
        for title, book in books.items():
            barcode = f"BAR-{book.isbn13[:6]}-01"
            copy = db.query(BookCopy).filter_by(barcode=barcode).first()
            if not copy:
                copy = BookCopy(
                    id=str(uuid.uuid4()),
                    bookId=book.id,
                    branchId=branch.id,
                    accessionNumber=f"ACC-{book.isbn13[:6]}-01",
                    barcode=barcode,
                    acquisitionDate=datetime.utcnow(),
                    acquisitionPrice=Decimal("500.00"),
                    condition="GOOD",
                    status="AVAILABLE"
                )
                db.add(copy)
                db.flush()

        # 6. Library Policies
        for m_type in ["STUDENT", "TEACHER"]:
            policy = db.query(LibraryPolicy).filter_by(memberType=m_type, branchId=branch.id).first()
            if not policy:
                policy = LibraryPolicy(
                    id=str(uuid.uuid4()),
                    memberType=m_type,
                    branchId=branch.id,
                    maxBooks=5 if m_type == "STUDENT" else 10,
                    loanDays=14,
                    renewalLimit=2,
                    reservationLimit=3,
                    finePerDay=Decimal("10.00"),
                    graceDays=3,
                    maxFine=Decimal("500.00")
                )
                db.add(policy)
                db.flush()

        # 7. Student Library Membership
        student_user = db.query(User).filter_by(email="student.demo@campusgpt.local").first()
        if student_user:
            memb = db.query(LibraryMembership).filter_by(userId=student_user.id).first()
            if not memb:
                memb = LibraryMembership(
                    id=str(uuid.uuid4()),
                    userId=student_user.id,
                    membershipNumber="MEMB-STUD-DEMO",
                    memberType="STUDENT",
                    branchId=branch.id,
                    activatedAt=datetime.utcnow(),
                    expiresAt=datetime.utcnow() + timedelta(days=365)
                )
                db.add(memb)
                db.flush()

        db.commit()
        print("Library catalog and demo structures seeded successfully!")
    except Exception as e:
        db.rollback()
        print("Seeding transaction failed and rolled back:", str(e))
    finally:
        db.close()

if __name__ == "__main__":
    run_seeder()
