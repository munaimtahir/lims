"""
Comprehensive tests for core app models and views.
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import User
from apps.core.models import SystemSettings


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

    @pytest.fixture
    def non_admin_user(self):
        """Create non-admin user."""
        return User.objects.create_user(
            username="receptionist",
            email="reception@test.com",
            password="testpass123",
            full_name="Reception User",
            role="Receptionist",
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

    def test_upload_report_header_image(self, api_client, user):
        """Test uploading report header image."""
        SystemSettings.objects.create(lab_name="Test Lab")
        api_client.force_authenticate(user=user)
        image_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\x0bIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\x0d\x0a\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        upload = SimpleUploadedFile("header.png", image_content, content_type="image/png")
        response = api_client.post(
            "/api/v1/core/settings/report-header-image/",
            {"report_header_image": upload},
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["report_header_image"]

    def test_upload_report_header_image_unauthorized(self, api_client, non_admin_user):
        """Test unauthorized upload of report header image."""
        SystemSettings.objects.create(lab_name="Test Lab")
        api_client.force_authenticate(user=non_admin_user)
        upload = SimpleUploadedFile("header.png", b"file", content_type="image/png")
        response = api_client.post(
            "/api/v1/core/settings/report-header-image/",
            {"report_header_image": upload},
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_settings_with_header_image(self, api_client, user):
        """Test settings GET includes header image URL."""
        settings = SystemSettings.objects.create(lab_name="Test Lab")
        settings.report_header_image = SimpleUploadedFile(
            "header.png", b"file", content_type="image/png"
        )
        settings.save()
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/core/settings/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["report_header_image"]
