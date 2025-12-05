"""
Tests for the results app.
"""
import pytest
from decimal import Decimal
from datetime import date
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test, TestParameter
from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult


@pytest.fixture
def api_client():
    """Return an API client for making requests."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="adminpass123",
        full_name="Admin User",
        role="Admin",
    )


@pytest.fixture
def technician_user(db):
    """Create and return a lab technician user."""
    return User.objects.create_user(
        username="technician",
        email="technician@test.com",
        password="techpass123",
        full_name="Lab Technician",
        role="Lab Technician",
    )


@pytest.fixture
def pathologist_user(db):
    """Create and return a pathologist user."""
    return User.objects.create_user(
        username="pathologist",
        email="pathologist@test.com",
        password="pathopass123",
        full_name="Pathologist User",
        role="Pathologist",
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
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
        gender="Male",
        phone="03001234567",
        created_by=admin_user,
    )


@pytest.fixture
def test_category(db):
    """Create and return a test category."""
    return TestCategory.objects.create(name="Hematology")


@pytest.fixture
def test_instance(db, test_category):
    """Create and return a test."""
    return Test.objects.create(
        category=test_category,
        test_code="CBC",
        test_name="Complete Blood Count",
        sample_type="EDTA Blood",
        price=Decimal("800.00"),
        turnaround_time=4,
    )


@pytest.fixture
def test_parameter(db, test_instance):
    """Create and return a test parameter."""
    return TestParameter.objects.create(
        test=test_instance,
        parameter_name="Hemoglobin",
        loinc_code="718-7",
        unit="g/dL",
        reference_min_male=Decimal("13.5"),
        reference_max_male=Decimal("17.5"),
        reference_min_female=Decimal("12.0"),
        reference_max_female=Decimal("15.5"),
        critical_low=Decimal("7.0"),
        critical_high=Decimal("20.0"),
        display_order=1,
    )


@pytest.fixture
def order(db, patient, admin_user, test_instance):
    """Create and return an order."""
    order = Order.objects.create(
        patient=patient, ordered_by=admin_user, status="pending"
    )
    OrderItem.objects.create(order=order, test=test_instance, price=test_instance.price)
    order.calculate_total()
    return order


@pytest.fixture
def test_result(db, order, test_parameter, technician_user):
    """Create and return a test result."""
    order_item = order.items.first()
    return TestResult.objects.create(
        order_item=order_item,
        test_parameter=test_parameter,
        result_value="14.5",
        entered_by=technician_user,
    )


@pytest.mark.django_db
class TestTestResultModel:
    """Tests for the TestResult model."""

    def test_create_result(self, order, test_parameter, technician_user):
        """Test creating a test result."""
        order_item = order.items.first()
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="15.0",
            entered_by=technician_user,
        )
        assert result.result_value == "15.0"
        assert result.status == "pending"

    def test_result_flag_normal(self, order, test_parameter, technician_user):
        """Test that normal result is flagged correctly (Male patient)."""
        order_item = order.items.first()
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="15.0",  # Within 13.5-17.5 for male
            entered_by=technician_user,
        )
        assert result.flag == "normal"

    def test_result_flag_high(self, order, test_parameter, technician_user):
        """Test that high result is flagged correctly."""
        order_item = order.items.first()
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="18.0",  # Above 17.5 for male
            entered_by=technician_user,
        )
        assert result.flag == "high"

    def test_result_flag_low(self, order, test_parameter, technician_user):
        """Test that low result is flagged correctly."""
        order_item = order.items.first()
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="12.0",  # Below 13.5 for male
            entered_by=technician_user,
        )
        assert result.flag == "low"

    def test_result_flag_critical_high(self, order, test_parameter, technician_user):
        """Test that critical high result is flagged correctly."""
        order_item = order.items.first()
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="21.0",  # >= 20.0 critical high
            entered_by=technician_user,
        )
        assert result.flag == "critical_high"

    def test_result_flag_critical_low(self, order, test_parameter, technician_user):
        """Test that critical low result is flagged correctly."""
        order_item = order.items.first()
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="6.5",  # <= 7.0 critical low
            entered_by=technician_user,
        )
        assert result.flag == "critical_low"


@pytest.mark.django_db
class TestTestResultViewSet:
    """Tests for the TestResult ViewSet."""

    def test_list_results(self, authenticated_client, test_result):
        """Test listing results."""
        response = authenticated_client.get("/api/v1/results/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_result(self, api_client, technician_user, order, test_parameter):
        """Test creating a result."""
        api_client.force_authenticate(user=technician_user)
        order_item = order.items.first()
        response = api_client.post(
            "/api/v1/results/",
            {
                "order_item": order_item.id,
                "test_parameter": test_parameter.id,
                "result_value": "14.0",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_verify_result(self, api_client, pathologist_user, test_result):
        """Test verifying a result."""
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(f"/api/v1/results/{test_result.id}/verify/")
        assert response.status_code == status.HTTP_200_OK
        test_result.refresh_from_db()
        assert test_result.status == "verified"
        assert test_result.verified_by == pathologist_user

    def test_reject_result(self, api_client, pathologist_user, test_result):
        """Test rejecting a result."""
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(f"/api/v1/results/{test_result.id}/reject/")
        assert response.status_code == status.HTTP_200_OK
        test_result.refresh_from_db()
        assert test_result.status == "rejected"

    def test_verify_result_non_pathologist_fails(
        self, api_client, technician_user, test_result
    ):
        """Test that non-pathologist cannot verify results."""
        api_client.force_authenticate(user=technician_user)
        response = api_client.post(f"/api/v1/results/{test_result.id}/verify/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
