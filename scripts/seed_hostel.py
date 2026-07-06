# scripts/seed_hostel.py
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
    Base, User, Role, Hostel, HostelBlock, HostelFloor, HostelRoom, HostelBed,
    HostelApplication, HostelAllocation, HostelFine, HostelComplaint,
    HostelVisitor, MessPlan, AcademicYear, HostelWardenAssignment
)

def run_seeder():
    db_url = settings.DATABASE_URL
    print("Connecting to database at:", db_url)
    try:
        engine = create_engine(db_url)
        conn = engine.connect()
        conn.close()
        # Initialize schema tables if they don't exist
        print("Ensuring tables are initialized...")
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print("\n[DB CONNECTION ERROR] Could not connect to database or initialize tables.")
        print("Reason:", str(e))
        return

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("Database connected. Starting hostel seeding transaction...")

        # 1. Ensure required roles exist
        admin_role = db.query(Role).filter_by(name="MASTER_ADMIN").first()
        if not admin_role:
            admin_role = Role(id=str(uuid.uuid4()), name="MASTER_ADMIN", description="Master Admin Role")
            db.add(admin_role)
            db.flush()

        student_role = db.query(Role).filter_by(name="STUDENT").first()
        if not student_role:
            student_role = Role(id=str(uuid.uuid4()), name="STUDENT", description="Student Role")
            db.add(student_role)
            db.flush()

        warden_role = db.query(Role).filter_by(name="WARDEN").first()
        if not warden_role:
            warden_role = Role(id=str(uuid.uuid4()), name="WARDEN", description="Hostel Warden Role")
            db.add(warden_role)
            db.flush()

        # 2. Ensure Academic Year exists
        ay = db.query(AcademicYear).filter_by(id="AY-2026").first()
        if not ay:
            ay = AcademicYear(
                id="AY-2026",
                name="Academic Year 2026",
                startDate=datetime.utcnow() - timedelta(days=100),
                endDate=datetime.utcnow() + timedelta(days=265),
                status="ACTIVE"
            )
            db.add(ay)
            db.flush()

        # 3. Create/Ensure Warden and Student Users
        admin_user = db.query(User).filter_by(email="admin@campusgpt.local").first()
        if not admin_user:
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@campusgpt.local",
                username="admin",
                name="Admin User",
                roleId=admin_role.id,
                passwordHash="$2b$12$Z0bC.W7.Gedh8L3vjF9YkuxE49zXy3X6/g239xQ/eYc.rV2Bv7c3C" # mock/password
            )
            db.add(admin_user)
            db.flush()

        student_user = db.query(User).filter_by(email="student@campusgpt.local").first()
        if not student_user:
            student_user = User(
                id="student-hostel-uid",
                email="student@campusgpt.local",
                username="student",
                name="Hostel Student",
                roleId=student_role.id,
                passwordHash="$2b$12$Z0bC.W7.Gedh8L3vjF9YkuxE49zXy3X6/g239xQ/eYc.rV2Bv7c3C"
            )
            db.add(student_user)
            db.flush()

        warden_user = db.query(User).filter_by(email="warden@campusgpt.local").first()
        if not warden_user:
            warden_user = User(
                id=str(uuid.uuid4()),
                email="warden@campusgpt.local",
                username="warden",
                name="Warden Bob",
                roleId=warden_role.id,
                passwordHash="$2b$12$Z0bC.W7.Gedh8L3vjF9YkuxE49zXy3X6/g239xQ/eYc.rV2Bv7c3C"
            )
            db.add(warden_user)
            db.flush()

        # 4. Hostels
        hostel = db.query(Hostel).filter_by(code="RBH").first()
        if not hostel:
            hostel = Hostel(
                id=str(uuid.uuid4()),
                name="Royal Boys Hostel",
                code="RBH",
                hostelType="BOYS",
                capacity=150,
                contactPhone="9988776655",
                active=True
            )
            db.add(hostel)
            db.flush()

            # Assign Warden
            assignment = HostelWardenAssignment(
                id=str(uuid.uuid4()),
                hostelId=hostel.id,
                wardenId=warden_user.id,
                assignmentType="HOSTEL_WARDEN",
                startDate=datetime.utcnow(),
                endDate=datetime.utcnow() + timedelta(days=365),
                active=True
            )
            db.add(assignment)
            db.flush()

        # 5. Blocks
        block = db.query(HostelBlock).filter_by(code="BLOCK-A").first()
        if not block:
            block = HostelBlock(
                id=str(uuid.uuid4()),
                hostelId=hostel.id,
                name="Block A",
                code="BLOCK-A",
                totalFloors=3,
                description="Main block for freshman boys"
            )
            db.add(block)
            db.flush()

        # 6. Floor
        floor = db.query(HostelFloor).filter_by(blockId=block.id, floorNumber=1).first()
        if not floor:
            floor = HostelFloor(
                id=str(uuid.uuid4()),
                blockId=block.id,
                floorNumber=1,
                name="First Floor"
            )
            db.add(floor)
            db.flush()

        # 7. Rooms
        room = db.query(HostelRoom).filter_by(floorId=floor.id, roomNumber="101").first()
        if not room:
            room = HostelRoom(
                id=str(uuid.uuid4()),
                floorId=floor.id,
                roomNumber="101",
                roomType="DOUBLE",
                capacity=2,
                monthlyRate=Decimal("3500.00"),
                amenities="Wifi, Attached Bathroom",
                status="AVAILABLE"
            )
            db.add(room)
            db.flush()

        # 8. Beds
        bed1 = db.query(HostelBed).filter_by(roomId=room.id, bedNumber="101-A").first()
        if not bed1:
            bed1 = HostelBed(id=str(uuid.uuid4()), roomId=room.id, bedNumber="101-A", status="AVAILABLE")
            db.add(bed1)
        bed2 = db.query(HostelBed).filter_by(roomId=room.id, bedNumber="101-B").first()
        if not bed2:
            bed2 = HostelBed(id=str(uuid.uuid4()), roomId=room.id, bedNumber="101-B", status="AVAILABLE")
            db.add(bed2)
        db.flush()

        # 9. Applications
        app = db.query(HostelApplication).filter_by(studentId=student_user.id).first()
        if not app:
            app = HostelApplication(
                id=str(uuid.uuid4()),
                studentId=student_user.id,
                academicYearId=ay.id,
                preferredHostelId=hostel.id,
                preferredRoomType="DOUBLE",
                emergencyContact="9998887776",
                status="APPROVED"
            )
            db.add(app)
            db.flush()

        # 10. Allocations
        alloc = db.query(HostelAllocation).filter_by(studentId=student_user.id).first()
        if not alloc:
            alloc = HostelAllocation(
                id=str(uuid.uuid4()),
                studentId=student_user.id,
                applicationId=app.id,
                bedId=bed1.id,
                allocatedBy=admin_user.id,
                startDate=datetime.utcnow(),
                expectedEndDate=datetime.utcnow() + timedelta(days=180),
                status="ACTIVE"
            )
            db.add(alloc)
            # Update bed status
            bed1.status = "ALLOCATED"
            db.flush()

        # 11. Complaints
        complaint = db.query(HostelComplaint).filter_by(studentId=student_user.id).first()
        if not complaint:
            complaint = HostelComplaint(
                id=str(uuid.uuid4()),
                studentId=student_user.id,
                category="ELECTRICAL",
                priority="HIGH",
                description="Power outlet not working near bed A",
                status="OPEN"
            )
            db.add(complaint)

        # 12. Visitor Records
        visitor = db.query(HostelVisitor).filter_by(studentId=student_user.id).first()
        if not visitor:
            visitor = HostelVisitor(
                id=str(uuid.uuid4()),
                visitorName="John Doe Sr",
                phone="555-0199",
                relation="Father",
                studentId=student_user.id,
                hostelId=hostel.id,
                purpose="Monthly Visit",
                identityType="Passport",
                identityReferenceMasked="XXX-XX-5678",
                checkInAt=datetime.utcnow() - timedelta(hours=2),
                status="CHECKED_IN"
            )
            db.add(visitor)

        # 13. Mess Plans
        mess_plan = db.query(MessPlan).filter_by(name="Standard Veg Plan").first()
        if not mess_plan:
            mess_plan = MessPlan(
                id=str(uuid.uuid4()),
                name="Standard Veg Plan",
                description="Standard three vegetarian meals a day",
                costPerMonth=Decimal("2200.00"),
                foodType="VEG",
                active=True
            )
            db.add(mess_plan)

        # 14. Fine Records
        fine = db.query(HostelFine).filter_by(studentId=student_user.id).first()
        if not fine:
            fine = HostelFine(
                id=str(uuid.uuid4()),
                studentId=student_user.id,
                fineType="DAMAGE",
                amount=Decimal("150.00"),
                reason="Broke desk drawer in Room 101",
                status="PENDING"
            )
            db.add(fine)

        db.commit()
        print("Hostel demo database seeding completed successfully!")
    except Exception as ex:
        db.rollback()
        print("Error during database seeding:")
        print(ex)
    finally:
        db.close()

if __name__ == "__main__":
    run_seeder()
