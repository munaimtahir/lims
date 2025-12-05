"""
Create sample test data for LIMS Phase 1 MVP.
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
from datetime import date
from decimal import Decimal

def create_sample_data():
    print("Creating sample test data...")
    
    # 1. Create Users
    print("\n1. Creating users...")
    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@lims.com',
            'full_name': 'Admin User',
            'role': 'Admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if not admin.has_usable_password():
        admin.set_password('admin123')
        admin.save()
    
    receptionist, _ = User.objects.get_or_create(
        username='receptionist',
        defaults={
            'email': 'receptionist@lims.com',
            'full_name': 'Reception Desk',
            'role': 'Receptionist'
        }
    )
    if not receptionist.has_usable_password():
        receptionist.set_password('recep123')
        receptionist.save()
    
    pathologist, _ = User.objects.get_or_create(
        username='pathologist',
        defaults={
            'email': 'pathologist@lims.com',
            'full_name': 'Dr. Pathologist',
            'role': 'Pathologist'
        }
    )
    if not pathologist.has_usable_password():
        pathologist.set_password('patho123')
        pathologist.save()
    
    print(f"   Created/Updated {User.objects.count()} users")
    
    # 2. Create Test Categories
    print("\n2. Creating test categories...")
    hematology = TestCategory.objects.create(
        name='Hematology',
        description='Blood tests and related parameters'
    )
    chemistry = TestCategory.objects.create(
        name='Clinical Chemistry',
        description='Chemical analysis of blood and body fluids'
    )
    print(f"   Created {TestCategory.objects.count()} categories")
    
    # 3. Create Tests
    print("\n3. Creating tests...")
    cbc = Test.objects.create(
        category=hematology,
        test_code='CBC',
        test_name='Complete Blood Count',
        loinc_code='58410-2',
        sample_type='EDTA Blood',
        sample_volume='3-5 mL',
        price=Decimal('500.00'),
        turnaround_time=2
    )
    
    # Add parameters for CBC
    TestParameter.objects.create(
        test=cbc,
        parameter_name='Hemoglobin',
        loinc_code='718-7',
        unit='g/dL',
        reference_min_male=Decimal('13.5'),
        reference_max_male=Decimal('17.5'),
        reference_min_female=Decimal('12.0'),
        reference_max_female=Decimal('15.5'),
        critical_low=Decimal('7.0'),
        critical_high=Decimal('20.0'),
        display_order=1
    )
    
    TestParameter.objects.create(
        test=cbc,
        parameter_name='WBC Count',
        loinc_code='6690-2',
        unit='x10^9/L',
        reference_min_male=Decimal('4.0'),
        reference_max_male=Decimal('11.0'),
        reference_min_female=Decimal('4.0'),
        reference_max_female=Decimal('11.0'),
        critical_low=Decimal('2.0'),
        critical_high=Decimal('30.0'),
        display_order=2
    )
    
    glucose = Test.objects.create(
        category=chemistry,
        test_code='GLU',
        test_name='Fasting Blood Glucose',
        loinc_code='1558-6',
        sample_type='Serum',
        sample_volume='2 mL',
        price=Decimal('200.00'),
        turnaround_time=1
    )
    
    TestParameter.objects.create(
        test=glucose,
        parameter_name='Glucose',
        loinc_code='2345-7',
        unit='mg/dL',
        reference_min_male=Decimal('70.0'),
        reference_max_male=Decimal('100.0'),
        reference_min_female=Decimal('70.0'),
        reference_max_female=Decimal('100.0'),
        critical_low=Decimal('40.0'),
        critical_high=Decimal('400.0'),
        display_order=1
    )
    
    print(f"   Created {Test.objects.count()} tests with {TestParameter.objects.count()} parameters")
    
    # 4. Create Test Panel
    print("\n4. Creating test panels...")
    basic_panel = TestPanel.objects.create(
        panel_code='BASIC',
        panel_name='Basic Health Panel',
        category=chemistry,
        sample_type='Blood',
        sample_volume='5 mL',
        price=Decimal('650.00'),
        turnaround_time=2,
        description='Basic health screening panel'
    )
    basic_panel.tests.add(cbc, glucose)
    print(f"   Created {TestPanel.objects.count()} panels")
    
    # 5. Create Patients
    print("\n5. Creating patients...")
    patient1 = Patient.objects.create(
        first_name='John',
        last_name='Doe',
        date_of_birth=date(1990, 5, 15),
        gender='Male',
        phone='03001234567',
        email='john.doe@email.com',
        created_by=receptionist
    )
    
    patient2 = Patient.objects.create(
        first_name='Jane',
        last_name='Smith',
        date_of_birth=date(1985, 8, 22),
        gender='Female',
        phone='03007654321',
        email='jane.smith@email.com',
        created_by=receptionist
    )
    print(f"   Created {Patient.objects.count()} patients")
    
    # 6. Create Orders
    print("\n6. Creating orders...")
    order1 = Order.objects.create(
        patient=patient1,
        ordered_by=receptionist,
        status='pending'
    )
    OrderItem.objects.create(
        order=order1,
        test=cbc,
        price=cbc.price
    )
    OrderItem.objects.create(
        order=order1,
        test=glucose,
        price=glucose.price
    )
    order1.calculate_total()
    order1.save()
    
    print(f"   Created {Order.objects.count()} orders with {OrderItem.objects.count()} items")
    
    print("\n" + "=" * 60)
    print("SAMPLE DATA CREATION COMPLETE")
    print("=" * 60)
    print(f"Users: {User.objects.count()}")
    print(f"Patients: {Patient.objects.count()}")
    print(f"Test Categories: {TestCategory.objects.count()}")
    print(f"Tests: {Test.objects.count()}")
    print(f"Test Parameters: {TestParameter.objects.count()}")
    print(f"Test Panels: {TestPanel.objects.count()}")
    print(f"Orders: {Order.objects.count()}")
    print(f"Order Items: {OrderItem.objects.count()}")

if __name__ == '__main__':
    create_sample_data()
