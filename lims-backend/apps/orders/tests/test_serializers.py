"""
Tests for order serializers.
"""
import pytest
from decimal import Decimal
from datetime import date
from rest_framework.test import APIRequestFactory
from apps.orders.serializers import OrderSerializer, OrderListSerializer
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test, TestPanel
from apps.orders.models import Order, OrderItem


@pytest.mark.django_db
class TestOrderSerializer:
    """Test OrderSerializer."""
    
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
    def test_panel(self, category, test_instance):
        """Create test panel."""
        panel = TestPanel.objects.create(
            panel_code="PANEL1",
            panel_name="Test Panel",
            category=category,
            sample_type="Blood",
            price=Decimal("100.00"),
            turnaround_time=24,
        )
        panel.tests.add(test_instance)
        return panel
    
    def test_create_order_with_tests(self, user, patient, test_instance):
        """Test creating order with test_ids."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = OrderSerializer(
            context={"request": request}
        )
        # Use validated_data format (patient object, not ID)
        validated_data = {
            "patient": patient,
            "test_ids": [test_instance.id],
            "status": "NEW",
        }
        order = serializer.create(validated_data)
        
        assert order.patient == patient
        assert order.ordered_by == user
        assert order.items.count() == 1
        assert order.items.first().test == test_instance
        assert order.total_amount == test_instance.price
    
    def test_create_order_with_panels(self, user, patient, test_panel):
        """Test creating order with panel_ids."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = OrderSerializer(
            context={"request": request}
        )
        validated_data = {
            "patient": patient,
            "panel_ids": [test_panel.id],
            "status": "NEW",
        }
        order = serializer.create(validated_data)
        
        assert order.patient == patient
        assert order.ordered_by == user
        assert order.items.count() == 1
        assert order.items.first().panel == test_panel
        assert order.total_amount == test_panel.price
    
    def test_create_order_with_tests_and_panels(self, user, patient, test_instance, test_panel):
        """Test creating order with both test_ids and panel_ids."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = OrderSerializer(
            context={"request": request}
        )
        validated_data = {
            "patient": patient,
            "test_ids": [test_instance.id],
            "panel_ids": [test_panel.id],
            "status": "NEW",
        }
        order = serializer.create(validated_data)
        
        assert order.items.count() == 2
        assert order.total_amount == test_instance.price + test_panel.price
    
    def test_create_order_with_invalid_test_id(self, user, patient, test_instance):
        """Test creating order with non-existent test_id."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = OrderSerializer(
            context={"request": request}
        )
        validated_data = {
            "patient": patient,
            "test_ids": [test_instance.id, 99999],  # Invalid ID
            "status": "NEW",
        }
        order = serializer.create(validated_data)
        
        # Should create order with only valid test
        assert order.items.count() == 1
        assert order.items.first().test == test_instance
    
    def test_create_order_with_invalid_panel_id(self, user, patient, test_panel):
        """Test creating order with non-existent panel_id."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = OrderSerializer(
            context={"request": request}
        )
        validated_data = {
            "patient": patient,
            "panel_ids": [test_panel.id, 99999],  # Invalid ID
            "status": "NEW",
        }
        order = serializer.create(validated_data)
        
        # Should create order with only valid panel
        assert order.items.count() == 1
        assert order.items.first().panel == test_panel
    
    def test_create_order_with_discount(self, user, patient, test_instance):
        """Test creating order with discount."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = OrderSerializer(
            context={"request": request}
        )
        validated_data = {
            "patient": patient,
            "test_ids": [test_instance.id],
            "status": "NEW",
            "discount": Decimal("10.00"),
        }
        order = serializer.create(validated_data)
        
        assert order.discount == Decimal("10.00")
        assert order.total_amount == test_instance.price
        assert order.net_amount == test_instance.price - Decimal("10.00")
    
    def test_create_order_no_user(self, patient, test_instance):
        """Test creating order without authenticated user."""
        factory = APIRequestFactory()
        request = factory.post('/')
        # No user set
        
        serializer = OrderSerializer(
            context={"request": request}
        )
        validated_data = {
            "patient": patient,
            "test_ids": [test_instance.id],
            "status": "NEW",
        }
        order = serializer.create(validated_data)
        
        assert order.patient == patient
        assert order.ordered_by is None


@pytest.mark.django_db
class TestOrderListSerializer:
    """Test OrderListSerializer."""
    
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
    def order(self, patient, user, test_instance):
        """Create test order."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=user,
            status="NEW",
        )
        OrderItem.objects.create(
            order=order,
            test=test_instance,
            price=test_instance.price,
        )
        order.calculate_total()
        return order
    
    def test_get_item_count(self, order):
        """Test get_item_count method."""
        serializer = OrderListSerializer(order)
        assert serializer.get_item_count(order) == 1
        
        # Add another item
        OrderItem.objects.create(
            order=order,
            test=order.items.first().test,
            price=Decimal("30.00"),
        )
        assert serializer.get_item_count(order) == 2
