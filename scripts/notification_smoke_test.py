import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_smoke_test():
    checks = []

    def log_check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {name} - {detail}")

    # 1. Login Admin
    admin_token = None
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json={
            "username_or_email": "admin_demo",
            "password": "password"
        })
        if res.status_code == 200:
            admin_token = res.json()["data"]["access_token"]
            log_check("Admin Login", True)
        else:
            log_check("Admin Login", False, f"Status code: {res.status_code}")
            return
    except Exception as e:
        log_check("Admin Login Connection", False, str(e))
        return

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Login Student
    student_token = None
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json={
            "username_or_email": "student_demo",
            "password": "password"
        })
        if res.status_code == 200:
            student_token = res.json()["data"]["access_token"]
            log_check("Student Login", True)
        else:
            log_check("Student Login", False, f"Status: {res.status_code}")
    except Exception as e:
        log_check("Student Login Connection", False, str(e))

    student_headers = {"Authorization": f"Bearer {student_token}"} if student_token else {}

    # 3. GET /notifications (Student)
    try:
        res = requests.get(f"{BASE_URL}/notifications", headers=student_headers)
        log_check("Get Notifications (Student)", res.status_code == 200, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Get Notifications", False, str(e))

    # 4. GET /unread-count (Student)
    try:
        res = requests.get(f"{BASE_URL}/notifications/unread-count", headers=student_headers)
        log_check("Get Unread Count (Student)", res.status_code == 200 and "unreadCount" in res.json()["data"])
    except Exception as e:
        log_check("Get Unread Count", False, str(e))

    # 5. GET /preferences (Student)
    try:
        res = requests.get(f"{BASE_URL}/notifications/preferences", headers=student_headers)
        log_check("Get Preferences (Student)", res.status_code == 200 and "inAppEnabled" in res.json()["data"])
    except Exception as e:
        log_check("Get Preferences", False, str(e))

    # 6. PATCH /preferences (Student) - Valid
    try:
        payload = {"emailEnabled": False, "timezone": "Asia/Kolkata"}
        res = requests.patch(f"{BASE_URL}/notifications/preferences", json=payload, headers=student_headers)
        log_check("Update Preferences Valid", res.status_code == 200)
    except Exception as e:
        log_check("Update Preferences Valid", False, str(e))

    # 7. PATCH /preferences (Student) - Invalid Quiet Hours Format
    try:
        payload = {"quietHoursEnabled": True, "quietHoursStart": "invalid_time"}
        res = requests.patch(f"{BASE_URL}/notifications/preferences", json=payload, headers=student_headers)
        log_check("Update Preferences Invalid Quiet Hours Blocked", res.status_code == 422, f"Got: {res.status_code}")
    except Exception as e:
        log_check("Update Preferences Invalid", False, str(e))

    # 8. GET /announcements (Student)
    try:
        res = requests.get(f"{BASE_URL}/notifications/announcements", headers=student_headers)
        log_check("Get Announcements (Student)", res.status_code == 200)
    except Exception as e:
        log_check("Get Announcements", False, str(e))

    # 9. POST /announcements (Student - Should be Forbidden)
    try:
        payload = {"title": "Hack", "body": "Hacked notice", "audienceType": "ALL"}
        res = requests.post(f"{BASE_URL}/notifications/announcements", json=payload, headers=student_headers)
        log_check("Post Announcement Student Blocked", res.status_code == 403, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Post Announcement Block Check", False, str(e))

    # 10. POST /announcements (Admin - Valid)
    announcement_id = None
    try:
        payload = {"title": "Smoke Test Notice", "body": "Notice Content", "audienceType": "ALL"}
        res = requests.post(f"{BASE_URL}/notifications/announcements", json=payload, headers=admin_headers)
        if res.status_code == 200:
            announcement_id = res.json()["data"]["id"]
            log_check("Post Announcement Admin Allowed", True)
        else:
            log_check("Post Announcement Admin Allowed", False, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Post Announcement Admin", False, str(e))

    # 11. GET /templates (Admin)
    try:
        res = requests.get(f"{BASE_URL}/notifications/templates", headers=admin_headers)
        log_check("Get Templates Admin", res.status_code == 200)
    except Exception as e:
        log_check("Get Templates Admin", False, str(e))

    # 12. GET /templates (Student - Should be Forbidden)
    try:
        res = requests.get(f"{BASE_URL}/notifications/templates", headers=student_headers)
        log_check("Get Templates Student Blocked", res.status_code == 403, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Get Templates Student Block", False, str(e))

    # 13. POST /campaigns (Admin)
    campaign_id = None
    try:
        payload = {"name": "Smoke Campaign", "title": "Subject line", "body": "Body text", "audienceType": "ALL"}
        res = requests.post(f"{BASE_URL}/notifications/campaigns", json=payload, headers=admin_headers)
        if res.status_code == 200:
            campaign_id = res.json()["data"]["id"]
            log_check("Create Campaign Admin Allowed", True)
        else:
            log_check("Create Campaign Admin Allowed", False, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Create Campaign", False, str(e))

    # 14. POST /campaigns/{id}/send (Admin)
    try:
        res = requests.post(f"{BASE_URL}/campaigns/{campaign_id}/send", headers=admin_headers) # Wait, prefix is notifications/campaigns
        res = requests.post(f"{BASE_URL}/notifications/campaigns/{campaign_id}/send", headers=admin_headers)
        log_check("Send Campaign Valid Trigger", res.status_code == 200)
    except Exception as e:
        log_check("Send Campaign Trigger", False, str(e))

    # 15. POST /campaigns/{id}/send (Admin - Duplicate Send Check)
    try:
        res = requests.post(f"{BASE_URL}/notifications/campaigns/{campaign_id}/send", headers=admin_headers)
        log_check("Prevent Duplicate Campaign Trigger", res.status_code == 400, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Prevent Duplicate Campaign", False, str(e))

    # 16. POST /emergency-alerts (Admin)
    emergency_id = None
    try:
        payload = {"title": "Smoke Alert", "message": "Emergency Alert Test", "severity": "HIGH", "targetAudience": "ALL"}
        res = requests.post(f"{BASE_URL}/notifications/emergency-alerts", json=payload, headers=admin_headers)
        if res.status_code == 200:
            emergency_id = res.json()["data"]["id"]
            log_check("Trigger Emergency Alert Admin", True)
        else:
            log_check("Trigger Emergency Alert Admin", False, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Trigger Emergency Alert", False, str(e))

    # 17. GET /emergency-alerts (Student)
    try:
        res = requests.get(f"{BASE_URL}/notifications/emergency-alerts", headers=student_headers)
        log_check("Get Active Emergencies", res.status_code == 200 and len(res.json()["data"]["alerts"]) >= 1)
    except Exception as e:
        log_check("Get Active Emergencies", False, str(e))

    # 18. PATCH /emergency-alerts/{id}/resolve (Admin)
    try:
        res = requests.patch(f"{BASE_URL}/notifications/emergency-alerts/{emergency_id}/resolve", headers=admin_headers)
        log_check("Resolve Emergency Alert Admin", res.status_code == 200)
    except Exception as e:
        log_check("Resolve Emergency Alert", False, str(e))

    # 19. GET /analytics (Admin)
    try:
        res = requests.get(f"{BASE_URL}/notifications/analytics", headers=admin_headers)
        log_check("Get Analytics Admin Allowed", res.status_code == 200 and "totalNotifications" in res.json()["data"])
    except Exception as e:
        log_check("Get Analytics Admin", False, str(e))

    # 20. GET /analytics (Student - Should be Forbidden)
    try:
        res = requests.get(f"{BASE_URL}/notifications/analytics", headers=student_headers)
        log_check("Get Analytics Student Blocked", res.status_code == 403, f"Code: {res.status_code}")
    except Exception as e:
        log_check("Get Analytics Student Block", False, str(e))

    # Summary
    passed_cnt = sum(1 for c in checks if c["passed"])
    total_cnt = len(checks)
    print(f"Smoke Test Summary: {passed_cnt}/{total_cnt} checks passed.")
    if passed_cnt == total_cnt:
        print("SUCCESS: Notification system smoke test passed successfully.")
    else:
        print("ERROR: Notification system smoke test failed checks.")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()
