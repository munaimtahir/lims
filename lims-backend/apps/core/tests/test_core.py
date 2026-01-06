"""
Comprehensive tests for core app models and views.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.core.models import LabTerminal, SystemSettings


@pytest.mark.django_db
class TestLabTerminalModel:
    """Test LabTerminal model."""
    
    def test_create_terminal(self):
        """Test creating a lab terminal."""
        terminal = LabTerminal.objects.create(
            code="RECEP-1",
            name="Reception Terminal 1",
            offline_range_start=1000,
            offline_range_end=2000,
        )
        assert terminal.code == "RECEP-1"
        assert terminal.name == "Reception Terminal 1"
        assert terminal.offline_range_start == 1000
        assert terminal.offline_range_end == 2000
        assert terminal.offline_current == 0
        assert terminal.is_active is True
    
    def test_terminal_str(self):
        """Test terminal string representation."""
        terminal = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab Terminal 1",
            offline_range_start=1000,
            offline_range_end=2000,
        )
        assert str(terminal) == "LAB1-PC - Lab Terminal 1"
    
    def test_terminal_clean_validation(self):
        """Test terminal validation."""
        terminal = LabTerminal(
            code="TEST",
            name="Test",
            offline_range_start=2000,
            offline_range_end=1000,  # Invalid: start > end
        )
        with pytest.raises(ValidationError):
            terminal.clean()
    
    def test_get_next_offline_mrn(self):
        """Test getting next offline MRN."""
        terminal = LabTerminal.objects.create(
            code="TEST",
            name="Test Terminal",
            offline_range_start=1000,
            offline_range_end=1005,
        )
        
        # First MRN should be start of range
        mrn1 = terminal.get_next_offline_mrn()
        assert mrn1 == 1000
        
        # Refresh from DB
        terminal.refresh_from_db()
        assert terminal.offline_current == 1000
        
        # Next MRN should increment
        mrn2 = terminal.get_next_offline_mrn()
        assert mrn2 == 1001
        
        terminal.refresh_from_db()
        assert terminal.offline_current == 1001
    
    def test_get_next_offline_mrn_exhausted(self):
        """Test MRN range exhaustion."""
        terminal = LabTerminal.objects.create(
            code="TEST",
            name="Test Terminal",
            offline_range_start=1000,
            offline_range_end=1002,
            offline_current=1001,  # One left
        )
        
        # Should get last MRN
        mrn = terminal.get_next_offline_mrn()
        assert mrn == 1002
        
        # Should fail on next attempt
        terminal.refresh_from_db()
        with pytest.raises(ValidationError):
            terminal.get_next_offline_mrn()


@pytest.mark.django_db
class TestSystemSettingsModel:
    """Test SystemSettings model."""
    
    def test_create_settings(self):
        """Test creating system settings."""
        settings = SystemSettings.objects.create(
            lab_name="Test Lab",
            lab_address="123 Test St",
            lab_phone="123-456-7890",
            currency="USD",
            tax_rate=Decimal("10.00"),
        )
        assert settings.lab_name == "Test Lab"
        assert settings.currency == "USD"
        assert settings.tax_rate == Decimal("10.00")
    
    def test_settings_singleton_pattern(self):
        """Test singleton pattern - only one settings instance."""
        settings1 = SystemSettings.objects.create(
            lab_name="Lab 1",
            currency="USD",
        )
        
        # Creating another should update existing
        settings2 = SystemSettings.objects.create(
            lab_name="Lab 2",
            currency="PKR",
        )
        
        # Should be the same instance
        assert settings1.id == settings2.id
        assert SystemSettings.objects.count() == 1
        settings1.refresh_from_db()
        assert settings1.lab_name == "Lab 2"
    
    def test_get_settings_classmethod(self):
        """Test get_settings classmethod."""
        # Should create if doesn't exist
        settings = SystemSettings.get_settings()
        assert settings is not None
        assert isinstance(settings, SystemSettings)
        
        # Should return same instance
        settings2 = SystemSettings.get_settings()
        assert settings.id == settings2.id
    
    def test_settings_str(self):
        """Test settings string representation."""
        settings = SystemSettings.objects.create(lab_name="Test Lab")
        assert "Test Lab" in str(settings)


@pytest.mark.django_db
class TestLabTerminalViewSet:
    """Test LabTerminalViewSet API."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
            role="Admin",
        )
    
    @pytest.fixture
    def terminal(self):
        """Create test terminal."""
        return LabTerminal.objects.create(
            code="TEST-1",
            name="Test Terminal",
            offline_range_start=1000,
            offline_range_end=2000,
        )
    
    def test_list_terminals(self, api_client, user, terminal):
        """Test listing terminals."""
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/core/terminals/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
    
    def test_create_terminal(self, api_client, user):
        """Test creating a terminal."""
        api_client.force_authenticate(user=user)
        data = {
            "code": "NEW-TERM",
            "name": "New Terminal",
            "offline_range_start": 2000,
            "offline_range_end": 3000,
        }
        response = api_client.post("/api/v1/core/terminals/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["code"] == "NEW-TERM"
    
    def test_get_next_mrn(self, api_client, user, terminal):
        """Test getting next MRN."""
        api_client.force_authenticate(user=user)
        response = api_client.post(f"/api/v1/core/terminals/{terminal.id}/get_next_mrn/")
        assert response.status_code == status.HTTP_200_OK
        assert "next_mrn" in response.data
        assert response.data["next_mrn"] == 1000
    
    def test_get_next_mrn_inactive_terminal(self, api_client, user, terminal):
        """Test getting MRN from inactive terminal."""
        terminal.is_active = False
        terminal.save()
        api_client.force_authenticate(user=user)
        response = api_client.post(f"/api/v1/core/terminals/{terminal.id}/get_next_mrn/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_reset_range(self, api_client, user, terminal):
        """Test resetting MRN range."""
        terminal.offline_current = 1500
        terminal.save()
        api_client.force_authenticate(user=user)
        response = api_client.post(f"/api/v1/core/terminals/{terminal.id}/reset_range/")
        assert response.status_code == status.HTTP_200_OK
        terminal.refresh_from_db()
        assert terminal.offline_current == 0
    
    def test_reset_range_non_admin(self, api_client, terminal):
        """Test reset range requires admin."""
        user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="testpass123",
            full_name="Regular User",
            role="Receptionist",
        )
        api_client.force_authenticate(user=user)
        response = api_client.post(f"/api/v1/core/terminals/{terminal.id}/reset_range/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_active_terminals(self, api_client, user, terminal):
        """Test getting active terminals."""
        # Create inactive terminal
        LabTerminal.objects.create(
            code="INACTIVE",
            name="Inactive Terminal",
            offline_range_start=3000,
            offline_range_end=4000,
            is_active=False,
        )
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/core/terminals/active/")
        assert response.status_code == status.HTTP_200_OK
        assert all(term["is_active"] for term in response.data["results"])


@pytest.mark.django_db
class TestSystemSettingsViewSet:
    """Test SystemSettingsViewSet API."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
            role="Admin",
        )
    
    def test_get_settings(self, api_client, user):
        """Test getting system settings."""
        SystemSettings.objects.create(
            lab_name="Test Lab",
            currency="USD",
        )
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/core/settings/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["lab_name"] == "Test Lab"
    
    def test_update_settings(self, api_client, user):
        """Test updating system settings."""
        SystemSettings.objects.create(
            lab_name="Old Lab",
            currency="USD",
        )
        api_client.force_authenticate(user=user)
        data = {"lab_name": "New Lab", "currency": "PKR"}
        response = api_client.put("/api/v1/core/settings/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["lab_name"] == "New Lab"
        assert response.data["currency"] == "PKR"
    
    def test_patch_settings(self, api_client, user):
        """Test patching system settings."""
        SystemSettings.objects.create(
            lab_name="Test Lab",
            currency="USD",
        )
        api_client.force_authenticate(user=user)
        data = {"lab_name": "Updated Lab"}
        response = api_client.patch("/api/v1/core/settings/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["lab_name"] == "Updated Lab"
    
    def test_settings_validation(self, api_client, user):
        """Test settings validation."""
        SystemSettings.objects.create(lab_name="Test Lab")
        api_client.force_authenticate(user=user)
        data = {"email_port": 70000}  # Invalid port
        response = api_client.patch("/api/v1/core/settings/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_settings_tax_rate_validation(self, api_client, user):
        """Test tax rate validation."""
        SystemSettings.objects.create(lab_name="Test Lab")
        api_client.force_authenticate(user=user)
        data = {"tax_rate": -10}  # Negative tax rate
        response = api_client.patch("/api/v1/core/settings/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


