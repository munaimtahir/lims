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
    "phone": "03001234567",  # Valid Pakistani mobile format: 0 followed by 3 and 9 digits
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
            response_data = response.json()
            # Handle wrapped response format
            data = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
            tests = data.get("results", []) if isinstance(data, dict) and "results" in data else (data if isinstance(data, list) else [])
            
            albumin = None
            for test in tests:
                if "albumin" in test.get("test_name", "").lower() or "albumin" in test.get("test_code", "").lower():
                    albumin = test
                    break
            
            if albumin:
                price = float(albumin.get("price", 0))
                is_active = albumin.get("is_active", False)
                # Test ID: use id field (test_id is an alias property)
                test_id = albumin.get("id") or albumin.get("test_id")
                
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
        
        response_data = response.json()
        # Handle wrapped response format
        categories = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
        cat_list = categories.get("results", []) if isinstance(categories, dict) and "results" in categories else (categories if isinstance(categories, list) else [])
        chemistry_cat = None
        for cat in cat_list:
            if "chemistry" in cat.get("name", "").lower():
                chemistry_cat = cat
                break
        # Fallback: use first available category, or create "Clinical Chemistry" if none exist
        if not chemistry_cat and cat_list:
            chemistry_cat = cat_list[0]
            log_step("Create Albumin Test", "INFO", f"Using first available category: {chemistry_cat.get('name')}")
        
        if not chemistry_cat:
            # Create a category so we can create the test (e.g. fresh DB)
            create_cat = requests.post(
                f"{API_BASE}/laboratory/categories/",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Clinical Chemistry", "is_active": True}
            )
            if create_cat.status_code in [200, 201]:
                cat_data = create_cat.json()
                chemistry_cat = cat_data.get("data", cat_data) if isinstance(cat_data, dict) and "data" in cat_data else cat_data
                log_step("Create Albumin Test", "INFO", f"Created category: {chemistry_cat.get('name')}")
            else:
                log_step("Create Albumin Test", "FAIL", f"No category and failed to create one: {create_cat.status_code}")
                return None
        
        if not chemistry_cat:
            log_step("Create Albumin Test", "FAIL", "No test category found.")
            return None
        
        # Create parameter (analyte) for Albumin (parameter_id must be format p<number>)
        # Find next available parameter ID
        param_list_response = requests.get(
            f"{API_BASE}/laboratory/analytes/",
            headers={"Authorization": f"Bearer {token}"}
        )
        max_param_num = 0
        if param_list_response.status_code == 200:
            params_data = param_list_response.json()
            params_list = params_data.get("results", []) if isinstance(params_data, dict) and "results" in params_data else (params_data if isinstance(params_data, list) else [])
            for p in params_list:
                param_id_str = p.get("parameter_id", "")
                if param_id_str and param_id_str.startswith("p") and param_id_str[1:].isdigit():
                    max_param_num = max(max_param_num, int(param_id_str[1:]))
        next_param_id = f"p{max_param_num + 1}"
        
        param_response = requests.post(
            f"{API_BASE}/laboratory/analytes/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parameter_id": next_param_id,  # Must be format p<number>
                "parameter_name": "Albumin",
                "unit": "g/dL"
            }
        )
        param_id = None
        if param_response.status_code in [200, 201]:
            param_data = param_response.json()
            # Handle wrapped response format
            param_obj = param_data.get("data", param_data) if isinstance(param_data, dict) and "data" in param_data else param_data
            param_id = param_obj.get("parameter_id") or param_obj.get("id")
        elif param_response.status_code == 400:
            # Parameter might already exist, try to get it
            param_get = requests.get(
                f"{API_BASE}/laboratory/analytes/",
                headers={"Authorization": f"Bearer {token}"},
                params={"search": "Albumin"}
            )
            if param_get.status_code == 200:
                params = param_get.json()
                param_list = params.get("results", []) if isinstance(params, dict) and "results" in params else (params if isinstance(params, list) else [])
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
            response_data = response.json()
            # Handle wrapped response format
            test = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
            log_step("Create Albumin Test", "PASS", f"Created: {test.get('test_name')}, Price: Rs {test.get('price')}", test)
            
            # Create test-parameter mapping if parameter exists
            # Endpoint: /laboratory/parameters/ (TestParameterViewSet)
            if param_id and (test.get("test_id") or test.get("id")):
                test_id = test.get("test_id") or test.get("id")
                # Handle wrapped response format for test
                test_obj = test.get("data", test) if isinstance(test, dict) and "data" in test else test
                test_id = test_obj.get("test_id") or test_obj.get("id") or test_id
                
                mapping_response = requests.post(
                    f"{API_BASE}/laboratory/parameters/",
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
                else:
                    log_step("Create Albumin Parameter Mapping", "FAIL", 
                            f"Status: {mapping_response.status_code}, Response: {mapping_response.text}")
            
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
        # Patient schema: full_name (or first_name/last_name), date_of_birth (YYYY-MM-DD), gender, phone
        response = requests.post(
            f"{API_BASE}/patients/",
            headers={"Authorization": f"Bearer {token}"},
            json=TEST_PATIENT
        )
        if response.status_code in [200, 201]:
            response_data = response.json()
            # Handle both wrapped and direct response formats
            patient = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
            patient_name = patient.get("full_name") or f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            # Store both ID and patient_id for logging
            patient_db_id = patient.get("id")
            patient_id_str = patient.get("patient_id") or patient.get("mrn")
            log_step("Register Patient", "PASS", 
                    f"Patient created: {patient_name}, DB ID: {patient_db_id}, Patient ID: {patient_id_str}",
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
            f"{API_BASE}/orders/orders/",  # Endpoint: /api/v1/orders/orders/ (router basename="order")
            headers={"Authorization": f"Bearer {token}"},
            json=order_data
        )
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            # Handle wrapped response format
            order = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
            total_amount = float(order.get("total_amount", 0))
            order_id = order.get("order_id") or order.get("id")
            
            log_step("Create Order", "PASS" if total_amount == 500 else "FAIL",
                    f"Order created: ID={order_id}, Total=Rs {total_amount}",
                    order)
            return order
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = json.dumps(error_json, indent=2)
            except:
                pass
            log_step("Create Order", "FAIL", f"Status: {response.status_code}, Response: {error_detail}")
            return None
    except Exception as e:
        log_step("Create Order", "FAIL", f"Exception: {str(e)}")
        return None

def get_order_items(token: str, order_id: int) -> Optional[list]:
    """Get order items for an order."""
    try:
        response = requests.get(
            f"{API_BASE}/orders/order-items/",
            headers={"Authorization": f"Bearer {token}"},
            params={"order": order_id}
        )
        if response.status_code == 200:
            response_data = response.json()
            # Handle wrapped response format
            data = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
            items = data.get("results", []) if isinstance(data, dict) and "results" in data else (data if isinstance(data, list) else [])
            return items
        return None
    except Exception as e:
        log_step("Get Order Items", "FAIL", f"Exception: {str(e)}")
        return None

def get_test_parameter(token: str, test_id: int) -> Optional[int]:
    """Get test parameter ID for a test."""
    try:
        # Get test details
        response = requests.get(
            f"{API_BASE}/laboratory/tests/{test_id}/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            response_data = response.json()
            # Handle wrapped response format
            test_data = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
            # Get test parameters (TestParameter mappings)
            # Endpoint: /laboratory/parameters/ (TestParameterViewSet)
            params_response = requests.get(
                f"{API_BASE}/laboratory/parameters/",
                headers={"Authorization": f"Bearer {token}"},
                params={"test": test_id}
            )
            if params_response.status_code == 200:
                response_data = params_response.json()
                # Handle wrapped response format
                params_data = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
                params_list = params_data.get("results", []) if isinstance(params_data, dict) and "results" in params_data else (params_data if isinstance(params_data, list) else [])
                if params_list:
                    # Return first test parameter mapping's ID (this is the TestParameter.id, not Parameter.id)
                    test_param_id = params_list[0].get("id")
                    return test_param_id
        return None
    except Exception as e:
        log_step("Get Test Parameter", "FAIL", f"Exception: {str(e)}")
        return None

def enter_result(token: str, order_item_id: int, test_parameter_id: int, result_value: str) -> Optional[Dict]:
    """Enter test result using bulk_entry endpoint."""
    try:
        # Bulk entry schema: {"results": [{"order_item": int, "test_parameter": int, "result_value": str, "remarks": str}]}
        payload = {
            "results": [
                {
                    "order_item": order_item_id,
                    "test_parameter": test_parameter_id,
                    "result_value": result_value,
                    "remarks": ""
                }
            ]
        }
        
        response = requests.post(
            f"{API_BASE}/results/bulk_entry/",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            # Handle wrapped response format
            result_data = response_data.get("data", response_data) if isinstance(response_data, dict) and "data" in response_data else response_data
            created_count = result_data.get("created", 0)
            log_step("Enter Result", "PASS", 
                    f"Result entered: {result_value}, Created: {created_count}",
                    result_data)
            return result_data
        else:
            log_step("Enter Result", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_step("Enter Result", "FAIL", f"Exception: {str(e)}")
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
    
    # Use database ID (integer) for API calls, not patient_id (string identifier)
    patient_id = patient.get("id")
    # Test ID: use id field (test_id is an alias property)
    test_id = albumin_test.get("id") or albumin_test.get("test_id")
    
    # Step 4: Create order
    order = create_order(admin_token, patient_id, test_id)
    if not order:
        print("\n❌ Failed to create order. Cannot proceed.")
        return
    
    order_id = order.get("order_id") or order.get("id")
    order_db_id = order.get("id")  # Database ID for API calls
    
    # Step 5: Get order items and test parameter for result entry
    order_items = get_order_items(admin_token, order_db_id)
    if not order_items or len(order_items) == 0:
        print("\n⚠️  No order items found. Cannot proceed with result entry.")
    else:
        order_item_id = order_items[0].get("id")
        test_parameter_id = get_test_parameter(admin_token, test_id)
        
        if order_item_id and test_parameter_id:
            # Step 6: Enter result (Albumin = 4.5)
            result = enter_result(admin_token, order_item_id, test_parameter_id, "4.5")
            if result:
                print(f"\n✅ Result entered successfully: Albumin = 4.5")
            else:
                print(f"\n⚠️  Result entry failed. Continue manually in UI.")
        else:
            print(f"\n⚠️  Could not get order item or test parameter. Continue manually in UI.")
    
    print("\n" + "=" * 80)
    print("WORKFLOW EXECUTION LOG")
    print("=" * 80)
    for entry in execution_log:
        status_icon = "✅" if entry["status"] == "PASS" else ("ℹ️" if entry["status"] == "INFO" else "❌")
        print(f"{status_icon} {entry['step']}: {entry['details']}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    patient_id_str = patient.get("patient_id") or patient.get("mrn") or "N/A"
    print(f"Patient ID (MRN): {patient_id_str}")
    print(f"Patient DB ID: {patient_id}")
    print(f"Order ID: {order_id}")
    print(f"Order DB ID: {order_db_id}")
    print(f"Albumin Test ID: {test_id}")
    print(f"Order Total: Rs {order.get('total_amount', 'N/A')}")
    print("\n⚠️  Note: Sample collection, verification, and PDF generation")
    print("    require UI interaction. Use the IDs above to continue in the frontend.")
    
    # Save execution log
    with open("/tmp/lims_e2e_log.json", "w") as f:
        json.dump(execution_log, f, indent=2, default=str)
    print(f"\n📝 Full log saved to: /tmp/lims_e2e_log.json")

if __name__ == "__main__":
    main()
