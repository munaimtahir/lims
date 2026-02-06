"""
Tests for the V2 numbering system.
"""
import pytest
from datetime import datetime, date
from django.utils import timezone
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor, as_completed
from apps.core.models import CollectionCenter, RegistrationCounter, LabDailyCounter
from apps.core.numbering import generate_registration_number, generate_lab_number
from apps.patients.models import Patient
from apps.orders.models import Order


@pytest.fixture
def center_00(db):
    """Head Office collection center."""
    center, _ = CollectionCenter.objects.get_or_create(
        code="00",
        defaults={"name": "Head Office", "is_active": True}
    )
    return center


@pytest.fixture
def center_10(db):
    """Test collection center."""
    center, _ = CollectionCenter.objects.get_or_create(
        code="10",
        defaults={"name": "Test Center", "is_active": True}
    )
    return center


@pytest.mark.django_db
class TestRegistrationNumbering:
    """Tests for Patient Registration Number generation."""
    
    def test_registration_number_format(self, center_00):
        """Test that registration number follows YYMM-CC-SSSS format."""
        dt = datetime(2026, 2, 7, 10, 30)
        reg_number = generate_registration_number(center_00, dt)
        
        assert reg_number == "2602-00-0001"
        assert len(reg_number) == 13
        
    def test_registration_number_increments(self, center_00):
        """Test that serial increments correctly."""
        dt = datetime(2026, 2, 7, 10, 30)
        
        num1 = generate_registration_number(center_00, dt)
        num2 = generate_registration_number(center_00, dt)
        num3 = generate_registration_number(center_00, dt)
        
        assert num1 == "2602-00-0001"
        assert num2 == "2602-00-0002"
        assert num3 == "2602-00-0003"
    
    def test_registration_number_monthly_reset(self, center_00):
        """Test that serial resets monthly per center."""
        feb_dt = datetime(2026, 2, 7, 10, 30)
        mar_dt = datetime(2026, 3, 7, 10, 30)
        
        feb_num1 = generate_registration_number(center_00, feb_dt)
        feb_num2 = generate_registration_number(center_00, feb_dt)
        
        # March should reset
        mar_num1 = generate_registration_number(center_00, mar_dt)
        
        assert feb_num1 == "2602-00-0001"
        assert feb_num2 == "2602-00-0002"
        assert mar_num1 == "2603-00-0001"  # Reset to 0001
    
    def test_registration_number_center_scoped(self, center_00, center_10):
        """Test that serial is scoped per center."""
        dt = datetime(2026, 2, 7, 10, 30)
        
        num_c00_1 = generate_registration_number(center_00, dt)
        num_c10_1 = generate_registration_number(center_10, dt)
        num_c00_2 = generate_registration_number(center_00, dt)
        
        assert num_c00_1 == "2602-00-0001"
        assert num_c10_1 == "2602-10-0001"  # Same serial, different center
        assert num_c00_2 == "2602-00-0002"
    
    def test_patient_auto_generates_registration_number(self, center_00):
        """Test that Patient model auto-generates registration number."""
        patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            phone="03001234567",
            registration_center=center_00
        )
        
        assert patient.registration_number is not None
        assert patient.registration_number.startswith("2602-00-")
        assert patient.registration_number == patient.mrn
        assert patient.registration_number == patient.patient_id


@pytest.mark.django_db
class TestLabNumbering:
    """Tests for Lab Number (Tube Label) generation."""
    
    def test_lab_number_format(self, center_00):
        """Test that lab number follows MDD-XXX format."""
        dt = datetime(2026, 2, 7, 10, 30)
        lab_number, serial = generate_lab_number(center_00, dt)
        
        assert lab_number == "B07-001"
        assert serial == 1
        assert len(lab_number) == 7
    
    def test_lab_number_month_letters(self, center_00):
        """Test month letter mapping."""
        test_cases = [
            (datetime(2026, 1, 15), "A15"),
            (datetime(2026, 2, 7), "B07"),
            (datetime(2026, 3, 20), "C20"),
            (datetime(2026, 12, 31), "L31"),
        ]
        
        for dt, expected_prefix in test_cases:
            lab_number, _ = generate_lab_number(center_00, dt)
            assert lab_number.startswith(expected_prefix)
    
    def test_lab_number_increments(self, center_00):
        """Test that daily serial increments correctly."""
        dt = datetime(2026, 2, 7, 10, 30)
        
        num1, serial1 = generate_lab_number(center_00, dt)
        num2, serial2 = generate_lab_number(center_00, dt)
        num3, serial3 = generate_lab_number(center_00, dt)
        
        assert num1 == "B07-001"
        assert num2 == "B07-002"
        assert num3 == "B07-003"
        assert serial1 == 1
        assert serial2 == 2
        assert serial3 == 3
    
    def test_lab_number_daily_reset(self, center_00):
        """Test that serial resets daily per center."""
        feb7_dt = datetime(2026, 2, 7, 10, 30)
        feb8_dt = datetime(2026, 2, 8, 10, 30)
        
        num1, _ = generate_lab_number(center_00, feb7_dt)
        num2, _ = generate_lab_number(center_00, feb7_dt)
        
        # Next day should reset
        num3, _ = generate_lab_number(center_00, feb8_dt)
        
        assert num1 == "B07-001"
        assert num2 == "B07-002"
        assert num3 == "B08-001"  # Reset to 001
    
    def test_lab_number_center_scoped(self, center_00, center_10):
        """Test that serial is scoped per center."""
        dt = datetime(2026, 2, 7, 10, 30)
        
        num_c00_1, _ = generate_lab_number(center_00, dt)
        num_c10_1, _ = generate_lab_number(center_10, dt)
        num_c00_2, _ = generate_lab_number(center_00, dt)
        
        assert num_c00_1 == "B07-001"
        assert num_c10_1 == "B07-001"  # Same serial, different center
        assert num_c00_2 == "B07-002"
    
    def test_lab_number_limit(self, center_00):
        """Test that daily limit (999) is enforced."""
        dt = datetime(2026, 2, 7, 10, 30)
        
        # Set counter to 999
        counter, _ = LabDailyCounter.objects.get_or_create(
            date=dt.date(),
            center=center_00,
            defaults={'last_value': 999}
        )
        counter.last_value = 999
        counter.save()
        
        # Next generation should fail
        with pytest.raises(ValueError, match="Daily serial limit"):
            generate_lab_number(center_00, dt)
    
    def test_order_auto_generates_lab_number(self, center_00):
        """Test that Order model auto-generates lab number."""
        patient = Patient.objects.create(
            first_name="Jane",
            last_name="Smith",
            phone="03009876543",
            registration_center=center_00
        )
        
        order = Order.objects.create(
            patient=patient,
            collection_center=center_00
        )
        
        assert order.lab_number is not None
        assert order.lab_number.startswith("B07-")
        assert order.lab_date is not None
        assert order.daily_serial is not None


@pytest.mark.django_db
class TestConcurrency:
    """Tests for concurrency safety."""
    
    def test_concurrent_registration_numbers(self, center_00):
        """Test that concurrent registrations don't create duplicates."""
        dt = datetime(2026, 2, 7, 10, 30)
        num_threads = 10
        
        def create_number():
            return generate_registration_number(center_00, dt)
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_number) for _ in range(num_threads)]
            results = [f.result() for f in as_completed(futures)]
        
        # All numbers should be unique
        assert len(results) == num_threads
        assert len(set(results)) == num_threads
        
        # Numbers should be sequential (though order may vary)
        serials = [int(r.split("-")[-1]) for r in results]
        assert sorted(serials) == list(range(1, num_threads + 1))
    
    def test_concurrent_lab_numbers(self, center_00):
        """Test that concurrent lab orders don't create duplicates."""
        dt = datetime(2026, 2, 7, 10, 30)
        num_threads = 10
        
        def create_number():
            lab_num, serial = generate_lab_number(center_00, dt)
            return lab_num, serial
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_number) for _ in range(num_threads)]
            results = [f.result() for f in as_completed(futures)]
        
        # All numbers should be unique
        lab_numbers = [r[0] for r in results]
        serials = [r[1] for r in results]
        
        assert len(lab_numbers) == num_threads
        assert len(set(lab_numbers)) == num_threads
        
        # Serials should be sequential (though order may vary)
        assert sorted(serials) == list(range(1, num_threads + 1))


@pytest.mark.django_db
class TestValidation:
    """Tests for validation and constraints."""
    
    def test_registration_number_unique(self, center_00):
        """Test that registration numbers are unique."""
        patient1 = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            phone="03001234567",
            registration_center=center_00
        )
        
        # Try to create another patient with same registration number
        with pytest.raises(Exception):  # IntegrityError
            Patient.objects.create(
                first_name="Jane",
                last_name="Smith",
                phone="03009876543",
                registration_number=patient1.registration_number,
                registration_center=center_00
            )
    
    def test_center_code_validation(self):
        """Test that center codes must be 2 digits."""
        # Valid codes
        center1 = CollectionCenter.objects.create(code="00", name="Test")
        center2 = CollectionCenter.objects.create(code="99", name="Test")
        
        assert center1.code == "00"
        assert center2.code == "99"
        
        # Invalid codes should fail validation
        with pytest.raises(Exception):  # ValidationError
            center = CollectionCenter(code="1", name="Invalid")
            center.full_clean()
        
        with pytest.raises(Exception):  # ValidationError
            center = CollectionCenter(code="ABC", name="Invalid")
            center.full_clean()
