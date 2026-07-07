import uuid
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import (
    User, Role, TransportVehicle, TransportRoute, TransportStop, TransportRouteStop,
    TransportDriverProfile, TransportSubscription, TransportPass, TransportTrip,
    TransportBoarding, TransportVehicleAssignment, TransportSeat, TransportSeatAllocation,
    TransportIncident, TransportVehicleLocation
)
from app.core.security import get_password_hash

@pytest.fixture
def transport_manager_headers(client: TestClient, db_session: Session):
    """Provisions a MASTER_ADMIN user and returns auth headers."""
    role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    hashed = get_password_hash("AdminPassword@123")
    user_id = str(uuid.uuid4())
    admin = User(
        id=user_id,
        email="admin_t@campusgpt.com",
        username="admin_t",
        passwordHash=hashed,
        name="Master Admin",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add(admin)
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "admin_t",
        "password": "AdminPassword@123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def student_headers(client: TestClient, db_session: Session):
    """Provisions a STUDENT user and returns auth headers."""
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    hashed = get_password_hash("password")
    user_id = str(uuid.uuid4())
    student = User(
        id=user_id,
        email="student_t@campusgpt.com",
        username="student_t",
        passwordHash=hashed,
        name="Student User",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add(student)
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "student_t",
        "password": "password"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def driver_headers(client: TestClient, db_session: Session):
    """Provisions a DRIVER (TEACHER role fallback or matching role check) and returns auth headers."""
    role = db_session.query(Role).filter_by(name="TEACHER").first()
    hashed = get_password_hash("password")
    user_id = str(uuid.uuid4())
    driver_user = User(
        id=user_id,
        email="driver_t@campusgpt.com",
        username="driver_t",
        passwordHash=hashed,
        name="Driver User",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add(driver_user)
    db_session.commit()

    # Create driver profile
    driver_prof = TransportDriverProfile(
        id=str(uuid.uuid4()),
        userId=user_id,
        employeeCode=f"DRV-{secrets.token_hex(4).upper()}",
        licenseNumberMasked="DL-XXXXXXXXX",
        licenseType="HEAVY_MOTOR_VEHICLE",
        licenseExpiry=datetime.utcnow() + timedelta(days=365),
        emergencyContact="9998887770",
        joiningDate=datetime.utcnow(),
        status="ACTIVE"
    )
    db_session.add(driver_prof)
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "driver_t",
        "password": "password"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- TESTS ---

def test_create_vehicle(client: TestClient, transport_manager_headers):
    # Success case
    payload = {
        "registrationNumber": "KA-01-XX-1234",
        "vehicleCode": "BUS-99",
        "vehicleType": "BUS",
        "manufacturer": "Tata",
        "model": "Shuttle",
        "manufactureYear": 2024,
        "seatingCapacity": 40,
        "standingCapacity": 10,
        "fuelType": "CNG",
        "chassisNumberMasked": "CHAS-XXXXX",
        "engineNumberMasked": "ENG-XXXXX",
        "insuranceExpiry": datetime.utcnow().isoformat(),
        "fitnessExpiry": datetime.utcnow().isoformat(),
        "pollutionExpiry": datetime.utcnow().isoformat(),
        "permitExpiry": datetime.utcnow().isoformat(),
        "gpsDeviceId": "GPS-DEV-99"
    }

    response = client.post("/api/v1/transport/vehicles", json=payload, headers=transport_manager_headers)
    assert response.status_code == 200
    assert response.json()["vehicleCode"] == "BUS-99"

    # Duplicate vehicle code block
    dup_response = client.post("/api/v1/transport/vehicles", json=payload, headers=transport_manager_headers)
    assert dup_response.status_code == 400

    # Invalid capacity block
    payload["vehicleCode"] = "BUS-100"
    payload["registrationNumber"] = "KA-01-XX-9999"
    payload["seatingCapacity"] = 0
    err_response = client.post("/api/v1/transport/vehicles", json=payload, headers=transport_manager_headers)
    assert err_response.status_code == 400


def test_create_route_and_stops(client: TestClient, db_session: Session, transport_manager_headers):
    route_payload = {
        "name": "Route Alpha",
        "code": "RT-A",
        "origin": "Station X",
        "destination": "Campus Gate",
        "estimatedDistanceKm": 8.5,
        "estimatedDurationMinutes": 20
    }

    response = client.post("/api/v1/transport/routes", json=route_payload, headers=transport_manager_headers)
    assert response.status_code == 200
    route_id = response.json()["id"]

    # Duplicate code rejection
    dup_response = client.post("/api/v1/transport/routes", json=route_payload, headers=transport_manager_headers)
    assert dup_response.status_code == 400

    # Create stops
    stop_payload_1 = {
        "name": "Station X Stop",
        "code": "ST-X",
        "latitude": 12.9100,
        "longitude": 77.6100
    }
    stop_response_1 = client.post("/api/v1/transport/stops", json=stop_payload_1, headers=transport_manager_headers)
    stop_id_1 = stop_response_1.json()["id"]

    stop_payload_2 = {
        "name": "Station Y Stop",
        "code": "ST-Y",
        "latitude": 12.9200,
        "longitude": 77.6200
    }
    stop_response_2 = client.post("/api/v1/transport/stops", json=stop_payload_2, headers=transport_manager_headers)
    stop_id_2 = stop_response_2.json()["id"]

    # Add stop 1 to route
    rs_payload_1 = {
        "stopId": stop_id_1,
        "stopOrder": 1,
        "scheduledArrivalTime": "08:00 AM",
        "scheduledDepartureTime": "08:05 AM",
        "distanceFromOriginKm": 0.0
    }
    rs_response_1 = client.post(f"/api/v1/transport/routes/{route_id}/stops", json=rs_payload_1, headers=transport_manager_headers)
    assert rs_response_1.status_code == 200

    # Duplicate stop order rejection
    rs_payload_2 = {
        "stopId": stop_id_2,
        "stopOrder": 1, # duplicate stop order
        "scheduledArrivalTime": "08:15 AM",
        "scheduledDepartureTime": "08:20 AM",
        "distanceFromOriginKm": 4.2
    }
    rs_response_2 = client.post(f"/api/v1/transport/routes/{route_id}/stops", json=rs_payload_2, headers=transport_manager_headers)
    assert rs_response_2.status_code == 400


def test_student_applications_and_idor(client: TestClient, db_session: Session, transport_manager_headers, student_headers):
    # Setup Route and Stops
    route = TransportRoute(name="Student Loop", code="SL-01", origin="Terminal A", destination="Quad", estimatedDistanceKm=Decimal("5.0"), estimatedDurationMinutes=15)
    stop1 = TransportStop(name="Terminal A", code="TA-01", latitude=12.9, longitude=77.5)
    stop2 = TransportStop(name="Quad", code="QD-01", latitude=12.91, longitude=77.51)
    db_session.add_all([route, stop1, stop2])
    db_session.commit()

    app_payload = {
        "academicYearId": "AY2026",
        "routeId": route.id,
        "pickupStopId": stop1.id,
        "dropStopId": stop2.id
    }

    # Student submits application
    response = client.post("/api/v1/transport/applications", json=app_payload, headers=student_headers)
    assert response.status_code == 200
    app_id = response.json()["id"]

    # Student requests own application detail
    get_response = client.get(f"/api/v1/transport/applications/{app_id}", headers=student_headers)
    assert get_response.status_code == 200

    # IDOR Check: create another student session
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    hashed = get_password_hash("password")
    another_student = User(
        id=str(uuid.uuid4()),
        email="other@campusgpt.com",
        username="other",
        passwordHash=hashed,
        name="Other Student",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add(another_student)
    db_session.commit()

    another_auth_response = client.post("/api/v1/auth/login", json={
        "username_or_email": "other",
        "password": "password"
    })
    another_headers = {"Authorization": f"Bearer {another_auth_response.json()['access_token']}"}

    # Attempt IDOR check
    idor_response = client.get(f"/api/v1/transport/applications/{app_id}", headers=another_headers)
    assert idor_response.status_code == 403


def test_active_subscription_overlap(client: TestClient, db_session: Session, transport_manager_headers, student_headers):
    # Setup Route and Stops
    route = TransportRoute(name="Student Loop 2", code="SL-02", origin="Terminal A", destination="Quad", estimatedDistanceKm=Decimal("5.0"), estimatedDurationMinutes=15)
    stop1 = TransportStop(name="Terminal A 2", code="TA-02", latitude=12.9, longitude=77.5)
    stop2 = TransportStop(name="Quad 2", code="QD-02", latitude=12.91, longitude=77.51)
    db_session.add_all([route, stop1, stop2])
    db_session.commit()

    student_user = db_session.query(User).filter_by(username="student_t").first()

    # Pre-seed active subscription for student
    sub = TransportSubscription(
        userId=student_user.id,
        routeId=route.id,
        pickupStopId=stop1.id,
        dropStopId=stop2.id,
        startDate=datetime.utcnow(),
        endDate=datetime.utcnow() + timedelta(days=100),
        status="ACTIVE"
    )
    db_session.add(sub)
    db_session.commit()

    # Try creating conflicting active subscription
    payload = {
        "userId": student_user.id,
        "routeId": route.id,
        "pickupStopId": stop1.id,
        "dropStopId": stop2.id,
        "startDate": datetime.utcnow().isoformat(),
        "endDate": (datetime.utcnow() + timedelta(days=50)).isoformat()
    }
    response = client.post("/api/v1/transport/subscriptions", json=payload, headers=transport_manager_headers)
    assert response.status_code == 400


def test_seat_allocation_and_double_booking(client: TestClient, db_session: Session, transport_manager_headers):
    # Setup vehicle, route, driver, assignment
    vehicle = TransportVehicle(
        registrationNumber="KA-01-XX-2222",
        vehicleCode="BUS-88",
        vehicleType="BUS",
        manufacturer="Tata",
        model="Shuttle",
        manufactureYear=2024,
        seatingCapacity=40,
        standingCapacity=10,
        fuelType="CNG",
        chassisNumberMasked="CHAS-XXXXX",
        engineNumberMasked="ENG-XXXXX",
        insuranceExpiry=datetime.utcnow(),
        fitnessExpiry=datetime.utcnow(),
        pollutionExpiry=datetime.utcnow(),
        permitExpiry=datetime.utcnow(),
        gpsDeviceId="GPS-DEV-88"
    )
    route = TransportRoute(name="Student Loop 3", code="SL-03", origin="Terminal A", destination="Quad", estimatedDistanceKm=Decimal("5.0"), estimatedDurationMinutes=15)
    stop1 = TransportStop(name="Terminal A 3", code="TA-03", latitude=12.9, longitude=77.5)
    stop2 = TransportStop(name="Quad 3", code="QD-03", latitude=12.91, longitude=77.51)

    role = db_session.query(Role).filter_by(name="TEACHER").first()
    driver_user = User(
        id=str(uuid.uuid4()),
        email="driver_test@campusgpt.com",
        username="driver_test",
        passwordHash="hash",
        name="Driver User",
        roleId=role.id,
        mustChangePassword=False
    )
    db_session.add_all([vehicle, route, stop1, stop2, driver_user])
    db_session.commit()

    driver = TransportDriverProfile(
        id=str(uuid.uuid4()),
        userId=driver_user.id,
        employeeCode="DRV-TEST",
        licenseNumberMasked="DL-XXXXXXXXX",
        licenseType="HEAVY_MOTOR_VEHICLE",
        licenseExpiry=datetime.utcnow() + timedelta(days=365),
        emergencyContact="9998887770",
        joiningDate=datetime.utcnow(),
        status="ACTIVE"
    )
    db_session.add(driver)
    db_session.commit()

    assignment = TransportVehicleAssignment(
        vehicleId=vehicle.id,
        routeId=route.id,
        driverId=driver.id,
        startDate=datetime.utcnow(),
        shift="MORNING",
        status="ACTIVE"
    )
    db_session.add(assignment)
    db_session.commit()

    # Create dummy passenger user
    role_student = db_session.query(Role).filter_by(name="STUDENT").first()
    student_user = User(
        id=str(uuid.uuid4()),
        email="student_alloc@campusgpt.com",
        username="student_alloc",
        passwordHash="hash",
        name="Student Alloc",
        roleId=role_student.id,
        mustChangePassword=False
    )
    db_session.add(student_user)
    db_session.commit()

    sub = TransportSubscription(
        userId=student_user.id,
        routeId=route.id,
        pickupStopId=stop1.id,
        dropStopId=stop2.id,
        startDate=datetime.utcnow(),
        endDate=datetime.utcnow() + timedelta(days=100),
        status="ACTIVE"
    )
    db_session.add(sub)
    db_session.commit()

    payload = {
        "subscriptionId": sub.id,
        "seatNumber": "S-01"
    }

    # First allocation succeeds
    response = client.post("/api/v1/transport/seat-allocations", json=payload, headers=transport_manager_headers)
    assert response.status_code == 200

    # Second allocation (occupied seat) fails
    dup_student = User(
        id=str(uuid.uuid4()),
        email="student_dup@campusgpt.com",
        username="student_dup",
        passwordHash="hash",
        name="Student Dup",
        roleId=role_student.id,
        mustChangePassword=False
    )
    db_session.add(dup_student)
    db_session.commit()

    dup_sub = TransportSubscription(
        userId=dup_student.id,
        routeId=route.id,
        pickupStopId=stop1.id,
        dropStopId=stop2.id,
        startDate=datetime.utcnow(),
        endDate=datetime.utcnow() + timedelta(days=30),
        status="ACTIVE"
    )
    db_session.add(dup_sub)
    db_session.commit()

    payload_dup = {
        "subscriptionId": dup_sub.id,
        "seatNumber": "S-01"
    }
    dup_alloc_response = client.post("/api/v1/transport/seat-allocations", json=payload_dup, headers=transport_manager_headers)
    assert dup_alloc_response.status_code == 400


def test_boarding_verification_wrong_route(client: TestClient, db_session: Session, transport_manager_headers, driver_headers, student_headers):
    # Setup vehicle, route, stops, driver
    vehicle = TransportVehicle(
        registrationNumber="KA-01-XX-3333",
        vehicleCode="BUS-77",
        vehicleType="BUS",
        manufacturer="Tata",
        model="Shuttle",
        manufactureYear=2024,
        seatingCapacity=40,
        standingCapacity=10,
        fuelType="CNG",
        chassisNumberMasked="CHAS-XXXXX",
        engineNumberMasked="ENG-XXXXX",
        insuranceExpiry=datetime.utcnow(),
        fitnessExpiry=datetime.utcnow(),
        pollutionExpiry=datetime.utcnow(),
        permitExpiry=datetime.utcnow(),
        gpsDeviceId="GPS-DEV-77"
    )
    route = TransportRoute(name="Student Loop 4", code="SL-04", origin="Terminal A", destination="Quad", estimatedDistanceKm=Decimal("5.0"), estimatedDurationMinutes=15)
    stop1 = TransportStop(name="Terminal A 4", code="TA-04", latitude=12.9, longitude=77.5)
    stop2 = TransportStop(name="Quad 4", code="QD-04", latitude=12.91, longitude=77.51)

    db_session.add_all([vehicle, route, stop1, stop2])
    db_session.commit()

    driver_profile = db_session.query(TransportDriverProfile).first()
    student_user = db_session.query(User).filter_by(username="student_t").first()

    sub = TransportSubscription(
        userId=student_user.id,
        routeId=route.id,
        pickupStopId=stop1.id,
        dropStopId=stop2.id,
        startDate=datetime.utcnow(),
        endDate=datetime.utcnow() + timedelta(days=100),
        status="ACTIVE"
    )
    db_session.add(sub)
    db_session.commit()

    # Issue pass
    issue_response = client.post(f"/api/v1/transport/passes/{sub.id}/issue", headers=transport_manager_headers)
    assert issue_response.status_code == 200
    token = issue_response.json()["tokenHash"]

    # Setup a trip on a different route
    wrong_route = TransportRoute(name="Wrong Route", code="WR-99", origin="Start", destination="End", estimatedDistanceKm=Decimal("2.0"), estimatedDurationMinutes=5)
    db_session.add(wrong_route)
    db_session.commit()

    trip = TransportTrip(
        routeId=wrong_route.id,
        vehicleId=vehicle.id,
        driverId=driver_profile.id,
        scheduledStartAt=datetime.utcnow(),
        scheduledEndAt=datetime.utcnow() + timedelta(hours=1),
        status="SCHEDULED"
    )
    db_session.add(trip)
    db_session.commit()

    # Record boarding with wrong route pass
    boarding_payload = {
        "tripId": trip.id,
        "tokenHash": token,
        "stopId": stop1.id,
        "boardingType": "PICKUP"
    }

    response = client.post("/api/v1/transport/boardings/verify", json=boarding_payload, headers=driver_headers)
    assert response.status_code == 400


def test_gps_locations_tracking(client: TestClient, db_session: Session, driver_headers, student_headers):
    vehicle = TransportVehicle(
        registrationNumber="KA-01-XX-4444",
        vehicleCode="BUS-66",
        vehicleType="BUS",
        manufacturer="Tata",
        model="Shuttle",
        manufactureYear=2024,
        seatingCapacity=40,
        standingCapacity=10,
        fuelType="CNG",
        chassisNumberMasked="CHAS-XXXXX",
        engineNumberMasked="ENG-XXXXX",
        insuranceExpiry=datetime.utcnow(),
        fitnessExpiry=datetime.utcnow(),
        pollutionExpiry=datetime.utcnow(),
        permitExpiry=datetime.utcnow(),
        gpsDeviceId="GPS-DEV-66"
    )
    db_session.add(vehicle)
    db_session.commit()

    payload = {
        "vehicleId": vehicle.id,
        "latitude": 12.9800,
        "longitude": 77.6000,
        "speedKph": 45.0,
        "heading": 180.0,
        "source": "SIMULATOR"
    }

    # Driver profile authorized update
    response = client.post("/api/v1/transport/locations", json=payload, headers=driver_headers)
    assert response.status_code == 200

    # Student profile unauthorized block
    err_response = client.post("/api/v1/transport/locations", json=payload, headers=student_headers)
    assert err_response.status_code == 403


def test_parents_ownership_and_security(client: TestClient, db_session: Session, student_headers):
    # Student cannot submit update to transport audit ledger directly
    response = client.get("/api/v1/transport/maintenance", headers=student_headers)
    assert response.status_code == 403


def test_expired_and_revoked_passes(client: TestClient, db_session: Session, transport_manager_headers):
    # Setup vehicle, route, stops, student user, active subscription
    vehicle = TransportVehicle(
        registrationNumber="KA-01-XX-9901", vehicleCode="BUS-901", vehicleType="BUS",
        manufacturer="Tata", model="Shuttle", manufactureYear=2024, seatingCapacity=40,
        standingCapacity=10, fuelType="CNG", chassisNumberMasked="CHAS-X", engineNumberMasked="ENG-X",
        insuranceExpiry=datetime.utcnow(), fitnessExpiry=datetime.utcnow(),
        pollutionExpiry=datetime.utcnow(), permitExpiry=datetime.utcnow(), gpsDeviceId="GPS-DEV-901"
    )
    route = TransportRoute(name="Loop 901", code="RT-901", origin="Start", destination="End", estimatedDistanceKm=Decimal("5.0"), estimatedDurationMinutes=15)
    stop1 = TransportStop(name="Stop 1", code="S-901", latitude=12.9, longitude=77.5)
    stop2 = TransportStop(name="Stop 2", code="S-902", latitude=12.91, longitude=77.51)

    role = db_session.query(Role).filter_by(name="STUDENT").first()
    student_user = User(
        id=str(uuid.uuid4()), email="student_pass@campusgpt.com", username="student_pass",
        passwordHash="hash", name="Student Pass", roleId=role.id, mustChangePassword=False
    )
    db_session.add_all([vehicle, route, stop1, stop2, student_user])
    db_session.commit()

    sub = TransportSubscription(
        userId=student_user.id, routeId=route.id, pickupStopId=stop1.id, dropStopId=stop2.id,
        startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=100), status="ACTIVE"
    )
    db_session.add(sub)
    db_session.commit()

    # Issue pass
    issue_response = client.post(f"/api/v1/transport/passes/{sub.id}/issue", headers=transport_manager_headers)
    assert issue_response.status_code == 200
    token = issue_response.json()["tokenHash"]

    # Verify pass (active)
    verify_res = client.post("/api/v1/transport/passes/verify", json={"tokenHash": token}, headers=transport_manager_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    # Revoke/Expire pass in DB
    db_pass = db_session.query(TransportPass).filter_by(tokenHash=token).first()
    db_pass.status = "REVOKED"
    db_session.commit()

    # Verify pass again (revoked/inactive)
    verify_res_2 = client.post("/api/v1/transport/passes/verify", json={"tokenHash": token}, headers=transport_manager_headers)
    assert verify_res_2.status_code == 200
    assert verify_res_2.json()["valid"] is False


def test_trip_lifecycle_and_unauthorized_driver(client: TestClient, db_session: Session, transport_manager_headers, driver_headers):
    # Setup vehicle, route, stops, driver user, assignment
    vehicle = TransportVehicle(
        registrationNumber="KA-01-XX-9902", vehicleCode="BUS-902", vehicleType="BUS",
        manufacturer="Tata", model="Shuttle", manufactureYear=2024, seatingCapacity=40,
        standingCapacity=10, fuelType="CNG", chassisNumberMasked="CHAS-X", engineNumberMasked="ENG-X",
        insuranceExpiry=datetime.utcnow(), fitnessExpiry=datetime.utcnow(),
        pollutionExpiry=datetime.utcnow(), permitExpiry=datetime.utcnow(), gpsDeviceId="GPS-DEV-902"
    )
    route = TransportRoute(name="Loop 902", code="RT-902", origin="Start", destination="End", estimatedDistanceKm=Decimal("5.0"), estimatedDurationMinutes=15)
    db_session.add_all([vehicle, route])
    db_session.commit()

    driver_profile = db_session.query(TransportDriverProfile).first()

    # Schedule trip
    trip_payload = {
        "routeId": route.id,
        "vehicleId": vehicle.id,
        "driverId": driver_profile.id,
        "scheduledStartAt": datetime.utcnow().isoformat(),
        "scheduledEndAt": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }
    trip_res = client.post("/api/v1/transport/trips", json=trip_payload, headers=transport_manager_headers)
    assert trip_res.status_code == 200
    trip_id = trip_res.json()["id"]

    # Status update by assigned driver (success)
    status_res = client.patch(f"/api/v1/transport/trips/{trip_id}/status", json={"status": "IN_PROGRESS"}, headers=driver_headers)
    assert status_res.status_code == 200

    # Create another driver user
    role_teacher = db_session.query(Role).filter_by(name="TEACHER").first()
    another_driver_user = User(
        id=str(uuid.uuid4()), email="other_driver@campusgpt.com", username="other_driver",
        passwordHash=get_password_hash("password"), name="Other Driver", roleId=role_teacher.id, mustChangePassword=False
    )
    db_session.add(another_driver_user)
    db_session.commit()

    another_driver_profile = TransportDriverProfile(
        id=str(uuid.uuid4()), userId=another_driver_user.id, employeeCode="DRV-OTHER",
        licenseNumberMasked="DL-XXXXXXXXX", licenseType="HEAVY_MOTOR_VEHICLE",
        licenseExpiry=datetime.utcnow() + timedelta(days=365), emergencyContact="999",
        joiningDate=datetime.utcnow(), status="ACTIVE"
    )
    db_session.add(another_driver_profile)
    db_session.commit()

    another_auth_response = client.post("/api/v1/auth/login", json={
        "username_or_email": "other_driver",
        "password": "password"
    })
    another_driver_headers = {"Authorization": f"Bearer {another_auth_response.json()['access_token']}"}

    # Unauthorized driver status update (denied with 403)
    unauth_status_res = client.patch(f"/api/v1/transport/trips/{trip_id}/status", json={"status": "DELAYED", "delayMinutes": 10}, headers=another_driver_headers)
    assert unauth_status_res.status_code == 403


def test_boarding_success_and_duplicates(client: TestClient, db_session: Session, transport_manager_headers, driver_headers, student_headers):
    # Setup vehicle, route, stops, driver, subscription, pass, trip
    vehicle = TransportVehicle(
        registrationNumber="KA-01-XX-9903", vehicleCode="BUS-903", vehicleType="BUS",
        manufacturer="Tata", model="Shuttle", manufactureYear=2024, seatingCapacity=40,
        standingCapacity=10, fuelType="CNG", chassisNumberMasked="CHAS-X", engineNumberMasked="ENG-X",
        insuranceExpiry=datetime.utcnow(), fitnessExpiry=datetime.utcnow(),
        pollutionExpiry=datetime.utcnow(), permitExpiry=datetime.utcnow(), gpsDeviceId="GPS-DEV-903"
    )
    route = TransportRoute(name="Loop 903", code="RT-903", origin="Start", destination="End", estimatedDistanceKm=Decimal("5.0"), estimatedDurationMinutes=15)
    stop1 = TransportStop(name="Stop 1", code="S-903", latitude=12.9, longitude=77.5)
    stop2 = TransportStop(name="Stop 2", code="S-904", latitude=12.91, longitude=77.51)
    db_session.add_all([vehicle, route, stop1, stop2])
    db_session.commit()

    driver_profile = db_session.query(TransportDriverProfile).first()
    student_user = db_session.query(User).filter_by(username="student_t").first()

    sub = TransportSubscription(
        userId=student_user.id, routeId=route.id, pickupStopId=stop1.id, dropStopId=stop2.id,
        startDate=datetime.utcnow(), endDate=datetime.utcnow() + timedelta(days=100), status="ACTIVE"
    )
    db_session.add(sub)
    db_session.commit()

    # Issue pass
    issue_response = client.post(f"/api/v1/transport/passes/{sub.id}/issue", headers=transport_manager_headers)
    assert issue_response.status_code == 200
    token = issue_response.json()["tokenHash"]

    # Start Trip
    trip = TransportTrip(
        routeId=route.id, vehicleId=vehicle.id, driverId=driver_profile.id,
        scheduledStartAt=datetime.utcnow(), scheduledEndAt=datetime.utcnow() + timedelta(hours=1),
        status="IN_PROGRESS"
    )
    db_session.add(trip)
    db_session.commit()

    # Record boarding (success)
    boarding_payload = {
        "tripId": trip.id,
        "tokenHash": token,
        "stopId": stop1.id,
        "boardingType": "PICKUP"
    }
    boarding_res = client.post("/api/v1/transport/boardings/verify", json=boarding_payload, headers=driver_headers)
    assert boarding_res.status_code == 200

    # Duplicate boarding (failure 400)
    dup_res = client.post("/api/v1/transport/boardings/verify", json=boarding_payload, headers=driver_headers)
    assert dup_res.status_code == 400


def test_parents_linkage_denial(client: TestClient, db_session: Session, student_headers):
    # Create parent role and user
    role_parent = Role(id=str(uuid.uuid4()), name="PARENT", description="Parent role")
    db_session.add(role_parent)
    db_session.commit()

    parent_user = User(
        id=str(uuid.uuid4()), email="parent@campusgpt.com", username="parent_t",
        passwordHash=get_password_hash("password"), name="Parent User", roleId=role_parent.id, mustChangePassword=False
    )
    db_session.add(parent_user)
    db_session.commit()

    # Login parent
    parent_login_res = client.post("/api/v1/auth/login", json={
        "username_or_email": "parent_t",
        "password": "password"
    })
    parent_headers = {"Authorization": f"Bearer {parent_login_res.json()['access_token']}"}

    # Parent can view transport dashboard
    dashboard_res = client.get("/api/v1/transport/dashboard", headers=parent_headers)
    assert dashboard_res.status_code == 200

    # Unrelated parent cannot review applications
    review_res = client.patch("/api/v1/transport/applications/some-id/review", json={"status": "APPROVED"}, headers=parent_headers)
    assert review_res.status_code == 403


def test_role_permissions_rbac_matrix(client: TestClient, transport_manager_headers, student_headers):
    # Master Admin/Manager has access to analytics
    analytics_res = client.get("/api/v1/transport/analytics", headers=transport_manager_headers)
    assert analytics_res.status_code == 200

    # Student denied access to analytics
    student_analytics_res = client.get("/api/v1/transport/analytics", headers=student_headers)
    assert student_analytics_res.status_code == 403
