import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.models import (
    User, Role, Notification, NotificationPreference,
    Announcement, NotificationTemplate, BroadcastCampaign,
    EmergencyAlert, CommunicationAudit, NotificationDelivery, NotificationReadReceipt
)
from app.core.security import get_password_hash
from app.services.notification_service import NotificationService

@pytest.fixture
def admin_role(db_session: Session) -> Role:
    role = db_session.query(Role).filter_by(name="MASTER_ADMIN").first()
    if not role:
        role = Role(id=str(uuid.uuid4()), name="MASTER_ADMIN", description="Admin role")
        db_session.add(role)
        db_session.commit()
    return role

@pytest.fixture
def student_role(db_session: Session) -> Role:
    role = db_session.query(Role).filter_by(name="STUDENT").first()
    if not role:
        role = Role(id=str(uuid.uuid4()), name="STUDENT", description="Student role")
        db_session.add(role)
        db_session.commit()
    return role

@pytest.fixture
def admin_user(db_session: Session, admin_role: Role) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="admin_notif@campusgpt.com",
        username="admin_notif",
        passwordHash=get_password_hash("password"),
        name="Admin Notif",
        roleId=admin_role.id,
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def student_user_x(db_session: Session, student_role: Role) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="student_x@campusgpt.com",
        username="student_x",
        passwordHash=get_password_hash("password"),
        name="Student X",
        roleId=student_role.id,
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def student_user_y(db_session: Session, student_role: Role) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="student_y@campusgpt.com",
        username="student_y",
        passwordHash=get_password_hash("password"),
        name="Student Y",
        roleId=student_role.id,
        mustChangePassword=False
    )
    db_session.add(user)
    db_session.commit()
    return user

# Helper headers
def get_auth_headers(client: TestClient, username: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": "password"})
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_notification_creation_and_list(client: TestClient, db_session: Session, student_user_x: User):
    headers = get_auth_headers(client, "student_x")

    # Send a notification to student X using backend service
    notif = NotificationService.create_notification(
        db=db_session,
        recipient_id=student_user_x.id,
        title="Test Title",
        body="Test Body",
        type="INFO",
        priority="MEDIUM",
        channel="IN_APP",
        category="ACADEMIC"
    )
    db_session.commit()

    # Query endpoint
    res = client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == 200
    notifs = res.json()["data"]["notifications"]
    assert len(notifs) >= 1
    assert notifs[0]["id"] == notif.id
    assert notifs[0]["title"] == "Test Title"

def test_unread_count(client: TestClient, db_session: Session, student_user_x: User):
    headers = get_auth_headers(client, "student_x")

    # Clear existing
    db_session.query(Notification).filter_by(recipientId=student_user_x.id).delete()
    db_session.commit()

    # Add 2 unread notifications
    NotificationService.create_notification(db_session, student_user_x.id, "T1", "B1")
    NotificationService.create_notification(db_session, student_user_x.id, "T2", "B2")
    db_session.commit()

    res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["unreadCount"] == 2

def test_mark_read_and_idor_protection(client: TestClient, db_session: Session, student_user_x: User, student_user_y: User):
    headers_x = get_auth_headers(client, "student_x")
    headers_y = get_auth_headers(client, "student_y")

    # Create notification for User X
    notif = NotificationService.create_notification(db_session, student_user_x.id, "User X Alert", "Details")
    db_session.commit()

    # User Y tries to mark User X's notification as read (should fail with 403)
    res_y = client.patch(f"/api/v1/notifications/{notif.id}/read", headers=headers_y)
    assert res_y.status_code == 403

    # User X marks own notification as read
    res_x = client.patch(f"/api/v1/notifications/{notif.id}/read", headers=headers_x)
    assert res_x.status_code == 200

    # Assert readReceipt was created
    receipt = db_session.query(NotificationReadReceipt).filter_by(notificationId=notif.id, userId=student_user_x.id).first()
    assert receipt is not None

def test_notification_preferences_crud(client: TestClient, student_user_x: User):
    headers = get_auth_headers(client, "student_x")

    # Get defaults
    res = client.get("/api/v1/notifications/preferences", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["emailEnabled"] is True

    # Update toggles
    payload = {
        "emailEnabled": False,
        "smsEnabled": False,
        "quietHoursEnabled": True,
        "quietHoursStart": "23:00",
        "quietHoursEnd": "06:00",
        "timezone": "America/New_York"
      }
    res_update = client.patch("/api/v1/notifications/preferences", json=payload, headers=headers)
    assert res_update.status_code == 200

    # Verify updates
    res_verify = client.get("/api/v1/notifications/preferences", headers=headers)
    assert res_verify.json()["data"]["emailEnabled"] is False
    assert res_verify.json()["data"]["smsEnabled"] is False
    assert res_verify.json()["data"]["quietHoursEnabled"] is True
    assert res_verify.json()["data"]["quietHoursStart"] == "23:00"

def test_quiet_hours_suppression(client: TestClient, db_session: Session, student_user_x: User):
    # Enable quiet hours right now
    pref = db_session.query(NotificationPreference).filter_by(userId=student_user_x.id).first()
    if not pref:
        pref = NotificationPreference(userId=student_user_x.id)
        db_session.add(pref)

    pref.quietHoursEnabled = True
    pref.quietHoursStart = "00:00"
    pref.quietHoursEnd = "23:59" # Cover whole day
    db_session.commit()

    # Attempt to send standard email notification (should result in FAILED status)
    notif = NotificationService.create_notification(
        db=db_session,
        recipient_id=student_user_x.id,
        title="Quiet Night Notice",
        body="Should not make sound",
        type="INFO",
        priority="LOW",
        channel="EMAIL",
        category="ACADEMIC"
    )
    db_session.commit()

    assert notif.status == "FAILED"
    delivery = db_session.query(NotificationDelivery).filter_by(notificationId=notif.id).first()
    assert delivery.status == "FAILED"
    assert delivery.failureReason == "QUIET_HOURS_SUPPRESSED"

def test_emergency_preference_override(client: TestClient, db_session: Session, student_user_x: User):
    # Disable all notifications for student X
    pref = db_session.query(NotificationPreference).filter_by(userId=student_user_x.id).first()
    if not pref:
        pref = NotificationPreference(userId=student_user_x.id)
        db_session.add(pref)

    pref.inAppEnabled = False
    pref.emailEnabled = False
    pref.academicEnabled = False
    pref.emergencyEnabled = False # Try to disable emergency
    db_session.commit()

    # Send an emergency alert (must bypass preference settings)
    notif = NotificationService.create_notification(
        db=db_session,
        recipient_id=student_user_x.id,
        title="FIRE EVACUATION",
        body="Leave the building immediately.",
        type="EMERGENCY",
        priority="CRITICAL",
        channel="IN_APP",
        category="EMERGENCY"
    )
    db_session.commit()

    # Emergency is always allowed
    assert notif.status == "DELIVERED"
    delivery = db_session.query(NotificationDelivery).filter_by(notificationId=notif.id).first()
    assert delivery.status == "SENT"

def test_campaign_creation_and_send(client: TestClient, admin_user: User):
    headers = get_auth_headers(client, "admin_notif")

    # Create campaign
    payload = {
        "name": "Fall Campaign",
        "title": "Welcome Back Students",
        "body": "Welcome to the new academic term.",
        "audienceType": "ALL"
    }
    res = client.post("/api/v1/notifications/campaigns", json=payload, headers=headers)
    assert res.status_code == 200
    campaign_id = res.json()["data"]["id"]

    # Trigger sending
    res_send = client.post(f"/api/v1/notifications/campaigns/{campaign_id}/send", headers=headers)
    assert res_send.status_code == 200

    # Ensure status is COMPLETED
    res_status = client.get(f"/api/v1/notifications/campaigns/{campaign_id}", headers=headers)
    assert res_status.json()["data"]["status"] == "COMPLETED"

def test_rbac_restrictions(client: TestClient, student_user_x: User):
    headers = get_auth_headers(client, "student_x")

    # Student should not be allowed to access analytics
    res = client.get("/api/v1/notifications/analytics", headers=headers)
    assert res.status_code == 403

    # Student should not be allowed to create campaigns
    payload = {
        "name": "Intruder Campaign",
        "title": "Hack",
        "body": "Hacked",
        "audienceType": "ALL"
    }
    res_campaign = client.post("/api/v1/notifications/campaigns", json=payload, headers=headers)
    assert res_campaign.status_code == 403
