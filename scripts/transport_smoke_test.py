# scripts/transport_smoke_test.py
import sys
import requests

def run_smoke_tests():
    base_url = "http://127.0.0.1:8000"
    results = {}

    print("Running CampusGPT X Smart Transport API Smoke Tests...")

    # 1. Health Endpoint
    try:
        res = requests.get(f"{base_url}/api/v1/health", timeout=5)
        results["1. Health Endpoint"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["1. Health Endpoint"] = f"FAIL (Connection refused: {e})"

    # 2. Vehicles Listing (Unauthorized)
    try:
        res = requests.get(f"{base_url}/api/v1/transport/vehicles", timeout=5)
        results["2. Vehicles Listing RBAC Protection"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["2. Vehicles Listing RBAC Protection"] = f"FAIL (Connection refused)"

    # 3. Create Vehicle (Unauthorized)
    try:
        res = requests.post(f"{base_url}/api/v1/transport/vehicles", json={"vehicleCode": "BUS-SMOKE"}, timeout=5)
        results["3. Vehicle Creation RBAC Protection"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["3. Vehicle Creation RBAC Protection"] = f"FAIL (Connection refused)"

    # Authenticate as Admin to get Token
    token = None
    passwords_to_try = ["AdminPassword@123", "password"]
    login_error_detail = ""
    for pwd in passwords_to_try:
        try:
            res = requests.post(f"{base_url}/api/v1/auth/login", json={
                "username_or_email": "admin",
                "password": pwd
            }, timeout=5)
            if res.status_code == 200:
                token = res.json().get("access_token")
                results["4. Admin Authentication"] = "PASS"
                break
            else:
                login_error_detail = f"HTTP {res.status_code}"
        except Exception as e:
            login_error_detail = f"Connection error: {e}"

    if not token:
        results["4. Admin Authentication"] = f"FAIL ({login_error_detail})"

    if not token:
        print("Could not obtain admin access token. Skipping authenticated checks.")
    else:
        headers = {"Authorization": f"Bearer {token}"}

        # 5. Dashboard Metrics (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/dashboard", headers=headers, timeout=5)
            results["5. Dashboard Metrics API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["5. Dashboard Metrics API"] = f"FAIL ({e})"

        # 6. Vehicles Directory (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/vehicles", headers=headers, timeout=5)
            results["6. Vehicles Directory API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["6. Vehicles Directory API"] = f"FAIL ({e})"

        # 7. Routes Directory (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/routes", headers=headers, timeout=5)
            results["7. Routes Directory API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["7. Routes Directory API"] = f"FAIL ({e})"

        # 8. Stops Directory (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/stops", headers=headers, timeout=5)
            results["8. Stops Directory API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["8. Stops Directory API"] = f"FAIL ({e})"

        # 9. Applications Queue (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/applications", headers=headers, timeout=5)
            results["9. Pass Applications Queue API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["9. Pass Applications Queue API"] = f"FAIL ({e})"

        # 10. Subscriptions (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/subscriptions", headers=headers, timeout=5)
            results["10. Pass Subscriptions Listing API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["10. Pass Subscriptions Listing API"] = f"FAIL ({e})"

        # 11. Scheduled Trips (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/trips", headers=headers, timeout=5)
            results["11. Trips Dispatch Listing API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["11. Trips Dispatch Listing API"] = f"FAIL ({e})"

        # 12. Maintenance (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/maintenance", headers=headers, timeout=5)
            results["12. Maintenance Records API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["12. Maintenance Records API"] = f"FAIL ({e})"

        # 13. Fuel logs (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/fuel-logs", headers=headers, timeout=5)
            results["13. Fuel Logs API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["13. Fuel Logs API"] = f"FAIL ({e})"

        # 14. Incidents (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/incidents", headers=headers, timeout=5)
            results["14. Incidents Log API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["14. Incidents Log API"] = f"FAIL ({e})"

        # 15. Analytics (Authenticated)
        try:
            res = requests.get(f"{base_url}/api/v1/transport/analytics", headers=headers, timeout=5)
            results["15. Transport Analytics API"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
        except Exception as e:
            results["15. Transport Analytics API"] = f"FAIL ({e})"

    # Print Report Matrix
    print("\n" + "="*55)
    print("TRANSPORT API SMOKE TEST REPORT MATRIX")
    print("="*55)
    failed = False
    for test_name, status in results.items():
        print(f"{test_name:<42} : {status}")
        if "FAIL" in status:
            failed = True
    print("="*55)

    if failed:
        print("\nSmoke tests failed. Some API endpoints did not behave as expected.")
        sys.exit(1)
    else:
        print("\nAll accessible Transport API smoke tests PASSED successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_smoke_tests()
