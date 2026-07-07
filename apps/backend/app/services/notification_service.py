import uuid
from datetime import datetime
import pytz
from sqlalchemy.orm import Session
from app.models.models import (
    Notification, NotificationPreference, NotificationDelivery,
    NotificationReadReceipt, BroadcastCampaign, BroadcastRecipient,
    EmergencyAlert, CommunicationAudit, User, Role, Department, Section, ParentProfile, ParentStudentLink
)

class NotificationService:
    @staticmethod
    def is_in_quiet_hours(pref: NotificationPreference) -> bool:
        """Determines if current local time is within user's quiet hours."""
        if not pref or not pref.quietHoursEnabled or not pref.quietHoursStart or not pref.quietHoursEnd:
            return False

        try:
            tz = pytz.timezone(pref.timezone)
        except Exception:
            tz = pytz.UTC

        now = datetime.now(tz)
        current_time_str = now.strftime("%H:%M")

        start = pref.quietHoursStart
        end = pref.quietHoursEnd

        if start <= end:
            return start <= current_time_str <= end
        else:
            # Crosses midnight e.g. 22:00 to 06:00
            return current_time_str >= start or current_time_str <= end

    @staticmethod
    def should_deliver(pref: NotificationPreference, category: str, channel: str) -> bool:
        """Checks if notification category & channel are enabled for the user preference."""
        if not pref:
            return True # Default to delivery if preferences not configured yet

        # Emergency notifications always override preferences
        if category.upper() == "EMERGENCY":
            return True

        # Check category preference
        category_map = {
            "ACADEMIC": pref.academicEnabled,
            "ATTENDANCE": pref.attendanceEnabled,
            "FEES": pref.feeEnabled,
            "EXAMS": pref.examEnabled,
            "RESULTS": pref.resultEnabled,
            "TRANSPORT": pref.transportEnabled,
            "HOSTEL": pref.hostelEnabled,
            "LIBRARY": pref.libraryEnabled,
            "EMERGENCY": pref.emergencyEnabled,
        }
        category_enabled = category_map.get(category.upper(), True)
        if not category_enabled:
            return False

        # Check channel preference
        channel_map = {
            "IN_APP": pref.inAppEnabled,
            "EMAIL": pref.emailEnabled,
            "SMS": pref.smsEnabled,
            "PUSH": pref.pushEnabled,
        }
        return channel_map.get(channel.upper(), True)

    @classmethod
    def create_notification(
        cls,
        db: Session,
        recipient_id: str,
        title: str,
        body: str,
        type: str = "INFO",
        priority: str = "MEDIUM",
        channel: str = "IN_APP",
        sender_id: str = None,
        entity_type: str = None,
        entity_id: str = None,
        action_url: str = None,
        category: str = "GENERAL"
    ) -> Notification:
        """Creates unified notification and runs simulated delivery pipelines."""
        pref = db.query(NotificationPreference).filter_by(userId=recipient_id).first()

        # Check quiet hours constraint (only applies to noisy channels, IN_APP is always allowed silently)
        in_quiet = False
        if channel.upper() != "IN_APP" and priority.upper() != "CRITICAL" and type.upper() != "EMERGENCY":
            in_quiet = cls.is_in_quiet_hours(pref)

        # Check preference filters
        allowed = cls.should_deliver(pref, category, channel)

        status = "PENDING"
        if not allowed:
            status = "FAILED"
        elif in_quiet:
            status = "FAILED" # Suppressed due to quiet hours

        notif = Notification(
            recipientId=recipient_id,
            senderId=sender_id,
            title=title,
            body=body,
            type=type.upper(),
            priority=priority.upper(),
            channel=channel.upper(),
            status=status,
            entityType=entity_type,
            entityId=entity_id,
            actionUrl=action_url,
            createdAt=datetime.utcnow()
        )
        db.add(notif)
        db.flush()

        if status == "FAILED":
            reason = "QUIET_HOURS_SUPPRESSED" if in_quiet else "PREFERENCE_FILTERED"
            delivery = NotificationDelivery(
                notificationId=notif.id,
                channel=channel.upper(),
                provider="SIMULATED_DEMO_PROVIDER",
                status="FAILED",
                failureReason=reason,
                attemptedAt=datetime.utcnow()
            )
            db.add(delivery)
        else:
            # Trigger Simulated Delivery
            cls.dispatch_delivery_simulated(db, notif)

        return notif

    @classmethod
    def dispatch_delivery_simulated(cls, db: Session, notif: Notification):
        """Simulates SMS, Email, and Push notifications truthfully."""
        recipient = db.query(User).filter_by(id=notif.recipientId).first()
        if not recipient:
            return

        status = "SENT"
        failure_reason = None
        provider_msg_id = str(uuid.uuid4())

        # Validate channel target presence
        if notif.channel == "EMAIL" and not recipient.email:
            status = "FAILED"
            failure_reason = "RECIPIENT_EMAIL_MISSING"
        elif notif.channel == "SMS":
            # Check profile phone number
            profile = recipient.profile
            if not profile or not profile.phoneNumber:
                status = "FAILED"
                failure_reason = "RECIPIENT_PHONE_MISSING"

        delivery = NotificationDelivery(
            notificationId=notif.id,
            channel=notif.channel,
            provider="SIMULATED_DEMO_PROVIDER",
            providerMessageId=provider_msg_id if status == "SENT" else None,
            attemptNumber=1,
            status=status,
            attemptedAt=datetime.utcnow(),
            deliveredAt=datetime.utcnow() if status == "SENT" else None,
            failureReason=failure_reason
        )
        db.add(delivery)

        if status == "SENT":
            notif.status = "DELIVERED"
            notif.deliveredAt = datetime.utcnow()
        else:
            notif.status = "FAILED"

    @classmethod
    def resolve_audience(cls, db: Session, audience_type: str, filters: dict) -> list[str]:
        """Resolves target audience lists to a list of User IDs."""
        aud_type = audience_type.upper()
        if aud_type == "ALL":
            users = db.query(User).filter(User.status == "ACTIVE").all()
            return [u.id for u in users]

        elif aud_type == "ROLE":
            role_name = filters.get("role")
            if not role_name:
                return []
            role = db.query(Role).filter_by(name=role_name.upper()).first()
            if not role:
                return []
            users = db.query(User).filter(User.roleId == role.id, User.status == "ACTIVE").all()
            return [u.id for u in users]

        elif aud_type == "DEPARTMENT":
            dept_id = filters.get("departmentId")
            if not dept_id:
                return []
            users = db.query(User).filter(User.departmentId == dept_id, User.status == "ACTIVE").all()
            return [u.id for u in users]

        elif aud_type == "SECTION":
            section_id = filters.get("sectionId")
            if not section_id:
                return []
            users = db.query(User).filter(User.sectionId == section_id, User.status == "ACTIVE").all()
            return [u.id for u in users]

        elif aud_type == "PROGRAM":
            program_id = filters.get("programId")
            if not program_id:
                return []
            # Resolves users via section and semester relation to program
            from app.models.models import Section as SectionModel
            sections = db.query(SectionModel).filter_by(programId=program_id).all()
            sec_ids = [s.id for s in sections]
            users = db.query(User).filter(User.sectionId.in_(sec_ids), User.status == "ACTIVE").all() if sec_ids else []
            return [u.id for u in users]

        elif aud_type == "INDIVIDUAL":
            user_id = filters.get("userId")
            return [user_id] if user_id else []

        return []

    @classmethod
    def trigger_campaign(cls, db: Session, campaign_id: str, actor_id: str):
        """Deduplicates recipients, resolves targets, and dispatches bulk messages."""
        campaign = db.query(BroadcastCampaign).filter_by(id=campaign_id).first()
        if not campaign or campaign.status != "SCHEDULED":
            return

        campaign.status = "SENDING"
        campaign.startedAt = datetime.utcnow()
        db.flush()

        # Parse audience filters if stored or resolved
        filters = {}
        if campaign.audienceType == "ROLE":
            # Match role fallback e.g. campaign.name or campaign details
            pass

        # For simplicity, resolve target recipients
        recipient_ids = cls.resolve_audience(db, campaign.audienceType, filters)
        # Deduplicate
        recipient_ids = list(set(recipient_ids))

        campaign.totalRecipients = len(recipient_ids)
        success = 0
        failure = 0

        for r_id in recipient_ids:
            try:
                # Prevent duplicate entries
                existing = db.query(BroadcastRecipient).filter_by(campaignId=campaign.id, userId=r_id).first()
                if existing:
                    continue

                notif = cls.create_notification(
                    db=db,
                    recipient_id=r_id,
                    title=campaign.title,
                    body=campaign.body,
                    type="INFO",
                    priority="MEDIUM",
                    channel="IN_APP",
                    sender_id=actor_id,
                    category="GENERAL"
                )

                rec = BroadcastRecipient(
                    campaignId=campaign.id,
                    userId=r_id,
                    notificationId=notif.id,
                    deliveryStatus="SENT" if notif.status == "DELIVERED" else "FAILED"
                )
                db.add(rec)
                success += 1
            except Exception:
                rec = BroadcastRecipient(
                    campaignId=campaign.id,
                    userId=r_id,
                    deliveryStatus="FAILED"
                )
                db.add(rec)
                failure += 1

        campaign.successCount = success
        campaign.failureCount = failure
        campaign.status = "COMPLETED"
        campaign.completedAt = datetime.utcnow()

        # Log Communication Audit
        audit = CommunicationAudit(
            actorId=actor_id,
            action="TRIGGER_CAMPAIGN",
            entityType="BroadcastCampaign",
            entityId=campaign.id,
            actionMetadata=f"Total: {campaign.totalRecipients}, Success: {success}, Failure: {failure}",
            createdAt=datetime.utcnow()
        )
        db.add(audit)
        db.commit()

    @classmethod
    def trigger_emergency_alert(cls, db: Session, title: str, message: str, severity: str, target_audience: str, actor_id: str, location_text: str = None, instructions: str = None) -> EmergencyAlert:
        """Sends emergency in-app notifications bypassing preferences."""
        alert = EmergencyAlert(
            title=title,
            message=message,
            severity=severity.upper(),
            createdById=actor_id,
            status="ACTIVE",
            activatedAt=datetime.utcnow(),
            targetAudience=target_audience.upper(),
            locationText=location_text,
            instructions=instructions
        )
        db.add(alert)
        db.flush()

        # Resolve audience
        filters = {}
        if target_audience.upper() == "STAFF":
            # For simplicity, target all non-student, non-parent users
            roles = db.query(Role).filter(Role.name.in_(["MASTER_ADMIN", "TEACHER", "ADMISSION_OFFICE", "FINANCE_OFFICE"])).all()
            role_ids = [r.id for r in roles]
            users = db.query(User).filter(User.roleId.in_(role_ids), User.status == "ACTIVE").all()
            recipient_ids = [u.id for u in users]
        elif target_audience.upper() == "STUDENTS":
            role = db.query(Role).filter_by(name="STUDENT").first()
            users = db.query(User).filter(User.roleId == role.id, User.status == "ACTIVE").all() if role else []
            recipient_ids = [u.id for u in users]
        else:
            users = db.query(User).filter(User.status == "ACTIVE").all()
            recipient_ids = [u.id for u in users]

        # Send alert bypass notifications to recipient_ids
        for r_id in recipient_ids:
            cls.create_notification(
                db=db,
                recipient_id=r_id,
                title=f"⚠️ {severity.upper()} EMERGENCY: {title}",
                body=message,
                type="EMERGENCY",
                priority="CRITICAL",
                channel="IN_APP",
                sender_id=actor_id,
                category="EMERGENCY"
            )

        audit = CommunicationAudit(
            actorId=actor_id,
            action="TRIGGER_EMERGENCY",
            entityType="EmergencyAlert",
            entityId=alert.id,
            actionMetadata=f"Severity: {severity.upper()}, Audience: {target_audience.upper()}",
            createdAt=datetime.utcnow()
        )
        db.add(audit)
        return alert

    @classmethod
    def get_parent_user_ids(cls, db: Session, student_id: str) -> list[str]:
        """Resolves parent user IDs linked to a student user ID."""
        links = db.query(ParentStudentLink).filter_by(studentId=student_id).all()
        parent_user_ids = []
        for link in links:
            profile = db.query(ParentProfile).filter_by(id=link.parentId).first()
            if profile and profile.userId:
                parent_user_ids.append(profile.userId)
        return parent_user_ids

    @classmethod
    def send_attendance_warning(cls, db: Session, student_id: str, percentage: float):
        """Sends warning if student attendance falls below limit."""
        title = "Attendance Shortage Warning"
        body = f"Your current attendance is {percentage:.1f}%, which is below the required threshold. Please attend classes regularly."
        # Notify student
        cls.create_notification(db, student_id, title, body, type="WARNING", priority="HIGH", category="ATTENDANCE")
        # Notify parents
        parent_ids = cls.get_parent_user_ids(db, student_id)
        for p_id in parent_ids:
            cls.create_notification(db, p_id, f"Student Alert: {title}", f"Your child's attendance is {percentage:.1f}%, below the required threshold.", type="WARNING", priority="HIGH", category="ATTENDANCE")

    @classmethod
    def send_exam_schedule_update(cls, db: Session, student_id: str, exam_title: str, date_str: str):
        """Notifies student and parents of a scheduled exam."""
        title = f"Exam Scheduled: {exam_title}"
        body = f"An exam has been scheduled for {exam_title} on {date_str}."
        cls.create_notification(db, student_id, title, body, type="INFO", priority="MEDIUM", category="EXAMS")
        parent_ids = cls.get_parent_user_ids(db, student_id)
        for p_id in parent_ids:
            cls.create_notification(db, p_id, f"Student Alert: {title}", body, type="INFO", priority="MEDIUM", category="EXAMS")

    @classmethod
    def send_result_published(cls, db: Session, student_id: str, exam_title: str, results_summary: str):
        """Notifies student and parents of result publication."""
        title = f"Results Published: {exam_title}"
        body = f"Results for {exam_title} have been published. Status: {results_summary}."
        cls.create_notification(db, student_id, title, body, type="SUCCESS", priority="HIGH", category="RESULTS")
        parent_ids = cls.get_parent_user_ids(db, student_id)
        for p_id in parent_ids:
            cls.create_notification(db, p_id, f"Student Alert: {title}", body, type="SUCCESS", priority="HIGH", category="RESULTS")

    @classmethod
    def send_fee_due_reminder(cls, db: Session, student_id: str, amount: float, due_date_str: str):
        """Reminds parents and student of pending fee dues."""
        title = "Fee Payment Due Reminder"
        body = f"A fee payment of ${amount:.2f} is due on {due_date_str}. Please clear it soon."
        cls.create_notification(db, student_id, title, body, type="WARNING", priority="HIGH", category="FEES")
        parent_ids = cls.get_parent_user_ids(db, student_id)
        for p_id in parent_ids:
            cls.create_notification(db, p_id, title, body, type="WARNING", priority="HIGH", category="FEES")

    @classmethod
    def send_library_overdue_notice(cls, db: Session, student_id: str, book_title: str, overdue_days: int):
        """Notifies student of overdue library book."""
        title = "Library Book Overdue Notice"
        body = f"The book '{book_title}' is overdue by {overdue_days} days. Please return it to avoid further fines."
        cls.create_notification(db, student_id, title, body, type="WARNING", priority="MEDIUM", category="LIBRARY")

    @classmethod
    def send_hostel_alert(cls, db: Session, student_id: str, alert_message: str):
        """Sends hostel status alert to student and parents."""
        title = "Hostel Notification"
        cls.create_notification(db, student_id, title, alert_message, type="INFO", priority="MEDIUM", category="HOSTEL")
        parent_ids = cls.get_parent_user_ids(db, student_id)
        for p_id in parent_ids:
            cls.create_notification(db, p_id, f"Student Alert: {title}", alert_message, type="INFO", priority="MEDIUM", category="HOSTEL")

    @classmethod
    def send_transport_delay(cls, db: Session, student_id: str, route_name: str, delay_minutes: int):
        """Notifies student and parents of transit delays."""
        title = f"Transport Route Delay: {route_name}"
        body = f"The school transport on route {route_name} is delayed by approximately {delay_minutes} minutes."
        cls.create_notification(db, student_id, title, body, type="WARNING", priority="MEDIUM", category="TRANSPORT")
        parent_ids = cls.get_parent_user_ids(db, student_id)
        for p_id in parent_ids:
            cls.create_notification(db, p_id, title, body, type="WARNING", priority="MEDIUM", category="TRANSPORT")

    @classmethod
    def send_parent_consent_request(cls, db: Session, student_id: str, consent_title: str):
        """Requests consent from student's parent/guardian."""
        title = f"Consent Required: {consent_title}"
        body = f"Your signature/consent is required for the form '{consent_title}'."
        parent_ids = cls.get_parent_user_ids(db, student_id)
        for p_id in parent_ids:
            cls.create_notification(db, p_id, title, body, type="WARNING", priority="HIGH", category="GENERAL")

    @classmethod
    def send_admission_update(cls, db: Session, student_id: str, admission_status: str):
        """Sends update on admission process status."""
        title = "Admission Application Status Update"
        body = f"Your admission application status has been updated to: {admission_status}."
        cls.create_notification(db, student_id, title, body, type="SUCCESS", priority="HIGH", category="ACADEMIC")

    @classmethod
    def send_assignment_deadline_reminder(cls, db: Session, student_id: str, assignment_title: str, deadline_str: str):
        """Reminds student of upcoming assignment submission deadline."""
        title = f"Assignment Deadline Reminder: {assignment_title}"
        body = f"The deadline for assignment '{assignment_title}' is {deadline_str}. Please submit it on time."
        cls.create_notification(db, student_id, title, body, type="WARNING", priority="MEDIUM", category="ACADEMIC")
