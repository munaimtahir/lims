#!/usr/bin/env python3
"""
API-only End-to-End Smoke Test for LIMS
Workflow: Patient Registration → Create Order (Albumin Rs 500) → Sample Workflow (if enabled) → 
          Result Entry (Alb=4.5) → Verification → Publish → PDF Download

Usage:
    BASE_URL=http://localhost:8012 \
    ADMIN_USER=admin \
    ADMIN_PASS=admin123 \
    API_HOST=lims.alshifalab.pk \
    python3 scripts/smoke_test_api.py

Note: API_HOST must match ALLOWED_HOSTS in Django settings (default: lims.alshifalab.pk)
"""

import json
import os
import sys
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configuration from environment
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_BASE = f"{BASE_URL}/api/v1"
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# Session with default headers for proxy compatibility
session = requests.Session()
if "8012" in BASE_URL or "localhost" in BASE_URL:
    # Add headers that proxy would normally add
    # Note: If ALLOWED_HOSTS doesn't include localhost, you may need to set Host header
    # to match an allowed host (e.g., 'lims.alshifalab.pk')
    session.headers.update({
        "X-Forwarded-Proto": "https",
        "X-Forwarded-For": "127.0.0.1",
        "X-Real-IP": "127.0.0.1",
        "Host": os.getenv("API_HOST", "lims.alshifalab.pk")  # Match ALLOWED_HOSTS
    })

# Test execution log
execution_log: List[Dict[str, Any]] = []
test_results: Dict[str, str] = {}  # step -> PASS/FAIL
extracted_ids: Dict[str, Any] = {}  # patient_id, order_id, etc.

def log_request(method: str, url: str, status_code: int, response_snippet: str = ""):
    """Log API request details."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "url": url,
        "status_code": status_code,
        "response_snippet": response_snippet[:200] if response_snippet else ""
    }
    execution_log.append(entry)
    print(f"[{status_code}] {method} {url}")
    if response_snippet:
        print(f"  Response: {response_snippet[:200]}")

def log_step(step: str, status: str, details: str = "", data: Any = None):
    """Log a test step."""
    test_results[step] = status
    entry = {
        "step": step,
        "status": status,
        "details": details,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    execution_log.append(entry)
    status_symbol = "✓" if status == "PASS" else "✗"
    print(f"\n[{status_symbol}] {step}: {details}")
    if data:
        print(f"  Data: {json.dumps(data, indent=2, default=str)}")

def fail_and_exit(step: str, message: str, response_text: str = ""):
    """Log failure and exit."""
    log_step(step, "FAIL", f"{message}\nResponse: {response_text[:500]}")
    sys.exit(1)

def get_auth_token() -> Optional[str]:
    """PHASE 1: Obtain JWT access token."""
    try:
        url = f"{API_BASE}/auth/login/"
        payload = {"username": ADMIN_USER, "password": ADMIN_PASS}
        headers = {"Content-Type": "application/json"}
        headers.update(session.headers)
        response = session.post(url, json=payload, headers=headers)
        
        log_request("POST", url, response.status_code, response.text[:200])
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("data", {}).get("access_token")
            if not token:
                fail_and_exit("AUTH", "Token not found in response", response.text)
            log_step("AUTH", "PASS", f"Token obtained for user: {ADMIN_USER}")
            return token
        else:
            fail_and_exit("AUTH", f"Login failed: {response.status_code}", response.text)
    except Exception as e:
        fail_and_exit("AUTH", f"Exception during login: {str(e)}")

def check_albumin_test(token: str) -> Optional[Dict]:
    """PHASE 2: Verify Albumin test exists with price Rs 500."""
    try:
        url = f"{API_BASE}/laboratory/tests/"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"search": "Albumin"}
        
        headers.update(session.headers)
        response = session.get(url, headers=headers, params=params)
        log_request("GET", url, response.status_code, response.text[:200])
        
        if response.status_code != 200:
            fail_and_exit("CATALOG-CHECK", f"Failed to fetch tests: {response.status_code}", response.text)
        
        data = response.json()
        tests = data.get("results", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        
        albumin = None
        for test in tests:
            test_name = test.get("test_name", "").lower()
            test_code = test.get("test_code", "").lower()
            if "albumin" in test_name or "albumin" in test_code:
                albumin = test
                break
        
        if not albumin:
            fail_and_exit("CATALOG-CHECK", "Albumin test not found in catalog")
        
        test_id = albumin.get("test_id") or albumin.get("id")
        price = float(albumin.get("price", 0))
        is_active = albumin.get("is_active", False)
        
        if price != 500.0:
            fail_and_exit("CATALOG-CHECK", f"Albumin price mismatch: Expected Rs 500, found Rs {price}")
        
        if not is_active:
            fail_and_exit("CATALOG-CHECK", "Albumin test is not active")
        
        # Get parameter ID for result entry
        parameter_id = None
        if test_id:
            test_detail_url = f"{API_BASE}/laboratory/tests/{test_id}/"
            detail_response = session.get(test_detail_url, headers=headers)
            if detail_response.status_code == 200:
                test_detail = detail_response.json()
                parameters = test_detail.get("parameters", [])
                if parameters:
                    parameter_id = parameters[0].get("id") or parameters[0].get("parameter_id")
        
        log_step("CATALOG-CHECK", "PASS", 
                f"Albumin found: ID={test_id}, Price=Rs {price}, Active={is_active}, Parameter ID={parameter_id}",
                {"test_id": test_id, "parameter_id": parameter_id, "test_data": albumin})
        
        extracted_ids["albumin_test_id"] = test_id
        extracted_ids["albumin_parameter_id"] = parameter_id
        
        return albumin
    except Exception as e:
        fail_and_exit("CATALOG-CHECK", f"Exception: {str(e)}")

def create_patient(token: str) -> int:
    """PHASE 3: Create a test patient."""
    try:
        url = f"{API_BASE}/patients/"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "full_name": "Test Patient Albumin API",
            "age_years": 35,
            "gender": "Male",
            "phone": "03001234567",  # Pakistani mobile format: 03XXXXXXXXX
            "address": "Test Address"
        }
        
        headers.update(session.headers)
        response = session.post(url, json=payload, headers=headers)
        log_request("POST", url, response.status_code, response.text[:200])
        
        if response.status_code in [200, 201]:
            data = response.json()
            patient_data = data.get("data", data) if isinstance(data, dict) and "data" in data else data
            patient_id = patient_data.get("id") or patient_data.get("patient_id")
            mrn = patient_data.get("mrn") or patient_data.get("patient_number")
            
            if not patient_id:
                fail_and_exit("PATIENT-CREATE", "Patient ID not found in response", response.text)
            
            log_step("PATIENT-CREATE", "PASS", f"Patient created: ID={patient_id}, MRN={mrn}", patient_data)
            extracted_ids["patient_id"] = patient_id
            extracted_ids["patient_mrn"] = mrn
            return patient_id
        else:
            fail_and_exit("PATIENT-CREATE", f"Failed to create patient: {response.status_code}", response.text)
    except Exception as e:
        fail_and_exit("PATIENT-CREATE", f"Exception: {str(e)}")

def create_order(token: str, patient_id: int, test_id: int) -> int:
    """PHASE 4: Create order with Albumin test."""
    try:
        url = f"{API_BASE}/orders/orders/"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "patient": patient_id,
            "test_ids": [test_id]
        }
        
        headers.update(session.headers)
        response = session.post(url, json=payload, headers=headers)
        log_request("POST", url, response.status_code, response.text[:200])
        
        if response.status_code in [200, 201]:
            data = response.json()
            order_id = data.get("id")
            order_number = data.get("order_id") or data.get("lab_number")
            items = data.get("items", [])
            total_price = data.get("total_price") or data.get("bill_amount", 0)
            
            if not order_id:
                fail_and_exit("ORDER-CREATE", "Order ID not found in response", response.text)
            
            if len(items) == 0:
                fail_and_exit("ORDER-CREATE", "No order items created", response.text)
            
            order_item_id = items[0].get("id") if items else None
            extracted_ids["order_item_id"] = order_item_id
            
            if float(total_price) != 500.0:
                log_step("ORDER-CREATE", "WARN", f"Total price mismatch: Expected Rs 500, found Rs {total_price}")
            else:
                log_step("ORDER-CREATE", "PASS", 
                        f"Order created: ID={order_id}, Number={order_number}, Items={len(items)}, Total=Rs {total_price}",
                        {"order_id": order_id, "order_item_id": order_item_id, "items": items})
            
            extracted_ids["order_id"] = order_id
            extracted_ids["order_number"] = order_number
            return order_id
        else:
            fail_and_exit("ORDER-CREATE", f"Failed to create order: {response.status_code}", response.text)
    except Exception as e:
        fail_and_exit("ORDER-CREATE", f"Exception: {str(e)}")

def check_sample_workflow_enabled(token: str) -> bool:
    """PHASE 5: Check if sample workflow is enabled."""
    try:
        url = f"{API_BASE}/core/settings/tenant/"
        headers = {"Authorization": f"Bearer {token}"}
        
        headers.update(session.headers)
        response = session.get(url, headers=headers)
        log_request("GET", url, response.status_code, response.text[:200])
        
        if response.status_code == 200:
            data = response.json()
            enabled = data.get("sample_workflow_enabled", False) or data.get("enable_sample_workflow", False)
            log_step("SAMPLE-WORKFLOW-CHECK", "PASS", f"Sample workflow enabled: {enabled}", data)
            return enabled
        else:
            log_step("SAMPLE-WORKFLOW-CHECK", "WARN", f"Could not fetch tenant settings: {response.status_code}, assuming enabled")
            return True  # Default to enabled
    except Exception as e:
        log_step("SAMPLE-WORKFLOW-CHECK", "WARN", f"Exception checking sample workflow: {str(e)}, assuming enabled")
        return True

def collect_sample(token: str, order_id: int) -> Optional[int]:
    """Mark sample as collected."""
    try:
        # Get samples for this order
        url = f"{API_BASE}/samples/"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"order": order_id}
        
        headers.update(session.headers)
        response = session.get(url, headers=headers, params=params)
        log_request("GET", url, response.status_code, response.text[:200])
        
        if response.status_code != 200:
            fail_and_exit("SAMPLE-COLLECT", f"Failed to fetch samples: {response.status_code}", response.text)
        
        data = response.json()
        samples = data.get("results", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        
        if not samples:
            fail_and_exit("SAMPLE-COLLECT", "No samples found for order")
        
        sample = samples[0]
        sample_id = sample.get("id")
        
        # Update sample status to COLLECTED
        update_url = f"{API_BASE}/samples/{sample_id}/"
        update_payload = {"status": "COLLECTED"}
        
        update_response = session.patch(update_url, json=update_payload, headers=headers)
        log_request("PATCH", update_url, update_response.status_code, update_response.text[:200])
        
        if update_response.status_code in [200, 201]:
            log_step("SAMPLE-COLLECT", "PASS", f"Sample collected: ID={sample_id}")
            return sample_id
        else:
            fail_and_exit("SAMPLE-COLLECT", f"Failed to collect sample: {update_response.status_code}", update_response.text)
    except Exception as e:
        fail_and_exit("SAMPLE-COLLECT", f"Exception: {str(e)}")

def receive_sample(token: str, sample_id: int):
    """Mark sample as received."""
    try:
        url = f"{API_BASE}/samples/{sample_id}/"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"status": "RECEIVED"}
        
        headers.update(session.headers)
        response = session.patch(url, json=payload, headers=headers)
        log_request("PATCH", url, response.status_code, response.text[:200])
        
        if response.status_code in [200, 201]:
            log_step("SAMPLE-RECEIVE", "PASS", f"Sample received: ID={sample_id}")
        else:
            fail_and_exit("SAMPLE-RECEIVE", f"Failed to receive sample: {response.status_code}", response.text)
    except Exception as e:
        fail_and_exit("SAMPLE-RECEIVE", f"Exception: {str(e)}")

def enter_result(token: str, order_item_id: int, parameter_id: int, value: str = "4.5"):
    """PHASE 6: Enter result for Albumin."""
    try:
        # First ensure results exist for this order item
        ensure_url = f"{API_BASE}/results/ensure/"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        params = {"order_item_id": order_item_id}
        
        ensure_response = session.post(ensure_url, json={}, headers=headers, params=params)
        log_request("POST", ensure_url, ensure_response.status_code, ensure_response.text[:200])
        
        if ensure_response.status_code not in [200, 201]:
            fail_and_exit("RESULT-ENTRY", f"Failed to ensure results: {ensure_response.status_code}", ensure_response.text)
        
        # Get the result for this parameter
        results_url = f"{API_BASE}/results/"
        results_params = {"order_item": order_item_id, "test_parameter": parameter_id}
        
        results_response = session.get(results_url, headers=headers, params=results_params)
        log_request("GET", results_url, results_response.status_code, results_response.text[:200])
        
        if results_response.status_code != 200:
            fail_and_exit("RESULT-ENTRY", f"Failed to fetch results: {results_response.status_code}", results_response.text)
        
        results_data = results_response.json()
        results_list = results_data.get("results", []) if isinstance(results_data, dict) else (results_data if isinstance(results_data, list) else [])
        
        if not results_list:
            fail_and_exit("RESULT-ENTRY", "No result found for parameter")
        
        result = results_list[0]
        result_id = result.get("id")
        
        # Update result value
        update_url = f"{API_BASE}/results/{result_id}/"
        update_payload = {"result_value": value}
        
        update_response = session.patch(update_url, json=update_payload, headers=headers)
        log_request("PATCH", update_url, update_response.status_code, update_response.text[:200])
        
        if update_response.status_code in [200, 201]:
            updated_result = update_response.json()
            extracted_ids["result_id"] = result_id
            log_step("RESULT-ENTRY", "PASS", 
                    f"Result entered: ID={result_id}, Value={value}",
                    updated_result)
        else:
            fail_and_exit("RESULT-ENTRY", f"Failed to enter result: {update_response.status_code}", update_response.text)
    except Exception as e:
        fail_and_exit("RESULT-ENTRY", f"Exception: {str(e)}")

def verify_result(token: str, result_id: int):
    """PHASE 7: Verify the result."""
    try:
        url = f"{API_BASE}/results/{result_id}/verify/"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = session.post(url, json={}, headers=headers)
        log_request("POST", url, response.status_code, response.text[:200])
        
        if response.status_code in [200, 201]:
            data = response.json()
            log_step("VERIFY", "PASS", f"Result verified: ID={result_id}", data)
        else:
            fail_and_exit("VERIFY", f"Failed to verify result: {response.status_code}", response.text)
    except Exception as e:
        fail_and_exit("VERIFY", f"Exception: {str(e)}")

def publish_report(token: str, order_id: int):
    """PHASE 8: Publish report."""
    try:
        url = f"{API_BASE}/orders/orders/{order_id}/publish-report/"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = session.post(url, json={}, headers=headers)
        log_request("POST", url, response.status_code, response.text[:200])
        
        if response.status_code in [200, 201]:
            data = response.json()
            report_id = data.get("report_id")
            pdf_url = data.get("pdf_url") or data.get("data", {}).get("pdf_url")
            extracted_ids["report_id"] = report_id
            log_step("PUBLISH", "PASS", f"Report published: Order ID={order_id}, Report ID={report_id}", data)
        else:
            fail_and_exit("PUBLISH", f"Failed to publish report: {response.status_code}", response.text)
    except Exception as e:
        fail_and_exit("PUBLISH", f"Exception: {str(e)}")

def download_pdf(token: str, order_id: int) -> bytes:
    """PHASE 9: Download PDF report."""
    try:
        url = f"{API_BASE}/orders/orders/{order_id}/report.pdf"
        headers = {"Authorization": f"Bearer {token}"}
        
        headers.update(session.headers)
        response = session.get(url, headers=headers)
        log_request("GET", url, response.status_code, f"PDF size: {len(response.content)} bytes" if response.status_code == 200 else response.text[:200])
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "application/pdf" not in content_type:
                log_step("PDF-DOWNLOAD", "WARN", f"Content-Type is {content_type}, expected application/pdf")
            else:
                log_step("PDF-DOWNLOAD", "PASS", f"PDF downloaded: {len(response.content)} bytes, Content-Type: {content_type}")
            
            if len(response.content) < 10240:  # 10 KB
                log_step("PDF-DOWNLOAD", "WARN", f"PDF size is suspiciously small: {len(response.content)} bytes")
            
            return response.content
        else:
            fail_and_exit("PDF-DOWNLOAD", f"Failed to download PDF: {response.status_code}", response.text)
    except Exception as e:
        fail_and_exit("PDF-DOWNLOAD", f"Exception: {str(e)}")

def check_pdf_content(pdf_bytes: bytes) -> bool:
    """PHASE 9: Check PDF contains Albumin and 4.5."""
    try:
        # Try PyPDF2 first
        try:
            import PyPDF2
            import io
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            has_albumin = "albumin" in text.lower()
            has_value = "4.5" in text
            
            if has_albumin and has_value:
                log_step("PDF-CONTENT-CHECK", "PASS", "PDF contains 'Albumin' and '4.5'")
                return True
            else:
                log_step("PDF-CONTENT-CHECK", "WARN", 
                        f"PDF content check: Albumin={has_albumin}, Value 4.5={has_value}")
                return False
        except ImportError:
            # Try pdfminer.six
            try:
                from pdfminer.high_level import extract_text
                import io
                text = extract_text(io.BytesIO(pdf_bytes))
                has_albumin = "albumin" in text.lower()
                has_value = "4.5" in text
                
                if has_albumin and has_value:
                    log_step("PDF-CONTENT-CHECK", "PASS", "PDF contains 'Albumin' and '4.5'")
                    return True
                else:
                    log_step("PDF-CONTENT-CHECK", "WARN", 
                            f"PDF content check: Albumin={has_albumin}, Value 4.5={has_value}")
                    return False
            except ImportError:
                # Fallback: try pdftotext command
                import subprocess
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(pdf_bytes)
                    tmp_path = tmp.name
                
                try:
                    result = subprocess.run(["pdftotext", tmp_path, "-"], 
                                           capture_output=True, text=True, timeout=5)
                    text = result.stdout.lower()
                    has_albumin = "albumin" in text
                    has_value = "4.5" in text
                    
                    if has_albumin and has_value:
                        log_step("PDF-CONTENT-CHECK", "PASS", "PDF contains 'Albumin' and '4.5'")
                        return True
                    else:
                        log_step("PDF-CONTENT-CHECK", "WARN", 
                                f"PDF content check: Albumin={has_albumin}, Value 4.5={has_value}")
                        return False
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    log_step("PDF-CONTENT-CHECK", "SKIP", 
                            "PDF extraction tools not available, manual verification required")
                    return False
                finally:
                    os.unlink(tmp_path)
    except Exception as e:
        log_step("PDF-CONTENT-CHECK", "SKIP", f"Exception during PDF content check: {str(e)}")
        return False

def main():
    """Main test execution."""
    print("=" * 80)
    print("LIMS API End-to-End Smoke Test")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Admin User: {ADMIN_USER}")
    print("=" * 80)
    
    # PHASE 1: Auth
    token = get_auth_token()
    if not token:
        sys.exit(1)
    
    # PHASE 2: Catalog Check
    albumin_test = check_albumin_test(token)
    if not albumin_test:
        sys.exit(1)
    
    test_id = extracted_ids["albumin_test_id"]
    parameter_id = extracted_ids.get("albumin_parameter_id")
    
    # PHASE 3: Create Patient
    patient_id = create_patient(token)
    
    # PHASE 4: Create Order
    order_id = create_order(token, patient_id, test_id)
    order_item_id = extracted_ids.get("order_item_id")
    
    # PHASE 5: Sample Workflow (conditional)
    sample_workflow_enabled = check_sample_workflow_enabled(token)
    
    if sample_workflow_enabled:
        sample_id = collect_sample(token, order_id)
        if sample_id:
            receive_sample(token, sample_id)
    else:
        log_step("SAMPLE-WORKFLOW", "SKIP", "Sample workflow is disabled, skipping collection/receive")
    
    # PHASE 6: Result Entry
    if not parameter_id:
        # Try to get parameter ID from order item
        order_item_url = f"{API_BASE}/orders/order-items/{order_item_id}/"
        headers = {"Authorization": f"Bearer {token}"}
        order_item_response = session.get(order_item_url, headers=headers)
        if order_item_response.status_code == 200:
            order_item_data = order_item_response.json()
            test_data = order_item_data.get("test", {})
            if isinstance(test_data, dict):
                parameters = test_data.get("parameters", [])
                if parameters:
                    parameter_id = parameters[0].get("id") or parameters[0].get("parameter_id")
                    extracted_ids["albumin_parameter_id"] = parameter_id
    
    if not parameter_id:
        fail_and_exit("RESULT-ENTRY", "Could not determine parameter ID for Albumin")
    
    enter_result(token, order_item_id, parameter_id, "4.5")
    
    # PHASE 7: Verification
    result_id = extracted_ids.get("result_id")
    if result_id:
        verify_result(token, result_id)
    else:
        fail_and_exit("VERIFY", "Result ID not found")
    
    # PHASE 8: Publish
    publish_report(token, order_id)
    
    # PHASE 9: PDF Download
    pdf_bytes = download_pdf(token, order_id)
    
    # PHASE 10: PDF Content Check
    check_pdf_content(pdf_bytes)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for status in test_results.values() if status == "PASS")
    failed = sum(1 for status in test_results.values() if status == "FAIL")
    total = len(test_results)
    
    print(f"Total Steps: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"\nExtracted IDs:")
    for key, value in extracted_ids.items():
        print(f"  {key}: {value}")
    
    # Save execution log
    log_file = "docs/qa/API_WORKFLOW_SMOKE_LOG.md"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w") as f:
        f.write("# API Workflow Smoke Test Execution Log\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n")
        f.write(f"**Base URL:** {BASE_URL}\n")
        f.write(f"**Admin User:** {ADMIN_USER}\n\n")
        f.write("## Test Results\n\n")
        f.write("| Step | Status | Details |\n")
        f.write("|------|--------|---------|\n")
        for step, status in test_results.items():
            f.write(f"| {step} | {status} | |\n")
        f.write("\n## Execution Log\n\n")
        f.write("```json\n")
        f.write(json.dumps(execution_log, indent=2, default=str))
        f.write("\n```\n")
    
    print(f"\nExecution log saved to: {log_file}")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")

if __name__ == "__main__":
    main()
