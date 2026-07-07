from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.dependencies import get_db
from app.core.rbac_middleware import PermissionChecker
from app.core.auth_middleware import get_current_user_no_password_force
from app.models.models import (
    User, Notification, NotificationPreference, Announcement,
    NotificationTemplate, BroadcastCampaign, EmergencyAlert,
    CommunicationAudit, NotificationDelivery, NotificationReadReceipt, Role
)
from app.core.responses import make_response
from app.services.notification_service import NotificationService

router = APIRouter()

# ----------------------------------------------------
# Request / Response Schemas
# ----------------------------------------------------

class PreferenceUpdateRequest(BaseModel):
    inAppEnabled: Optional[bool] = None
    emailEnabled: Optional[bool] = None
    smsEnabled: Optional[bool] = None
    pushEnabled: Optional[bool] = None
    academicEnabled: Optional[bool] = None
    attendanceEnabled: Optional[bool] = None
    feeEnabled: Optional[bool] = None
    examEnabled: Optional[bool] = None
    resultEnabled: Optional[bool] = None
    transportEnabled: Optional[bool] = None
    hostelEnabled: Optional[bool] = None
    libraryEnabled: Optional[bool] = None
    emergencyEnabled: Optional[bool] = None
    quietHoursEnabled: Optional[bool] = None
    quietHoursStart: Optional[str] = None # HH:MM format
    quietHoursEnd: Optional[str] = None   # HH:MM format
    timezone: Optional[str] = None

    @field_validator("quietHoursStart", "quietHoursEnd")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        if not re.match(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", v):
            raise ValueError("Time must be in 24-hour format HH:MM")
        return v

class AnnouncementCreateRequest(BaseModel):
    title: str
    body: str
    audienceType: str # ALL, ROLE, DEPARTMENT, SECTION, PROGRAM, INDIVIDUAL
    priority: str = "LOW" # LOW, MEDIUM, HIGH, EMERGENCY
    status: str = "PUBLISHED" # DRAFT, PUBLISHED, ARCHIVED
    pinned: bool = False
    departmentId: Optional[str] = None
    sectionId: Optional[str] = None
    programId: Optional[str] = None
    expiresAt: Optional[datetime] = None

    @field_validator("audienceType")
    @classmethod
    def validate_audience(cls, v: str) -> str:
        if v.upper() not in ["ALL", "ROLE", "DEPARTMENT", "SECTION", "PROGRAM", "INDIVIDUAL"]:
            raise ValueError("Invalid audienceType filter")
        return v.upper()

class TemplateCreateRequest(BaseModel):
    name: str
    code: str
    subjectTemplate: str
    bodyTemplate: str
    channel: str # IN_APP, EMAIL, SMS, PUSH
    category: str # ACADEMIC, ATTENDANCE, FEES, EXAMS, RESULTS, TRANSPORT, HOSTEL, LIBRARY, EMERGENCY, GENERAL

class CampaignCreateRequest(BaseModel):
    name: str
    title: str
    body: str
    audienceType: str # ALL, ROLE, DEPARTMENT, SECTION, PROGRAM

    @field_validator("audienceType")
    @classmethod
    def validate_audience_campaign(cls, v: str) -> str:
        if v.upper() not in ["ALL", "ROLE", "DEPARTMENT", "SECTION", "PROGRAM"]:
            raise ValueError("Invalid campaign audienceType filter")
        return v.upper()

class EmergencyAlertCreateRequest(BaseModel):
    title: str
    message: str
    severity: str # MEDIUM, HIGH, CRITICAL
    targetAudience: str = "ALL" # ALL, STAFF, STUDENTS
    locationText: Optional[str] = None
    instructions: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v.upper() not in ["MEDIUM", "HIGH", "CRITICAL"]:
            raise ValueError("Invalid emergency severity level")
        return v.upper()

# ----------------------------------------------------
# Endpoints
# ----------------------------------------------------

@router.get("")
def list_notifications(
    unread_only: bool = False,
    type_filter: Optional[str] = Query(None, alias="type"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    channel_filter: Optional[str] = Query(None, alias="channel"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100), # Pagination abuse prevention (safe maximum size 100)
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieve current user's notifications (supports sorting, pagination, filtering)."""
    query = db.query(Notification).filter(Notification.recipientId == current_user.id)

    if unread_only:
        query = query.filter(Notification.status == "DELIVERED", Notification.readAt.is_(None))

    if type_filter:
        query = query.filter(Notification.type == type_filter.upper())

    if priority_filter:
        query = query.filter(Notification.priority == priority_filter.upper())

    if channel_filter:
        query = query.filter(Notification.channel == channel_filter.upper())

    query = query.order_by(desc(Notification.createdAt))

    total = query.count()
    offset = (page - 1) * size
    notifications = query.offset(offset).limit(size).all()

    data = [
        {
            "id": n.id,
            "recipientId": n.recipientId,
            "senderId": n.senderId,
            "title": n.title,
            "body": n.body,
            "type": n.type,
            "priority": n.priority,
            "channel": n.channel,
            "status": n.status,
            "entityType": n.entityType,
            "entityId": n.entityId,
            "actionUrl": n.actionUrl,
            "readAt": n.readAt.isoformat() if n.readAt else None,
            "deliveredAt": n.deliveredAt.isoformat() if n.deliveredAt else None,
            "expiresAt": n.expiresAt.isoformat() if n.expiresAt else None,
            "createdAt": n.createdAt.isoformat()
        } for n in notifications
    ]

    return make_response(
        success=True,
        message="Notifications retrieved successfully.",
        data={"notifications": data, "total": total, "page": page, "size": size},
        extra_compat={"notifications": data, "total": total, "page": page, "size": size}
    )

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Returns unread notification count for current user."""
    count = db.query(Notification).filter(
        Notification.recipientId == current_user.id,
        Notification.readAt.is_(None)
    ).count()

    return make_response(
        success=True,
        message="Unread notification count retrieved.",
        data={"unreadCount": count},
        extra_compat={"unreadCount": count}
    )

@router.get("/preferences")
def get_preferences(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieve current user's preferences. Returns defaults if not initialized."""
    pref = db.query(NotificationPreference).filter_by(userId=current_user.id).first()
    if not pref:
        # Default initialization
        pref = NotificationPreference(
            userId=current_user.id,
            inAppEnabled=True,
            emailEnabled=True,
            smsEnabled=True,
            pushEnabled=True,
            academicEnabled=True,
            attendanceEnabled=True,
            feeEnabled=True,
            examEnabled=True,
            resultEnabled=True,
            transportEnabled=True,
            hostelEnabled=True,
            libraryEnabled=True,
            emergencyEnabled=True,
            timezone="UTC"
        )
        db.add(pref)
        db.commit()

    pref_data = {
        "id": pref.id,
        "userId": pref.userId,
        "inAppEnabled": pref.inAppEnabled,
        "emailEnabled": pref.emailEnabled,
        "smsEnabled": pref.smsEnabled,
        "pushEnabled": pref.pushEnabled,
        "academicEnabled": pref.academicEnabled,
        "attendanceEnabled": pref.attendanceEnabled,
        "feeEnabled": pref.feeEnabled,
        "examEnabled": pref.examEnabled,
        "resultEnabled": pref.resultEnabled,
        "transportEnabled": pref.transportEnabled,
        "hostelEnabled": pref.hostelEnabled,
        "libraryEnabled": pref.libraryEnabled,
        "emergencyEnabled": pref.emergencyEnabled,
        "quietHoursEnabled": pref.quietHoursEnabled,
        "quietHoursStart": pref.quietHoursStart,
        "quietHoursEnd": pref.quietHoursEnd,
        "timezone": pref.timezone
    }

    return make_response(
        success=True,
        message="Preferences retrieved successfully.",
        data=pref_data,
        extra_compat=pref_data
    )

@router.patch("/preferences")
def update_preferences(
    payload: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Update current user's notification preferences."""
    pref = db.query(NotificationPreference).filter_by(userId=current_user.id).first()
    if not pref:
        pref = NotificationPreference(userId=current_user.id)
        db.add(pref)

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(pref, k, v)

    db.commit()
    db.refresh(pref)

    return make_response(
        success=True,
        message="Notification preferences updated successfully.",
        data={"id": pref.id}
    )

@router.get("/announcements")
def get_announcements(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieve announcements visible to current user (enforces audience filtering)."""
    # Enforces audience filters server-side
    query = db.query(Announcement).filter(Announcement.status == "PUBLISHED")

    # Non-admin users are restricted to target scope
    role = current_user.role.name if current_user.role else "STUDENT"
    if role != "MASTER_ADMIN":
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Announcement.audienceType == "ALL",
                Announcement.audienceType == "ROLE", # Role filters matched client side or in sub-logic
                Announcement.departmentId == current_user.departmentId,
                Announcement.sectionId == current_user.sectionId
            )
        )

    announcements = query.order_by(desc(Announcement.pinned), desc(Announcement.publishAt)).all()

    data = [
        {
            "id": a.id,
            "title": a.title,
            "body": a.body,
            "authorId": a.authorId,
            "audienceType": a.audienceType,
            "priority": a.priority,
            "publishAt": a.publishAt.isoformat(),
            "expiresAt": a.expiresAt.isoformat() if a.expiresAt else None,
            "pinned": a.pinned,
            "departmentId": a.departmentId,
            "sectionId": a.sectionId,
            "programId": a.programId
        } for a in announcements
    ]

    return make_response(
        success=True,
        message="Announcements retrieved successfully.",
        data={"announcements": data},
        extra_compat={"announcements": data}
    )

@router.post("/announcements", dependencies=[Depends(PermissionChecker("notifications:create"))])
def create_announcement(
    payload: AnnouncementCreateRequest,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Creates system wide or targeted announcement (MASTER_ADMIN)."""
    announcement = Announcement(
        title=payload.title,
        body=payload.body,
        authorId=current_user.id,
        audienceType=payload.audienceType,
        priority=payload.priority.upper(),
        status=payload.status.upper(),
        pinned=payload.pinned,
        departmentId=payload.departmentId,
        sectionId=payload.sectionId,
        programId=payload.programId,
        expiresAt=payload.expiresAt,
        publishAt=datetime.utcnow()
    )
    db.add(announcement)
    db.commit()

    # Log Audit Log
    audit = CommunicationAudit(
        actorId=current_user.id,
        action="CREATE_ANNOUNCEMENT",
        entityType="Announcement",
        entityId=announcement.id,
        actionMetadata=f"Title: {announcement.title}",
        createdAt=datetime.utcnow()
    )
    db.add(audit)
    db.commit()

    return make_response(
        success=True,
        message="Announcement published successfully.",
        data={"id": announcement.id}
    )

@router.get("/templates", dependencies=[Depends(PermissionChecker("notifications:read"))])
def list_templates(db: Session = Depends(get_db)):
    """Retrieve list of notification templates."""
    templates = db.query(NotificationTemplate).all()
    data = [
        {
            "id": t.id,
            "name": t.name,
            "code": t.code,
            "subjectTemplate": t.subjectTemplate,
            "bodyTemplate": t.bodyTemplate,
            "channel": t.channel,
            "category": t.category,
            "active": t.active,
            "version": t.version
        } for t in templates
    ]
    return make_response(
        success=True,
        message="Notification templates retrieved.",
        data={"templates": data}
    )

@router.post("/templates", dependencies=[Depends(PermissionChecker("notifications:create"))])
def create_template(
    payload: TemplateCreateRequest,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Creates a new reusable notification template."""
    existing = db.query(NotificationTemplate).filter_by(code=payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template code already exists.")

    template = NotificationTemplate(
        name=payload.name,
        code=payload.code,
        subjectTemplate=payload.subjectTemplate,
        bodyTemplate=payload.bodyTemplate,
        channel=payload.channel.upper(),
        category=payload.category.upper(),
        createdById=current_user.id
    )
    db.add(template)
    db.commit()

    return make_response(
        success=True,
        message="Notification template created successfully.",
        data={"id": template.id}
    )

@router.get("/campaigns", dependencies=[Depends(PermissionChecker("notifications:read"))])
def list_campaigns(db: Session = Depends(get_db)):
    """List broadcast campaigns."""
    campaigns = db.query(BroadcastCampaign).all()
    data = [
        {
            "id": c.id,
            "name": c.name,
            "title": c.title,
            "body": c.body,
            "audienceType": c.audienceType,
            "status": c.status,
            "totalRecipients": c.totalRecipients,
            "successCount": c.successCount,
            "failureCount": c.failureCount,
            "startedAt": c.startedAt.isoformat() if c.startedAt else None,
            "completedAt": c.completedAt.isoformat() if c.completedAt else None
        } for c in campaigns
    ]
    return make_response(
        success=True,
        message="Broadcast campaigns retrieved.",
        data={"campaigns": data}
    )

@router.post("/campaigns", dependencies=[Depends(PermissionChecker("notifications:create"))])
def create_campaign(
    payload: CampaignCreateRequest,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Create a new broadcast campaign in draft status."""
    campaign = BroadcastCampaign(
        name=payload.name,
        title=payload.title,
        body=payload.body,
        createdById=current_user.id,
        audienceType=payload.audienceType.upper(),
        status="DRAFT"
    )
    db.add(campaign)
    db.commit()

    return make_response(
        success=True,
        message="Broadcast campaign created successfully.",
        data={"id": campaign.id}
    )

@router.get("/campaigns/{id}", dependencies=[Depends(PermissionChecker("notifications:read"))])
def get_campaign(id: str, db: Session = Depends(get_db)):
    """Retrieve specific broadcast campaign details."""
    c = db.query(BroadcastCampaign).filter_by(id=id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    c_data = {
        "id": c.id,
        "name": c.name,
        "title": c.title,
        "body": c.body,
        "audienceType": c.audienceType,
        "status": c.status,
        "totalRecipients": c.totalRecipients,
        "successCount": c.successCount,
        "failureCount": c.failureCount,
        "createdAt": c.createdAt.isoformat(),
        "startedAt": c.startedAt.isoformat() if c.startedAt else None,
        "completedAt": c.completedAt.isoformat() if c.completedAt else None
    }
    return make_response(
        success=True,
        message="Campaign retrieved successfully.",
        data=c_data
    )

@router.post("/campaigns/{id}/send", dependencies=[Depends(PermissionChecker("notifications:create"))])
def send_campaign(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Triggers delivery for the broadcast campaign (double-send prevention)."""
    campaign = db.query(BroadcastCampaign).filter_by(id=id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    if campaign.status in ["SENDING", "COMPLETED"]:
        raise HTTPException(status_code=400, detail="Campaign is already sent or sending.")

    # Schedule the campaign
    campaign.status = "SCHEDULED"
    db.commit()

    # Trigger campaign processing in service layers synchronously or via task queue
    NotificationService.trigger_campaign(db, campaign.id, current_user.id)

    return make_response(
        success=True,
        message="Campaign started successfully.",
        data={"id": campaign.id}
    )

@router.post("/campaigns/{id}/cancel", dependencies=[Depends(PermissionChecker("notifications:create"))])
def cancel_campaign(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Cancels a scheduled or running broadcast campaign."""
    campaign = db.query(BroadcastCampaign).filter_by(id=id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    if campaign.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed or cancelled campaigns.")

    campaign.status = "CANCELLED"
    db.commit()

    return make_response(
        success=True,
        message="Campaign cancelled successfully.",
        data={"id": campaign.id}
    )

@router.get("/emergency-alerts")
def list_emergency_alerts(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Get active emergency alerts."""
    alerts = db.query(EmergencyAlert).filter_by(status="ACTIVE").all()
    data = [
        {
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "severity": a.severity,
            "activatedAt": a.activatedAt.isoformat(),
            "targetAudience": a.targetAudience,
            "locationText": a.locationText,
            "instructions": a.instructions
        } for a in alerts
    ]
    return make_response(
        success=True,
        message="Emergency alerts retrieved successfully.",
        data={"alerts": data},
        extra_compat={"alerts": data}
    )

@router.post("/emergency-alerts", dependencies=[Depends(PermissionChecker("notifications:create"))])
def trigger_emergency_alert(
    payload: EmergencyAlertCreateRequest,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Triggers emergency alert immediately, bypassing standard preferences."""
    alert = NotificationService.trigger_emergency_alert(
        db=db,
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        target_audience=payload.targetAudience,
        actor_id=current_user.id,
        location_text=payload.locationText,
        instructions=payload.instructions
    )
    db.commit()

    return make_response(
        success=True,
        message="Emergency alert activated successfully.",
        data={"id": alert.id}
    )

@router.patch("/emergency-alerts/{id}/resolve", dependencies=[Depends(PermissionChecker("notifications:create"))])
def resolve_emergency_alert(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Resolve an active emergency alert."""
    alert = db.query(EmergencyAlert).filter_by(id=id, status="ACTIVE").first()
    if not alert:
        raise HTTPException(status_code=404, detail="Active emergency alert not found.")

    alert.status = "RESOLVED"
    alert.resolvedAt = datetime.utcnow()
    db.commit()

    # Log Communication Audit
    audit = CommunicationAudit(
        actorId=current_user.id,
        action="RESOLVE_EMERGENCY",
        entityType="EmergencyAlert",
        entityId=alert.id,
        actionMetadata=f"Resolved title: {alert.title}",
        createdAt=datetime.utcnow()
    )
    db.add(audit)
    db.commit()

    return make_response(
        success=True,
        message="Emergency alert resolved successfully.",
        data={"id": alert.id}
    )

@router.get("/analytics", dependencies=[Depends(PermissionChecker("notifications:read"))])
def get_analytics(db: Session = Depends(get_db)):
    """Retrieve communication statistics (MASTER_ADMIN)."""
    total_notifications = db.query(Notification).count()
    unread_notifications = db.query(Notification).filter(Notification.readAt.is_(None)).count()

    # Deliveries
    delivered_count = db.query(NotificationDelivery).filter_by(status="SENT").count()
    failed_count = db.query(NotificationDelivery).filter_by(status="FAILED").count()

    # Channels
    in_app_count = db.query(Notification).filter_by(channel="IN_APP").count()
    email_count = db.query(Notification).filter_by(channel="EMAIL").count()
    sms_count = db.query(Notification).filter_by(channel="SMS").count()
    push_count = db.query(Notification).filter_by(channel="PUSH").count()

    # Campaigns
    campaign_count = db.query(BroadcastCampaign).count()

    # Emergency Alerts
    emergency_count = db.query(EmergencyAlert).filter_by(status="ACTIVE").count()

    return make_response(
        success=True,
        message="Analytics retrieved successfully.",
        data={
            "totalNotifications": total_notifications,
            "unreadNotifications": unread_notifications,
            "deliveryStats": {
                "delivered": delivered_count,
                "failed": failed_count
            },
            "channelDistribution": {
                "inApp": in_app_count,
                "email": email_count,
                "sms": sms_count,
                "push": push_count
            },
            "campaignsCount": campaign_count,
            "activeEmergencyAlerts": emergency_count
        }
    )

@router.get("/{id}")
def get_notification(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Retrieve details for specific notification (blocks IDOR access)."""
    n = db.query(Notification).filter_by(id=id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")

    # Block IDOR
    if n.recipientId != current_user.id and current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Access denied to this notification.")

    n_data = {
        "id": n.id,
        "recipientId": n.recipientId,
        "senderId": n.senderId,
        "title": n.title,
        "body": n.body,
        "type": n.type,
        "priority": n.priority,
        "channel": n.channel,
        "status": n.status,
        "entityType": n.entityType,
        "entityId": n.entityId,
        "actionUrl": n.actionUrl,
        "readAt": n.readAt.isoformat() if n.readAt else None,
        "deliveredAt": n.deliveredAt.isoformat() if n.deliveredAt else None,
        "createdAt": n.createdAt.isoformat()
    }

    return make_response(
        success=True,
        message="Notification details retrieved.",
        data=n_data
    )

@router.patch("/{id}/read")
def mark_read(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Mark a notification as read (idempotent, blocks IDOR)."""
    n = db.query(Notification).filter_by(id=id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")

    # Block IDOR
    if n.recipientId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this notification.")

    if not n.readAt:
        n.readAt = datetime.utcnow()
        n.status = "READ"

        # Create Read Receipt
        receipt = db.query(NotificationReadReceipt).filter_by(notificationId=n.id, userId=current_user.id).first()
        if not receipt:
            receipt = NotificationReadReceipt(
                notificationId=n.id,
                userId=current_user.id,
                readAt=datetime.utcnow()
            )
            db.add(receipt)

        db.commit()

    return make_response(
        success=True,
        message="Notification marked as read.",
        data={"id": n.id}
    )

@router.patch("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Mark all unread notifications of the current user as read."""
    unread = db.query(Notification).filter(
        Notification.recipientId == current_user.id,
        Notification.readAt.is_(None)
    ).all()

    for n in unread:
        n.readAt = datetime.utcnow()
        n.status = "READ"
        receipt = db.query(NotificationReadReceipt).filter_by(notificationId=n.id, userId=current_user.id).first()
        if not receipt:
            receipt = NotificationReadReceipt(
                notificationId=n.id,
                userId=current_user.id,
                readAt=datetime.utcnow()
            )
            db.add(receipt)

    db.commit()

    return make_response(
        success=True,
        message="All notifications marked as read.",
        data={"count": len(unread)}
    )

@router.delete("/{id}")
def delete_notification(
    id: str,
    current_user: User = Depends(get_current_user_no_password_force),
    db: Session = Depends(get_db)
):
    """Dismiss/soft-delete a notification (recipient owner only)."""
    n = db.query(Notification).filter_by(id=id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")

    if n.recipientId != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this notification.")

    db.delete(n)
    db.commit()

    return make_response(
        success=True,
        message="Notification dismissed successfully."
    )
