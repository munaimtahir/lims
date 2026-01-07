"""
Tests for results serializers.
"""
import pytest
from decimal import Decimal
from datetime import date
from rest_framework.test import APIRequestFactory
from apps.results.serializers import TestResultSerializer
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test, TestParameter
from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult


@pytest.mark.django_db
class TestTestResultSerializer:
    """Test TestResultSerializer."""
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass",
            full_name="Test User",
            role="Lab Technician",
        )
    
    @pytest.fixture
    def patient(self, user):
        """Create test patient."""
        return Patient.objects.create(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="1234567890",
            created_by=user,
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
        return TestParameter.objects.create(
            test=test_instance,
            parameter_name="WBC",
            unit="10*3/uL",
        )
    
    @pytest.fixture
    def order(self, patient, user):
        """Create test order."""
        return Order.objects.create(
            patient=patient,
            ordered_by=user,
            status="in_progress",
        )
    
    @pytest.fixture
    def order_item(self, order, test_instance):
        """Create test order item."""
        return OrderItem.objects.create(
            order=order,
            test=test_instance,
            price=test_instance.price,
        )
    
    def test_create_result_with_user(self, user, order_item, parameter):
        """Test creating result with authenticated user."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = TestResultSerializer(
            context={"request": request}
        )
        # Use validated_data format (objects, not IDs)
        validated_data = {
            "order_item": order_item,
            "test_parameter": parameter,
            "result_value": "5.0",
            "remarks": "Normal value",
        }
        result = serializer.create(validated_data)
        
        assert result.order_item == order_item
        assert result.test_parameter == parameter
        assert result.result_value == "5.0"
        assert result.entered_by == user
        assert result.entered_at is not None
    
    def test_create_result_without_user(self, order_item, parameter):
        """Test creating result without authenticated user."""
        factory = APIRequestFactory()
        request = factory.post('/')
        # No user set
        
        serializer = TestResultSerializer(
            context={"request": request}
        )
        validated_data = {
            "order_item": order_item,
            "test_parameter": parameter,
            "result_value": "5.0",
        }
        result = serializer.create(validated_data)
        
        assert result.order_item == order_item
        assert result.test_parameter == parameter
        assert result.entered_by is None
