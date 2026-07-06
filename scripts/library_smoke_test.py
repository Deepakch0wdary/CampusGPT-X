# scripts/library_smoke_test.py
import sys
import requests

def run_smoke_tests():
    base_url = "http://127.0.0.1:8000"
    results = {}

    print("Running CampusGPT X Library API Smoke Tests...")

    # 1. Health
    try:
        res = requests.get(f"{base_url}/api/v1/health", timeout=5)
        results["Health Endpoint"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Health Endpoint"] = f"FAIL (Connection refused)"

    # 2. Get Branches
    try:
        res = requests.get(f"{base_url}/api/v1/library/branches", timeout=5)
        results["Get Branches List"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Get Branches List"] = f"FAIL (Connection refused)"

    # 3. List Books Catalog
    try:
        res = requests.get(f"{base_url}/api/v1/library/books", timeout=5)
        results["List Books Catalog"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["List Books Catalog"] = f"FAIL (Connection refused)"

    # 4. Protected Membership endpoint (without JWT)
    try:
        res = requests.get(f"{base_url}/api/v1/library/memberships", timeout=5)
        results["Memberships RBAC Protection"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Memberships RBAC Protection"] = f"FAIL (Connection refused)"

    # 5. Protected Analytics endpoint (without JWT)
    try:
        res = requests.get(f"{base_url}/api/v1/library/analytics", timeout=5)
        results["Analytics RBAC Protection"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Analytics RBAC Protection"] = f"FAIL (Connection refused)"

    # Print Report Matrix
    print("\n" + "="*50)
    print("LIBRARY API SMOKE TEST REPORT MATRIX")
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
        print("\nAll accessible Library API smoke tests PASSED successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_smoke_tests()
