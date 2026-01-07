"""
Tests for core serializers.
"""
import pytest
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.core.serializers import LabTerminalSerializer, SystemSettingsSerializer
from apps.core.models import LabTerminal, SystemSettings
from apps.accounts.models import User


@pytest.mark.django_db
class TestLabTerminalSerializer:
    """Test LabTerminalSerializer."""
    
    def test_validate_range_start_greater_than_end(self):
        """Test validation when start >= end."""
        serializer = LabTerminalSerializer()
        data = {
            "code": "TERM1",
            "name": "Terminal 1",
            "offline_range_start": 1000,
            "offline_range_end": 500,
        }
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate(data)
        assert "offline_range_end" in str(exc_info.value)
    
    def test_validate_range_start_equal_to_end(self):
        """Test validation when start == end."""
        serializer = LabTerminalSerializer()
        data = {
            "code": "TERM1",
            "name": "Terminal 1",
            "offline_range_start": 1000,
            "offline_range_end": 1000,
        }
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate(data)
        assert "offline_range_end" in str(exc_info.value)
    
    def test_validate_valid_range(self):
        """Test validation with valid range."""
        serializer = LabTerminalSerializer()
        data = {
            "code": "TERM1",
            "name": "Terminal 1",
            "offline_range_start": 1000,
            "offline_range_end": 2000,
        }
        result = serializer.validate(data)
        assert result == data
    
    def test_validate_no_range(self):
        """Test validation without range values."""
        serializer = LabTerminalSerializer()
        data = {
            "code": "TERM1",
            "name": "Terminal 1",
        }
        result = serializer.validate(data)
        assert result == data


@pytest.mark.django_db
class TestSystemSettingsSerializer:
    """Test SystemSettingsSerializer."""
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            full_name="Admin User",
            role="Admin",
        )
    
    def test_validate_email_port_too_low(self, user):
        """Test validation with email port too low."""
        serializer = SystemSettingsSerializer()
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate_email_port(0)
        assert "Email port must be between 1 and 65535" in str(exc_info.value)
    
    def test_validate_email_port_too_high(self, user):
        """Test validation with email port too high."""
        serializer = SystemSettingsSerializer()
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate_email_port(65536)
        assert "Email port must be between 1 and 65535" in str(exc_info.value)
    
    def test_validate_email_port_valid(self, user):
        """Test validation with valid email port."""
        serializer = SystemSettingsSerializer()
        result = serializer.validate_email_port(587)
        assert result == 587
    
    def test_validate_email_port_edge_cases(self, user):
        """Test validation with edge case email ports."""
        serializer = SystemSettingsSerializer()
        # Minimum valid
        result = serializer.validate_email_port(1)
        assert result == 1
        # Maximum valid
        result = serializer.validate_email_port(65535)
        assert result == 65535
    
    def test_validate_tax_rate_negative(self, user):
        """Test validation with negative tax rate."""
        serializer = SystemSettingsSerializer()
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate_tax_rate(-1)
        assert "Tax rate cannot be negative" in str(exc_info.value)
    
    def test_validate_tax_rate_valid(self, user):
        """Test validation with valid tax rate."""
        serializer = SystemSettingsSerializer()
        result = serializer.validate_tax_rate(0.15)
        assert result == 0.15
    
    def test_validate_tax_rate_zero(self, user):
        """Test validation with zero tax rate."""
        serializer = SystemSettingsSerializer()
        result = serializer.validate_tax_rate(0)
        assert result == 0
