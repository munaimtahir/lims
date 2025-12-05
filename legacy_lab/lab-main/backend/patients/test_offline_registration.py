"""Tests for offline registration numbering system."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from core.models import LabTerminal
from patients.models import Patient
from patients.services import allocate_patient_mrn

User = get_user_model()


@pytest.mark.django_db
class TestLabTerminalModel:
    """Test LabTerminal model."""

    def test_create_lab_terminal(self):
        """Test creating a lab terminal."""
        terminal = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=719999,
        )
        assert terminal.code == "LAB1-PC"
        assert terminal.offline_current == 0
        assert terminal.is_active is True

    def test_lab_terminal_str(self):
        """Test string representation."""
        terminal = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=719999,
        )
        assert str(terminal) == "LAB1-PC - Lab 1 Workstation"

    def test_get_next_offline_mrn_first_allocation(self):
        """Test getting first MRN from range."""
        terminal = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=719999,
        )
        mrn = terminal.get_next_offline_mrn()
        assert mrn == 710000
        terminal.refresh_from_db()
        assert terminal.offline_current == 710000

    def test_get_next_offline_mrn_sequential(self):
        """Test sequential MRN allocation."""
        terminal = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=719999,
            offline_current=710000,
        )
        mrn = terminal.get_next_offline_mrn()
        assert mrn == 710001
        terminal.refresh_from_db()
        assert terminal.offline_current == 710001

    def test_get_next_offline_mrn_exhausted(self):
        """Test that exhausted range raises error."""
        terminal = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=710005,
            offline_current=710005,
        )
        with pytest.raises(ValidationError) as exc_info:
            terminal.get_next_offline_mrn()
        assert "exhausted" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestAllocationService:
    """Test patient MRN allocation service."""

    def test_allocate_online_mode(self):
        """Test online allocation returns None to use normal generation."""
        mrn, terminal, is_offline = allocate_patient_mrn(offline=False)
        assert mrn is None
        assert terminal is None
        assert is_offline is False

    def test_allocate_offline_mode_success(self):
        """Test offline allocation from terminal range."""
        terminal = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=719999,
        )
        mrn, returned_terminal, is_offline = allocate_patient_mrn(
            origin_terminal_code="LAB1-PC", offline=True
        )
        assert mrn == "710000"
        assert returned_terminal.id == terminal.id
        assert is_offline is True

    def test_allocate_offline_mode_missing_terminal_code(self):
        """Test offline mode without terminal code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            allocate_patient_mrn(offline=True)
        assert "required" in str(exc_info.value).lower()

    def test_allocate_offline_mode_invalid_terminal(self):
        """Test offline mode with invalid terminal code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            allocate_patient_mrn(origin_terminal_code="INVALID-PC", offline=True)
        assert "not found" in str(exc_info.value).lower()

    def test_allocate_offline_mode_inactive_terminal(self):
        """Test offline mode with inactive terminal raises error."""
        LabTerminal.objects.create(
            code="INACTIVE-PC",
            name="Inactive Terminal",
            offline_range_start=720000,
            offline_range_end=729999,
            is_active=False,
        )
        with pytest.raises(ValidationError) as exc_info:
            allocate_patient_mrn(origin_terminal_code="INACTIVE-PC", offline=True)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestOfflinePatientRegistration:
    """Test offline patient registration through API."""

    @pytest.fixture
    def admin_client(self):
        """Create an authenticated admin client."""
        user = User.objects.create_user(
            username="admin",
            password="admin123",
            role="ADMIN",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def lab_terminal(self):
        """Create a lab terminal for testing."""
        return LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=719999,
        )

    def test_create_patient_online_default(self, admin_client):
        """Test default online patient creation still works."""
        data = {
            "full_name": "John Doe",
            "father_name": "James Doe",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001234567",
            "cnic": "12345-1234567-1",
            "address": "123 Main St",
        }
        response = admin_client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["mrn"].startswith("PAT-")
        assert response.data["is_offline_entry"] is False
        assert response.data["origin_terminal"] is None

    def test_create_patient_online_explicit(self, admin_client):
        """Test explicit online mode."""
        data = {
            "full_name": "Jane Doe",
            "father_name": "James Doe",
            "dob": "1992-01-01",
            "sex": "F",
            "phone": "03001234568",
            "cnic": "12345-1234567-2",
            "address": "123 Main St",
            "offline": False,
        }
        response = admin_client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["mrn"].startswith("PAT-")
        assert response.data["is_offline_entry"] is False

    def test_create_patient_offline_success(self, admin_client, lab_terminal):
        """Test offline patient creation from terminal range."""
        data = {
            "full_name": "Offline Patient",
            "father_name": "Offline Father",
            "dob": "1985-05-15",
            "sex": "M",
            "phone": "03009876543",
            "cnic": "54321-7654321-1",
            "address": "456 Lab St",
            "offline": True,
            "origin_terminal_code": "LAB1-PC",
        }
        response = admin_client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["mrn"] == "710000"
        assert response.data["is_offline_entry"] is True
        assert response.data["origin_terminal"] == lab_terminal.id
        assert response.data["synced_at"] is not None

    def test_create_multiple_offline_patients_sequential(
        self, admin_client, lab_terminal
    ):
        """Test multiple offline patients get sequential MRNs."""
        base_data = {
            "father_name": "Test Father",
            "dob": "1990-01-01",
            "sex": "M",
            "address": "Test Address",
            "offline": True,
            "origin_terminal_code": "LAB1-PC",
        }

        # Create first patient
        data1 = {
            **base_data,
            "full_name": "Patient 1",
            "phone": "03001111111",
            "cnic": "11111-1111111-1",
        }
        response1 = admin_client.post("/api/patients/", data1)
        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.data["mrn"] == "710000"

        # Create second patient
        data2 = {
            **base_data,
            "full_name": "Patient 2",
            "phone": "03002222222",
            "cnic": "22222-2222222-2",
        }
        response2 = admin_client.post("/api/patients/", data2)
        assert response2.status_code == status.HTTP_201_CREATED
        assert response2.data["mrn"] == "710001"

        # Create third patient
        data3 = {
            **base_data,
            "full_name": "Patient 3",
            "phone": "03003333333",
            "cnic": "33333-3333333-3",
        }
        response3 = admin_client.post("/api/patients/", data3)
        assert response3.status_code == status.HTTP_201_CREATED
        assert response3.data["mrn"] == "710002"

    def test_create_offline_patient_missing_terminal_code(self, admin_client):
        """Test offline registration without terminal code fails."""
        data = {
            "full_name": "Test Patient",
            "father_name": "Test Father",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001234569",
            "cnic": "12345-1234567-3",
            "address": "123 Main St",
            "offline": True,
        }
        response = admin_client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "terminal" in str(response.data).lower()

    def test_create_offline_patient_invalid_terminal(self, admin_client):
        """Test offline registration with invalid terminal fails."""
        data = {
            "full_name": "Test Patient",
            "father_name": "Test Father",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001234570",
            "cnic": "12345-1234567-4",
            "address": "123 Main St",
            "offline": True,
            "origin_terminal_code": "INVALID-PC",
        }
        response = admin_client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "invalid" in str(response.data).lower()
            or "terminal" in str(response.data).lower()
        )

    def test_offline_range_exhaustion(self, admin_client):
        """Test that exhausted range returns proper error."""
        # Create terminal with small range
        LabTerminal.objects.create(
            code="SMALL-PC",
            name="Small Range Terminal",
            offline_range_start=800000,
            offline_range_end=800002,
        )

        base_data = {
            "father_name": "Test Father",
            "dob": "1990-01-01",
            "sex": "M",
            "address": "Test Address",
            "offline": True,
            "origin_terminal_code": "SMALL-PC",
        }

        # Create patients to exhaust range
        for i in range(3):
            data = {
                **base_data,
                "full_name": f"Patient {i}",
                "phone": f"0300{i:07d}",
                "cnic": f"{i:05d}-{i:07d}-{i}",
            }
            response = admin_client.post("/api/patients/", data)
            assert response.status_code == status.HTTP_201_CREATED

        # Next one should fail
        data = {
            **base_data,
            "full_name": "Patient Fail",
            "phone": "03009999999",
            "cnic": "99999-9999999-9",
        }
        response = admin_client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "exhausted" in str(response.data).lower()
            or "range" in str(response.data).lower()
        )

    def test_multiple_terminals_no_collision(self, admin_client):
        """Test that multiple terminals don't collide in MRN ranges."""
        # Create two terminals with different ranges
        terminal1 = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 Workstation",
            offline_range_start=710000,
            offline_range_end=719999,
        )
        terminal2 = LabTerminal.objects.create(
            code="LAB2-PC",
            name="Lab 2 Workstation",
            offline_range_start=720000,
            offline_range_end=729999,
        )

        # Create patient from terminal 1
        data1 = {
            "full_name": "Patient Lab1",
            "father_name": "Father Lab1",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001111111",
            "cnic": "11111-1111111-1",
            "address": "Lab 1 Address",
            "offline": True,
            "origin_terminal_code": "LAB1-PC",
        }
        response1 = admin_client.post("/api/patients/", data1)
        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.data["mrn"] == "710000"
        assert response1.data["origin_terminal"] == terminal1.id

        # Create patient from terminal 2
        data2 = {
            "full_name": "Patient Lab2",
            "father_name": "Father Lab2",
            "dob": "1992-01-01",
            "sex": "F",
            "phone": "03002222222",
            "cnic": "22222-2222222-2",
            "address": "Lab 2 Address",
            "offline": True,
            "origin_terminal_code": "LAB2-PC",
        }
        response2 = admin_client.post("/api/patients/", data2)
        assert response2.status_code == status.HTTP_201_CREATED
        assert response2.data["mrn"] == "720000"
        assert response2.data["origin_terminal"] == terminal2.id

        # Verify no collision
        assert response1.data["mrn"] != response2.data["mrn"]

    def test_duplicate_mrn_handled(self, admin_client, lab_terminal):
        """Test that duplicate MRN is handled gracefully."""
        from django.db import IntegrityError

        # Create a patient with offline MRN
        data1 = {
            "full_name": "First Patient",
            "father_name": "First Father",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001234567",
            "cnic": "12345-1234567-1",
            "address": "First Address",
            "offline": True,
            "origin_terminal_code": "LAB1-PC",
        }
        response1 = admin_client.post("/api/patients/", data1)
        assert response1.status_code == status.HTTP_201_CREATED
        mrn = response1.data["mrn"]

        # Try to create another patient with same MRN (simulate race condition)
        # This should not happen in normal operation but test error handling
        with pytest.raises(IntegrityError):
            Patient.objects.create(
                mrn=mrn,
                full_name="Duplicate",
                father_name="Duplicate Father",
                dob=date(1990, 1, 1),
                sex="M",
                phone="03009999999",
                cnic="99999-9999999-9",
                address="Duplicate Address",
            )
