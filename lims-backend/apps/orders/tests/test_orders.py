"""
Tests for the orders app.
"""
import pytest
from decimal import Decimal
from datetime import date
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test, TestPanel
from apps.orders.models import Order, OrderItem


@pytest.fixture
def api_client():
    """Return an API client for making requests."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='adminpass123',
        full_name='Admin User',
        role='Admin'
    )
    return user


@pytest.fixture
def receptionist_user(db):
    """Create and return a receptionist user."""
    user = User.objects.create_user(
        username='receptionist',
        email='receptionist@test.com',
        password='receppass123',
        full_name='Reception User',
        role='Receptionist'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def patient(db, receptionist_user):
    """Create and return a patient."""
    return Patient.objects.create(
        first_name='John',
        last_name='Doe',
        date_of_birth=date(1990, 5, 15),
        gender='Male',
        phone='03001234567',
        created_by=receptionist_user
    )


@pytest.fixture
def test_category(db):
    """Create and return a test category."""
    return TestCategory.objects.create(name='Hematology')


@pytest.fixture
def test_instance(db, test_category):
    """Create and return a test."""
    return Test.objects.create(
        category=test_category,
        test_code='CBC',
        test_name='Complete Blood Count',
        sample_type='EDTA Blood',
        price=Decimal('800.00'),
        turnaround_time=4
    )


@pytest.fixture
def test_panel(db, test_category, test_instance):
    """Create and return a test panel."""
    panel = TestPanel.objects.create(
        panel_code='CBC_PANEL',
        panel_name='CBC Panel',
        category=test_category,
        sample_type='EDTA Blood',
        price=Decimal('700.00'),
        turnaround_time=4
    )
    panel.tests.add(test_instance)
    return panel


@pytest.fixture
def order(db, patient, receptionist_user, test_instance):
    """Create and return an order."""
    order = Order.objects.create(
        patient=patient,
        ordered_by=receptionist_user,
        status='pending'
    )
    OrderItem.objects.create(
        order=order,
        test=test_instance,
        price=test_instance.price
    )
    order.calculate_total()
    return order


@pytest.mark.django_db
class TestOrderModel:
    """Tests for the Order model."""

    def test_create_order(self, patient, receptionist_user):
        """Test creating an order."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user
        )
        assert order.order_id is not None
        assert order.order_id.startswith('ORD-')
        assert order.status == 'pending'

    def test_order_id_generation(self, patient, receptionist_user):
        """Test auto-generation of order ID."""
        order1 = Order.objects.create(patient=patient, ordered_by=receptionist_user)
        order2 = Order.objects.create(patient=patient, ordered_by=receptionist_user)

        assert order1.order_id != order2.order_id

    def test_calculate_total(self, order, test_instance):
        """Test order total calculation."""
        assert order.total_amount == test_instance.price
        assert order.net_amount == test_instance.price

    def test_order_with_discount(self, patient, receptionist_user, test_instance):
        """Test order with discount."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            discount=Decimal('100.00')
        )
        OrderItem.objects.create(
            order=order,
            test=test_instance,
            price=test_instance.price
        )
        order.calculate_total()

        assert order.total_amount == Decimal('800.00')
        assert order.net_amount == Decimal('700.00')


@pytest.mark.django_db
class TestOrderItemModel:
    """Tests for the OrderItem model."""

    def test_create_order_item_with_test(self, order, test_instance):
        """Test creating an order item with a test."""
        item = order.items.first()
        assert item.test == test_instance
        assert item.price == test_instance.price

    def test_create_order_item_with_panel(self, patient, receptionist_user, test_panel):
        """Test creating an order item with a panel."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user
        )
        item = OrderItem.objects.create(
            order=order,
            panel=test_panel,
            price=test_panel.price
        )
        assert item.panel == test_panel
        assert item.price == test_panel.price


@pytest.mark.django_db
class TestOrderViewSet:
    """Tests for the Order ViewSet."""

    def test_list_orders(self, authenticated_client, order):
        """Test listing orders."""
        response = authenticated_client.get('/api/v1/orders/orders/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_order_with_tests(self, authenticated_client, patient, test_instance):
        """Test creating an order with tests."""
        response = authenticated_client.post('/api/v1/orders/orders/', {
            'patient': patient.id,
            'test_ids': [test_instance.id],
            'notes': 'Test order'
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['order_id'] is not None

    def test_create_order_with_panel(self, authenticated_client, patient, test_panel):
        """Test creating an order with a panel."""
        response = authenticated_client.post('/api/v1/orders/orders/', {
            'patient': patient.id,
            'panel_ids': [test_panel.id]
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_order(self, authenticated_client, order):
        """Test retrieving an order."""
        response = authenticated_client.get(f'/api/v1/orders/orders/{order.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'items' in response.data

    def test_cancel_order(self, authenticated_client, order):
        """Test canceling an order."""
        response = authenticated_client.post(f'/api/v1/orders/orders/{order.id}/cancel/')
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == 'cancelled'

    def test_cancel_completed_order_fails(self, authenticated_client, order):
        """Test that canceling a completed order fails."""
        order.status = 'completed'
        order.save()
        response = authenticated_client.post(f'/api/v1/orders/orders/{order.id}/cancel/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
