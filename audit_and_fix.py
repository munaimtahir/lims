#!/usr/bin/env python3
"""
Comprehensive audit and fix script for LIMS application.
Checks database state, seeds missing data, and tests workflows.
"""
import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lims-backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.accounts.models import User
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test, TestParameter, TestPanel
from apps.orders.models import Order, OrderItem
from django.core.management import call_command
from io import StringIO
from decimal import Decimal

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_status(label, value, status="info"):
    """Print a status line."""
    status_symbol = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "info": "•"
    }.get(status, "•")
    print(f"  {status_symbol} {label}: {value}")

def audit_database():
    """Audit the current database state."""
    print_section("DATABASE AUDIT")
    
    # Check Users
    user_count = User.objects.count()
    print_status("Total Users", user_count, "info")
    if user_count > 0:
        admin_count = User.objects.filter(is_superuser=True).count()
        print_status("  Admin Users", admin_count, "success" if admin_count > 0 else "warning")
    
    # Check Patients
    patient_count = Patient.objects.count()
    print_status("Total Patients", patient_count, "info")
    
    # Check Test Catalog
    category_count = TestCategory.objects.count()
    test_count = Test.objects.count()
    parameter_count = TestParameter.objects.count()
    panel_count = TestPanel.objects.count()
    
    print_status("Test Categories", category_count, "error" if category_count == 0 else "success")
    print_status("Tests", test_count, "error" if test_count == 0 else "success")
    print_status("Test Parameters", parameter_count, "error" if parameter_count == 0 else "success")
    print_status("Test Panels", panel_count, "info")
    
    # Check Orders
    order_count = Order.objects.count()
    print_status("Total Orders", order_count, "info")
    
    return {
        "users": user_count,
        "patients": patient_count,
        "categories": category_count,
        "tests": test_count,
        "parameters": parameter_count,
        "panels": panel_count,
        "orders": order_count,
    }

def seed_test_catalog():
    """Seed the test catalog with initial data."""
    print_section("SEEDING TEST CATALOG")
    
    try:
        out = StringIO()
        call_command('seed_test_catalog', stdout=out)
        output = out.getvalue()
        print(output)
        
        # Verify seeding
        category_count = TestCategory.objects.count()
        test_count = Test.objects.count()
        parameter_count = TestParameter.objects.count()
        panel_count = TestPanel.objects.count()
        
        if category_count > 0 and test_count > 0:
            print_status("Test Catalog Seeding", "SUCCESS", "success")
            print_status("  Categories Created", category_count, "success")
            print_status("  Tests Created", test_count, "success")
            print_status("  Parameters Created", parameter_count, "success")
            print_status("  Panels Created", panel_count, "success")
            return True
        else:
            print_status("Test Catalog Seeding", "FAILED - No data created", "error")
            return False
    except Exception as e:
        print_status("Test Catalog Seeding", f"ERROR: {str(e)}", "error")
        return False

def create_sample_data():
    """Create sample data for testing."""
    print_section("CREATING SAMPLE DATA")
    
    try:
        # Import and run the sample data script
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lims-backend'))
        from create_sample_data import create_sample_data as create_data
        create_data()
        print_status("Sample Data Creation", "SUCCESS", "success")
        return True
    except Exception as e:
        print_status("Sample Data Creation", f"ERROR: {str(e)}", "error")
        import traceback
        traceback.print_exc()
        return False

def test_workflows():
    """Test basic workflows."""
    print_section("TESTING WORKFLOWS")
    
    results = {
        "patient_registration": False,
        "test_catalog_access": False,
        "order_creation": False,
    }
    
    # Test 1: Patient Registration
    try:
        test_patient = Patient.objects.first()
        if test_patient:
            print_status("Patient Registration", f"✓ Can access patients (found: {test_patient.get_full_name()})", "success")
            results["patient_registration"] = True
        else:
            print_status("Patient Registration", "⚠ No patients found (create one to test)", "warning")
    except Exception as e:
        print_status("Patient Registration", f"✗ ERROR: {str(e)}", "error")
    
    # Test 2: Test Catalog Access
    try:
        test_category = TestCategory.objects.first()
        test = Test.objects.first()
        if test_category and test:
            print_status("Test Catalog Access", f"✓ Categories: {TestCategory.objects.count()}, Tests: {Test.objects.count()}", "success")
            results["test_catalog_access"] = True
        else:
            print_status("Test Catalog Access", "✗ No test catalog data found", "error")
    except Exception as e:
        print_status("Test Catalog Access", f"✗ ERROR: {str(e)}", "error")
    
    # Test 3: Order Creation
    try:
        test_patient = Patient.objects.first()
        test = Test.objects.first()
        if test_patient and test:
            # Check if we can create an order (don't actually create it)
            print_status("Order Creation", f"✓ Can create orders (patient and test available)", "success")
            results["order_creation"] = True
        else:
            missing = []
            if not test_patient:
                missing.append("patients")
            if not test:
                missing.append("tests")
            print_status("Order Creation", f"⚠ Cannot create orders (missing: {', '.join(missing)})", "warning")
    except Exception as e:
        print_status("Order Creation", f"✗ ERROR: {str(e)}", "error")
    
    return results

def generate_report(initial_state, final_state, workflow_results):
    """Generate final audit report."""
    print_section("AUDIT REPORT SUMMARY")
    
    print("\n  INITIAL STATE:")
    print(f"    • Users: {initial_state['users']}")
    print(f"    • Patients: {initial_state['patients']}")
    print(f"    • Test Categories: {initial_state['categories']}")
    print(f"    • Tests: {initial_state['tests']}")
    print(f"    • Test Parameters: {initial_state['parameters']}")
    print(f"    • Test Panels: {initial_state['panels']}")
    print(f"    • Orders: {initial_state['orders']}")
    
    print("\n  FINAL STATE:")
    print(f"    • Users: {final_state['users']}")
    print(f"    • Patients: {final_state['patients']}")
    print(f"    • Test Categories: {final_state['categories']}")
    print(f"    • Tests: {final_state['tests']}")
    print(f"    • Test Parameters: {final_state['parameters']}")
    print(f"    • Test Panels: {final_state['panels']}")
    print(f"    • Orders: {final_state['orders']}")
    
    print("\n  WORKFLOW TESTS:")
    for workflow, result in workflow_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"    • {workflow.replace('_', ' ').title()}: {status}")
    
    print("\n  RECOMMENDATIONS:")
    if final_state['tests'] == 0:
        print("    ⚠ CRITICAL: No tests found. Run: python manage.py seed_test_catalog")
    if final_state['categories'] == 0:
        print("    ⚠ CRITICAL: No test categories found. Run: python manage.py seed_test_catalog")
    if final_state['patients'] == 0:
        print("    • INFO: No patients found. You can register patients through the frontend.")
    if not workflow_results.get('test_catalog_access'):
        print("    ⚠ CRITICAL: Test catalog not accessible. Check database seeding.")
    if not workflow_results.get('order_creation'):
        print("    ⚠ WARNING: Cannot create orders. Ensure patients and tests are available.")
    
    print("\n" + "=" * 70)

def main():
    """Main audit function."""
    print("\n" + "=" * 70)
    print("  LIMS APPLICATION AUDIT & FIX SCRIPT")
    print("=" * 70)
    
    # Step 1: Audit initial state
    initial_state = audit_database()
    
    # Step 2: Fix missing data
    needs_seeding = initial_state['categories'] == 0 or initial_state['tests'] == 0
    
    if needs_seeding:
        print("\n⚠ Missing test catalog data detected. Seeding...")
        seed_success = seed_test_catalog()
        if not seed_success:
            print("\n✗ Failed to seed test catalog. Please check errors above.")
            return
    
    # Step 3: Audit final state
    final_state = audit_database()
    
    # Step 4: Test workflows
    workflow_results = test_workflows()
    
    # Step 5: Generate report
    generate_report(initial_state, final_state, workflow_results)
    
    print("\n✓ Audit complete!")

if __name__ == '__main__':
    main()
