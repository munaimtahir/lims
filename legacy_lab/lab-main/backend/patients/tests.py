"""Tests for patients app."""

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from .models import Patient

User = get_user_model()


@pytest.mark.django_db
class TestPatientModel:
    """Test Patient model."""

    def test_create_patient(self):
        """Test creating a patient."""
        patient = Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )
        assert patient.full_name == "John Doe"
        assert patient.mrn.startswith("PAT-")
        assert len(patient.mrn) == 17  # PAT-YYYYMMDD-NNNN

    def test_patient_mrn_generation(self):
        """Test MRN auto-generation."""
        patient1 = Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )
        patient2 = Patient.objects.create(
            full_name="Jane Doe",
            father_name="James Doe",
            dob=date(1992, 1, 1),
            sex="F",
            phone="03001234568",
            cnic="12345-1234567-2",
            address="124 Main St",
        )
        assert patient1.mrn != patient2.mrn
        assert patient1.mrn.startswith("PAT-")
        assert patient2.mrn.startswith("PAT-")

    def test_patient_str(self):
        """Test patient string representation."""
        patient = Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )
        assert "John Doe" in str(patient)
        assert patient.mrn in str(patient)


@pytest.mark.django_db
class TestPatientAPI:
    """Test Patient API endpoints."""

    def setup_method(self):
        """Set up test client and users."""
        self.client = APIClient()
        self.reception_user = User.objects.create_user(
            username="reception",
            password="testpass123",
            role="RECEPTION",
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            role="ADMIN",
        )
        self.tech_user = User.objects.create_user(
            username="tech",
            password="testpass123",
            role="TECHNOLOGIST",
        )

    def test_create_patient_as_reception(self):
        """Test creating a patient as reception user."""
        self.client.force_authenticate(user=self.reception_user)
        data = {
            "full_name": "John Doe",
            "father_name": "James Doe",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001234567",
            "cnic": "12345-1234567-1",
            "address": "123 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["full_name"] == "John Doe"
        assert "mrn" in response.data
        assert response.data["mrn"].startswith("PAT-")

    def test_create_patient_as_admin(self):
        """Test creating a patient as admin user."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "full_name": "Jane Doe",
            "father_name": "James Doe",
            "dob": "1992-01-01",
            "sex": "F",
            "phone": "03001234568",
            "cnic": "12345-1234567-2",
            "address": "124 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_patient_as_tech_forbidden(self):
        """Test that tech user cannot create patients."""
        self.client.force_authenticate(user=self.tech_user)
        data = {
            "full_name": "Bob Smith",
            "father_name": "John Smith",
            "dob": "1985-01-01",
            "sex": "M",
            "phone": "03001234569",
            "cnic": "12345-1234567-3",
            "address": "125 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_patient_unauthenticated(self):
        """Test that unauthenticated users cannot create patients."""
        data = {
            "full_name": "Bob Smith",
            "father_name": "John Smith",
            "dob": "1985-01-01",
            "sex": "M",
            "phone": "03001234569",
            "cnic": "12345-1234567-3",
            "address": "125 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_patient_invalid_dob(self):
        """Test creating a patient with future date of birth."""
        self.client.force_authenticate(user=self.reception_user)
        future_date = (date.today() + timedelta(days=1)).isoformat()
        data = {
            "full_name": "Future Baby",
            "father_name": "John Doe",
            "dob": future_date,
            "sex": "M",
            "phone": "03001234567",
            "cnic": "12345-1234567-4",
            "address": "123 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_patient_invalid_cnic(self):
        """Test creating a patient with invalid CNIC."""
        self.client.force_authenticate(user=self.reception_user)
        data = {
            "full_name": "John Doe",
            "father_name": "James Doe",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001234567",
            "cnic": "invalid-cnic",
            "address": "123 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_patient_duplicate_cnic(self):
        """Test creating a patient with duplicate CNIC."""
        self.client.force_authenticate(user=self.reception_user)
        # Create first patient
        Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )
        # Try to create second patient with same CNIC
        data = {
            "full_name": "Jane Doe",
            "father_name": "James Doe",
            "dob": "1992-01-01",
            "sex": "F",
            "phone": "03001234568",
            "cnic": "12345-1234567-1",  # Same CNIC
            "address": "124 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_patients_by_name(self):
        """Test searching patients by name."""
        self.client.force_authenticate(user=self.reception_user)
        # Create test patients
        Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )
        Patient.objects.create(
            full_name="Jane Smith",
            father_name="Bob Smith",
            dob=date(1992, 1, 1),
            sex="F",
            phone="03001234568",
            cnic="12345-1234567-2",
            address="124 Main St",
        )

        # Search by name
        response = self.client.get("/api/patients/?query=John")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["full_name"] == "John Doe"

    def test_search_patients_by_phone(self):
        """Test searching patients by phone."""
        self.client.force_authenticate(user=self.reception_user)
        Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )

        response = self.client.get("/api/patients/?query=0300123")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_patients_by_cnic_prefix(self):
        """Test searching patients by CNIC prefix."""
        self.client.force_authenticate(user=self.reception_user)
        Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )

        response = self.client.get("/api/patients/?query=12345")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_patients_pagination(self):
        """Test patient list pagination."""
        self.client.force_authenticate(user=self.reception_user)
        # Create 25 patients
        for i in range(25):
            Patient.objects.create(
                full_name=f"Patient {i}",
                father_name="Test Father",
                dob=date(1990, 1, 1),
                sex="M",
                phone=f"030012345{i:02d}",
                cnic=f"12345-123456{i:01d}-{i % 10}",
                address="Test Address",
            )

        response = self.client.get("/api/patients/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "count" in response.data
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20  # Default page size

    def test_get_patient_detail(self):
        """Test getting patient detail."""
        self.client.force_authenticate(user=self.reception_user)
        patient = Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )

        response = self.client.get(f"/api/patients/{patient.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "John Doe"
        assert response.data["mrn"] == patient.mrn

    def test_create_patient_invalid_phone_format(self):
        """Test creating a patient with invalid phone format."""
        self.client.force_authenticate(user=self.reception_user)
        data = {
            "full_name": "John Doe",
            "father_name": "James Doe",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "invalid_phone",
            "cnic": "12345-1234567-1",
            "address": "123 Main St",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_patient_invalid_phone_prefix(self):
        """Test creating patient with invalid phone prefix."""
        self.client.force_authenticate(user=self.reception_user)
        data = {
            "full_name": "Test Invalid Phone",
            "father_name": "Test Father",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "1234567890",  # Doesn't start with +92 or 0
            "cnic": "12345-1234567-9",
            "address": "Test Address",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check that phone error is in the response
        # (either directly or in error envelope)
        assert ("phone" in response.data) or (
            "phone" in response.data.get("error", {}).get("details", {})
        )

    def test_create_patient_invalid_cnic_format(self):
        """Test creating patient with invalid CNIC format."""
        self.client.force_authenticate(user=self.reception_user)
        data = {
            "full_name": "Test Invalid CNIC",
            "father_name": "Test Father",
            "dob": "1990-01-01",
            "sex": "M",
            "phone": "03001234567",
            "cnic": "12345678901234",  # Wrong format
            "address": "Test Address",
        }
        response = self.client.post("/api/patients/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check that CNIC error is in the response
        # (either directly or in error envelope)
        assert ("cnic" in response.data) or (
            "cnic" in response.data.get("error", {}).get("details", {})
        )


@pytest.mark.django_db
class TestPatientSerializerValidation:
    """Test Patient serializer validation methods directly."""

    def test_validate_phone_invalid_prefix(self):
        """Test phone validation with invalid prefix."""
        from rest_framework import serializers as drf_serializers

        from .serializers import PatientSerializer

        serializer = PatientSerializer()
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_phone("1234567890")
        assert "Phone must start with +92 or 0" in str(exc_info.value)

    def test_validate_phone_valid(self):
        """Test phone validation with valid number."""
        from .serializers import PatientSerializer

        serializer = PatientSerializer()
        result = serializer.validate_phone("+923001234567")
        assert result == "+923001234567"

    def test_validate_cnic_invalid_format(self):
        """Test CNIC validation with invalid format."""
        from rest_framework import serializers as drf_serializers

        from .serializers import PatientSerializer

        serializer = PatientSerializer()
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_cnic("invalid-cnic")
        assert "CNIC must be in format #####-#######-#" in str(exc_info.value)

    def test_validate_cnic_valid(self):
        """Test CNIC validation with valid format."""
        from .serializers import PatientSerializer

        serializer = PatientSerializer()
        result = serializer.validate_cnic("12345-1234567-1")
        assert result == "12345-1234567-1"
