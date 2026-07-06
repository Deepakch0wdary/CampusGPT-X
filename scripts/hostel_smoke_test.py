# scripts/hostel_smoke_test.py
import sys
import requests

def run_smoke_tests():
    base_url = "http://127.0.0.1:8000"
    results = {}

    print("Running CampusGPT X Hostel API Smoke Tests...")

    # 1. Health
    try:
        res = requests.get(f"{base_url}/api/v1/health", timeout=5)
        results["Health Endpoint"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Health Endpoint"] = f"FAIL (Connection refused)"

    # 2. Get Hostels List (Public Catalog)
    try:
        res = requests.get(f"{base_url}/api/v1/hostel/hostels", timeout=5)
        results["Hostels Catalog Listing"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Hostels Catalog Listing"] = f"FAIL (Connection refused)"

    # 3. Create Hostel (Protected Writes)
    try:
        res = requests.post(f"{base_url}/api/v1/hostel/hostels", json={"name": "Smoke Test Hostel", "code": "SMOKE-1", "hostelType": "BOYS", "capacity": 10}, timeout=5)
        results["Hostel Creation RBAC Protection"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Hostel Creation RBAC Protection"] = f"FAIL (Connection refused)"

    # 4. Get Visitors Log without JWT (Protected)
    try:
        res = requests.get(f"{base_url}/api/v1/hostel/visitors", timeout=5)
        results["Visitors Log RBAC Protection"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Visitors Log RBAC Protection"] = f"FAIL (Connection refused)"

    # 5. Get Fines without JWT (Protected)
    try:
        res = requests.get(f"{base_url}/api/v1/hostel/fines", timeout=5)
        results["Fines Ledger RBAC Protection"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Fines Ledger RBAC Protection"] = f"FAIL (Connection refused)"

    # Print Report Matrix
    print("\n" + "="*50)
    print("HOSTEL API SMOKE TEST REPORT MATRIX")
    print("="*50)
    failed = False
    for test_name, status in results.items():
        print(f"{test_name:<40} : {status}")
        if "FAIL" in status:
            failed = True
    print("="*50)

    if failed:
        print("\nSmoke tests failed. Some API endpoints did not behave as expected.")
        sys.exit(1)
    else:
        print("\nAll accessible Hostel API smoke tests PASSED successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_smoke_tests()
