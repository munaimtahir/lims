"""
Tests for the patients app.
"""
import pytest
from datetime import date, timedelta
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.patients.models import Patient


@pytest.fixture
def api_client():
    """Return an API client for making requests."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    user = User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="adminpass123",
        full_name="Admin User",
        role="Admin",
    )
    return user


@pytest.fixture
def receptionist_user(db):
    """Create and return a receptionist user."""
    user = User.objects.create_user(
        username="receptionist",
        email="receptionist@test.com",
        password="receppass123",
        full_name="Reception User",
        role="Receptionist",
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def sample_patient(db, receptionist_user):
    """Create and return a sample patient."""
    patient = Patient.objects.create(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
        gender="Male",
        phone="03001234567",
        email="john.doe@test.com",
        national_id="1234567890123",
        address="123 Test Street",
        created_by=receptionist_user,
    )
    return patient


@pytest.mark.django_db
class TestPatientModel:
    """Tests for the Patient model."""

    def test_create_patient(self, receptionist_user):
        """Test creating a patient."""
        patient = Patient.objects.create(
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 8, 22),
            gender="Female",
            phone="03007654321",
            created_by=receptionist_user,
        )
        assert patient.first_name == "Jane"
        assert patient.last_name == "Smith"
        assert patient.patient_id is not None
        assert patient.patient_id.startswith("P-")

    def test_patient_id_generation(self, receptionist_user):
        """Test auto-generation of patient ID."""
        patient1 = Patient.objects.create(
            first_name="Patient",
            last_name="One",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="03001111111",
            created_by=receptionist_user,
        )
        patient2 = Patient.objects.create(
            first_name="Patient",
            last_name="Two",
            date_of_birth=date(1990, 2, 2),
            gender="Female",
            phone="03002222222",
            created_by=receptionist_user,
        )

        # Both should have unique patient IDs
        assert patient1.patient_id != patient2.patient_id
        # IDs should be sequential
        id1 = int(patient1.patient_id.split("-")[-1])
        id2 = int(patient2.patient_id.split("-")[-1])
        assert id2 == id1 + 1

    def test_patient_age_calculation(self, sample_patient):
        """Test age calculation from date of birth."""
        # sample_patient has DOB of 1990-05-15
        today = date.today()
        expected_age = today.year - 1990
        if (today.month, today.day) < (5, 15):
            expected_age -= 1
        assert sample_patient.age == expected_age

    def test_patient_full_name(self, sample_patient):
        """Test full name property."""
        assert sample_patient.get_full_name() == "John Doe"

    def test_patient_str(self, sample_patient):
        """Test string representation of patient."""
        assert sample_patient.patient_id in str(sample_patient)
        assert "John Doe" in str(sample_patient)


@pytest.mark.django_db
class TestPatientViewSet:
    """Tests for the Patient ViewSet."""

    def test_create_patient(self, authenticated_client, admin_user):
        """Test creating a patient via API."""
        response = authenticated_client.post(
            "/api/v1/patients/",
            {
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-01-15",
                "gender": "Male",
                "phone": "03009876543",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["first_name"] == "Test"
        assert "patient_id" in response.data["data"]

    def test_create_patient_validation_phone(self, authenticated_client):
        """Test patient creation with invalid phone."""
        response = authenticated_client.post(
            "/api/v1/patients/",
            {
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-01-15",
                "gender": "Male",
                "phone": "123",  # Too short
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_patient_future_dob(self, authenticated_client):
        """Test patient creation with future date of birth."""
        future_date = date.today() + timedelta(days=1)
        response = authenticated_client.post(
            "/api/v1/patients/",
            {
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": future_date.isoformat(),
                "gender": "Male",
                "phone": "03009876543",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_patients(self, authenticated_client, sample_patient):
        """Test listing patients."""
        response = authenticated_client.get("/api/v1/patients/")
        assert response.status_code == status.HTTP_200_OK
        # Paginated response wraps our data differently
        # It should have results or our custom format
        assert (
            "results" in response.data
            or "data" in response.data
            or "success" in response.data
        )

    def test_retrieve_patient(self, authenticated_client, sample_patient):
        """Test retrieving a single patient."""
        response = authenticated_client.get(f"/api/v1/patients/{sample_patient.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["first_name"] == "John"

    def test_update_patient(self, authenticated_client, sample_patient):
        """Test updating a patient."""
        response = authenticated_client.patch(
            f"/api/v1/patients/{sample_patient.id}/", {"phone": "03001112233"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["phone"] == "03001112233"

    def test_search_patients(self, authenticated_client, sample_patient):
        """Test searching patients."""
        response = authenticated_client.get("/api/v1/patients/", {"search": "John"})
        assert response.status_code == status.HTTP_200_OK

    def test_patient_history(self, authenticated_client, sample_patient):
        """Test patient history endpoint."""
        response = authenticated_client.get(
            f"/api/v1/patients/{sample_patient.id}/history/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "orders" in response.data["data"]
        assert "patient" in response.data["data"]

    def test_unauthenticated_access(self, api_client, sample_patient):
        """Test that unauthenticated access is denied."""
        response = api_client.get("/api/v1/patients/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
