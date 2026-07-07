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
    User, TransportVehicle, TransportDriverProfile, TransportStaffProfile,
    TransportRoute, TransportStop, TransportRouteStop, TransportVehicleAssignment,
    TransportApplication, TransportSubscription, TransportSeat, TransportSeatAllocation,
    TransportPass, TransportTrip, TransportBoarding, TransportVehicleLocation,
    TransportMaintenance, TransportFuelLog, TransportIncident, TransportDelay, TransportAudit
)

router = APIRouter()

# --- HELPERS ---
def log_audit(db: Session, user_id: str, action: str, details: str):
    audit = TransportAudit(userId=user_id, action=action, details=details)
    db.add(audit)
    db.commit()

# --- SCHEMAS ---
class VehicleCreate(BaseModel):
    registrationNumber: str
    vehicleCode: str
    vehicleType: str
    manufacturer: str
    model: str
    manufactureYear: int
    seatingCapacity: int
    standingCapacity: int
    fuelType: str
    chassisNumberMasked: str
    engineNumberMasked: str
    insuranceExpiry: datetime
    fitnessExpiry: datetime
    pollutionExpiry: datetime
    permitExpiry: datetime
    gpsDeviceId: str

class VehicleUpdate(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    seatingCapacity: Optional[int] = None
    standingCapacity: Optional[int] = None
    insuranceExpiry: Optional[datetime] = None
    fitnessExpiry: Optional[datetime] = None
    pollutionExpiry: Optional[datetime] = None
    permitExpiry: Optional[datetime] = None

class VehicleStatusUpdate(BaseModel):
    status: str

class DriverAssign(BaseModel):
    userId: str
    employeeCode: str
    licenseNumberMasked: str
    licenseType: str
    licenseExpiry: datetime
    emergencyContact: str
    joiningDate: datetime

class RouteCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    origin: str
    destination: str
    estimatedDistanceKm: Decimal
    estimatedDurationMinutes: int

class RouteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    estimatedDistanceKm: Optional[Decimal] = None
    estimatedDurationMinutes: Optional[int] = None

class StopCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    landmark: Optional[str] = None

class RouteStopAdd(BaseModel):
    stopId: str
    stopOrder: int
    scheduledArrivalTime: str
    scheduledDepartureTime: str
    pickupAllowed: bool = True
    dropAllowed: bool = True
    distanceFromOriginKm: Decimal

class ApplicationCreate(BaseModel):
    academicYearId: str
    routeId: str
    pickupStopId: str
    dropStopId: str
    reason: Optional[str] = None

class ApplicationReview(BaseModel):
    status: str # APPROVED, REJECTED, WAITLISTED

class SubscriptionCreate(BaseModel):
    userId: str
    routeId: str
    pickupStopId: str
    dropStopId: str
    startDate: datetime
    endDate: datetime

class SeatAllocationCreate(BaseModel):
    subscriptionId: str
    seatNumber: str # e.g. "S-01"
    seatType: str = "REGULAR"

class PassVerifyRequest(BaseModel):
    tokenHash: str

class TripCreate(BaseModel):
    routeId: str
    vehicleId: str
    driverId: str
    conductorId: Optional[str] = None
    scheduledStartAt: datetime
    scheduledEndAt: datetime

class TripStatusUpdate(BaseModel):
    status: str # BOARDING, IN_PROGRESS, DELAYED, COMPLETED, CANCELLED, BREAKDOWN
    delayMinutes: Optional[int] = 0

class BoardingVerifyRequest(BaseModel):
    tripId: str
    tokenHash: str # Pass Opaque Verification Token
    stopId: str
    boardingType: str # PICKUP, DROP

class LocationCreate(BaseModel):
    vehicleId: str
    tripId: Optional[str] = None
    latitude: float
    longitude: float
    speedKph: float
    heading: float
    source: str # GPS_DEVICE, DRIVER_APP, SIMULATOR, MANUAL

class MaintenanceCreate(BaseModel):
    vehicleId: str
    maintenanceType: str # PREVENTIVE, CORRECTIVE, BREAKDOWN, INSPECTION, SERVICE
    description: str
    scheduledDate: datetime
    odometerKm: int
    estimatedCost: Decimal
    vendorName: str

class MaintenanceComplete(BaseModel):
    actualCost: Decimal
    completedAt: datetime

class FuelLogCreate(BaseModel):
    vehicleId: str
    filledAt: datetime
    quantityLitres: Decimal
    unitPrice: Decimal
    totalAmount: Decimal
    odometerKm: int
    fuelStation: str

class IncidentCreate(BaseModel):
    tripId: Optional[str] = None
    vehicleId: str
    type: str # ACCIDENT, BREAKDOWN, DELAY, MEDICAL, SECURITY, BEHAVIOR, OTHER
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    locationText: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    occurredAt: datetime

class IncidentResolve(BaseModel):
    resolution: str


# --- ENDPOINTS ---

# 1. Transport Dashboard Metrics
@router.get("/dashboard", response_model=dict)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "STUDENT", "DRIVER", "TEACHER", "PARENT"]:
        raise HTTPException(status_code=403, detail="Not authorized to view transport dashboard")

    total_vehicles = db.query(TransportVehicle).count()
    active_vehicles = db.query(TransportVehicle).filter_by(status="ACTIVE").count()
    maintenance_vehicles = db.query(TransportVehicle).filter_by(status="MAINTENANCE").count()
    total_routes = db.query(TransportRoute).count()
    total_stops = db.query(TransportStop).count()
    active_subscriptions = db.query(TransportSubscription).filter_by(status="ACTIVE").count()
    allocated_seats = db.query(TransportSeatAllocation).filter_by(status="ACTIVE").count()
    active_trips = db.query(TransportTrip).filter_by(status="IN_PROGRESS").count()
    incidents_today = db.query(TransportIncident).count()

    return {
        "totalVehicles": total_vehicles,
        "activeVehicles": active_vehicles,
        "maintenanceVehicles": maintenance_vehicles,
        "totalRoutes": total_routes,
        "totalStops": total_stops,
        "activeSubscriptions": active_subscriptions,
        "allocatedSeats": allocated_seats,
        "activeTrips": active_trips,
        "incidentsToday": incidents_today
    }


# 2. Vehicle Management
@router.get("/vehicles", response_model=List[dict])
def list_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "DRIVER"]:
        raise HTTPException(status_code=403, detail="Not authorized to view vehicles")

    vehicles = db.query(TransportVehicle).all()
    return [
        {
            "id": v.id,
            "registrationNumber": v.registrationNumber,
            "vehicleCode": v.vehicleCode,
            "vehicleType": v.vehicleType,
            "manufacturer": v.manufacturer,
            "model": v.model,
            "manufactureYear": v.manufactureYear,
            "seatingCapacity": v.seatingCapacity,
            "standingCapacity": v.standingCapacity,
            "fuelType": v.fuelType,
            "chassisNumberMasked": v.chassisNumberMasked,
            "engineNumberMasked": v.engineNumberMasked,
            "insuranceExpiry": v.insuranceExpiry.isoformat() if v.insuranceExpiry else None,
            "fitnessExpiry": v.fitnessExpiry.isoformat() if v.fitnessExpiry else None,
            "pollutionExpiry": v.pollutionExpiry.isoformat() if v.pollutionExpiry else None,
            "permitExpiry": v.permitExpiry.isoformat() if v.permitExpiry else None,
            "gpsDeviceId": v.gpsDeviceId,
            "status": v.status,
            "active": v.active
        } for v in vehicles
    ]

@router.post("/vehicles", response_model=dict)
def create_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to create vehicles")

    if payload.seatingCapacity <= 0:
        raise HTTPException(status_code=400, detail="Capacity must be greater than zero")

    if db.query(TransportVehicle).filter_by(registrationNumber=payload.registrationNumber).first():
        raise HTTPException(status_code=400, detail="Registration number already exists")
    if db.query(TransportVehicle).filter_by(vehicleCode=payload.vehicleCode).first():
        raise HTTPException(status_code=400, detail="Vehicle code already exists")
    if db.query(TransportVehicle).filter_by(gpsDeviceId=payload.gpsDeviceId).first():
        raise HTTPException(status_code=400, detail="GPS device ID already registered")

    vehicle = TransportVehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    log_audit(db, current_user.id, "CREATE_VEHICLE", f"Created vehicle {vehicle.vehicleCode}")
    return {
        "message": "Vehicle created successfully",
        "id": vehicle.id,
        "vehicleCode": vehicle.vehicleCode,
        "registrationNumber": vehicle.registrationNumber
    }

@router.get("/vehicles/{id}", response_model=dict)
def get_vehicle(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "DRIVER"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    v = db.query(TransportVehicle).filter_by(id=id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {
        "id": v.id,
        "registrationNumber": v.registrationNumber,
        "vehicleCode": v.vehicleCode,
        "vehicleType": v.vehicleType,
        "manufacturer": v.manufacturer,
        "model": v.model,
        "seatingCapacity": v.seatingCapacity,
        "gpsDeviceId": v.gpsDeviceId,
        "status": v.status
    }

@router.put("/vehicles/{id}", response_model=dict)
def update_vehicle(
    id: str,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    vehicle = db.query(TransportVehicle).filter_by(id=id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, k, v)
    db.commit()
    log_audit(db, current_user.id, "UPDATE_VEHICLE", f"Updated vehicle {vehicle.vehicleCode}")
    return {"message": "Vehicle updated successfully", "id": vehicle.id}

@router.patch("/vehicles/{id}/status", response_model=dict)
def patch_vehicle_status(
    id: str,
    payload: VehicleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    vehicle = db.query(TransportVehicle).filter_by(id=id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.status = payload.status
    db.commit()
    log_audit(db, current_user.id, "PATCH_VEHICLE_STATUS", f"Updated status of {vehicle.vehicleCode} to {payload.status}")
    return {"message": "Vehicle status patched successfully", "id": vehicle.id, "status": vehicle.status}


# 3. Driver Management
@router.get("/drivers", response_model=List[dict])
def list_drivers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    drivers = db.query(TransportDriverProfile).all()
    return [
        {
            "id": d.id,
            "userId": d.userId,
            "employeeCode": d.employeeCode,
            "licenseNumberMasked": d.licenseNumberMasked,
            "licenseExpiry": d.licenseExpiry.isoformat() if d.licenseExpiry else None,
            "joiningDate": d.joiningDate.isoformat() if d.joiningDate else None,
            "status": d.status
        } for d in drivers
    ]

@router.post("/drivers/assign", response_model=dict)
def assign_driver(
    payload: DriverAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    target_user = db.query(User).filter_by(id=payload.userId).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db.query(TransportDriverProfile).filter_by(userId=payload.userId).first():
        raise HTTPException(status_code=400, detail="Driver profile already exists for this user")

    profile = TransportDriverProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    log_audit(db, current_user.id, "ASSIGN_DRIVER", f"Assigned user {target_user.username} as driver")
    return {"message": "Driver assigned successfully", "id": profile.id}


# 4. Route Management
@router.get("/routes", response_model=List[dict])
def list_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "STUDENT", "DRIVER", "TEACHER", "PARENT"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    routes = db.query(TransportRoute).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "code": r.code,
            "origin": r.origin,
            "destination": r.destination,
            "estimatedDistanceKm": float(r.estimatedDistanceKm) if r.estimatedDistanceKm else 0.0,
            "estimatedDurationMinutes": r.estimatedDurationMinutes,
            "status": r.status
        } for r in routes
    ]

@router.post("/routes", response_model=dict)
def create_route(
    payload: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if db.query(TransportRoute).filter_by(code=payload.code).first():
        raise HTTPException(status_code=400, detail="Route code already exists")

    route = TransportRoute(**payload.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)
    log_audit(db, current_user.id, "CREATE_ROUTE", f"Created route {route.code}")
    return {"message": "Route created successfully", "id": route.id, "code": route.code}

@router.get("/routes/{id}", response_model=dict)
def get_route(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "STUDENT", "DRIVER", "TEACHER", "PARENT"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    route = db.query(TransportRoute).filter_by(id=id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return {
        "id": route.id,
        "name": route.name,
        "code": route.code,
        "origin": route.origin,
        "destination": route.destination,
        "estimatedDistanceKm": float(route.estimatedDistanceKm) if route.estimatedDistanceKm else 0.0,
        "estimatedDurationMinutes": route.estimatedDurationMinutes,
        "status": route.status
    }

@router.put("/routes/{id}", response_model=dict)
def update_route(
    id: str,
    payload: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    route = db.query(TransportRoute).filter_by(id=id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(route, k, v)
    db.commit()
    log_audit(db, current_user.id, "UPDATE_ROUTE", f"Updated route {route.code}")
    return {"message": "Route updated successfully", "id": route.id}


# 5. Stop Management
@router.get("/stops", response_model=List[dict])
def list_stops(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "STUDENT", "DRIVER", "TEACHER", "PARENT"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    stops = db.query(TransportStop).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "address": s.address,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "landmark": s.landmark
        } for s in stops
    ]

@router.post("/stops", response_model=dict)
def create_stop(
    payload: StopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if db.query(TransportStop).filter_by(code=payload.code).first():
        raise HTTPException(status_code=400, detail="Stop code already exists")

    stop = TransportStop(**payload.model_dump())
    db.add(stop)
    db.commit()
    db.refresh(stop)
    log_audit(db, current_user.id, "CREATE_STOP", f"Created stop {stop.code}")
    return {"message": "Stop created successfully", "id": stop.id, "code": stop.code}


# 6. Route-Stop Ordering
@router.get("/routes/{id}/stops", response_model=List[dict])
def get_route_stops(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "STUDENT", "DRIVER", "TEACHER", "PARENT"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    route = db.query(TransportRoute).filter_by(id=id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    route_stops = db.query(TransportRouteStop).filter_by(routeId=id).order_by(TransportRouteStop.stopOrder).all()

    stops_data = []
    for rs in route_stops:
        stops_data.append({
            "id": rs.id,
            "stopId": rs.stopId,
            "stopName": rs.stop.name,
            "stopCode": rs.stop.code,
            "stopOrder": rs.stopOrder,
            "scheduledArrivalTime": rs.scheduledArrivalTime,
            "scheduledDepartureTime": rs.scheduledDepartureTime,
            "pickupAllowed": rs.pickupAllowed,
            "dropAllowed": rs.dropAllowed,
            "distanceFromOriginKm": float(rs.distanceFromOriginKm) if rs.distanceFromOriginKm else 0.0
        })
    return stops_data

@router.post("/routes/{id}/stops", response_model=dict)
def add_route_stop(
    id: str,
    payload: RouteStopAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    route = db.query(TransportRoute).filter_by(id=id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    stop = db.query(TransportStop).filter_by(id=payload.stopId).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    if db.query(TransportRouteStop).filter_by(routeId=id, stopId=payload.stopId).first():
        raise HTTPException(status_code=400, detail="Stop already added to this route")

    if db.query(TransportRouteStop).filter_by(routeId=id, stopOrder=payload.stopOrder).first():
        raise HTTPException(status_code=400, detail="Stop order already occupied on this route")

    route_stop = TransportRouteStop(routeId=id, **payload.model_dump())
    db.add(route_stop)
    db.commit()
    db.refresh(route_stop)
    log_audit(db, current_user.id, "ADD_ROUTE_STOP", f"Added stop {stop.code} to route {route.code}")
    return {"message": "Route stop added successfully", "id": route_stop.id, "stopId": route_stop.stopId}


# 7. Student/Staff Applications (IDOR Scoping checks)
@router.get("/applications", response_model=List[dict])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name in ["STUDENT", "TEACHER"]:
        apps = db.query(TransportApplication).filter_by(applicantUserId=current_user.id).all()
    elif current_user.role.name in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        apps = db.query(TransportApplication).all()
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    return [
        {
            "id": a.id,
            "applicantUserId": a.applicantUserId,
            "applicantName": a.applicant.name if a.applicant else "Unknown",
            "academicYearId": a.academicYearId,
            "routeId": a.routeId,
            "routeCode": a.route.code if a.route else "N/A",
            "pickupStopId": a.pickupStopId,
            "dropStopId": a.dropStopId,
            "reason": a.reason,
            "status": a.status,
            "submittedAt": a.submittedAt.isoformat() if a.submittedAt else None
        } for a in apps
    ]

@router.post("/applications", response_model=dict)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["STUDENT", "MASTER_ADMIN", "TEACHER"]:
         raise HTTPException(status_code=403, detail="Not authorized to submit applications")

    route = db.query(TransportRoute).filter_by(id=payload.routeId).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    pickup = db.query(TransportStop).filter_by(id=payload.pickupStopId).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="Pickup stop not found")
    drop = db.query(TransportStop).filter_by(id=payload.dropStopId).first()
    if not drop:
        raise HTTPException(status_code=404, detail="Drop stop not found")

    application = TransportApplication(
        applicantUserId=current_user.id,
        status="SUBMITTED",
        **payload.model_dump()
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    log_audit(db, current_user.id, "SUBMIT_TRANSPORT_APP", f"Submitted application for route {route.code}")
    return {"message": "Application submitted successfully", "id": application.id}

@router.get("/applications/{id}", response_model=dict)
def get_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    app = db.query(TransportApplication).filter_by(id=id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role.name in ["STUDENT", "TEACHER"] and app.applicantUserId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to other user applications")

    return {
        "id": app.id,
        "applicantUserId": app.applicantUserId,
        "academicYearId": app.academicYearId,
        "routeId": app.routeId,
        "pickupStopId": app.pickupStopId,
        "dropStopId": app.dropStopId,
        "reason": app.reason,
        "status": app.status
    }

@router.patch("/applications/{id}/review", response_model=dict)
def review_application(
    id: str,
    payload: ApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to review applications")

    app = db.query(TransportApplication).filter_by(id=id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.status in ["APPROVED", "REJECTED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Application is already processed")

    app.status = payload.status
    app.reviewedAt = datetime.utcnow()
    app.reviewedBy = current_user.id

    if payload.status == "APPROVED":
        subscription = TransportSubscription(
            userId=app.applicantUserId,
            routeId=app.routeId,
            pickupStopId=app.pickupStopId,
            dropStopId=app.dropStopId,
            startDate=datetime.utcnow(),
            endDate=datetime.utcnow() + timedelta(days=180),
            status="ACTIVE",
            approvedBy=current_user.id
        )
        db.add(subscription)

    db.commit()
    log_audit(db, current_user.id, "REVIEW_TRANSPORT_APP", f"Reviewed application {id} status to {payload.status}")
    return {"message": "Application processed", "id": app.id, "status": app.status}


# 8. Transport Subscriptions
@router.get("/subscriptions", response_model=List[dict])
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name in ["STUDENT", "TEACHER"]:
        subs = db.query(TransportSubscription).filter_by(userId=current_user.id).all()
    elif current_user.role.name in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        subs = db.query(TransportSubscription).all()
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    return [
        {
            "id": s.id,
            "userId": s.userId,
            "routeId": s.routeId,
            "routeCode": s.route.code if s.route else "N/A",
            "pickupStopId": s.pickupStopId,
            "dropStopId": s.dropStopId,
            "startDate": s.startDate.isoformat() if s.startDate else None,
            "endDate": s.endDate.isoformat() if s.endDate else None,
            "status": s.status
        } for s in subs
    ]

@router.post("/subscriptions", response_model=dict)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    active_sub = db.query(TransportSubscription).filter_by(userId=payload.userId, status="ACTIVE").first()
    if active_sub:
        raise HTTPException(status_code=400, detail="User already has an active transport subscription")

    subscription = TransportSubscription(
        status="ACTIVE",
        approvedBy=current_user.id,
        **payload.model_dump()
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    log_audit(db, current_user.id, "CREATE_SUBSCRIPTION", f"Created subscription for user {payload.userId}")
    return {"message": "Subscription created successfully", "id": subscription.id}


# 9. Seat Allocations
@router.get("/seats", response_model=List[dict])
def list_seats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "STUDENT", "DRIVER", "TEACHER", "PARENT"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    seats = db.query(TransportSeat).all()
    return [
        {
            "id": s.id,
            "vehicleId": s.vehicleId,
            "seatNumber": s.seatNumber,
            "seatType": s.seatType,
            "status": s.status
        } for s in seats
    ]

@router.post("/seat-allocations", response_model=dict)
def allocate_seat(
    payload: SeatAllocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    subscription = db.query(TransportSubscription).filter_by(id=payload.subscriptionId).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    assignment = db.query(TransportVehicleAssignment).filter_by(routeId=subscription.routeId, status="ACTIVE").first()
    if not assignment:
        raise HTTPException(status_code=400, detail="No vehicle assigned to this route yet")

    seat = db.query(TransportSeat).filter_by(vehicleId=assignment.vehicleId, seatNumber=payload.seatNumber).first()
    if not seat:
        seat = TransportSeat(
            vehicleId=assignment.vehicleId,
            seatNumber=payload.seatNumber,
            seatType=payload.seatType,
            status="AVAILABLE"
        )
        db.add(seat)
        db.commit()
        db.refresh(seat)

    if seat.status == "ALLOCATED":
        raise HTTPException(status_code=400, detail="Seat is already allocated to another passenger")

    existing_alloc = db.query(TransportSeatAllocation).filter_by(subscriptionId=payload.subscriptionId, status="ACTIVE").first()
    if existing_alloc:
        raise HTTPException(status_code=400, detail="Passenger already allocated a seat")

    allocation = TransportSeatAllocation(
        subscriptionId=payload.subscriptionId,
        seatId=seat.id,
        allocatedBy=current_user.id,
        startDate=subscription.startDate,
        endDate=subscription.endDate,
        status="ACTIVE"
    )
    seat.status = "ALLOCATED"
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    log_audit(db, current_user.id, "ALLOCATE_SEAT", f"Allocated seat {seat.seatNumber} to subscription {subscription.id}")
    return {"message": "Seat allocated successfully", "id": allocation.id}


# 10. Pass Generation & Verification
@router.get("/passes/me", response_model=List[dict])
def get_my_passes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    passes = db.query(TransportPass).filter_by(userId=current_user.id).all()
    return [
        {
            "id": p.id,
            "passNumber": p.passNumber,
            "tokenHash": p.tokenHash,
            "expiresAt": p.expiresAt.isoformat() if p.expiresAt else None,
            "status": p.status
        } for p in passes
    ]

@router.post("/passes/{subscriptionId}/issue", response_model=dict)
def issue_pass(
    subscriptionId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    subscription = db.query(TransportSubscription).filter_by(id=subscriptionId).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    token = secrets.token_hex(20)
    pass_number = f"PASS-{secrets.token_hex(4).upper()}"

    tpass = TransportPass(
        subscriptionId=subscriptionId,
        passNumber=pass_number,
        tokenHash=token,
        issuedAt=datetime.utcnow(),
        expiresAt=subscription.endDate,
        status="ACTIVE",
        userId=subscription.userId
    )
    db.add(tpass)
    db.commit()
    db.refresh(tpass)
    log_audit(db, current_user.id, "ISSUE_PASS", f"Issued pass {pass_number} for subscription {subscriptionId}")
    return {"message": "Pass issued successfully", "id": tpass.id, "tokenHash": tpass.tokenHash}

@router.post("/passes/verify", response_model=dict)
def verify_pass(
    payload: PassVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    tpass = db.query(TransportPass).filter_by(tokenHash=payload.tokenHash).first()
    if not tpass:
        raise HTTPException(status_code=404, detail="Invalid pass token")

    if tpass.status != "ACTIVE":
        return {"valid": False, "reason": f"Pass is {tpass.status}"}

    if tpass.expiresAt < datetime.utcnow():
        tpass.status = "EXPIRED"
        db.commit()
        return {"valid": False, "reason": "Pass has expired"}

    subscriber = db.query(User).filter_by(id=tpass.userId).first()
    return {
        "valid": True,
        "passNumber": tpass.passNumber,
        "userName": subscriber.name if subscriber else "Unknown User",
        "expiresAt": tpass.expiresAt.isoformat()
    }


# 11. Trip Management
@router.get("/trips", response_model=List[dict])
def list_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "STUDENT", "DRIVER", "TEACHER", "PARENT"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    trips = db.query(TransportTrip).all()
    return [
        {
            "id": t.id,
            "routeId": t.routeId,
            "routeCode": t.route.code if t.route else "N/A",
            "vehicleId": t.vehicleId,
            "driverId": t.driverId,
            "scheduledStartAt": t.scheduledStartAt.isoformat() if t.scheduledStartAt else None,
            "status": t.status,
            "delayMinutes": t.delayMinutes
        } for t in trips
    ]

@router.post("/trips", response_model=dict)
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    route = db.query(TransportRoute).filter_by(id=payload.routeId).first()
    if not route:
         raise HTTPException(status_code=404, detail="Route not found")
    vehicle = db.query(TransportVehicle).filter_by(id=payload.vehicleId).first()
    if not vehicle:
         raise HTTPException(status_code=404, detail="Vehicle not found")
    driver = db.query(TransportDriverProfile).filter_by(id=payload.driverId).first()
    if not driver:
         raise HTTPException(status_code=404, detail="Driver not found")

    trip = TransportTrip(
        status="SCHEDULED",
        **payload.model_dump()
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    log_audit(db, current_user.id, "CREATE_TRIP", f"Scheduled trip on route {route.code}")
    return {"message": "Trip created successfully", "id": trip.id}

@router.get("/trips/{id}", response_model=dict)
def get_trip(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    trip = db.query(TransportTrip).filter_by(id=id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {
        "id": trip.id,
        "routeId": trip.routeId,
        "vehicleId": trip.vehicleId,
        "status": trip.status,
        "delayMinutes": trip.delayMinutes
    }

@router.patch("/trips/{id}/status", response_model=dict)
def patch_trip_status(
    id: str,
    payload: TripStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    trip = db.query(TransportTrip).filter_by(id=id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    is_driver = False
    if current_user.role.name == "DRIVER" or current_user.role.name == "TEACHER":
        driver_profile = db.query(TransportDriverProfile).filter_by(userId=current_user.id).first()
        if driver_profile and trip.driverId == driver_profile.id:
            is_driver = True

    if not is_driver and current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to update trip status")

    trip.status = payload.status
    if payload.status == "IN_PROGRESS" and not trip.actualStartAt:
        trip.actualStartAt = datetime.utcnow()
    elif payload.status == "COMPLETED" and not trip.actualEndAt:
        trip.actualEndAt = datetime.utcnow()

    if payload.delayMinutes:
        trip.delayMinutes = payload.delayMinutes
        delay = TransportDelay(
            tripId=trip.id,
            delayMinutes=payload.delayMinutes,
            reason=f"Status update delay reported: {payload.status}"
        )
        db.add(delay)

    db.commit()
    log_audit(db, current_user.id, "PATCH_TRIP_STATUS", f"Updated trip {id} status to {payload.status}")
    return {"message": "Trip status updated", "id": trip.id, "status": trip.status}


# 12. Boarding Verification
@router.post("/boardings/verify", response_model=dict)
def record_boarding(
    payload: BoardingVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    is_driver = False
    if current_user.role.name in ["DRIVER", "TEACHER"]:
        is_driver = True
    if not is_driver and current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to verify boarding")

    trip = db.query(TransportTrip).filter_by(id=payload.tripId).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    stop = db.query(TransportStop).filter_by(id=payload.stopId).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    tpass = db.query(TransportPass).filter_by(tokenHash=payload.tokenHash).first()
    if not tpass:
        raise HTTPException(status_code=404, detail="Invalid pass token")
    if tpass.status != "ACTIVE" or tpass.expiresAt < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Pass has expired or is invalid")

    subscription = db.query(TransportSubscription).filter_by(id=tpass.subscriptionId).first()
    if not subscription or subscription.routeId != trip.routeId:
        raise HTTPException(status_code=400, detail="Pass is registered for a different route")

    dup_boarding = db.query(TransportBoarding).filter_by(tripId=payload.tripId, userId=tpass.userId).first()
    if dup_boarding:
        raise HTTPException(status_code=400, detail="Boarding already recorded for this passenger on this trip")

    boarding = TransportBoarding(
        tripId=payload.tripId,
        userId=tpass.userId,
        stopId=payload.stopId,
        boardingType=payload.boardingType,
        boardedAt=datetime.utcnow(),
        verifiedBy=current_user.id,
        status="VERIFIED"
    )
    db.add(boarding)
    db.commit()
    db.refresh(boarding)
    log_audit(db, current_user.id, "VERIFY_BOARDING", f"Recorded boarding for user {tpass.userId} on trip {payload.tripId}")
    return {"message": "Boarding verified", "id": boarding.id}

@router.get("/trips/{id}/boardings", response_model=List[dict])
def list_trip_boardings(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "DRIVER", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    boardings = db.query(TransportBoarding).filter_by(tripId=id).all()
    return [
        {
            "id": b.id,
            "userId": b.userId,
            "stopId": b.stopId,
            "boardingType": b.boardingType,
            "boardedAt": b.boardedAt.isoformat() if b.boardedAt else None,
            "status": b.status
        } for b in boardings
    ]


# 13. GPS Location tracking
@router.post("/locations", response_model=dict)
def update_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "DRIVER", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    location = TransportVehicleLocation(**payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return {"message": "Location updated", "id": location.id}

@router.get("/vehicles/{id}/location", response_model=dict)
def get_latest_location(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    loc = db.query(TransportVehicleLocation).filter_by(vehicleId=id).order_by(TransportVehicleLocation.recordedAt.desc()).first()
    if not loc:
        return {
            "vehicleId": id,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "speedKph": 0.0,
            "heading": 0.0,
            "recordedAt": datetime.utcnow().isoformat(),
            "source": "SIMULATED DEMO LOCATION (FALLBACK)"
        }
    return {
        "vehicleId": loc.vehicleId,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "speedKph": loc.speedKph,
        "heading": loc.heading,
        "recordedAt": loc.recordedAt.isoformat() if loc.recordedAt else None,
        "source": loc.source
    }

@router.get("/vehicles/{id}/location-history", response_model=List[dict])
def get_location_history(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    locs = db.query(TransportVehicleLocation).filter_by(vehicleId=id).order_by(TransportVehicleLocation.recordedAt.desc()).limit(100).all()
    return [
        {
            "id": l.id,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "speedKph": l.speedKph,
            "recordedAt": l.recordedAt.isoformat() if l.recordedAt else None
        } for l in locs
    ]


# 14. Vehicle Maintenance
@router.get("/maintenance", response_model=List[dict])
def list_maintenance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    maints = db.query(TransportMaintenance).all()
    return [
        {
            "id": m.id,
            "vehicleId": m.vehicleId,
            "maintenanceType": m.maintenanceType,
            "scheduledDate": m.scheduledDate.isoformat() if m.scheduledDate else None,
            "estimatedCost": float(m.estimatedCost) if m.estimatedCost else 0.0,
            "actualCost": float(m.actualCost) if m.actualCost else 0.0,
            "status": m.status
        } for m in maints
    ]

@router.post("/maintenance", response_model=dict)
def create_maintenance(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    record = TransportMaintenance(
        status="SCHEDULED",
        **payload.model_dump()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    log_audit(db, current_user.id, "SCHEDULE_MAINTENANCE", f"Scheduled maintenance for vehicle {payload.vehicleId}")
    return {"message": "Maintenance scheduled", "id": record.id}

@router.patch("/maintenance/{id}", response_model=dict)
def complete_maintenance(
    id: str,
    payload: MaintenanceComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    record = db.query(TransportMaintenance).filter_by(id=id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    record.actualCost = payload.actualCost
    record.completedAt = payload.completedAt
    record.status = "COMPLETED"

    vehicle = db.query(TransportVehicle).filter_by(id=record.vehicleId).first()
    if vehicle:
        vehicle.status = "ACTIVE"

    db.commit()
    log_audit(db, current_user.id, "COMPLETE_MAINTENANCE", f"Completed maintenance {id}")
    return {"message": "Maintenance completed", "id": record.id}


# 15. Fuel Logs
@router.get("/fuel-logs", response_model=List[dict])
def list_fuel_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    fuels = db.query(TransportFuelLog).all()
    return [
        {
            "id": f.id,
            "vehicleId": f.vehicleId,
            "quantityLitres": float(f.quantityLitres) if f.quantityLitres else 0.0,
            "totalAmount": float(f.totalAmount) if f.totalAmount else 0.0,
            "odometerKm": f.odometerKm,
            "fuelStation": f.fuelStation
        } for f in fuels
    ]

@router.post("/fuel-logs", response_model=dict)
def create_fuel_log(
    payload: FuelLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    fuel = TransportFuelLog(
        recordedBy=current_user.id,
        **payload.model_dump()
    )
    db.add(fuel)
    db.commit()
    db.refresh(fuel)
    log_audit(db, current_user.id, "ADD_FUEL_LOG", f"Recorded fuel log for vehicle {payload.vehicleId}")
    return {"message": "Fuel log recorded", "id": fuel.id}


# 16. Incident Management
@router.get("/incidents", response_model=List[dict])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "DRIVER", "TEACHER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    incidents = db.query(TransportIncident).all()
    return [
        {
            "id": i.id,
            "vehicleId": i.vehicleId,
            "type": i.type,
            "severity": i.severity,
            "description": i.description,
            "status": i.status
        } for i in incidents
    ]

@router.post("/incidents", response_model=dict)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER", "DRIVER", "TEACHER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    incident = TransportIncident(
        reportedBy=current_user.id,
        status="OPEN",
        **payload.model_dump()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    log_audit(db, current_user.id, "REPORT_INCIDENT", f"Incident reported on vehicle {payload.vehicleId}")
    return {"message": "Incident reported", "id": incident.id}

@router.patch("/incidents/{id}", response_model=dict)
def resolve_incident(
    id: str,
    payload: IncidentResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    incident = db.query(TransportIncident).filter_by(id=id).first()
    if not incident:
         raise HTTPException(status_code=404, detail="Incident not found")

    incident.resolution = payload.resolution
    incident.status = "RESOLVED"
    db.commit()
    log_audit(db, current_user.id, "RESOLVE_INCIDENT", f"Resolved incident {id}")
    return {"message": "Incident resolved successfully", "id": incident.id}


# 17. Analytics
@router.get("/analytics", response_model=dict)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TRANSPORT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")

    routes = db.query(TransportRoute).all()
    route_occupancy = []
    for r in routes:
        subs = db.query(TransportSubscription).filter_by(routeId=r.id, status="ACTIVE").count()
        route_occupancy.append({
            "routeCode": r.code,
            "routeName": r.name,
            "activeSubscriptions": subs
        })

    trips = db.query(TransportTrip).all()
    total_trips = len(trips)
    avg_delay = sum(t.delayMinutes for t in trips) / total_trips if total_trips > 0 else 0

    return {
        "routeOccupancy": route_occupancy,
        "averageDelayMinutes": avg_delay,
        "totalTripsRun": total_trips
    }
