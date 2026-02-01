"""
Tests for laboratory serializers.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.laboratory.serializers import ReferenceRangeSerializer
from apps.laboratory.models import TestCategory, Test, TestParameter, ReferenceRange, Parameter
from apps.accounts.models import User


@pytest.mark.django_db
class TestReferenceRangeSerializer:
    """Test ReferenceRangeSerializer."""
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass",
            full_name="Test User",
            role="Admin",
        )
    
    @pytest.fixture
    def category(self):
        """Create test category."""
        return TestCategory.objects.create(name="Hematology")
    
    @pytest.fixture
    def test_instance(self, category):
        """Create test instance."""
        return Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
    
    @pytest.fixture
    def parameter(self, test_instance):
        """Create test parameter."""
        parameter = Parameter.objects.create(
            parameter_id="p1",
            parameter_name="WBC",
            unit="10*3/uL",
        )
        return TestParameter.objects.create(
            test=test_instance,
            parameter=parameter,
        )
    
    def test_validate_age_min_greater_than_max(self, parameter, user):
        """Test validation when age_min >= age_max."""
        serializer = ReferenceRangeSerializer()
        data = {
            "parameter": parameter,
            "age_min": 50,
            "age_max": 40,
        }
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate(data)
        assert "age_max" in str(exc_info.value)
    
    def test_validate_reference_min_greater_than_max(self, parameter, user):
        """Test validation when reference_min >= reference_max."""
        serializer = ReferenceRangeSerializer()
        data = {
            "parameter": parameter,
            "reference_min": 20.0,
            "reference_max": 10.0,
        }
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate(data)
        assert "reference_max" in str(exc_info.value)
    
    def test_validate_valid_data(self, parameter, user):
        """Test validation with valid data."""
        serializer = ReferenceRangeSerializer()
        data = {
            "parameter": parameter,
            "age_min": 18,
            "age_max": 65,
            "reference_min": 4.0,
            "reference_max": 11.0,
            "gender": "Both",
        }
        result = serializer.validate(data)
        assert result == data
    
    def test_create_reference_range(self, parameter, user):
        """Test creating a reference range."""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        serializer = ReferenceRangeSerializer(
            context={"request": request}
        )
        data = {
            "parameter": parameter,
            "age_min": 18,
            "age_max": 65,
            "reference_min": 4.0,
            "reference_max": 11.0,
            "gender": "Both",
        }
        reference_range = serializer.create(data)
        
        assert reference_range.parameter == parameter
        assert reference_range.version == 1
        assert reference_range.is_active is True
        assert reference_range.created_by == user
    
    def test_create_reference_range_deactivates_old(self, parameter, user):
        """Test that creating a new range deactivates old ranges."""
        from rest_framework.test import APIRequestFactory
        
        # Create old range
        old_range = ReferenceRange.objects.create(
            parameter=parameter,
            age_min=18,
            age_max=65,
            reference_min=4.0,
            reference_max=11.0,
            gender="Both",
            version=1,
            is_active=True,
            created_by=user,
        )
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        serializer = ReferenceRangeSerializer(
            context={"request": request}
        )
        data = {
            "parameter": parameter,
            "age_min": 18,
            "age_max": 65,
            "reference_min": 5.0,  # Different value
            "reference_max": 12.0,
            "gender": "Both",
        }
        new_range = serializer.create(data)
        
        old_range.refresh_from_db()
        assert old_range.is_active is False
        assert new_range.version == 2
        assert new_range.is_active is True
    
    def test_create_reference_range_increments_version(self, parameter, user):
        """Test that version is incremented correctly."""
        from rest_framework.test import APIRequestFactory
        
        # Create first range
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        serializer = ReferenceRangeSerializer(
            context={"request": request}
        )
        data = {
            "parameter": parameter,
            "age_min": 18,
            "age_max": 65,
            "reference_min": 4.0,
            "reference_max": 11.0,
            "gender": "Both",
        }
        range1 = serializer.create(data)
        assert range1.version == 1
        
        # Create second range (different age range, so won't deactivate first)
        data2 = {
            "parameter": parameter,
            "age_min": 0,
            "age_max": 17,
            "reference_min": 3.0,
            "reference_max": 10.0,
            "gender": "Both",
        }
        range2 = serializer.create(data2)
        assert range2.version == 1  # Different age range, starts at 1
        
        # Create third range (same age range as first, should increment)
        data3 = {
            "parameter": parameter,
            "age_min": 18,
            "age_max": 65,
            "reference_min": 4.5,
            "reference_max": 11.5,
            "gender": "Both",
        }
        range3 = serializer.create(data3)
        assert range3.version == 2  # Should increment from range1
    
    def test_create_reference_range_no_user(self, parameter):
        """Test creating reference range without authenticated user."""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/')
        # No user set
        
        serializer = ReferenceRangeSerializer(
            context={"request": request}
        )
        data = {
            "parameter": parameter,
            "age_min": 18,
            "age_max": 65,
            "reference_min": 4.0,
            "reference_max": 11.0,
            "gender": "Both",
        }
        reference_range = serializer.create(data)
        
        assert reference_range.parameter == parameter
        assert reference_range.created_by is None
