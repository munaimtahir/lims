"""
Tests for patient serializers.
"""
import pytest
from datetime import date
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.patients.serializers import PatientSerializer, PatientCreateSerializer
from apps.patients.models import Patient
from apps.accounts.models import User


@pytest.mark.django_db
class TestPatientSerializer:
    """Test PatientSerializer."""
    
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
    
    def test_validate_phone_valid(self, user):
        """Test phone validation with valid phone."""
        serializer = PatientSerializer()
        result = serializer.validate_phone("1234567890")
        assert result == "1234567890"
    
    def test_validate_phone_empty(self, user):
        """Test phone validation with empty phone."""
        serializer = PatientSerializer()
        with pytest.raises(DRFValidationError):
            serializer.validate_phone("")
    
    def test_validate_phone_too_short(self, user):
        """Test phone validation with too short phone."""
        serializer = PatientSerializer()
        with pytest.raises(DRFValidationError):
            serializer.validate_phone("123")
    
    def test_validate_date_of_birth_valid(self, user):
        """Test date of birth validation with valid date."""
        serializer = PatientSerializer()
        result = serializer.validate_date_of_birth(date(1990, 1, 1))
        assert result == date(1990, 1, 1)
    
    def test_validate_date_of_birth_future(self, user):
        """Test date of birth validation with future date."""
        serializer = PatientSerializer()
        future_date = date.today() + date.resolution
        with pytest.raises(DRFValidationError):
            serializer.validate_date_of_birth(future_date)


@pytest.mark.django_db
class TestPatientCreateSerializer:
    """Test PatientCreateSerializer."""
    
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
    
    def test_validate_phone_valid(self, user):
        """Test phone validation with valid phone."""
        serializer = PatientCreateSerializer()
        result = serializer.validate_phone("1234567890")
        assert result == "1234567890"
    
    def test_validate_phone_empty(self, user):
        """Test phone validation with empty phone."""
        serializer = PatientCreateSerializer()
        with pytest.raises(DRFValidationError):
            serializer.validate_phone("")
    
    def test_validate_phone_too_short(self, user):
        """Test phone validation with too short phone."""
        serializer = PatientCreateSerializer()
        with pytest.raises(DRFValidationError):
            serializer.validate_phone("123")
