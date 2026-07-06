import sys
import requests
import json

def run_smoke_tests():
    base_url = "http://127.0.0.1:8000"
    results = {}

    print("Running CampusGPT X API Smoke Tests...")
    print("Backend URL target:", base_url)

    # 1. Health check
    try:
        res = requests.get(f"{base_url}/api/v1/health", timeout=5)
        results["Health Check (/health)"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Health Check (/health)"] = f"FAIL (Connection refused: {e})"

    # 2. Docs verification
    try:
        res = requests.get(f"{base_url}/docs", timeout=5)
        results["Docs/Swagger Verification"] = ("PASS" if res.status_code == 200 else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Docs/Swagger Verification"] = f"FAIL (Connection refused)"

    # 3. Protected endpoint rejection (Without JWT)
    try:
        res = requests.get(f"{base_url}/api/v1/admissions", timeout=5)
        # Expected: 401 Unauthorized or 403 Forbidden since no token is passed
        results["Protected Route Guard (RBAC check)"] = ("PASS" if res.status_code in [401, 403] else f"FAIL (HTTP {res.status_code})")
    except Exception as e:
        results["Protected Route Guard (RBAC check)"] = f"FAIL (Connection refused)"

    # Print Report Matrix
    print("\n" + "="*50)
    print("API SMOKE TEST REPORT MATRIX")
    print("="*50)
    failed = False
    for test_name, status in results.items():
        print(f"{test_name:<40} : {status}")
        if "FAIL" in status:
            failed = True
    print("="*50)

    if failed:
        print("\nSmoke tests failed. Some backend components are unreachable.")
        sys.exit(1)
    else:
        print("\nAll accessible smoke tests PASSED successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_smoke_tests()
