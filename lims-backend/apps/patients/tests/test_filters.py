"""
Tests for patient filters.
"""
from datetime import date, timedelta

import pytest

from apps.accounts.models import User
from apps.patients.filters import PatientFilter
from apps.patients.models import Patient


@pytest.mark.django_db
class TestPatientFilter:
    """Test PatientFilter."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass",
            full_name="Test User",
            role="Receptionist",
        )

    @pytest.fixture
    def patient1(self, user):
        """Create test patient 1."""
        return Patient.objects.create(
            patient_id="PAT-001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="1234567890",
            created_by=user,
        )

    @pytest.fixture
    def patient2(self, user):
        """Create test patient 2."""
        return Patient.objects.create(
            patient_id="PAT-002",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 5, 15),
            gender="Female",
            phone="0987654321",
            created_by=user,
        )

    def test_filter_by_name_first_name(self, patient1, patient2):
        """Test filtering by first name."""
        filter_set = PatientFilter({"name": "John"}, queryset=Patient.objects.all())
        results = list(filter_set.qs)
        assert patient1 in results
        assert patient2 not in results

    def test_filter_by_name_last_name(self, patient1, patient2):
        """Test filtering by last name."""
        filter_set = PatientFilter({"name": "Smith"}, queryset=Patient.objects.all())
        results = list(filter_set.qs)
        assert patient2 in results
        assert patient1 not in results

    def test_filter_by_age_min(self, patient1, patient2):
        """Test filtering by minimum age."""
        from datetime import date

        today = date.today()
        # Calculate actual ages
        age1 = (
            today.year
            - patient1.date_of_birth.year
            - (
                (today.month, today.day)
                < (patient1.date_of_birth.month, patient1.date_of_birth.day)
            )
        )
        age2 = (
            today.year
            - patient2.date_of_birth.year
            - (
                (today.month, today.day)
                < (patient2.date_of_birth.month, patient2.date_of_birth.day)
            )
        )

        # Filter for age_min = 40 (should exclude patient1 if age1 < 40, include patient2 if age2 >= 40)
        filter_set = PatientFilter({"age_min": 40}, queryset=Patient.objects.all())
        results = list(filter_set.qs)
        # Should include patient2 if age2 >= 40, exclude patient1 if age1 < 40
        if age2 >= 40:
            assert patient2 in results
        if age1 < 40:
            assert patient1 not in results

    def test_filter_by_age_max(self, patient1, patient2):
        """Test filtering by maximum age."""
        from datetime import date

        today = date.today()
        # Calculate actual ages
        age1 = (
            today.year
            - patient1.date_of_birth.year
            - (
                (today.month, today.day)
                < (patient1.date_of_birth.month, patient1.date_of_birth.day)
            )
        )
        age2 = (
            today.year
            - patient2.date_of_birth.year
            - (
                (today.month, today.day)
                < (patient2.date_of_birth.month, patient2.date_of_birth.day)
            )
        )

        # Filter for age_max = 35 (should include patient1 if age1 <= 35, exclude patient2 if age2 > 35)
        filter_set = PatientFilter({"age_max": 35}, queryset=Patient.objects.all())
        results = list(filter_set.qs)
        # Should include patient1 if age1 <= 35, exclude patient2 if age2 > 35
        if age1 <= 35:
            assert patient1 in results
        if age2 > 35:
            assert patient2 not in results

    def test_filter_by_age_range(self, patient1, patient2):
        """Test filtering by age range."""
        from datetime import date

        today = date.today()
        # Calculate actual ages
        age1 = (
            today.year
            - patient1.date_of_birth.year
            - (
                (today.month, today.day)
                < (patient1.date_of_birth.month, patient1.date_of_birth.day)
            )
        )
        age2 = (
            today.year
            - patient2.date_of_birth.year
            - (
                (today.month, today.day)
                < (patient2.date_of_birth.month, patient2.date_of_birth.day)
            )
        )

        # Filter for age range 30-40 (should include both if they're in range)
        filter_set = PatientFilter(
            {"age_min": 30, "age_max": 40}, queryset=Patient.objects.all()
        )
        results = list(filter_set.qs)
        # Should include patient1 if 30 <= age1 <= 40
        if 30 <= age1 <= 40:
            assert patient1 in results
        # Should include patient2 if 30 <= age2 <= 40
        if 30 <= age2 <= 40:
            assert patient2 in results

    def test_filter_by_gender(self, patient1, patient2):
        """Test filtering by gender."""
        filter_set = PatientFilter({"gender": "Male"}, queryset=Patient.objects.all())
        results = list(filter_set.qs)
        assert patient1 in results
        assert patient2 not in results

    def test_filter_by_created_from(self, patient1, patient2, user):
        """Test filtering by created_from date."""
        from django.utils import timezone

        # Create new patients with specific created_at dates
        yesterday = timezone.now() - timedelta(days=1)
        patient_yesterday = Patient.objects.create(
            patient_id="PAT-YESTERDAY",
            first_name="Yesterday",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="1111111111",
            created_by=user,
        )
        Patient.objects.filter(id=patient_yesterday.id).update(created_at=yesterday)

        today = timezone.now()
        patient_today = Patient.objects.create(
            patient_id="PAT-TODAY",
            first_name="Today",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="2222222222",
            created_by=user,
        )
        Patient.objects.filter(id=patient_today.id).update(created_at=today)

        # Filter from today
        today_date = today.date()
        filter_set = PatientFilter(
            {"created_from": today_date.isoformat()}, queryset=Patient.objects.all()
        )
        results = list(filter_set.qs)
        # Should include patient_today but not patient_yesterday
        assert patient_today in results
        assert patient_yesterday not in results

    def test_filter_by_created_to(self, patient1, patient2, user):
        """Test filtering by created_to date."""
        from django.utils import timezone

        # Create new patients with specific created_at dates
        yesterday = timezone.now() - timedelta(days=1)
        patient_yesterday = Patient.objects.create(
            patient_id="PAT-YESTERDAY2",
            first_name="Yesterday2",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="3333333333",
            created_by=user,
        )
        Patient.objects.filter(id=patient_yesterday.id).update(created_at=yesterday)

        today = timezone.now()
        patient_today = Patient.objects.create(
            patient_id="PAT-TODAY2",
            first_name="Today2",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="4444444444",
            created_by=user,
        )
        Patient.objects.filter(id=patient_today.id).update(created_at=today)

        # Filter to yesterday (use end of day for datetime comparison)
        from datetime import datetime

        yesterday_end = datetime.combine(yesterday.date(), datetime.max.time())
        yesterday_end = timezone.make_aware(yesterday_end)
        filter_set = PatientFilter(
            {"created_to": yesterday.date().isoformat()}, queryset=Patient.objects.all()
        )
        results = list(filter_set.qs)
        # Should include patient_yesterday but not patient_today
        # Refresh from DB to get updated created_at
        patient_yesterday.refresh_from_db()
        patient_today.refresh_from_db()
        assert patient_yesterday in results
        assert patient_today not in results

    def test_filter_by_phone(self, patient1, patient2):
        """Test filtering by phone."""
        filter_set = PatientFilter(
            {"phone": "1234567890"}, queryset=Patient.objects.all()
        )
        results = list(filter_set.qs)
        assert patient1 in results
        assert patient2 not in results

    def test_filter_by_national_id(self, patient1, patient2):
        """Test filtering by national_id."""
        patient1.national_id = "12345"
        patient1.save()

        filter_set = PatientFilter(
            {"national_id": "12345"}, queryset=Patient.objects.all()
        )
        results = list(filter_set.qs)
        assert patient1 in results
        assert patient2 not in results
