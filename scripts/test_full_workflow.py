
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def log(msg):
    print(f"[TEST] {msg}")

def check(response, expected_status=200, context=""):
    if response.status_code != expected_status:
        log(f"FAILED {context}: Expected {expected_status}, got {response.status_code}")
        log(f"Response: {response.text}")
        sys.exit(1)
    return response.json()

def main():
    # 1. Login
    log("Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/token/", data={"username": USERNAME, "password": PASSWORD})
    check(resp, 200, "Login")
    data = resp.json()
    access_token = data.get("access") or data.get("data", {}).get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}
    log("Login success")

    # 2. Create Patient
    log("Creating patient...")
    patient_data = {
        "first_name": "Test",
        "last_name": "Workflow",
        "gender": "Male",
        "age_years": 30,
        "phone": "03001234567"
    }
    resp = requests.post(f"{BASE_URL}/patients/", json=patient_data, headers=headers)
    patient = check(resp, 201, "Create Patient")
    patient_id = patient.get("id") or patient.get("data", {}).get("id")
    log(f"Patient created: ID {patient_id}")

    # 3. Get a Test to order
    log("Fetching a test...")
    resp = requests.get(f"{BASE_URL}/laboratory/tests/", headers=headers, params={"limit": 1})
    tests = check(resp, 200, "Get Tests").get("results", [])
    if not tests:
        log("No tests found. Cannot proceed.")
        return
    test_id = tests[0]["id"]
    log(f"Using test ID {test_id}: {tests[0]['test_name']}")

    # 4. Create Order
    log("Creating order...")
    order_data = {
        "patient": patient_id,
        "test_ids": [test_id],
        "priority": "ROUTINE"
    }
    resp = requests.post(f"{BASE_URL}/orders/orders/", json=order_data, headers=headers)
    order = check(resp, 201, "Create Order")
    order_id = order.get("id")
    log(f"Order created: ID {order_id}")

    # 5. Get Samples
    log("Fetching samples...")
    resp = requests.get(f"{BASE_URL}/samples/", headers=headers, params={"order": order_id})
    samples = check(resp, 200, "Get Samples").get("results", [])
    if not samples:
        log("No samples generated for order!")
        return
    sample = samples[0]
    sample_id = sample["id"]
    log(f"Sample found: ID {sample_id}, Status: {sample['status']}")

    # 6. Postpone Sample
    log("Postponing sample...")
    resp = requests.patch(
        f"{BASE_URL}/samples/{sample_id}/", 
        json={"status": "POSTPONED", "postponement_reason": "Patient not ready"}, 
        headers=headers
    )
    sample = check(resp, 200, "Postpone Sample")
    if sample["status"] != "POSTPONED":
        log(f"Sample postponement failed. Status is {sample['status']}")
        sys.exit(1)
    log("Sample postponed successfully")

    # 7. Mark Collected
    log("Collecting sample...")
    resp = requests.patch(
        f"{BASE_URL}/samples/{sample_id}/", 
        json={"status": "COLLECTED", "barcode": f"SAM-{order_id}-01"}, 
        headers=headers
    )
    sample = check(resp, 200, "Collect Sample")
    if sample["status"] != "COLLECTED":
        log("Sample collection failed")
        sys.exit(1)
    log("Sample collected")

    # 8. Check if Results created (Draft)
    log("Checking for draft results...")
    # Get OrderItem ID
    order_item_id = sample["order_item"] 
    resp = requests.get(f"{BASE_URL}/results/", headers=headers, params={"order_item": order_item_id})
    results = check(resp, 200, "Get Results").get("results", [])
    if not results:
        log("No results created after collection!") # This verifies perform_update hook
        sys.exit(1)
    
    result = results[0]
    result_id = result["id"]
    log(f"Result found: ID {result_id}, Status: {result['status']}") # Should be DRAFT

    # 9. Enter Result
    log("Entering result...")
    # Assuming result_value expects a string
    resp = requests.patch(
        f"{BASE_URL}/results/{result_id}/",
        json={"result_value": "10.5", "status": "ENTERED"},
        headers=headers
    )
    result = check(resp, 200, "Enter Result")
    log(f"Result entered. Status: {result['status']}")

    # 10. Verify Result
    log("Verifying result...")
    resp = requests.post(f"{BASE_URL}/results/{result_id}/verify/", headers=headers)
    check(resp, 200, "Verify Result")
    log("Result verified")

    # 11. Check Report Generation
    log("Checking report...")
    resp = requests.get(f"{BASE_URL}/reports/", headers=headers, params={"order": order_id})
    reports = check(resp, 200, "Get Reports").get("results", [])
    if not reports:
        log("Report NOT generated automatically!")
        sys.exit(1)
    
    report = reports[0]
    log(f"Report found: ID {report['id']}, Status: {report['status']}")
    if not report['is_final']:
         log("Report is not marked as final/final status!")

    log("TEST SUCCESSFUL: Workflow verified.")

if __name__ == "__main__":
    main()
