# scripts/finance_smoke_test.py
import sys
import requests

def run_smoke_tests():
    base_url = "http://127.0.0.1:8000"
    results = {}

    print("Running CampusGPT X Finance API Smoke Tests...")

    # Helper helper login function
    def login_user(email, password):
        try:
            res = requests.post(f"{base_url}/api/v1/auth/login", json={
                "username_or_email": email,
                "password": password
            }, timeout=5)
            if res.status_code == 200:
                data = res.json()
                # If make_response is used, token could be inside "data"
                if "data" in data and "access_token" in data["data"]:
                    return data["data"]["access_token"]
                return data.get("access_token")
            return None
        except Exception:
            return None

    # 1. Health check
    try:
        res = requests.get(f"{base_url}/api/v1/health", timeout=5)
        results["1. Health Check"] = ("PASS" if res.status_code == 200 else f"FAIL ({res.status_code})")
    except Exception:
        results["1. Health Check"] = "FAIL (Connection refused)"

    # Login tokens
    finance_token = login_user("finance_fee@campusgpt.com", "FinancePassword@123")
    student_a_token = login_user("student_fee_a@campusgpt.com", "StudentPassword@123")
    student_b_token = login_user("student_fee_b@campusgpt.com", "StudentPassword@123")
    parent_token = login_user("parent_fee@campusgpt.com", "ParentPassword@123")

    results["2. Finance Officer Login"] = "PASS" if finance_token else "FAIL"
    results["3. Student A Login"] = "PASS" if student_a_token else "FAIL"
    results["4. Parent Login"] = "PASS" if parent_token else "FAIL"

    if not finance_token or not student_a_token:
        print("[!] Login failures. Ensure backend is running and seed was applied.")
        # Proceed with simulation of the remaining results as skips/fails to allow report generation
        results["5. Invoices List"] = "FAIL (No Token)"
    else:
        # 5. Student own invoices list
        headers_a = {"Authorization": f"Bearer {student_a_token}"}
        try:
            res = requests.get(f"{base_url}/api/v1/finance/invoices/me", headers=headers_a, timeout=5)
            results["5. Own Invoices List"] = "PASS" if res.status_code == 200 else f"FAIL ({res.status_code})"
            invoice_id = None
            if res.status_code == 200 and res.json().get("data"):
                invoice_id = res.json()["data"][0]["id"]
        except Exception:
            results["5. Own Invoices List"] = "FAIL"

        # 6. Invoice Details
        if invoice_id:
            try:
                res = requests.get(f"{base_url}/api/v1/finance/invoices/{invoice_id}", headers=headers_a, timeout=5)
                results["6. Invoice Details"] = "PASS" if res.status_code == 200 else f"FAIL ({res.status_code})"
            except Exception:
                results["6. Invoice Details"] = "FAIL"
        else:
            results["6. Invoice Details"] = "SKIP"

        # 7. Demo Payment
        if invoice_id:
            try:
                res = requests.post(f"{base_url}/api/v1/finance/payments/demo", headers=headers_a, json={
                    "invoiceId": invoice_id,
                    "amount": 100.00,
                    "method": "UPI",
                    "idempotencyKey": f"idem-smoke-{uuid_hash()}"
                }, timeout=5)
                if res.status_code == 200:
                    data = res.json()["data"]
                    is_simulated = (data.get("providerMode") == "SIMULATED_DEMO_PAYMENT_PROVIDER" and data.get("realMoneyMoved") is False)
                    results["7. Demo Payment (Simulated)"] = "PASS" if is_simulated else "FAIL"
                else:
                    results["7. Demo Payment (Simulated)"] = f"FAIL ({res.status_code})"
            except Exception:
                results["7. Demo Payment (Simulated)"] = "FAIL"
        else:
            results["7. Demo Payment (Simulated)"] = "SKIP"

        # 8. Parent Linked Child summary
        headers_p = {"Authorization": f"Bearer {parent_token}"}
        try:
            # First find linked child id
            res_child = requests.get(f"{base_url}/api/v1/finance/parent/children", headers=headers_p, timeout=5)
            child_id = None
            if res_child.status_code == 200 and res_child.json().get("data"):
                child_id = res_child.json()["data"][0]["id"]

            if child_id:
                res_sum = requests.get(f"{base_url}/api/v1/finance/parent/children/{child_id}/summary", headers=headers_p, timeout=5)
                results["8. Parent Linked Child View"] = "PASS" if res_sum.status_code == 200 else f"FAIL ({res_sum.status_code})"
            else:
                results["8. Parent Linked Child View"] = "FAIL (No linked child)"
        except Exception:
            results["8. Parent Linked Child View"] = "FAIL"

        # 9. Parent Unrelated Child Blocked
        try:
            # Student B is unrelated to Parent
            res_block = requests.get(f"{base_url}/api/v1/finance/parent/children/student_fee_b/summary", headers=headers_p, timeout=5)
            # Expecting 403 Forbidden or 404 (we filter link)
            results["9. Parent Unrelated Child Blocked"] = "PASS" if res_block.status_code in [403, 404] else f"FAIL ({res_block.status_code})"
        except Exception:
            results["9. Parent Unrelated Child Blocked"] = "FAIL"

        # 10. Admin Analytics
        headers_f = {"Authorization": f"Bearer {finance_token}"}
        try:
            res_an = requests.get(f"{base_url}/api/v1/finance/analytics/overview", headers=headers_f, timeout=5)
            results["10. Admin Analytics"] = "PASS" if res_an.status_code == 200 else f"FAIL ({res_an.status_code})"
        except Exception:
            results["10. Admin Analytics"] = "FAIL"

    # Print Report Matrix
    print("\n" + "="*50)
    print("FINANCE API SMOKE TEST REPORT MATRIX")
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
        print("\nAll Finance API smoke tests PASSED successfully!")
        sys.exit(0)

def uuid_hash():
    import uuid
    return uuid.uuid4().hex[:6]

if __name__ == "__main__":
    run_smoke_tests()
