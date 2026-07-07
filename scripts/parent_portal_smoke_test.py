import requests
import sys

def run_smoke_tests():
    base_url = "http://127.0.0.1:8000/api/v1"
    print("Starting Parent Portal programmatic API smoke check...")

    # 1. Login
    login_payload = {
        "username_or_email": "parent_demo",
        "password": "password"
    }
    res = requests.post(f"{base_url}/auth/login", json=login_payload)
    if res.status_code != 200:
        print(f"FAILED: Login failed with code {res.status_code}: {res.text}")
        sys.exit(1)

    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Success: Parent authenticated successfully.")

    # 2. Get children
    res = requests.get(f"{base_url}/parent/children", headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Get children returned {res.status_code}")
        sys.exit(1)

    children = res.json()
    print(f"Success: Retrieved {len(children)} linked children.")
    if len(children) == 0:
        print("FAILED: No children linked to the parent.")
        sys.exit(1)

    student_id = children[0]["id"]
    print(f"Testing endpoints for student ID: {student_id}")

    # 3. Test student-specific details endpoints
    endpoints = [
        ("overview", f"/parent/children/{student_id}/overview"),
        ("academics", f"/parent/children/{student_id}/academics"),
        ("attendance", f"/parent/children/{student_id}/attendance"),
        ("assignments", f"/parent/children/{student_id}/assignments"),
        ("exams", f"/parent/children/{student_id}/exams"),
        ("results", f"/parent/children/{student_id}/results"),
        ("fees", f"/parent/children/{student_id}/fees"),
        ("library", f"/parent/children/{student_id}/library"),
        ("hostel", f"/parent/children/{student_id}/hostel"),
        ("transport", f"/parent/children/{student_id}/transport"),
        ("alerts", f"/parent/alerts?studentId={student_id}")
    ]

    for name, path in endpoints:
        resp = requests.get(f"{base_url}{path}", headers=headers)
        if resp.status_code == 200:
            print(f"  OK: endpoint '{name}' returned 200")
        else:
            print(f"  FAILED: endpoint '{name}' returned {resp.status_code}: {resp.text}")
            sys.exit(1)

    # 4. Test Meetings, Consents, Preferences endpoints
    p_endpoints = [
        ("meetings list", "/parent/meetings"),
        ("consents list", "/parent/consents"),
        ("preferences GET", "/parent/notification-preferences")
    ]

    for name, path in p_endpoints:
        resp = requests.get(f"{base_url}{path}", headers=headers)
        if resp.status_code == 200:
            print(f"  OK: endpoint '{name}' returned 200")
        else:
            print(f"  FAILED: endpoint '{name}' returned {resp.status_code}: {resp.text}")
            sys.exit(1)

    # 5. Check preferences PUT endpoint
    pref_payload = {"attendanceAlerts": False}
    resp = requests.put(f"{base_url}/parent/notification-preferences", json=pref_payload, headers=headers)
    if resp.status_code == 200:
        print("  OK: endpoint 'preferences PUT' returned 200")
    else:
        print(f"  FAILED: endpoint 'preferences PUT' returned {resp.status_code}: {resp.text}")
        sys.exit(1)

    print("\nALL PARENT PORTAL PROGRAMMATIC SMOKE CHECKS PASSED SUCCESSFULLY (15/15 checks)!")

if __name__ == "__main__":
    run_smoke_tests()
