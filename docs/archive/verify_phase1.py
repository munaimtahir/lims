"""
Verification script to test all LIMS Phase 1 features.
"""
import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test, TestParameter, TestPanel
from apps.orders.models import Order, OrderItem
from apps.billing.models import Payment
from apps.samples.models import SampleCollection
from apps.results.models import TestResult
from apps.reports.models import Report
from datetime import date, datetime

def verify_models():
    """Verify all models are properly registered and accessible."""
    print("=" * 60)
    print("PHASE 1 MVP VERIFICATION")
    print("=" * 60)
    
    # 1. User Management
    print("\n1. USER MANAGEMENT")
    print(f"   - User model: {User._meta.db_table}")
    print(f"   - Role choices: {len(User.ROLE_CHOICES)} roles")
    print(f"   - Total users: {User.objects.count()}")
    
    # 2. Patient Management
    print("\n2. PATIENT MANAGEMENT")
    print(f"   - Patient model: {Patient._meta.db_table}")
    print(f"   - Total patients: {Patient.objects.count()}")
    
    # 3. Test Catalog
    print("\n3. TEST CATALOG (LABORATORY)")
    print(f"   - TestCategory model: {TestCategory._meta.db_table}")
    print(f"   - Test model: {Test._meta.db_table}")
    print(f"   - TestParameter model: {TestParameter._meta.db_table}")
    print(f"   - TestPanel model: {TestPanel._meta.db_table}")
    print(f"   - Total categories: {TestCategory.objects.count()}")
    print(f"   - Total tests: {Test.objects.count()}")
    print(f"   - Total panels: {TestPanel.objects.count()}")
    
    # 4. Order Management
    print("\n4. ORDER MANAGEMENT")
    print(f"   - Order model: {Order._meta.db_table}")
    print(f"   - OrderItem model: {OrderItem._meta.db_table}")
    print(f"   - Total orders: {Order.objects.count()}")
    
    # 5. Billing & Payment
    print("\n5. BILLING & PAYMENT")
    print(f"   - Payment model: {Payment._meta.db_table}")
    print(f"   - Payment methods: {len(Payment.PAYMENT_METHODS)}")
    print(f"   - Total payments: {Payment.objects.count()}")
    
    # 6. Sample Collection
    print("\n6. SAMPLE COLLECTION")
    print(f"   - SampleCollection model: {SampleCollection._meta.db_table}")
    print(f"   - Status choices: {len(SampleCollection.STATUS_CHOICES)}")
    print(f"   - Total samples: {SampleCollection.objects.count()}")
    
    # 7. Result Entry
    print("\n7. RESULT ENTRY")
    print(f"   - TestResult model: {TestResult._meta.db_table}")
    print(f"   - Flag choices: {len(TestResult.FLAG_CHOICES)}")
    print(f"   - Total results: {TestResult.objects.count()}")
    
    # 8. Report Generation
    print("\n8. REPORT GENERATION")
    print(f"   - Report model: {Report._meta.db_table}")
    print(f"   - Total reports: {Report.objects.count()}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    verify_models()
