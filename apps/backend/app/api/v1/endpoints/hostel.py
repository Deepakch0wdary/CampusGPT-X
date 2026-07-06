from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import (
    User, Hostel, HostelBlock, HostelFloor, HostelRoom, HostelBed,
    HostelApplication, HostelAllocation, HostelCheckIn, HostelCheckOut,
    HostelTransferRequest, HostelWardenAssignment, HostelVisitor,
    HostelComplaint, HostelComplaintComment, HostelMaintenanceRequest,
    HostelLeaveRequest, HostelGatePass, MessPlan, MessSubscription,
    MessMenu, MessAttendance, HostelFine, HostelIncident, HostelAudit
)

router = APIRouter()

# --- HELPERS ---
def log_audit(db: Session, user_id: str, action: str, details: str):
    audit = HostelAudit(userId=user_id, action=action, details=details)
    db.add(audit)
    db.commit()

# --- SCHEMAS ---
class HostelCreate(BaseModel):
    name: str
    code: str
    hostelType: str
    capacity: int
    description: Optional[str] = None
    address: Optional[str] = None
    contactPhone: Optional[str] = None
    contactEmail: Optional[str] = None

class BlockCreate(BaseModel):
    hostelId: str
    name: str
    code: str
    totalFloors: int
    description: Optional[str] = None

class RoomCreate(BaseModel):
    floorId: str
    roomNumber: str
    roomType: str
    capacity: int
    monthlyRate: float
    amenities: Optional[str] = None

class BedCreate(BaseModel):
    roomId: str
    bedNumber: str

class ApplicationCreate(BaseModel):
    academicYearId: str
    preferredHostelId: str
    preferredRoomType: str
    emergencyContact: str
    reason: Optional[str] = None
    medicalNotes: Optional[str] = None

class ApplicationReview(BaseModel):
    status: str # APPROVED, REJECTED, WAITLISTED

class AllocationCreate(BaseModel):
    applicationId: str
    bedId: str
    startDate: datetime
    expectedEndDate: datetime

class CheckInCreate(BaseModel):
    inventoryNotes: Optional[str] = None
    conditionNotes: Optional[str] = None
    acknowledgement: bool

class CheckOutCreate(BaseModel):
    damageNotes: Optional[str] = None
    damageCost: float = 0.0
    inventoryNotes: Optional[str] = None

class TransferRequestCreate(BaseModel):
    currentAllocationId: str
    preferredBedId: str
    reason: str

class TransferReview(BaseModel):
    status: str # APPROVED, REJECTED

class VisitorCreate(BaseModel):
    visitorName: str
    phone: str
    relation: str
    studentId: str
    hostelId: str
    purpose: str
    identityType: str
    identityReference: str

class ComplaintCreate(BaseModel):
    category: str
    priority: str
    description: str

class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    assignedTo: Optional[str] = None

class MaintenanceCreate(BaseModel):
    hostelId: str
    roomId: Optional[str] = None
    bedId: Optional[str] = None
    category: str
    description: str
    priority: str
    assignedTo: str
    estimatedCost: float

class MaintenanceUpdate(BaseModel):
    status: str # COMPLETED, IN_PROGRESS
    actualCost: Optional[float] = None

class LeaveCreate(BaseModel):
    allocationId: str
    leaveType: str
    reason: str
    destination: str
    startAt: datetime
    expectedReturnAt: datetime
    guardianContact: str

class LeaveReview(BaseModel):
    status: str # APPROVED, REJECTED

class GatePassCreate(BaseModel):
    studentId: str
    purpose: str
    expiryMinutes: int = 120

class MessPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    costPerMonth: float
    foodType: str

class MessMenuCreate(BaseModel):
    planId: str
    dayOfWeek: str
    mealType: str
    menuDetails: str

class MessAttendanceCreate(BaseModel):
    planId: str
    mealDate: datetime
    mealType: str
    status: str = "PRESENT"

# --- HOSTELS CRUD ---
@router.post("/hostels", response_model=dict)
def create_hostel(payload: HostelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    # Check uniqueness
    existing = db.query(Hostel).filter((Hostel.code == payload.code) | (Hostel.name == payload.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Hostel code or name already exists")

    hostel = Hostel(
        name=payload.name,
        code=payload.code,
        hostelType=payload.hostelType,
        capacity=payload.capacity,
        description=payload.description,
        address=payload.address,
        contactPhone=payload.contactPhone,
        contactEmail=payload.contactEmail
    )
    db.add(hostel)
    db.commit()
    db.refresh(hostel)
    log_audit(db, current_user.id, "CREATE_HOSTEL", f"Hostel {hostel.name} created")
    return {"message": "Hostel created successfully", "hostel_id": hostel.id}

@router.get("/hostels", response_model=List[dict])
def get_hostels(db: Session = Depends(get_db)):
    hostels = db.query(Hostel).all()
    result = []
    for h in hostels:
        result.append({
            "id": h.id,
            "name": h.name,
            "code": h.code,
            "hostelType": h.hostelType,
            "capacity": h.capacity,
            "description": h.description,
            "address": h.address,
            "contactPhone": h.contactPhone,
            "contactEmail": h.contactEmail,
            "active": h.active
        })
    return result

@router.get("/hostels/{id}", response_model=dict)
def get_hostel(id: str, db: Session = Depends(get_db)):
    h = db.query(Hostel).filter(Hostel.id == id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hostel not found")
    return {
        "id": h.id,
        "name": h.name,
        "code": h.code,
        "hostelType": h.hostelType,
        "capacity": h.capacity,
        "description": h.description,
        "address": h.address,
        "contactPhone": h.contactPhone,
        "contactEmail": h.contactEmail,
        "active": h.active
    }

@router.put("/hostels/{id}", response_model=dict)
def update_hostel(id: str, payload: HostelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    h = db.query(Hostel).filter(Hostel.id == id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hostel not found")

    h.name = payload.name
    h.code = payload.code
    h.hostelType = payload.hostelType
    h.capacity = payload.capacity
    h.description = payload.description
    h.address = payload.address
    h.contactPhone = payload.contactPhone
    h.contactEmail = payload.contactEmail
    db.commit()
    log_audit(db, current_user.id, "UPDATE_HOSTEL", f"Hostel {h.name} updated")
    return {"message": "Hostel updated successfully"}

# --- BLOCKS CRUD ---
@router.post("/blocks", response_model=dict)
def create_block(payload: BlockCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    # Check unique code
    existing = db.query(HostelBlock).filter(HostelBlock.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Block code already exists")

    block = HostelBlock(
        hostelId=payload.hostelId,
        name=payload.name,
        code=payload.code,
        totalFloors=payload.totalFloors,
        description=payload.description
    )
    db.add(block)
    db.commit()
    db.refresh(block)

    # Automatically generate HostelFloor records
    for i in range(1, payload.totalFloors + 1):
        floor = HostelFloor(blockId=block.id, floorNumber=i, name=f"Floor {i}")
        db.add(floor)
    db.commit()

    log_audit(db, current_user.id, "CREATE_BLOCK", f"Block {block.name} created")
    return {"message": "Block created successfully", "block_id": block.id}

@router.get("/blocks", response_model=List[dict])
def get_blocks(db: Session = Depends(get_db)):
    blocks = db.query(HostelBlock).all()
    result = []
    for b in blocks:
        result.append({
            "id": b.id,
            "hostelId": b.hostelId,
            "hostelName": b.hostel.name if b.hostel else "Unknown",
            "name": b.name,
            "code": b.code,
            "totalFloors": b.totalFloors,
            "description": b.description,
            "active": b.active
        })
    return result

# --- ROOMS CRUD ---
@router.post("/rooms", response_model=dict)
def create_room(payload: RoomCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    existing = db.query(HostelRoom).filter(HostelRoom.roomNumber == payload.roomNumber).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room number already exists")

    room = HostelRoom(
        floorId=payload.floorId,
        roomNumber=payload.roomNumber,
        roomType=payload.roomType,
        capacity=payload.capacity,
        monthlyRate=Decimal(str(payload.monthlyRate)),
        amenities=payload.amenities
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # Auto-generate beds
    for i in range(1, payload.capacity + 1):
        bed = HostelBed(roomId=room.id, bedNumber=f"{room.roomNumber}-B{i}")
        db.add(bed)
    db.commit()

    log_audit(db, current_user.id, "CREATE_ROOM", f"Room {room.roomNumber} created with {payload.capacity} beds")
    return {"message": "Room created successfully", "room_id": room.id}

@router.get("/rooms", response_model=List[dict])
def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(HostelRoom).all()
    result = []
    for r in rooms:
        result.append({
            "id": r.id,
            "floorId": r.floorId,
            "roomNumber": r.roomNumber,
            "roomType": r.roomType,
            "capacity": r.capacity,
            "monthlyRate": float(r.monthlyRate),
            "status": r.status,
            "amenities": r.amenities,
            "active": r.active
        })
    return result

@router.get("/rooms/{id}", response_model=dict)
def get_room(id: str, db: Session = Depends(get_db)):
    r = db.query(HostelRoom).filter(HostelRoom.id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "id": r.id,
        "floorId": r.floorId,
        "roomNumber": r.roomNumber,
        "roomType": r.roomType,
        "capacity": r.capacity,
        "monthlyRate": float(r.monthlyRate),
        "status": r.status,
        "amenities": r.amenities,
        "active": r.active
    }

@router.put("/rooms/{id}", response_model=dict)
def update_room(id: str, payload: RoomCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    r = db.query(HostelRoom).filter(HostelRoom.id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")

    r.roomNumber = payload.roomNumber
    r.roomType = payload.roomType
    r.capacity = payload.capacity
    r.monthlyRate = Decimal(str(payload.monthlyRate))
    r.amenities = payload.amenities
    db.commit()
    log_audit(db, current_user.id, "UPDATE_ROOM", f"Room {r.roomNumber} updated")
    return {"message": "Room updated successfully"}

# --- BEDS CRUD ---
@router.post("/beds", response_model=dict)
def create_bed(payload: BedCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    # Check if duplicate in room
    existing = db.query(HostelBed).filter(HostelBed.roomId == payload.roomId, HostelBed.bedNumber == payload.bedNumber).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bed number already exists in this room")

    bed = HostelBed(roomId=payload.roomId, bedNumber=payload.bedNumber)
    db.add(bed)
    db.commit()
    db.refresh(bed)
    return {"message": "Bed created successfully", "bed_id": bed.id}

@router.get("/beds", response_model=List[dict])
def get_beds(db: Session = Depends(get_db)):
    beds = db.query(HostelBed).all()
    result = []
    for b in beds:
        result.append({
            "id": b.id,
            "roomId": b.roomId,
            "roomNumber": b.room.roomNumber if b.room else "Unknown",
            "bedNumber": b.bedNumber,
            "status": b.status,
            "active": b.active
        })
    return result

# --- APPLICATIONS CRUD & REVIEW ---
@router.post("/applications", response_model=dict)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can apply for hostels")

    # Ensure student does not have another active application
    existing = db.query(HostelApplication).filter(HostelApplication.studentId == current_user.id, HostelApplication.status.in_(["SUBMITTED", "UNDER_REVIEW", "APPROVED", "WAITLISTED"])).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active application")

    app = HostelApplication(
        studentId=current_user.id,
        academicYearId=payload.academicYearId,
        preferredHostelId=payload.preferredHostelId,
        preferredRoomType=payload.preferredRoomType,
        emergencyContact=payload.emergencyContact,
        reason=payload.reason,
        medicalNotes=payload.medicalNotes
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    log_audit(db, current_user.id, "CREATE_APPLICATION", f"Hostel application submitted by {current_user.name}")
    return {"message": "Application submitted successfully", "application_id": app.id}

@router.get("/applications", response_model=List[dict])
def get_applications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name == "STUDENT":
        apps = db.query(HostelApplication).filter(HostelApplication.studentId == current_user.id).all()
    elif current_user.role.name in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        apps = db.query(HostelApplication).all()
    else:
        raise HTTPException(status_code=403, detail="Permission Denied")

    result = []
    for a in apps:
        result.append({
            "id": a.id,
            "studentId": a.studentId,
            "studentName": a.student.name if a.student else "Unknown",
            "preferredHostelId": a.preferredHostelId,
            "preferredHostelName": a.preferredHostel.name if a.preferredHostel else "Unknown",
            "preferredRoomType": a.preferredRoomType,
            "emergencyContact": a.emergencyContact,
            "status": a.status,
            "submittedAt": a.submittedAt
        })
    return result

@router.get("/applications/{id}", response_model=dict)
def get_application(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    app = db.query(HostelApplication).filter(HostelApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # IDOR check
    if current_user.role.name == "STUDENT" and app.studentId != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")

    return {
        "id": app.id,
        "studentId": app.studentId,
        "studentName": app.student.name if app.student else "Unknown",
        "preferredHostelId": app.preferredHostelId,
        "preferredHostelName": app.preferredHostel.name if app.preferredHostel else "Unknown",
        "preferredRoomType": app.preferredRoomType,
        "reason": app.reason,
        "medicalNotes": app.medicalNotes,
        "emergencyContact": app.emergencyContact,
        "status": app.status,
        "submittedAt": app.submittedAt
    }

@router.patch("/applications/{id}/review", response_model=dict)
def review_application(id: str, payload: ApplicationReview, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    app = db.query(HostelApplication).filter(HostelApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.status not in ["APPROVED", "REJECTED", "WAITLISTED"]:
        raise HTTPException(status_code=400, detail="Invalid target status")

    app.status = payload.status
    app.reviewedAt = datetime.utcnow()
    app.reviewedBy = current_user.id
    db.commit()

    log_audit(db, current_user.id, "REVIEW_APPLICATION", f"Application {app.id} marked as {payload.status}")
    return {"message": f"Application status updated to {payload.status}"}

# --- ALLOCATIONS CRUD, CHECK-IN, CHECK-OUT ---
@router.post("/allocations", response_model=dict)
def create_allocation(payload: AllocationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    app = db.query(HostelApplication).filter(HostelApplication.id == payload.applicationId).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    bed = db.query(HostelBed).filter(HostelBed.id == payload.bedId).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    if bed.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Selected bed is already booked or maintenance blocked")

    # Check if student already has another active allocation
    existing_allocation = db.query(HostelAllocation).filter(HostelAllocation.studentId == app.studentId, HostelAllocation.status == "ACTIVE").first()
    if existing_allocation:
        raise HTTPException(status_code=400, detail="Student is already allocated an active bed")

    # Save allocation
    allocation = HostelAllocation(
        studentId=app.studentId,
        applicationId=app.id,
        bedId=bed.id,
        allocatedBy=current_user.id,
        startDate=payload.startDate,
        expectedEndDate=payload.expectedEndDate,
        status="ACTIVE"
    )
    db.add(allocation)

    # Update application & bed
    app.status = "ALLOCATED"
    bed.status = "ALLOCATED"

    # Update room status based on occupancy
    room = bed.room
    occupied_beds_count = db.query(HostelBed).filter(HostelBed.roomId == room.id, HostelBed.status == "ALLOCATED").count() + 1
    if occupied_beds_count >= room.capacity:
        room.status = "FULL"
    else:
        room.status = "PARTIALLY_OCCUPIED"

    db.commit()
    log_audit(db, current_user.id, "ALLOCATE_BED", f"Bed {bed.bedNumber} allocated to Student {app.studentId}")
    return {"message": "Bed allocated successfully", "allocation_id": allocation.id}

@router.get("/allocations", response_model=List[dict])
def get_allocations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name == "STUDENT":
        allocs = db.query(HostelAllocation).filter(HostelAllocation.studentId == current_user.id).all()
    elif current_user.role.name in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        allocs = db.query(HostelAllocation).all()
    else:
        raise HTTPException(status_code=403, detail="Permission Denied")

    result = []
    for al in allocs:
        result.append({
            "id": al.id,
            "studentId": al.studentId,
            "studentName": al.student.name if al.student else "Unknown",
            "bedId": al.bedId,
            "bedNumber": al.bed.bedNumber if al.bed else "Unknown",
            "roomNumber": al.bed.room.roomNumber if al.bed and al.bed.room else "Unknown",
            "status": al.status,
            "startDate": al.startDate,
            "expectedEndDate": al.expectedEndDate
        })
    return result

@router.post("/allocations/{id}/check-in", response_model=dict)
def check_in_student(id: str, payload: CheckInCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    al = db.query(HostelAllocation).filter(HostelAllocation.id == id).first()
    if not al:
        raise HTTPException(status_code=404, detail="Allocation not found")

    check_in = HostelCheckIn(
        allocationId=al.id,
        checkedInBy=current_user.id,
        inventoryNotes=payload.inventoryNotes,
        conditionNotes=payload.conditionNotes,
        acknowledgement=payload.acknowledgement
    )
    db.add(check_in)
    db.commit()

    log_audit(db, current_user.id, "CHECK_IN_STUDENT", f"Check-in verified for student {al.studentId}")
    return {"message": "Student check-in completed successfully"}

@router.post("/allocations/{id}/check-out", response_model=dict)
def check_out_student(id: str, payload: CheckOutCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    al = db.query(HostelAllocation).filter(HostelAllocation.id == id, HostelAllocation.status == "ACTIVE").first()
    if not al:
        raise HTTPException(status_code=404, detail="Active allocation not found")

    # Releases bed
    bed = al.bed
    bed.status = "AVAILABLE"

    # Update room status
    room = bed.room
    room.status = "AVAILABLE"

    # Update allocation
    al.status = "COMPLETED"
    al.actualEndDate = datetime.utcnow()

    checkout = HostelCheckOut(
        allocationId=al.id,
        checkedOutBy=current_user.id,
        damageNotes=payload.damageNotes,
        damageCost=Decimal(str(payload.damageCost)),
        inventoryNotes=payload.inventoryNotes,
        status="COMPLETED" if payload.damageCost == 0 else "PENALIZED"
    )
    db.add(checkout)

    # If damage cost assessed, insert a HostelFine
    if payload.damageCost > 0:
        fine = HostelFine(
            studentId=al.studentId,
            allocationId=al.id,
            fineType="DAMAGE",
            amount=Decimal(str(payload.damageCost)),
            reason=payload.damageNotes or "Room Damage Fee assessed at Checkout"
        )
        db.add(fine)

    db.commit()
    log_audit(db, current_user.id, "CHECK_OUT_STUDENT", f"Check-out processed for Student {al.studentId}")
    return {"message": "Check-out completed and bed released"}

# --- ROOM TRANSFER REQUESTS ---
@router.post("/transfers", response_model=dict)
def create_transfer_request(payload: TransferRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Access Denied")

    al = db.query(HostelAllocation).filter(HostelAllocation.id == payload.currentAllocationId, HostelAllocation.studentId == current_user.id, HostelAllocation.status == "ACTIVE").first()
    if not al:
        raise HTTPException(status_code=400, detail="Active allocation not found for you")

    target_bed = db.query(HostelBed).filter(HostelBed.id == payload.preferredBedId).first()
    if not target_bed or target_bed.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Target preferred bed is not available")

    req = HostelTransferRequest(
        studentId=current_user.id,
        currentAllocationId=al.id,
        preferredBedId=payload.preferredBedId,
        reason=payload.reason
    )
    db.add(req)
    db.commit()
    log_audit(db, current_user.id, "TRANSFER_REQUEST", f"Transfer request submitted to bed {payload.preferredBedId}")
    return {"message": "Transfer request submitted", "request_id": req.id}

@router.patch("/transfers/{id}/review", response_model=dict)
def review_transfer(id: str, payload: TransferReview, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    req = db.query(HostelTransferRequest).filter(HostelTransferRequest.id == id, HostelTransferRequest.status == "PENDING").first()
    if not req:
        raise HTTPException(status_code=404, detail="Pending request not found")

    if payload.status == "APPROVED":
        old_alloc = db.query(HostelAllocation).filter(HostelAllocation.id == req.currentAllocationId).first()
        old_bed = old_alloc.bed
        old_bed.status = "AVAILABLE"

        target_bed = db.query(HostelBed).filter(HostelBed.id == req.preferredBedId).first()
        target_bed.status = "ALLOCATED"

        old_alloc.status = "TRANSFERRED"
        old_alloc.actualEndDate = datetime.utcnow()

        new_alloc = HostelAllocation(
            studentId=old_alloc.studentId,
            applicationId=old_alloc.applicationId,
            bedId=target_bed.id,
            allocatedBy=current_user.id,
            startDate=datetime.utcnow(),
            expectedEndDate=old_alloc.expectedEndDate,
            status="ACTIVE"
        )
        db.add(new_alloc)
        req.status = "COMPLETED"
    else:
        req.status = "REJECTED"

    req.reviewedBy = current_user.id
    req.reviewedAt = datetime.utcnow()
    db.commit()

    log_audit(db, current_user.id, "REVIEW_TRANSFER", f"Transfer request {id} reviewed: {payload.status}")
    return {"message": f"Transfer request review processed as {payload.status}"}

# --- VISITORS ---
@router.post("/visitors", response_model=dict)
def create_visitor(payload: VisitorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN", "STUDENT"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    visitor = HostelVisitor(
        visitorName=payload.visitorName,
        phone=payload.phone,
        relation=payload.relation,
        studentId=payload.studentId,
        hostelId=payload.hostelId,
        purpose=payload.purpose,
        identityType=payload.identityType,
        identityReferenceMasked=f"XXX-XX-{payload.identityReference[-4:]}" if len(payload.identityReference) >= 4 else "Masked"
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    return {"message": "Visitor record registered", "visitor_id": visitor.id}

@router.get("/visitors", response_model=List[dict])
def get_visitors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name == "STUDENT":
        visitors = db.query(HostelVisitor).filter(HostelVisitor.studentId == current_user.id).all()
    else:
        visitors = db.query(HostelVisitor).all()

    result = []
    for v in visitors:
        result.append({
            "id": v.id,
            "visitorName": v.visitorName,
            "relation": v.relation,
            "phone": v.phone,
            "purpose": v.purpose,
            "identityReferenceMasked": v.identityReferenceMasked,
            "checkInAt": v.checkInAt,
            "checkOutAt": v.checkOutAt,
            "status": v.status
        })
    return result

@router.post("/visitors/{id}/check-in", response_model=dict)
def visitor_check_in(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    v = db.query(HostelVisitor).filter(HostelVisitor.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Visitor not found")
    v.status = "CHECKED_IN"
    v.checkInAt = datetime.utcnow()
    v.approvedBy = current_user.id
    db.commit()
    return {"message": "Visitor check-in logged"}

@router.post("/visitors/{id}/check-out", response_model=dict)
def visitor_check_out(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    v = db.query(HostelVisitor).filter(HostelVisitor.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Visitor not found")
    v.status = "CHECKED_OUT"
    v.checkOutAt = datetime.utcnow()
    db.commit()
    return {"message": "Visitor check-out logged"}

# --- COMPLAINTS & MAINTENANCE ---
@router.post("/complaints", response_model=dict)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can submit room complaints")
    comp = HostelComplaint(
        studentId=current_user.id,
        category=payload.category,
        priority=payload.priority,
        description=payload.description
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return {"message": "Complaint logged successfully", "complaint_id": comp.id}

@router.get("/complaints", response_model=List[dict])
def get_complaints(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name == "STUDENT":
        comps = db.query(HostelComplaint).filter(HostelComplaint.studentId == current_user.id).all()
    else:
        comps = db.query(HostelComplaint).all()
    result = []
    for c in comps:
        result.append({
            "id": c.id,
            "studentId": c.studentId,
            "category": c.category,
            "priority": c.priority,
            "description": c.description,
            "status": c.status,
            "openedAt": c.openedAt
        })
    return result

@router.patch("/complaints/{id}", response_model=dict)
def update_complaint(id: str, payload: ComplaintUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    comp = db.query(HostelComplaint).filter(HostelComplaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if payload.status:
        comp.status = payload.status
        if payload.status in ["RESOLVED", "CLOSED"]:
            comp.resolvedAt = datetime.utcnow()
    if payload.assignedTo:
        comp.assignedTo = payload.assignedTo

    db.commit()
    return {"message": "Complaint updated successfully"}

@router.post("/maintenance", response_model=dict)
def create_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    req = HostelMaintenanceRequest(
        hostelId=payload.hostelId,
        roomId=payload.roomId,
        bedId=payload.bedId,
        category=payload.category,
        description=payload.description,
        priority=payload.priority,
        assignedTo=payload.assignedTo,
        estimatedCost=Decimal(str(payload.estimatedCost))
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"message": "Maintenance task scheduled", "task_id": req.id}

@router.get("/maintenance", response_model=List[dict])
def get_maintenance_list(db: Session = Depends(get_db)):
    tasks = db.query(HostelMaintenanceRequest).all()
    result = []
    for t in tasks:
        result.append({
            "id": t.id,
            "hostelId": t.hostelId,
            "category": t.category,
            "priority": t.priority,
            "description": t.description,
            "status": t.status,
            "estimatedCost": float(t.estimatedCost),
            "actualCost": float(t.actualCost)
        })
    return result

@router.patch("/maintenance/{id}", response_model=dict)
def update_maintenance_status(id: str, payload: MaintenanceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    t = db.query(HostelMaintenanceRequest).filter(HostelMaintenanceRequest.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Maintenance task not found")

    t.status = payload.status
    if payload.status == "COMPLETED":
        t.completedAt = datetime.utcnow()
        if payload.actualCost is not None:
            t.actualCost = Decimal(str(payload.actualCost))

    db.commit()
    return {"message": "Maintenance task updated"}

# --- LEAVE REQUESTS & GATE PASSES ---
@router.post("/leave-requests", response_model=dict)
def apply_leave(payload: LeaveCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Access Denied")

    leave = HostelLeaveRequest(
        studentId=current_user.id,
        allocationId=payload.allocationId,
        leaveType=payload.leaveType,
        reason=payload.reason,
        destination=payload.destination,
        startAt=payload.startAt,
        expectedReturnAt=payload.expectedReturnAt,
        guardianContact=payload.guardianContact
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    log_audit(db, current_user.id, "APPLY_LEAVE", f"Student applied leave request ID: {leave.id}")
    return {"message": "Leave request submitted", "leave_id": leave.id}

@router.get("/leave-requests", response_model=List[dict])
def get_leave_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name == "STUDENT":
        leaves = db.query(HostelLeaveRequest).filter(HostelLeaveRequest.studentId == current_user.id).all()
    else:
        leaves = db.query(HostelLeaveRequest).all()
    result = []
    for l in leaves:
        result.append({
            "id": l.id,
            "studentId": l.studentId,
            "studentName": l.student.name if l.student else "Unknown",
            "leaveType": l.leaveType,
            "destination": l.destination,
            "startAt": l.startAt,
            "expectedReturnAt": l.expectedReturnAt,
            "status": l.status
        })
    return result

@router.patch("/leave-requests/{id}/review", response_model=dict)
def review_leave(id: str, payload: LeaveReview, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    leave = db.query(HostelLeaveRequest).filter(HostelLeaveRequest.id == id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave.status = payload.status
    db.commit()

    # Auto-generate Gate Pass if approved
    if payload.status == "APPROVED":
        token = secrets.token_hex(16)
        pass_record = HostelGatePass(
            studentId=leave.studentId,
            leaveRequestId=leave.id,
            passToken=token,
            purpose=f"Approved Leave Outing ({leave.leaveType})",
            expiryAt=leave.expectedReturnAt + timedelta(hours=12)
        )
        db.add(pass_record)
        db.commit()

    log_audit(db, current_user.id, "REVIEW_LEAVE", f"Leave request {id} status set to {payload.status}")
    return {"message": f"Leave status updated to {payload.status}"}

@router.post("/gate-passes", response_model=dict)
def create_gate_pass(payload: GatePassCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    token = secrets.token_hex(16)
    gp = HostelGatePass(
        studentId=payload.studentId,
        passToken=token,
        purpose=payload.purpose,
        expiryAt=datetime.utcnow() + timedelta(minutes=payload.expiryMinutes)
    )
    db.add(gp)
    db.commit()
    return {"message": "Gate Pass created successfully", "token": token}

@router.post("/gate-passes/verify", response_model=dict)
def verify_gate_pass(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    gp = db.query(HostelGatePass).filter(HostelGatePass.passToken == token, HostelGatePass.status == "ACTIVE").first()
    if not gp:
        raise HTTPException(status_code=404, detail="Gate pass not active or invalid token")
    if gp.expiryAt < datetime.utcnow():
        gp.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=400, detail="Gate pass has expired")

    gp.status = "USED"
    db.commit()
    return {"message": "Gate pass verified and marked as used", "student_id": gp.studentId, "purpose": gp.purpose}

# --- MESS MANAGEMENT ---
@router.post("/mess/plans", response_model=dict)
def create_mess_plan(payload: MessPlanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied")
    plan = MessPlan(
        name=payload.name,
        description=payload.description,
        costPerMonth=Decimal(str(payload.costPerMonth)),
        foodType=payload.foodType
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"message": "Mess plan created", "plan_id": plan.id}

@router.get("/mess/plans", response_model=List[dict])
def get_mess_plans(db: Session = Depends(get_db)):
    plans = db.query(MessPlan).all()
    result = []
    for p in plans:
        result.append({
            "id": p.id,
            "name": p.name,
            "costPerMonth": float(p.costPerMonth),
            "foodType": p.foodType,
            "description": p.description,
            "active": p.active
        })
    return result

@router.post("/mess/menu", response_model=dict)
def create_mess_menu(payload: MessMenuCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Permission Denied")

    menu = db.query(MessMenu).filter(MessMenu.planId == payload.planId, MessMenu.dayOfWeek == payload.dayOfWeek, MessMenu.mealType == payload.mealType).first()
    if not menu:
        menu = MessMenu(
            planId=payload.planId,
            dayOfWeek=payload.dayOfWeek,
            mealType=payload.mealType,
            menuDetails=payload.menuDetails
        )
        db.add(menu)
    else:
        menu.menuDetails = payload.menuDetails
    db.commit()
    return {"message": "Mess menu updated"}

@router.get("/mess/menu", response_model=List[dict])
def get_mess_menu(db: Session = Depends(get_db)):
    menus = db.query(MessMenu).all()
    result = []
    for m in menus:
        result.append({
            "id": m.id,
            "planId": m.planId,
            "dayOfWeek": m.dayOfWeek,
            "mealType": m.mealType,
            "menuDetails": m.menuDetails
        })
    return result

@router.post("/mess/attendance", response_model=dict)
def log_mess_attendance(payload: MessAttendanceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    sub = db.query(MessSubscription).filter(MessSubscription.studentId == current_user.id, MessSubscription.planId == payload.planId, MessSubscription.status == "ACTIVE").first()
    if not sub:
        raise HTTPException(status_code=400, detail="You do not have an active subscription to this mess plan")

    existing = db.query(MessAttendance).filter(
        MessAttendance.studentId == current_user.id,
        MessAttendance.planId == payload.planId,
        MessAttendance.mealDate == payload.mealDate.date(),
        MessAttendance.mealType == payload.mealType
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already logged for this meal today")

    att = MessAttendance(
        studentId=current_user.id,
        planId=payload.planId,
        mealDate=payload.mealDate.date(),
        mealType=payload.mealType,
        status=payload.status,
        qrCodeScanned=True
    )
    db.add(att)
    db.commit()
    return {"message": "Mess attendance recorded"}

# --- FINES ---
@router.get("/fines", response_model=List[dict])
def get_fines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name == "STUDENT":
        fines = db.query(HostelFine).filter(HostelFine.studentId == current_user.id).all()
    else:
        fines = db.query(HostelFine).all()
    result = []
    for f in fines:
        result.append({
            "id": f.id,
            "studentId": f.studentId,
            "studentName": f.student.name if f.student else "Unknown",
            "fineType": f.fineType,
            "amount": float(f.amount),
            "reason": f.reason,
            "status": f.status,
            "assessedAt": f.assessedAt
        })
    return result

@router.post("/fines/{id}/waive", response_model=dict)
def waive_fine(id: str, reason: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER"]:
        raise HTTPException(status_code=403, detail="Permission Denied to waive fines")
    fine = db.query(HostelFine).filter(HostelFine.id == id, HostelFine.status == "PENDING").first()
    if not fine:
        raise HTTPException(status_code=404, detail="Pending fine not found")

    fine.status = "WAIVED"
    fine.waivedAt = datetime.utcnow()
    fine.waivedBy = current_user.id
    fine.waiverReason = reason
    db.commit()

    log_audit(db, current_user.id, "WAIVE_FINE", f"Fine {id} waived. Reason: {reason}")
    return {"message": "Fine waived successfully"}

# --- ANALYTICS ---
@router.get("/analytics", response_model=dict)
def get_hostel_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if current_user.role.name not in ["MASTER_ADMIN", "HOSTEL_MANAGER", "WARDEN"]:
        raise HTTPException(status_code=403, detail="Access Denied")

    total_hostels = db.query(Hostel).count()
    total_capacity_sum = sum([r.capacity for r in db.query(HostelRoom).all()])

    occupied_beds = db.query(HostelBed).filter(HostelBed.status == "ALLOCATED").count()
    available_beds = db.query(HostelBed).filter(HostelBed.status == "AVAILABLE").count()

    pending_apps = db.query(HostelApplication).filter(HostelApplication.status == "SUBMITTED").count()
    active_complaints = db.query(HostelComplaint).filter(HostelComplaint.status == "OPEN").count()

    return {
        "totalHostels": total_hostels,
        "totalCapacity": total_capacity_sum,
        "occupiedBeds": occupied_beds,
        "availableBeds": available_beds,
        "occupancyPercentage": round((occupied_beds / total_capacity_sum * 100), 2) if total_capacity_sum > 0 else 0.0,
        "pendingApplications": pending_apps,
        "activeComplaints": active_complaints
    }
