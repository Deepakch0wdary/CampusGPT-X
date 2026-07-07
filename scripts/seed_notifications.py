import os
import sys
from datetime import datetime, timedelta

# Add backend app path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))

from app.core.dependencies import SessionLocal, engine
from app.models.models import (
    Base, User, Role, NotificationTemplate, Announcement, BroadcastCampaign, NotificationPreference
)

def seed_notifications():
    # 0. Ensure tables exist in SQLAlchemy engine
    Base.metadata.create_all(bind=engine)
    print("Ensured all SQLAlchemy metadata tables are created in the database.")

    db = SessionLocal()
    try:
        # 1. Fetch Creator (MASTER_ADMIN)
        admin_role = db.query(Role).filter_by(name="MASTER_ADMIN").first()
        if not admin_role:
            print("ERROR: MASTER_ADMIN role not found. Run standard database migrations first.")
            return

        admin_user = db.query(User).filter_by(roleId=admin_role.id).first()
        if not admin_user:
            # Fallback to first user in system
            admin_user = db.query(User).first()
            if not admin_user:
                print("ERROR: No users found in database to author seeded data.")
                return

        print(f"Using user '{admin_user.username}' as author/creator for notifications seeding.")

        # 2. Seed Notification Templates
        templates_data = [
            {
                "name": "Attendance Shortage Email Notice",
                "code": "ATTENDANCE_WARN",
                "subjectTemplate": "ATTENTION: Attendance Shortage for {{ studentName }}",
                "bodyTemplate": "Dear Parent/Student,

This is to notify you that the attendance of {{ studentName }} has fallen below the minimum required limit. Current percentage: {{ percentage }}%.

Regards,
Academic Office",
                "channel": "EMAIL",
                "category": "ATTENDANCE"
            },
            {
                "name": "Exam Schedule Portal Alert",
                "code": "EXAM_SCHEDULE",
                "subjectTemplate": "Exam Schedule Updated: {{ examName }}",
                "bodyTemplate": "Please note that the schedule for {{ examName }} has been published. Date: {{ date }}. Location: {{ room }}.",
                "channel": "IN_APP",
                "category": "EXAMS"
            },
            {
                "name": "Library Overdue SMS Warning",
                "code": "LIBRARY_OVERDUE",
                "subjectTemplate": "Library Book Overdue Alert",
                "bodyTemplate": "Reminder: The book '{{ bookTitle }}' is past its return date by {{ days }} days. Please return it to avoid further fines.",
                "channel": "SMS",
                "category": "LIBRARY"
            },
            {
                "name": "Fee Due Payment Link Reminder",
                "code": "FEE_REMIND",
                "subjectTemplate": "Term Payment Due Notice",
                "bodyTemplate": "Dear Parent/Student, a fee invoice of ${{ amount }} is due on {{ date }}. Please clear it using the portal payment links.",
                "channel": "EMAIL",
                "category": "FEES"
            }
        ]

        for t_info in templates_data:
            existing = db.query(NotificationTemplate).filter_by(code=t_info["code"]).first()
            if not existing:
                t = NotificationTemplate(
                    name=t_info["name"],
                    code=t_info["code"],
                    subjectTemplate=t_info["subjectTemplate"],
                    bodyTemplate=t_info["bodyTemplate"],
                    channel=t_info["channel"],
                    category=t_info["category"],
                    createdById=admin_user.id
                )
                db.add(t)
                print(f"Seeded template: {t_info['code']}")

        # 3. Seed Announcements
        announcements_data = [
            {
                "title": "Welcome to CampusGPT X 2026 Academic Term",
                "body": "Welcome back all students, staff, and faculty members! We are proud to present our brand new integrated notifications dashboard and communication center.",
                "audienceType": "ALL",
                "priority": "LOW",
                "status": "PUBLISHED",
                "pinned": True
            },
            {
                "title": "Upcoming Campus Health Checkup Camp",
                "body": "A medical checkup camp is scheduled in Block C next Monday from 9:00 AM to 4:00 PM. Registration is mandatory on the student dashboard.",
                "audienceType": "ALL",
                "priority": "MEDIUM",
                "status": "PUBLISHED",
                "pinned": False
            }
        ]

        for a_info in announcements_data:
            existing = db.query(Announcement).filter_by(title=a_info["title"]).first()
            if not existing:
                a = Announcement(
                    title=a_info["title"],
                    body=a_info["body"],
                    authorId=admin_user.id,
                    audienceType=a_info["audienceType"],
                    priority=a_info["priority"],
                    status=a_info["status"],
                    pinned=a_info["pinned"],
                    publishAt=datetime.utcnow()
                )
                db.add(a)
                print(f"Seeded announcement: {a_info['title']}")

        # 4. Seed Broadcast Campaigns
        campaigns_data = [
            {
                "name": "System Upgrade Maintenance Notification",
                "title": "SCHEDULED MAINTENANCE: Portal Offline",
                "body": "The Smart Campus Portal will undergo maintenance on Saturday from 2:00 AM to 6:00 AM. Thank you for your cooperation.",
                "audienceType": "ALL",
                "status": "DRAFT"
            }
        ]

        for c_info in campaigns_data:
            existing = db.query(BroadcastCampaign).filter_by(name=c_info["name"]).first()
            if not existing:
                c = BroadcastCampaign(
                    name=c_info["name"],
                    title=c_info["title"],
                    body=c_info["body"],
                    audienceType=c_info["audienceType"],
                    createdById=admin_user.id,
                    status=c_info["status"]
                )
                db.add(c)
                print(f"Seeded campaign: {c_info['name']}")

        # 5. Initialize NotificationPreference for all active users
        users = db.query(User).all()
        for u in users:
            existing_pref = db.query(NotificationPreference).filter_by(userId=u.id).first()
            if not existing_pref:
                pref = NotificationPreference(
                    userId=u.id,
                    inAppEnabled=True,
                    emailEnabled=True,
                    smsEnabled=True,
                    pushEnabled=True,
                    timezone="UTC"
                )
                db.add(pref)
        print(f"Verified notification preferences for {len(users)} users.")

        db.commit()
        print("SUCCESS: Notification database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"ERROR: Seeding failed. {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_notifications()
