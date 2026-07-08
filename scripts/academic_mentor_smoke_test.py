import sys
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def login(username, password):
    res = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username_or_email": username, "password": password}
    )
    if res.status_code == 200:
        return res.json()["access_token"]
    return None

def run_smoke_test():
    print("Starting CampusGPT X Academic Mentor Smoke Test...")
    print("Backend Target:", BASE_URL)

    checks = []

    def log_check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name} {f'({detail})' if detail else ''}")

    # 1. Health check
    try:
        res = requests.get(f"{BASE_URL}/api/v1/health")
        log_check("1. System Health", res.status_code == 200)
    except Exception as e:
        log_check("1. System Health", False, str(e))

    # Logins
    student_token = login("studenta", "password")
    other_student_token = login("studentb", "password")
    insufficient_student_token = login("studentc", "password")
    parent_token = login("parent_demo", "password")
    teacher_token = login("teacher_demo", "password")
    admin_token = login("admin", "AdminPassword@123")

    # Headers setup
    student_headers = {"Authorization": f"Bearer {student_token}"} if student_token else {}
    other_headers = {"Authorization": f"Bearer {other_student_token}"} if other_student_token else {}
    insufficient_headers = {"Authorization": f"Bearer {insufficient_student_token}"} if insufficient_student_token else {}
    parent_headers = {"Authorization": f"Bearer {parent_token}"} if parent_token else {}
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"} if teacher_token else {}
    admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

    # Verify logins
    log_check("2. Student Login", student_token is not None)
    log_check("12. Parent Login", parent_token is not None)
    log_check("16. Teacher Login", teacher_token is not None)
    log_check("19. Admin Login", admin_token is not None)

    # If any login failed, exit early
    if not (student_token and parent_token and teacher_token and admin_token):
        print("[✘] Login credentials verification failed. Ensure backend server is running and seeded.")
        sys.exit(1)

    # 3. own overview
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/me/overview", headers=student_headers)
        log_check("3. Student Own Overview", res.status_code == 200 and "profile" in res.json()["data"])
    except Exception as e:
        log_check("3. Student Own Overview", False, str(e))

    # 4. own insights
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/me/insights", headers=student_headers)
        log_check("4. Student Own Insights", res.status_code == 200)
    except Exception as e:
        log_check("4. Student Own Insights", False, str(e))

    # 5. own risk assessment
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/me/risk-assessment", headers=student_headers)
        log_check("5. Student Own Risk Assessment", res.status_code == 200 and "factors" in res.json()["data"])
    except Exception as e:
        log_check("5. Student Own Risk Assessment", False, str(e))

    # 6. own recommendations
    rec_id = None
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/me/recommendations", headers=student_headers)
        recs = res.json()["data"]
        log_check("6. Student Own Recommendations", res.status_code == 200)
        if recs:
            rec_id = recs[0]["id"]
    except Exception as e:
        log_check("6. Student Own Recommendations", False, str(e))

    # 7. recommendation transition
    if rec_id:
        try:
            res = requests.patch(
                f"{BASE_URL}/api/v1/academic-mentor/me/recommendations/{rec_id}",
                headers=student_headers,
                json={"status": "ACCEPTED"}
            )
            log_check("7. Recommendation Transition", res.status_code == 200 and res.json()["data"]["status"] == "ACCEPTED")
        except Exception as e:
            log_check("7. Recommendation Transition", False, str(e))
    else:
        log_check("7. Recommendation Transition (Skip)", True, "No active recommendations to transition")

    # 8. study plans list
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/me/study-plans", headers=student_headers)
        log_check("8. Study Plans List", res.status_code == 200)
    except Exception as e:
        log_check("8. Study Plans List", False, str(e))

    # 9. create study plan
    try:
        plan_payload = {
            "title": "Study Plan Demo",
            "description": "Tutoring plan",
            "startDate": "2026-07-08T10:00:00Z",
            "endDate": "2026-07-15T10:00:00Z",
            "items": [
                {
                    "title": "Practice Problems",
                    "description": "Complete assignment 2 problems",
                    "scheduledDate": "2026-07-09T10:00:00Z",
                    "estimatedMinutes": 60
                }
            ]
        }
        res = requests.post(f"{BASE_URL}/api/v1/academic-mentor/me/study-plans", headers=student_headers, json=plan_payload)
        log_check("9. Create Study Plan", res.status_code == 200)
    except Exception as e:
        log_check("9. Create Study Plan", False, str(e))

    # 10. goals list
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/me/goals", headers=student_headers)
        log_check("10. Goals List", res.status_code == 200)
    except Exception as e:
        log_check("10. Goals List", False, str(e))

    # 11. create goal
    try:
        res = requests.post(
            f"{BASE_URL}/api/v1/academic-mentor/me/goals",
            headers=student_headers,
            json={"title": "Improve ML Score", "targetType": "MARKS", "targetValue": 85.0}
        )
        log_check("11. Create Goal", res.status_code == 200)
    except Exception as e:
        log_check("11. Create Goal", False, str(e))

    # Fetch student ID
    try:
        res_profile = requests.get(f"{BASE_URL}/api/v1/academic-mentor/me/overview", headers=student_headers)
        student_id = res_profile.json()["data"]["assessment"]["studentId"]
    except Exception:
        # Fallback to hardcoded seed user ID
        student_id = "student-a-uuid"

    # 13. linked children list
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/children", headers=parent_headers)
        log_check("13. Linked Children List", res.status_code == 200 and len(res.json()["data"]) > 0)
        linked_student_id = res.json()["data"][0]["id"]
    except Exception as e:
        linked_student_id = None
        log_check("13. Linked Children List", False, str(e))

    # 14. linked child overview
    if linked_student_id:
        try:
            res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/children/{linked_student_id}/overview", headers=parent_headers)
            log_check("14. Linked Child Overview", res.status_code == 200)
        except Exception as e:
            log_check("14. Linked Child Overview", False, str(e))
    else:
        log_check("14. Linked Child Overview (Skip)", True, "No child linked")

    # 15. unrelated child blocked (Using Student C)
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/children/student-c-uuid/overview", headers=parent_headers)
        log_check("15. Unrelated Child Blocked", res.status_code == 403)
    except Exception as e:
        log_check("15. Unrelated Child Blocked", False, str(e))

    # 17. scoped students list
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/students", headers=teacher_headers)
        log_check("17. Scoped Students List", res.status_code == 200 and len(res.json()["data"]) > 0)
    except Exception as e:
        log_check("17. Scoped Students List", False, str(e))

    # 18. unrelated student blocked (using a dummy ID)
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/students/unrelated-student-id/overview", headers=teacher_headers)
        log_check("18. Unrelated Student Blocked", res.status_code == 403 or res.status_code == 404)
    except Exception as e:
        log_check("18. Unrelated Student Blocked", False, str(e))

    # 20. admin analytics
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/analytics", headers=admin_headers)
        log_check("20. Admin Analytics Authorized", res.status_code == 200)
    except Exception as e:
        log_check("20. Admin Analytics Authorized", False, str(e))

    # 21. unauthorized bulk recalculation blocked
    try:
        res = requests.post(f"{BASE_URL}/api/v1/academic-mentor/recalculate", headers=student_headers)
        log_check("21. Unauthorized Recalculation Blocked", res.status_code == 403)
    except Exception as e:
        log_check("21. Unauthorized Recalculation Blocked", False, str(e))

    # 22. audit endpoint authorized
    try:
        res = requests.get(f"{BASE_URL}/api/v1/academic-mentor/audits", headers=admin_headers)
        log_check("22. Audit Endpoint Authorized", res.status_code == 200)
    except Exception as e:
        log_check("22. Audit Endpoint Authorized", False, str(e))

    # Summary
    passed_cnt = sum(1 for c in checks if c["passed"])
    total_cnt = len(checks)
    print(f"\nSmoke Test Summary: {passed_cnt}/{total_cnt} checks passed.")
    if passed_cnt == total_cnt:
        print("SUCCESS: Academic Mentor smoke test completed successfully.")
        sys.exit(0)
    else:
        print("ERROR: Academic Mentor smoke test failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()
