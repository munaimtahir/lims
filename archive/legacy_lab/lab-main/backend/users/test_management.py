"""Tests for management commands."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from catalog.models import TestCatalog
from patients.models import Patient

User = get_user_model()


@pytest.mark.django_db
class TestSeedDataCommand:
    """Test seed_data management command."""

    def test_seed_data_creates_users(self):
        """Test that seed_data creates demo users."""
        call_command("seed_data")

        assert User.objects.filter(username="admin").exists()
        assert User.objects.filter(username="reception").exists()
        assert User.objects.filter(username="tech").exists()
        assert User.objects.filter(username="pathologist").exists()

        admin = User.objects.get(username="admin")
        assert admin.role == "ADMIN"

    def test_seed_data_creates_test_catalog(self):
        """Test that seed_data creates test catalog."""
        call_command("seed_data")

        assert TestCatalog.objects.count() >= 5
        assert TestCatalog.objects.filter(code="CBC").exists()
        assert TestCatalog.objects.filter(code="LFT").exists()

    def test_seed_data_creates_patients(self):
        """Test that seed_data creates sample patients."""
        call_command("seed_data")

        assert Patient.objects.count() >= 2

    def test_seed_data_idempotent(self):
        """Test that seed_data can be run multiple times."""
        call_command("seed_data")
        user_count = User.objects.count()
        test_count = TestCatalog.objects.count()
        patient_count = Patient.objects.count()

        # Run again
        call_command("seed_data")

        # Counts should remain the same (idempotent)
        assert User.objects.count() == user_count
        assert TestCatalog.objects.count() == test_count
        assert Patient.objects.count() == patient_count
