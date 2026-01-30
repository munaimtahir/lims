#!/usr/bin/env python3
"""
LIMS v1.0 - Internal Smoke Test Script V2 (Contract Aware)
Tests all workflows end-to-end with tolerant key-name mapping via direct backend port.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
API_BASE = f"{BASE_URL}/api/v1"
ARTIFACTS_DIR = "_smoke_artifacts"

# Ensure artifacts dir exists
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Track test results
test_results = []
issues_found = []

# ID extraction helpers
def get_any(d, keys, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default

def get_test_id(obj):
    return get_any(obj, ["id", "test_id", "pk", "uuid"])

def get_param_id(obj):
    return get_any(obj, ["id", "parameter", "parameter_id", "param_id", "pk", "uuid"])

def log_test(step, result, message, details=None):
    """Log a test step result."""
    status_icon = "✅" if result == "PASS" else "❌"
    print(f"{status_icon} {step}: {message}")
    test_results.append({
        "step": step,
        "result": result,
        "message": message,
        "details": details
    })
    if result == "FAIL":
        issues_found.append(f"{step}: {message}")
        if details:
            redacted_details = str(details)
            for secret in ["token", "access", "password"]:
                if secret in redacted_details.lower():
                    redacted_details = "[REDACTED]"
            print(f"   Details: {redacted_details}")

def login(username, password, role_name):
    """Login and return auth token."""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login/",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            token = None
            if "data" in data:
                token = data["data"].get("access_token")
            else:
                token = data.get("access") or data.get("access_token")
            
            if token:
                log_test(f"AUTH-{role_name}", "PASS", f"Login successful for {username}")
                return token
            else:
                log_test(f"AUTH-{role_name}", "FAIL", f"Token not found in response for {username}")
                return None
        else:
            log_test(f"AUTH-{role_name}", "FAIL", f"Login failed for {username}: {response.status_code}")
            return None
    except Exception as e:
        log_test(f"AUTH-{role_name}", "FAIL", f"Login exception for {username}: {str(e)}")
        return None

def create_patient(token):
    """Create a patient and return patient ID."""
    try:
        payload = {
            "first_name": "InternalSmoke",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "phone": f"0311{datetime.now().strftime('%H%M%S%f')[:7]}"
        }
        response = requests.post(
            f"{API_BASE}/patients/",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        if response.status_code == 201:
            data = response.json()
            obj = data.get("data", data)
            patient_id = get_any(obj, ["id", "pk"])
            mrn = get_any(obj, ["patient_id", "mrn"])
            log_test("PATIENT-CREATE", "PASS", f"Patient created (ID: {patient_id}, MRN: {mrn})")
            return patient_id, mrn
        else:
            log_test("PATIENT-CREATE", "FAIL", f"Failed to create patient: {response.status_code}", response.text)
            return None, None
    except Exception as e:
        log_test("PATIENT-CREATE", "FAIL", f"Exception: {str(e)}")
        return None, None

def get_available_tests(token):
    """Get list of available tests."""
    try:
        response = requests.get(
            f"{API_BASE}/laboratory/tests/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            tests = data.get("results", data) if isinstance(data, dict) else data
            test_ids = [get_test_id(t) for t in tests[:2]] if len(tests) >= 2 else []
            log_test("TEST-LIST", "PASS", f"Found {len(tests)} tests, using IDs: {test_ids}")
            return test_ids
        else:
            log_test("TEST-LIST", "FAIL", f"Failed to get tests: {response.status_code}")
            return []
    except Exception as e:
        log_test("TEST-LIST", "FAIL", f"Exception: {str(e)}")
        return []

def create_order(token, patient_id, test_ids):
    """Create order with tests and return order ID."""
    try:
        response = requests.post(
            f"{API_BASE}/orders/orders/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "patient": patient_id,
                "test_ids": test_ids,
                "status": "NEW"
            }
        )
        if response.status_code == 201:
            data = response.json()
            order_id = get_any(data, ["id", "pk"])
            order_number = get_any(data, ["order_id", "order_number"])
            items = data.get("items", [])
            log_test("ORDER-CREATE", "PASS", f"Order created (ID: {order_id}, Number: {order_number}, Items: {len(items)})")
            return order_id, data
        else:
            log_test("ORDER-CREATE", "FAIL", f"Failed to create order: {response.status_code}", response.text)
            return None, None
    except Exception as e:
        log_test("ORDER-CREATE", "FAIL", f"Exception: {str(e)}")
        return None, None

def verify_samples_auto_created(token, order_id, expected_count):
    """Verify samples were auto-created."""
    try:
        response = requests.get(
            f"{API_BASE}/samples/?order_item__order={order_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            samples = data.get("results", data) if isinstance(data, dict) else data
            sample_count = len(samples)
            if sample_count == expected_count:
                log_test("REGRESSION-ISSUE1", "PASS", f"Samples auto-created ({sample_count}/{expected_count})")
                return samples
            else:
                log_test("REGRESSION-ISSUE1", "FAIL", f"Expected {expected_count}, found {sample_count}")
                return []
        else:
            log_test("REGRESSION-ISSUE1", "FAIL", f"Failed: {response.status_code}")
            return []
    except Exception as e:
        log_test("REGRESSION-ISSUE1", "FAIL", f"Exception: {str(e)}")
        return []

def get_test_parameters(token, test_id):
    """Get parameters for a test."""
    try:
        response = requests.get(
            f"{API_BASE}/laboratory/parameters/?test={test_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            params = data.get("results", data) if isinstance(data, dict) else data
            log_test("TEST-PARAMS", "PASS", f"Found {len(params)} parameters")
            return params
        else:
            log_test("TEST-PARAMS", "FAIL", f"Failed: {response.status_code}")
            return []
    except Exception as e:
        log_test("TEST-PARAMS", "FAIL", f"Exception: {str(e)}")
        return []

def collect_sample(token, sample_id):
    """Mark sample as collected."""
    try:
        response = requests.patch(
            f"{API_BASE}/samples/{sample_id}/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "status": "COLLECTED",
                "barcode": f"BARCODE-{sample_id}-{datetime.now().strftime('%H%M%S')}"
            }
        )
        if response.status_code == 200:
            log_test("SAMPLE-COLLECT", "PASS", f"Sample {sample_id} collected")
            return True
        else:
            log_test("SAMPLE-COLLECT", "FAIL", f"Failed: {response.status_code}")
            return False
    except Exception as e:
        log_test("SAMPLE-COLLECT", "FAIL", f"Exception: {str(e)}")
        return False

def enter_result_bulk(token, order_item_id, test_parameter_id, value):
    """Enter result via bulk_entry."""
    try:
        response = requests.post(
            f"{API_BASE}/results/bulk_entry/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "results": [
                    {
                        "order_item": order_item_id,
                        "test_parameter": test_parameter_id,
                        "result_value": str(value),
                        "remarks": "Internal smoke v2"
                    }
                ]
            }
        )
        if response.status_code == 201:
            data = response.json()
            results = data.get("results", [])
            if results:
                result_id = get_any(results[0], ["id", "pk"])
                log_test("RESULT-ENTRY", "PASS", f"Result entered (ID: {result_id})")
                return result_id
            return None
        else:
            log_test("RESULT-ENTRY", "FAIL", f"Failed: {response.status_code}")
            return None
    except Exception as e:
        log_test("RESULT-ENTRY", "FAIL", f"Exception: {str(e)}")
        return None

def verify_result(token, result_id):
    """Verify a result."""
    try:
        response = requests.post(
            f"{API_BASE}/results/{result_id}/verify/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            log_test("RESULT-VERIFY", "PASS", f"Result {result_id} verified")
            return True
        else:
            log_test("RESULT-VERIFY", "FAIL", f"Failed: {response.status_code}")
            return False
    except Exception as e:
        log_test("RESULT-VERIFY", "FAIL", f"Exception: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("LIMS v1.0 - INTERNAL SMOKE TEST V2 (CONTRACT AWARE)")
    print("=" * 80)
    print(f"Target: {BASE_URL}")
    
    admin_token = login("admin", "admin123", "Admin")
    receptionist_token = login("receptionist", "recep123", "Receptionist")
    phlebotomist_token = login("phlebotomist", "phleb123", "Phlebotomist")
    labtech_token = login("labtech", "labtech123", "LabTech")
    pathologist_token = login("pathologist", "patho123", "Pathologist")
    
    if not all([admin_token, receptionist_token, phlebotomist_token, labtech_token, pathologist_token]):
        print("❌ Critical Auth Failure")
        return False

    patient_id, mrn = create_patient(receptionist_token)
    if not patient_id: return False
    
    test_ids = get_available_tests(receptionist_token)
    if not test_ids: return False
    
    order_id, order_data = create_order(receptionist_token, patient_id, test_ids)
    if not order_id: return False
    
    items = order_data.get("items", [])
    samples = verify_samples_auto_created(receptionist_token, order_id, len(items))
    if not samples: return False
    
    sample_id = get_any(samples[0], ["id", "pk"])
    if not collect_sample(phlebotomist_token, sample_id): return False
    
    order_item_id = get_any(items[0], ["id", "pk"])
    # For order items, the 'test' key is the actual test ID. 'id' is order_item_id.
    test_id = get_any(items[0], ["test", "test_id"])
    
    params = get_test_parameters(labtech_token, test_id)
    if not params: return False
    
    param_id = get_param_id(params[0])
    result_id = enter_result_bulk(labtech_token, order_item_id, param_id, "9.9")
    if not result_id: return False
    
    if not verify_result(pathologist_token, result_id): return False
    
    print("\n" + "=" * 80)
    print("✅ INTERNAL SMOKE TEST V2 PASSED")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
