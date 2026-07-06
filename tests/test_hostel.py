import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import User, Role, Hostel, HostelBlock, HostelFloor, HostelRoom, HostelBed, HostelApplication, HostelAllocation, HostelFine, HostelGatePass, HostelVisitor

def create_test_user(db_session: Session, email: str, username: str, name: str, role_name: str) -> User:
    role = db_session.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name, description=f"{role_name} test role")
        db_session.add(role)
        db_session.commit()

    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username=username,
            name=name,
            roleId=role.id,
            passwordHash="mock_hash"
        )
        db_session.add(user)
        db_session.commit()
    return user

def test_hostel_structure_and_double_booking(client: TestClient, db_session: Session):
    admin = create_test_user(db_session, "admin@campusgpt.local", "admin", "Admin", "MASTER_ADMIN")
    app.dependency_overrides[get_current_user_no_password_force] = lambda: admin

    # Create Hostel
    hostel_payload = {
        "name": "Test Boys Hostel",
        "code": "TBH001",
        "hostelType": "BOYS",
        "capacity": 100,
        "description": "Test"
    }
    response = client.post("/api/v1/hostel/hostels", json=hostel_payload)
    assert response.status_code == 200
    hostel_id = response.json()["hostel_id"]

    # Create Block
    block_payload = {
        "hostelId": hostel_id,
        "name": "Block X",
        "code": "BX01",
        "totalFloors": 1,
        "description": "Block X"
    }
    response = client.post("/api/v1/hostel/blocks", json=block_payload)
    assert response.status_code == 200
    block_id = response.json()["block_id"]

    # Get floor
    floor = db_session.query(HostelFloor).filter(HostelFloor.blockId == block_id).first()
    assert floor is not None

    # Create Room
    room_payload = {
        "floorId": floor.id,
        "roomNumber": "X-101",
        "roomType": "DOUBLE",
        "capacity": 2,
        "monthlyRate": 2500.0,
        "amenities": "Wifi, Fan"
    }
    response = client.post("/api/v1/hostel/rooms", json=room_payload)
    assert response.status_code == 200
    room_id = response.json()["room_id"]

    # Query beds
    beds = db_session.query(HostelBed).filter(HostelBed.roomId == room_id).all()
    assert len(beds) == 2

    # Create Student Users
    student1 = create_test_user(db_session, "student1@campusgpt.local", "student1", "Student One", "STUDENT")
    student2 = create_test_user(db_session, "student2@campusgpt.local", "student2", "Student Two", "STUDENT")

    # Create Applications
    app1 = HostelApplication(studentId=student1.id, academicYearId="AY-01", preferredHostelId=hostel_id, preferredRoomType="DOUBLE", emergencyContact="123")
    app2 = HostelApplication(studentId=student2.id, academicYearId="AY-01", preferredHostelId=hostel_id, preferredRoomType="DOUBLE", emergencyContact="456")
    db_session.add_all([app1, app2])
    db_session.commit()

    # Allocate Bed 1 to Student 1
    app.dependency_overrides[get_current_user_no_password_force] = lambda: admin
    alloc_payload1 = {
        "applicationId": app1.id,
        "bedId": beds[0].id,
        "startDate": datetime.utcnow().isoformat(),
        "expectedEndDate": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    response = client.post("/api/v1/hostel/allocations", json=alloc_payload1)
    assert response.status_code == 200

    # Try allocating same Bed 1 to Student 2 (Should Fail)
    alloc_payload2 = {
        "applicationId": app2.id,
        "bedId": beds[0].id,
        "startDate": datetime.utcnow().isoformat(),
        "expectedEndDate": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    response = client.post("/api/v1/hostel/allocations", json=alloc_payload2)
    assert response.status_code == 400
    assert "already booked" in str(response.json())


def test_leave_and_gate_pass_verification(client: TestClient, db_session: Session):
    student = create_test_user(db_session, "student@campusgpt.local", "student", "Student", "STUDENT")

    # Ensure a hostel and allocation exists
    hostel = db_session.query(Hostel).first()
    if not hostel:
        hostel = Hostel(name="Boys Hostel", code="BH01", hostelType="BOYS", capacity=10)
        db_session.add(hostel)
        db_session.commit()

    block = db_session.query(HostelBlock).first()
    if not block:
        block = HostelBlock(hostelId=hostel.id, name="Block A", code="BA01", totalFloors=1)
        db_session.add(block)
        db_session.commit()

    floor = db_session.query(HostelFloor).filter(HostelFloor.blockId == block.id).first()
    if not floor:
        floor = HostelFloor(blockId=block.id, floorNumber=1, name="Floor 1")
        db_session.add(floor)
        db_session.commit()

    room = db_session.query(HostelRoom).first()
    if not room:
        room = HostelRoom(floorId=floor.id, roomNumber="R-101", roomType="SINGLE", capacity=1, monthlyRate=Decimal("2000.0"))
        db_session.add(room)
        db_session.commit()

    bed = db_session.query(HostelBed).first()
    if not bed:
        bed = HostelBed(roomId=room.id, bedNumber="B-1")
        db_session.add(bed)
        db_session.commit()

    app_record = db_session.query(HostelApplication).filter(HostelApplication.studentId == student.id).first()
    if not app_record:
        app_record = HostelApplication(studentId=student.id, academicYearId="AY-01", preferredHostelId=hostel.id, preferredRoomType="SINGLE", emergencyContact="123")
        db_session.add(app_record)
        db_session.commit()

    allocation = db_session.query(HostelAllocation).filter(HostelAllocation.studentId == student.id).first()
    if not allocation:
        allocation = HostelAllocation(studentId=student.id, applicationId=app_record.id, bedId=bed.id, allocatedBy=student.id, startDate=datetime.utcnow(), expectedEndDate=datetime.utcnow() + timedelta(days=30))
        db_session.add(allocation)
        db_session.commit()

    # Apply for leave
    leave_payload = {
        "allocationId": allocation.id,
        "leaveType": "HOME_HOLIDAY",
        "reason": "Family gathering",
        "destination": "New York",
        "startAt": datetime.utcnow().isoformat(),
        "expectedReturnAt": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        "guardianContact": "9998887776"
    }
    app.dependency_overrides[get_current_user_no_password_force] = lambda: student
    response = client.post("/api/v1/hostel/leave-requests", json=leave_payload)
    assert response.status_code == 200
    leave_id = response.json()["leave_id"]

    # Review leave (Warden / Admin role)
    admin = create_test_user(db_session, "admin@campusgpt.local", "admin", "Admin", "MASTER_ADMIN")
    app.dependency_overrides[get_current_user_no_password_force] = lambda: admin
    response = client.patch(f"/api/v1/hostel/leave-requests/{leave_id}/review", json={"status": "APPROVED"})
    assert response.status_code == 200

    # Verify Gate Pass exists
    gate_pass = db_session.query(HostelGatePass).filter(HostelGatePass.leaveRequestId == leave_id).first()
    assert gate_pass is not None
    assert gate_pass.status == "ACTIVE"

    # Verify Gate Pass via Token
    response = client.post(f"/api/v1/hostel/gate-passes/verify?token={gate_pass.passToken}")
    assert response.status_code == 200
    assert response.json()["message"] == "Gate pass verified and marked as used"


def test_visitor_registration_and_masking(client: TestClient, db_session: Session):
    student = create_test_user(db_session, "student@campusgpt.local", "student", "Student", "STUDENT")
    app.dependency_overrides[get_current_user_no_password_force] = lambda: student

    hostel = db_session.query(Hostel).first()
    if not hostel:
        hostel = Hostel(name="Boys Hostel", code="BH01", hostelType="BOYS", capacity=10)
        db_session.add(hostel)
        db_session.commit()

    visitor_payload = {
        "visitorName": "John Doe Sr",
        "phone": "555-0199",
        "relation": "Father",
        "studentId": student.id,
        "hostelId": hostel.id,
        "purpose": "Monthly Visit",
        "identityType": "Passport",
        "identityReference": "US12345678"
    }
    response = client.post("/api/v1/hostel/visitors", json=visitor_payload)
    assert response.status_code == 200
    visitor_id = response.json()["visitor_id"]

    # Retrieve visitors and check masking
    response = client.get("/api/v1/hostel/visitors")
    assert response.status_code == 200
    visitors_list = response.json()
    my_visitor = next(v for v in visitors_list if v["id"] == visitor_id)
    assert my_visitor["identityReferenceMasked"] == "XXX-XX-5678"


def test_fine_waiver_security_and_audit(client: TestClient, db_session: Session):
    student = create_test_user(db_session, "student@campusgpt.local", "student", "Student", "STUDENT")
    admin = create_test_user(db_session, "admin@campusgpt.local", "admin", "Admin", "MASTER_ADMIN")

    # Create a Fine
    fine = HostelFine(studentId=student.id, fineType="DAMAGE", amount=Decimal("150.0"), reason="Broke chair")
    db_session.add(fine)
    db_session.commit()

    # Try waiving as student (Should be Denied)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: student
    response = client.post(f"/api/v1/hostel/fines/{fine.id}/waive?reason=StudentRequest")
    assert response.status_code == 403

    # Waive as Master Admin (Should Pass)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: admin
    response = client.post(f"/api/v1/hostel/fines/{fine.id}/waive?reason=WardenApprovedWaiver")
    assert response.status_code == 200

    # Verify Fine Status is Waived
    db_session.refresh(fine)
    assert fine.status == "WAIVED"
    assert fine.waiverReason == "WardenApprovedWaiver"


def test_student_idor_prevention(client: TestClient, db_session: Session):
    student1 = create_test_user(db_session, "student1@campusgpt.local", "student1", "Student One", "STUDENT")
    student2 = create_test_user(db_session, "student2@campusgpt.local", "student2", "Student Two", "STUDENT")

    hostel = db_session.query(Hostel).first()
    if not hostel:
        hostel = Hostel(name="Boys Hostel", code="BH01", hostelType="BOYS", capacity=10)
        db_session.add(hostel)
        db_session.commit()

    app_record = db_session.query(HostelApplication).filter(HostelApplication.studentId == student2.id).first()
    if not app_record:
        app_record = HostelApplication(studentId=student2.id, academicYearId="AY-01", preferredHostelId=hostel.id, preferredRoomType="SINGLE", emergencyContact="123")
        db_session.add(app_record)
        db_session.commit()

    # Login as student 1 and try retrieving student 2's application details (Should fail)
    app.dependency_overrides[get_current_user_no_password_force] = lambda: student1
    response = client.get(f"/api/v1/hostel/applications/{app_record.id}")
    assert response.status_code == 403
