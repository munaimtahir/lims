"""
Tests for the samples app.
"""
import pytest
from decimal import Decimal
from datetime import date
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test
from apps.orders.models import Order, OrderItem
from apps.samples.models import SampleCollection


@pytest.fixture
def api_client():
    """Return an API client for making requests."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='adminpass123',
        full_name='Admin User',
        role='Admin'
    )


@pytest.fixture
def phlebotomist_user(db):
    """Create and return a phlebotomist user."""
    return User.objects.create_user(
        username='phlebotomist',
        email='phlebotomist@test.com',
        password='phlebopass123',
        full_name='Phlebotomist User',
        role='Phlebotomist'
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def patient(db, admin_user):
    """Create and return a patient."""
    return Patient.objects.create(
        first_name='John',
        last_name='Doe',
        date_of_birth=date(1990, 5, 15),
        gender='Male',
        phone='03001234567',
        created_by=admin_user
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
def order(db, patient, admin_user, test_instance):
    """Create and return an order."""
    order = Order.objects.create(
        patient=patient,
        ordered_by=admin_user,
        status='pending'
    )
    OrderItem.objects.create(
        order=order,
        test=test_instance,
        price=test_instance.price
    )
    order.calculate_total()
    return order


@pytest.fixture
def sample(db, order, phlebotomist_user):
    """Create and return a sample collection."""
    sample = SampleCollection.objects.create(
        order=order,
        sample_type='EDTA Blood',
        barcode='BC-001',
        status='pending'
    )
    sample.order_items.set(order.items.all())
    return sample


@pytest.mark.django_db
class TestSampleCollectionModel:
    """Tests for the SampleCollection model."""

    def test_create_sample(self, order):
        """Test creating a sample collection."""
        sample = SampleCollection.objects.create(
            order=order,
            sample_type='EDTA Blood',
            barcode='BC-002'
        )
        assert sample.status == 'pending'
        assert sample.order == order

    def test_sample_str(self, sample):
        """Test sample string representation."""
        assert 'BC-001' in str(sample) or str(sample.id) in str(sample)


@pytest.mark.django_db
class TestSampleCollectionViewSet:
    """Tests for the SampleCollection ViewSet."""

    def test_list_samples(self, authenticated_client, sample):
        """Test listing samples."""
        response = authenticated_client.get('/api/v1/samples/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_sample(self, authenticated_client, order):
        """Test creating a sample collection."""
        response = authenticated_client.post('/api/v1/samples/', {
            'order': order.id,
            'sample_type': 'Serum',
            'barcode': 'BC-003',
            'order_items': [item.id for item in order.items.all()]
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_sample_to_collected(self, authenticated_client, sample, phlebotomist_user):
        """Test updating sample status to collected."""
        api_client = APIClient()
        api_client.force_authenticate(user=phlebotomist_user)

        response = api_client.patch(f'/api/v1/samples/{sample.id}/', {
            'status': 'collected'
        })
        assert response.status_code == status.HTTP_200_OK
        sample.refresh_from_db()
        assert sample.status == 'collected'
        assert sample.collected_by == phlebotomist_user
        assert sample.collected_at is not None

    def test_filter_samples_by_status(self, authenticated_client, sample):
        """Test filtering samples by status."""
        response = authenticated_client.get('/api/v1/samples/', {'status': 'pending'})
        assert response.status_code == status.HTTP_200_OK
