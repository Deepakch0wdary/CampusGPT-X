# scripts/seed_transport.py
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
    Base, User, Role, AcademicYear, TransportVehicle, TransportDriverProfile,
    TransportRoute, TransportStop, TransportRouteStop, TransportVehicleAssignment,
    TransportApplication, TransportSubscription, TransportSeat, TransportSeatAllocation,
    TransportPass, TransportTrip, TransportBoarding, TransportVehicleLocation,
    TransportMaintenance, TransportFuelLog, TransportIncident
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
        print("Database connected. Starting transport seeding transaction...")

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

        teacher_role = db.query(Role).filter_by(name="TEACHER").first()
        if not teacher_role:
            teacher_role = Role(id=str(uuid.uuid4()), name="TEACHER", description="Teacher Role")
            db.add(teacher_role)
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

        # 3. Create Users
        admin_user = db.query(User).filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@campusgpt.local",
                username="admin",
                name="Admin User",
                roleId=admin_role.id,
                passwordHash="$2b$12$Z0bC.W7.Gedh8L3vjF9YkuxE49zXy3X6/g239xQ/eYc.rV2Bv7c3C" # password
            )
            db.add(admin_user)
            db.flush()

        student_user = db.query(User).filter_by(username="student").first()
        if not student_user:
            student_user = User(
                id="student-transport-uid",
                email="student@campusgpt.local",
                username="student",
                name="Transport Student",
                roleId=student_role.id,
                passwordHash="$2b$12$Z0bC.W7.Gedh8L3vjF9YkuxE49zXy3X6/g239xQ/eYc.rV2Bv7c3C"
            )
            db.add(student_user)
            db.flush()

        driver_user = db.query(User).filter_by(username="driver").first()
        if not driver_user:
            driver_user = User(
                id="driver-transport-uid",
                email="driver@campusgpt.local",
                username="driver",
                name="Transport Driver User",
                roleId=teacher_role.id,
                passwordHash="$2b$12$Z0bC.W7.Gedh8L3vjF9YkuxE49zXy3X6/g239xQ/eYc.rV2Bv7c3C"
            )
            db.add(driver_user)
            db.flush()

        # 4. Driver Profile
        driver_profile = db.query(TransportDriverProfile).filter_by(userId=driver_user.id).first()
        if not driver_profile:
            driver_profile = TransportDriverProfile(
                id="driver-profile-uid",
                userId=driver_user.id,
                employeeCode="DRV-001",
                licenseNumberMasked="DL-552X-XXXX",
                licenseType="HEAVY_MOTOR_VEHICLE",
                licenseExpiry=datetime.utcnow() + timedelta(days=365),
                emergencyContact="9988776655",
                joiningDate=datetime.utcnow() - timedelta(days=200),
                status="ACTIVE"
            )
            db.add(driver_profile)
            db.flush()

        # 5. Create Vehicle
        vehicle = db.query(TransportVehicle).filter_by(vehicleCode="BUS-01").first()
        if not vehicle:
            vehicle = TransportVehicle(
                id="vehicle-bus-01-uid",
                registrationNumber="KA-03-MC-1024",
                vehicleCode="BUS-01",
                vehicleType="ELECTRIC_BUS",
                manufacturer="Tata Motors",
                model="Ultra EV",
                manufactureYear=2024,
                seatingCapacity=40,
                standingCapacity=15,
                fuelType="ELECTRICITY",
                chassisNumberMasked="CHAS-9988X-XXXX",
                engineNumberMasked="ENG-7766X-XXXX",
                insuranceExpiry=datetime.utcnow() + timedelta(days=120),
                fitnessExpiry=datetime.utcnow() + timedelta(days=180),
                pollutionExpiry=datetime.utcnow() + timedelta(days=90),
                permitExpiry=datetime.utcnow() + timedelta(days=240),
                gpsDeviceId="GPS-DEVICE-BUS01",
                status="ACTIVE",
                active=True
            )
            db.add(vehicle)
            db.flush()

        # 6. Create Route
        route = db.query(TransportRoute).filter_by(code="RT-01").first()
        if not route:
            route = TransportRoute(
                id="route-rt-01-uid",
                name="Metro Junction to Main Campus Loop",
                code="RT-01",
                description="Serves morning and evening commute for students boarding from Metro connector.",
                origin="Metro Junction Terminal",
                destination="Main Admin Building",
                estimatedDistanceKm=Decimal("12.5"),
                estimatedDurationMinutes=35,
                status="ACTIVE"
            )
            db.add(route)
            db.flush()

        # 7. Create Stops
        stop1 = db.query(TransportStop).filter_by(code="ST-01").first()
        if not stop1:
            stop1 = TransportStop(
                id="stop-st-01-uid",
                name="Metro Junction Terminal",
                code="ST-01",
                address="Near Metro Station Exit 2, Outer Ring Road",
                latitude=12.9279,
                longitude=77.6271,
                landmark="Metro Exit Escalator"
            )
            db.add(stop1)
            db.flush()

        stop2 = db.query(TransportStop).filter_by(code="ST-02").first()
        if not stop2:
            stop2 = TransportStop(
                id="stop-st-02-uid",
                name="University Arch Crossing",
                code="ST-02",
                address="Phase 3 Crossing, Outer Road",
                latitude=12.9104,
                longitude=77.6409,
                landmark="Arch Clock Tower"
            )
            db.add(stop2)
            db.flush()

        stop3 = db.query(TransportStop).filter_by(code="ST-03").first()
        if not stop3:
            stop3 = TransportStop(
                id="stop-st-03-uid",
                name="Main Admin Building",
                code="ST-03",
                address="Admin Circle, Campus Main Gate",
                latitude=12.9080,
                longitude=77.6450,
                landmark="Central Water Fountain"
            )
            db.add(stop3)
            db.flush()

        # 8. Create Route Stops Ordering
        rs1 = db.query(TransportRouteStop).filter_by(routeId=route.id, stopId=stop1.id).first()
        if not rs1:
            rs1 = TransportRouteStop(
                id="rs-rt01-st01-uid",
                routeId=route.id,
                stopId=stop1.id,
                stopOrder=1,
                scheduledArrivalTime="08:00 AM",
                scheduledDepartureTime="08:05 AM",
                pickupAllowed=True,
                dropAllowed=False,
                distanceFromOriginKm=Decimal("0.0")
            )
            db.add(rs1)

        rs2 = db.query(TransportRouteStop).filter_by(routeId=route.id, stopId=stop2.id).first()
        if not rs2:
            rs2 = TransportRouteStop(
                id="rs-rt01-st02-uid",
                routeId=route.id,
                stopId=stop2.id,
                stopOrder=2,
                scheduledArrivalTime="08:15 AM",
                scheduledDepartureTime="08:17 AM",
                pickupAllowed=True,
                dropAllowed=True,
                distanceFromOriginKm=Decimal("6.5")
            )
            db.add(rs2)

        rs3 = db.query(TransportRouteStop).filter_by(routeId=route.id, stopId=stop3.id).first()
        if not rs3:
            rs3 = TransportRouteStop(
                id="rs-rt01-st03-uid",
                routeId=route.id,
                stopId=stop3.id,
                stopOrder=3,
                scheduledArrivalTime="08:35 AM",
                scheduledDepartureTime="08:40 AM",
                pickupAllowed=False,
                dropAllowed=True,
                distanceFromOriginKm=Decimal("12.5")
            )
            db.add(rs3)
        db.flush()

        # 9. Create Vehicle Assignment
        assignment = db.query(TransportVehicleAssignment).filter_by(vehicleId=vehicle.id, routeId=route.id).first()
        if not assignment:
            assignment = TransportVehicleAssignment(
                id="assignment-bus01-rt01-uid",
                vehicleId=vehicle.id,
                routeId=route.id,
                driverId=driver_profile.id,
                startDate=datetime.utcnow() - timedelta(days=30),
                shift="MORNING",
                status="ACTIVE"
            )
            db.add(assignment)
            db.flush()

        # 10. Student Pass Application & Subscription
        app = db.query(TransportApplication).filter_by(applicantUserId=student_user.id).first()
        if not app:
            app = TransportApplication(
                id="app-transport-student-uid",
                applicantUserId=student_user.id,
                academicYearId="AY-2026",
                routeId=route.id,
                pickupStopId=stop1.id,
                dropStopId=stop3.id,
                reason="Commute from PG accommodation near metro station",
                status="APPROVED",
                submittedAt=datetime.utcnow() - timedelta(days=25),
                reviewedAt=datetime.utcnow() - timedelta(days=24),
                reviewedBy=admin_user.id
            )
            db.add(app)
            db.flush()

        subscription = db.query(TransportSubscription).filter_by(userId=student_user.id).first()
        if not subscription:
            subscription = TransportSubscription(
                id="subscription-student-uid",
                userId=student_user.id,
                routeId=route.id,
                pickupStopId=stop1.id,
                dropStopId=stop3.id,
                startDate=datetime.utcnow() - timedelta(days=24),
                endDate=datetime.utcnow() + timedelta(days=156),
                status="ACTIVE",
                approvedBy=admin_user.id
            )
            db.add(subscription)
            db.flush()

        # 11. Seat Allocation
        alloc = db.query(TransportSeatAllocation).filter_by(subscriptionId=subscription.id).first()
        if not alloc:
            seat = TransportSeat(
                id="seat-bus01-01-uid",
                vehicleId=vehicle.id,
                seatNumber="S-01",
                seatType="REGULAR",
                status="ALLOCATED"
            )
            db.add(seat)
            db.flush()

            alloc = TransportSeatAllocation(
                id="alloc-seat01-student-uid",
                subscriptionId=subscription.id,
                seatId=seat.id,
                allocatedBy=admin_user.id,
                startDate=subscription.startDate,
                endDate=subscription.endDate,
                status="ACTIVE"
            )
            db.add(alloc)
            db.flush()

        # 12. Transport Pass
        tpass = db.query(TransportPass).filter_by(subscriptionId=subscription.id).first()
        if not tpass:
            tpass = TransportPass(
                id="pass-student-uid",
                subscriptionId=subscription.id,
                passNumber="PASS-T-9021",
                tokenHash="demo_student_opaque_token_hash_value_xyz",
                issuedAt=datetime.utcnow() - timedelta(days=24),
                expiresAt=subscription.endDate,
                status="ACTIVE",
                userId=student_user.id
            )
            db.add(tpass)
            db.flush()

        # 13. Trip Schedule
        trip = db.query(TransportTrip).filter_by(vehicleId=vehicle.id, routeId=route.id).first()
        if not trip:
            trip = TransportTrip(
                id="trip-today-uid",
                routeId=route.id,
                vehicleId=vehicle.id,
                driverId=driver_profile.id,
                scheduledStartAt=datetime.utcnow() - timedelta(minutes=30),
                scheduledEndAt=datetime.utcnow() + timedelta(minutes=15),
                actualStartAt=datetime.utcnow() - timedelta(minutes=25),
                status="IN_PROGRESS",
                delayMinutes=5
            )
            db.add(trip)
            db.flush()

        # 14. Boarding Log
        boarding = db.query(TransportBoarding).filter_by(tripId=trip.id, userId=student_user.id).first()
        if not boarding:
            boarding = TransportBoarding(
                id="boarding-student-uid",
                tripId=trip.id,
                userId=student_user.id,
                stopId=stop1.id,
                boardingType="PICKUP",
                boardedAt=datetime.utcnow() - timedelta(minutes=20),
                verifiedBy=driver_user.id,
                status="VERIFIED"
            )
            db.add(boarding)
            db.flush()

        # 15. Vehicle Location Updates
        location = db.query(TransportVehicleLocation).filter_by(vehicleId=vehicle.id).first()
        if not location:
            location = TransportVehicleLocation(
                id="loc-update-today-uid",
                vehicleId=vehicle.id,
                tripId=trip.id,
                latitude=12.9150,
                longitude=77.6350,
                speedKph=35.5,
                heading=45.0,
                recordedAt=datetime.utcnow(),
                source="DRIVER_APP"
            )
            db.add(location)
            db.flush()

        # 16. Fuel Log
        fuel = db.query(TransportFuelLog).filter_by(vehicleId=vehicle.id).first()
        if not fuel:
            fuel = TransportFuelLog(
                id="fuel-log-1-uid",
                vehicleId=vehicle.id,
                filledAt=datetime.utcnow() - timedelta(days=1),
                quantityLitres=Decimal("60.0"),
                unitPrice=Decimal("101.5"),
                totalAmount=Decimal("6090.0"),
                odometerKm=15430,
                fuelStation="Nandi Fuel Point",
                recordedBy=admin_user.id
            )
            db.add(fuel)
            db.flush()

        # 17. Scheduled Maintenance
        maintenance = db.query(TransportMaintenance).filter_by(vehicleId=vehicle.id).first()
        if not maintenance:
            maintenance = TransportMaintenance(
                id="maintenance-log-1-uid",
                vehicleId=vehicle.id,
                maintenanceType="PREVENTIVE",
                description="Routine brake pad checks and HVAC servicing.",
                scheduledDate=datetime.utcnow() + timedelta(days=5),
                odometerKm=16000,
                estimatedCost=Decimal("3500.0"),
                vendorName="Tata Service Center HSR",
                status="SCHEDULED"
            )
            db.add(maintenance)
            db.flush()

        # 18. Incidents
        incident = db.query(TransportIncident).filter_by(vehicleId=vehicle.id).first()
        if not incident:
            incident = TransportIncident(
                id="incident-log-1-uid",
                tripId=trip.id,
                vehicleId=vehicle.id,
                type="BREAKDOWN",
                severity="MEDIUM",
                description="Air conditioning unit stopped cooling during loop run.",
                locationText="Arch Road Crossing",
                latitude=12.9104,
                longitude=77.6409,
                occurredAt=datetime.utcnow() - timedelta(minutes=15),
                reportedBy=driver_user.id,
                status="OPEN"
            )
            db.add(incident)
            db.flush()

        db.commit()
        print("[SUCCESS] Smart Transport system data seeded successfully!")

    except Exception as e:
        db.rollback()
        print("\n[TRANSACTION FAILED] Could not seed transport database.")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_seeder()
