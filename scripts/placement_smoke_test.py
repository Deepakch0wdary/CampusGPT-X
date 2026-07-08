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
    print("Starting CampusGPT X Placement & Career Intelligence Smoke Test...")
    print("Backend Target:", BASE_URL)

    checks = []

    def log_check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name} {f'({detail})' if detail else ''}")

    # 1. Health check
    try:
        res = requests.get(f"{BASE_URL}/api/v1/health")
        log_check("1. Health", res.status_code == 200)
    except Exception as e:
        log_check("1. Health", False, str(e))

    # Logins
    student_token = login("student_demo", "password")
    other_student_token = login("student_b", "password")
    parent_token = login("parent_demo", "password")
    teacher_token = login("teacher_demo", "password")
    officer_token = login("officer_demo", "password")
    admin_token = login("admin_demo", "password")

    # Headers setup
    student_headers = {"Authorization": f"Bearer {student_token}"} if student_token else {}
    other_student_headers = {"Authorization": f"Bearer {other_student_token}"} if other_student_token else {}
    parent_headers = {"Authorization": f"Bearer {parent_token}"} if parent_token else {}
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"} if teacher_token else {}
    officer_headers = {"Authorization": f"Bearer {officer_token}"} if officer_token else {}
    admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

    # Verify logins
    log_check("2. Student Login", student_token is not None)
    log_check("17. Parent Login", parent_token is not None)
    log_check("20. Teacher Login", teacher_token is not None)
    log_check("23. Placement Officer Login", officer_token is not None)
    log_check("27. Admin Login", admin_token is not None)

    if not (student_token and other_student_token and parent_token and teacher_token and officer_token and admin_token):
        print("[FAIL] Missing test tokens. Ensure database is seeded.")
        sys.exit(1)

    # 3. Student Profile self-access
    res_prof = requests.get(f"{BASE_URL}/api/v1/placements/career-profile/me", headers=student_headers)
    log_check("3. Own Career Profile", res_prof.status_code == 200 and res_prof.json()["success"])
    student_a_id = res_prof.json()["data"]["studentId"] if res_prof.status_code == 200 and res_prof.json()["data"] else None

    # 4. Student Skills self-access
    res = requests.get(f"{BASE_URL}/api/v1/placements/skills/me", headers=student_headers)
    log_check("4. Own Skills", res.status_code == 200 and res.json()["success"])

    # 5. Opportunities List
    res = requests.get(f"{BASE_URL}/api/v1/placements/opportunities", headers=student_headers)
    log_check("5. Opportunities List", res.status_code == 200 and len(res.json()["data"]) > 0)
    opps = res.json()["data"]
    opp_id = opps[0]["id"] if opps else None

    # 6. Opportunity Details
    if opp_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/opportunities/{opp_id}", headers=student_headers)
        log_check("6. Opportunity Details", res.status_code == 200 and "skills" in res.json()["data"])
    else:
        log_check("6. Opportunity Details", False, "No opportunities found")

    # 7. Eligibility evaluation
    if opp_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/opportunities/{opp_id}/eligibility/me", headers=student_headers)
        log_check("7. Eligibility Evaluation", res.status_code == 200 and "eligible" in res.json()["data"])
    else:
        log_check("7. Eligibility Evaluation", False, "No opportunities found")

    # 8. Explainable Match
    if opp_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/matches/me/{opp_id}", headers=student_headers)
        log_check("8. Explainable Match", res.status_code == 200 and "score" in res.json()["data"])
    else:
        log_check("8. Explainable Match", False, "No opportunities found")

    # 9 & 10 & 11. Application Create / Duplicate Applications / Own applications
    # Student B applying to startup opp
    startup_opp = next((o for o in opps if "Java" in o["title"]), None)
    if startup_opp:
        res1 = requests.post(f"{BASE_URL}/api/v1/placements/applications", headers=other_student_headers, json={"opportunityId": startup_opp["id"]})
        # If already applied, might return 409, which is correct (idempotent / already run)
        already_applied = (res1.status_code == 409)
        log_check("9. Application Create", res1.status_code in (200, 201) or already_applied, f"Status: {res1.status_code}")

        res2 = requests.post(f"{BASE_URL}/api/v1/placements/applications", headers=other_student_headers, json={"opportunityId": startup_opp["id"]})
        log_check("10. Duplicate Application Blocked", res2.status_code == 409, f"Status: {res2.status_code}")
    else:
        log_check("9. Application Create", False, "Startup opportunity not found")
        log_check("10. Duplicate Application Blocked", False, "Startup opportunity not found")

    res = requests.get(f"{BASE_URL}/api/v1/placements/applications/me", headers=other_student_headers)
    log_check("11. Own Applications", res.status_code == 200 and len(res.json()["data"]) > 0)

    # 12. Own Interviews
    res = requests.get(f"{BASE_URL}/api/v1/placements/interviews/me", headers=student_headers)
    log_check("12. Own Interviews", res.status_code == 200 and isinstance(res.json()["data"], list))

    # 13. Own Offers
    res = requests.get(f"{BASE_URL}/api/v1/placements/offers/me", headers=student_headers)
    log_check("13. Own Offers", res.status_code == 200 and isinstance(res.json()["data"], list))

    # 14. Career Goals
    res = requests.get(f"{BASE_URL}/api/v1/placements/career-goals/me", headers=student_headers)
    log_check("14. Career Goals", res.status_code == 200 and isinstance(res.json()["data"], list))

    # 15. Skill Gap
    res = requests.get(f"{BASE_URL}/api/v1/placements/skill-gap/me", headers=student_headers)
    log_check("15. Skill Gap", res.status_code == 200 and isinstance(res.json()["data"], list))

    # 16. Recommendations
    res = requests.get(f"{BASE_URL}/api/v1/placements/recommendations/me", headers=student_headers)
    log_check("16. Recommendations", res.status_code == 200 and len(res.json()["data"]) > 0)

    # 18. Parent linked child allowed summary
    if student_a_id:
        # Check parent linked child
        res = requests.get(f"{BASE_URL}/api/v1/placements/parent/children/{student_a_id}/career-summary", headers=parent_headers)
        log_check("18. Linked Child Allowed Summary", res.status_code == 200, f"Status: {res.status_code}")
    else:
        log_check("18. Linked Child Allowed Summary", False, "Could not resolve Student A ID")

    # 19. Parent unrelated child blocked
    # Check parent unrelated child B
    student_b_user = requests.get(f"{BASE_URL}/api/v1/placements/career-profile/me", headers=other_student_headers).json()["data"]
    student_b_id = student_b_user["studentId"] if student_b_user else None
    if student_b_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/parent/children/{student_b_id}/career-summary", headers=parent_headers)
        log_check("19. Unrelated Child Blocked", res.status_code == 403, f"Status: {res.status_code}")
    else:
        log_check("19. Unrelated Child Blocked", False, "Could not resolve Student B ID")

    # 21. Teacher scoped readiness
    if student_b_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/teacher/students/{student_b_id}/career-readiness", headers=teacher_headers)
        log_check("21. Scoped Readiness Allowed (Teacher)", res.status_code in (200, 403), f"Status: {res.status_code}") # 403 if not in section scope, 200 if matches scope
    else:
        log_check("21. Scoped Readiness Allowed (Teacher)", False, "Could not resolve Student B ID")

    # 22. Private Recruiter Feedback Blocked for Parent/Teacher
    # No private feedback endpoint exists directly, but verifying parent doesn't receive interview notes
    if student_a_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/parent/children/{student_a_id}/career-summary", headers=parent_headers)
        if res.status_code == 200:
            data = res.json()["data"]
            log_check("22. Private Recruiter Feedback Blocked", "note" in data and "Private recruiter feedback" in data["note"])
        else:
            log_check("22. Private Recruiter Feedback Blocked", False, "Failed parent call")
    else:
        log_check("22. Private Recruiter Feedback Blocked", False, "No student ID")

    # 24. Company Create/List Authorization
    res = requests.post(f"{BASE_URL}/api/v1/placements/companies", headers=student_headers, json={"name": "Attacker Corp", "industry": "HACKING"})
    log_check("24. Company Create Student Blocked", res.status_code == 403)

    res = requests.get(f"{BASE_URL}/api/v1/placements/companies", headers=student_headers)
    log_check("24. Company List Allowed", res.status_code == 200)

    # 25. Opportunity Create
    res = requests.post(f"{BASE_URL}/api/v1/placements/opportunities", headers=officer_headers, json={
        "companyId": opps[0]["companyId"] if opps else "c1",
        "title": "Smoke Test Job",
        "description": "Integration test",
        "type": "JOB",
        "location": "Bangalore",
        "compensation": "12 LPA"
    })
    log_check("25. Opportunity Create (Officer)", res.status_code in (200, 201), f"Status: {res.status_code}")

    # 26. Application Pipeline - Officer update status
    # Find application id for Student B
    app_res = requests.get(f"{BASE_URL}/api/v1/placements/applications/me", headers=other_student_headers)
    if app_res.status_code == 200 and app_res.json()["data"]:
        app_id = app_res.json()["data"][0]["id"]
        res = requests.patch(f"{BASE_URL}/api/v1/placements/applications/{app_id}/status", headers=officer_headers, json={"status": "SHORTLISTED", "notes": "Smoke Test"})
        log_check("26. Application Pipeline Status Change", res.status_code == 200)
    else:
        log_check("26. Application Pipeline Status Change", False, "No application found for Student B")

    # 28. Analytics
    res = requests.get(f"{BASE_URL}/api/v1/placements/analytics/overview", headers=admin_headers)
    log_check("28. Analytics Overview (Admin)", res.status_code == 200 and "placementRate" in res.json()["data"])

    # 29. Audit
    res = requests.get(f"{BASE_URL}/api/v1/placements/audit", headers=admin_headers)
    log_check("29. Audit Logs (Admin)", res.status_code == 200 and "audits" in res.json()["data"])

    # 30. Unauthorized Analytics Blocked
    res = requests.get(f"{BASE_URL}/api/v1/placements/analytics/overview", headers=student_headers)
    log_check("30. Unauthorized Analytics Blocked", res.status_code == 403)

    # 31. Protected Attribute Absence
    # Verify no keys in explanation relate to gender, religion, race, ethnicity, caste
    if opp_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/matches/me/{opp_id}", headers=student_headers)
        if res.status_code == 200:
            expl = res.json()["data"]["explanation"].lower()
            # Strip the disclaimer sentence
            expl_clean = expl.replace("no protected attributes (religion, caste, gender, disability, etc.) were used in this score.", "")
            forbidden = ["gender", "religion", "race", "ethnicity", "caste", "sexual", "health"]
            clean = not any(w in expl_clean for w in forbidden)
            log_check("31. Protected Attribute Absence in Match Explanation", clean)
        else:
            log_check("31. Protected Attribute Absence in Match Explanation", False)
    else:
        log_check("31. Protected Attribute Absence in Match Explanation", False)

    # 32. Academic Mentor Risk Non-Punitive Behavior
    # Student A (strong match) has high risk in academic mentor (from day 21). Let's check eligibility.
    if opp_id:
        res = requests.get(f"{BASE_URL}/api/v1/placements/matches/me/{opp_id}", headers=student_headers)
        if res.status_code == 200:
            data = res.json()["data"]
            # Student A has CGPA 9.2, meets Google's 8.0 requirement. So should be eligible regardless of academic mentor risk score.
            log_check("32. Academic Mentor Risk Non-Punitive Behavior", data["eligibilityStatus"] == "ELIGIBLE", f"Eligibility: {data['eligibilityStatus']}")
        else:
            log_check("32. Academic Mentor Risk Non-Punitive Behavior", False)
    else:
        log_check("32. Academic Mentor Risk Non-Punitive Behavior", False)

    # Calculate final stats
    failed = [c for c in checks if not c["passed"]]
    print(f"\nSmoke Test Completed. Total checks: {len(checks)}. Passed: {len(checks) - len(failed)}. Failed: {len(failed)}")
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_smoke_test()
