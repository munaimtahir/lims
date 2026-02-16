#!/usr/bin/env python3
"""
End-to-end workflow test for LIMS
Tests: Login → Register Patient → Create Order (Albumin Rs 500) → Sample Collection → Result Entry → Verification → PDF Report
"""

import json
import sys
import requests
from datetime import date, timedelta
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8012"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

# Calculate DOB for age 35 (approximately)
dob_date = date.today() - timedelta(days=35*365)
TEST_PATIENT = {
    "full_name": "Test Patient Albumin",
    "date_of_birth": dob_date.isoformat(),  # Format: YYYY-MM-DD
    "gender": "Male",
    "phone": "0300-0000000",
}

# Execution log
execution_log = []

def log_step(step: str, status: str, details: str = "", data: Any = None):
    """Log a test step."""
    entry = {
        "step": step,
        "status": status,
        "details": details,
        "data": data
    }
    execution_log.append(entry)
    print(f"[{status}] {step}: {details}")
    if data:
        print(f"  Data: {json.dumps(data, indent=2, default=str)}")

def get_auth_token(username: str, password: str) -> Optional[str]:
    """Login and get JWT token."""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login/",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("data", {}).get("access_token")
            log_step(f"Login ({username})", "PASS", f"Status: {response.status_code}", {"user": username})
            return token
        else:
            log_step(f"Login ({username})", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_step(f"Login ({username})", "FAIL", f"Exception: {str(e)}")
        return None

def check_albumin_test(token: str) -> Optional[Dict]:
    """Check if Albumin test exists and verify price."""
    try:
        # Search for Albumin test
        response = requests.get(
            f"{API_BASE}/laboratory/tests/",
            headers={"Authorization": f"Bearer {token}"},
            params={"search": "Albumin"}
        )
        if response.status_code == 200:
            data = response.json()
            tests = data.get("results", []) if isinstance(data, dict) and "results" in data else (data if isinstance(data, list) else [])
            
            albumin = None
            for test in tests:
                if "albumin" in test.get("test_name", "").lower() or "albumin" in test.get("test_code", "").lower():
                    albumin = test
                    break
            
            if albumin:
                price = float(albumin.get("price", 0))
                is_active = albumin.get("is_active", False)
                test_id = albumin.get("test_id") or albumin.get("id")
                
                log_step("Check Albumin Test", "PASS" if price == 500 and is_active else "FAIL",
                        f"Found: {albumin.get('test_name')}, Price: Rs {price}, Active: {is_active}",
                        albumin)
                return albumin if price == 500 and is_active else None
            else:
                log_step("Check Albumin Test", "FAIL", "Albumin test not found")
                return None
        else:
            log_step("Check Albumin Test", "FAIL", f"API Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        log_step("Check Albumin Test", "FAIL", f"Exception: {str(e)}")
        return None

def create_albumin_test(token: str) -> Optional[Dict]:
    """Create Albumin test with price 500."""
    try:
        # First get categories
        response = requests.get(
            f"{API_BASE}/laboratory/categories/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            log_step("Create Albumin Test", "FAIL", f"Failed to get categories: {response.status_code}")
            return None
        
        categories = response.json()
        chemistry_cat = None
        for cat in (categories.get("results", []) if isinstance(categories, dict) else categories):
            if "chemistry" in cat.get("name", "").lower():
                chemistry_cat = cat
                break
        
        if not chemistry_cat:
            log_step("Create Albumin Test", "FAIL", "Clinical Chemistry category not found")
            return None
        
        # Create parameter for Albumin
        param_response = requests.post(
            f"{API_BASE}/laboratory/parameters/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parameter_id": "p_albumin",
                "parameter_name": "Albumin",
                "unit": "g/dL"
            }
        )
        param_id = None
        if param_response.status_code in [200, 201]:
            param_data = param_response.json()
            param_id = param_data.get("parameter_id") or param_data.get("id")
        elif param_response.status_code == 400:
            # Parameter might already exist, try to get it
            param_get = requests.get(
                f"{API_BASE}/laboratory/parameters/",
                headers={"Authorization": f"Bearer {token}"},
                params={"search": "Albumin"}
            )
            if param_get.status_code == 200:
                params = param_get.json()
                param_list = params.get("results", []) if isinstance(params, dict) else params
                for p in param_list:
                    if "albumin" in p.get("parameter_name", "").lower():
                        param_id = p.get("parameter_id") or p.get("id")
                        break
        
        # Create test
        test_data = {
            "test_code": "ALBUMIN",
            "test_name": "Albumin",
            "category": chemistry_cat.get("id") or chemistry_cat.get("category_id"),
            "sample_type": "Serum",
            "price": "500.00",
            "turnaround_time": 24,
            "is_active": True
        }
        
        response = requests.post(
            f"{API_BASE}/laboratory/tests/",
            headers={"Authorization": f"Bearer {token}"},
            json=test_data
        )
        
        if response.status_code in [200, 201]:
            test = response.json()
            log_step("Create Albumin Test", "PASS", f"Created: {test.get('test_name')}, Price: Rs {test.get('price')}", test)
            
            # Create parameter mapping if parameter exists
            if param_id and test.get("test_id") or test.get("id"):
                test_id = test.get("test_id") or test.get("id")
                mapping_response = requests.post(
                    f"{API_BASE}/laboratory/test-parameters/",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "test": test_id,
                        "parameter": param_id,
                        "display_order": 1,
                        "reportable": True
                    }
                )
                if mapping_response.status_code in [200, 201]:
                    log_step("Create Albumin Parameter Mapping", "PASS", "Parameter mapped to test")
            
            return test
        else:
            log_step("Create Albumin Test", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_step("Create Albumin Test", "FAIL", f"Exception: {str(e)}")
        return None

def register_patient(token: str) -> Optional[Dict]:
    """Register a new patient."""
    try:
        response = requests.post(
            f"{API_BASE}/patients/",
            headers={"Authorization": f"Bearer {token}"},
            json=TEST_PATIENT
        )
        if response.status_code in [200, 201]:
            patient = response.json()
            log_step("Register Patient", "PASS", 
                    f"Patient created: {patient.get('name')}, ID: {patient.get('patient_id') or patient.get('id')}",
                    patient)
            return patient
        else:
            log_step("Register Patient", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_step("Register Patient", "FAIL", f"Exception: {str(e)}")
        return None

def create_order(token: str, patient_id: int, test_id: int) -> Optional[Dict]:
    """Create an order with Albumin test."""
    try:
        # Order schema: patient (int), test_ids (list[int]), panel_ids (optional list[int])
        order_data = {
            "patient": patient_id,
            "test_ids": [test_id],  # Correct field name: test_ids not tests
        }
        
        response = requests.post(
            f"{API_BASE}/orders/orders/",  # Correct endpoint: /orders/orders/
            headers={"Authorization": f"Bearer {token}"},
            json=order_data
        )
        
        if response.status_code in [200, 201]:
            order = response.json()
            total_amount = order.get("total_amount", 0)
            order_id = order.get("order_id") or order.get("id")
            receipt_number = order.get("receipt_number") or order.get("receipt_no")
            
            log_step("Create Order", "PASS" if total_amount == 500 else "FAIL",
                    f"Order created: ID={order_id}, Receipt={receipt_number}, Total=Rs {total_amount}",
                    order)
            return order
        else:
            log_step("Create Order", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_step("Create Order", "FAIL", f"Exception: {str(e)}")
        return None

def main():
    """Run the complete workflow test."""
    print("=" * 80)
    print("LIMS End-to-End Workflow Test")
    print("=" * 80)
    print()
    
    # Step 1: Login as admin
    admin_token = get_auth_token(ADMIN_CREDENTIALS["username"], ADMIN_CREDENTIALS["password"])
    if not admin_token:
        print("\n❌ Failed to login as admin. Cannot proceed.")
        return
    
    # Step 2: Check/Create Albumin test
    albumin_test = check_albumin_test(admin_token)
    if not albumin_test:
        print("\n⚠️  Albumin test not found or price incorrect. Attempting to create...")
        albumin_test = create_albumin_test(admin_token)
        if not albumin_test:
            print("\n❌ Failed to create Albumin test. Cannot proceed.")
            return
    
    # Step 3: Register patient
    patient = register_patient(admin_token)
    if not patient:
        print("\n❌ Failed to register patient. Cannot proceed.")
        return
    
    patient_id = patient.get("patient_id") or patient.get("id")
    test_id = albumin_test.get("test_id") or albumin_test.get("id")
    
    # Step 4: Create order
    order = create_order(admin_token, patient_id, test_id)
    if not order:
        print("\n❌ Failed to create order. Cannot proceed.")
        return
    
    order_id = order.get("order_id") or order.get("id")
    
    print("\n" + "=" * 80)
    print("WORKFLOW EXECUTION LOG")
    print("=" * 80)
    for entry in execution_log:
        status_icon = "✅" if entry["status"] == "PASS" else "❌"
        print(f"{status_icon} {entry['step']}: {entry['details']}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Patient ID: {patient_id}")
    print(f"Order ID: {order_id}")
    print(f"Albumin Test ID: {test_id}")
    print(f"Order Total: Rs {order.get('total_amount', 'N/A')}")
    print("\n⚠️  Note: Sample collection, result entry, verification, and PDF generation")
    print("    require UI interaction. Use the IDs above to continue in the frontend.")
    
    # Save execution log
    with open("/tmp/lims_e2e_log.json", "w") as f:
        json.dump(execution_log, f, indent=2, default=str)
    print(f"\n📝 Full log saved to: /tmp/lims_e2e_log.json")

if __name__ == "__main__":
    main()
