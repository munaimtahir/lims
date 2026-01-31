"""
Tests for the billing app.
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
from apps.billing.models import Payment


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
def cashier_user(db):
    """Create and return a cashier user."""
    return User.objects.create_user(
        username="cashier",
        email="cashier@test.com",
        password="cashierpass123",
        full_name="Cashier User",
        role="Cashier",
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
def order(db, patient, admin_user, test_instance):
    """Create and return an order."""
    order = Order.objects.create(
        patient=patient, ordered_by=admin_user, status="pending"
    )
    OrderItem.objects.create(order=order, test=test_instance, price=test_instance.price)
    order.calculate_total()
    return order


@pytest.fixture
def payment(db, order, cashier_user):
    """Create and return a payment."""
    return Payment.objects.create(
        order=order,
        amount=Decimal("500.00"),
        payment_method="cash",
        recorded_by=cashier_user,
    )


@pytest.mark.django_db
class TestPaymentModel:
    """Tests for the Payment model."""

    def test_create_payment(self, order, cashier_user):
        """Test creating a payment."""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("400.00"),
            payment_method="cash",
            recorded_by=cashier_user,
        )
        assert payment.amount == Decimal("400.00")
        assert payment.order == order

    def test_payment_str(self, payment):
        """Test payment string representation."""
        assert "500" in str(payment)

    def test_full_payment_marks_order_paid(self, order, cashier_user):
        """Test that full payment marks order as paid."""
        assert not order.is_paid
        Payment.objects.create(
            order=order,
            amount=order.net_amount,
            payment_method="cash",
            recorded_by=cashier_user,
        )
        order.refresh_from_db()
        assert order.is_paid

    def test_partial_payment_does_not_mark_paid(self, order, cashier_user):
        """Test that partial payment does not mark order as paid."""
        Payment.objects.create(
            order=order,
            amount=Decimal("100.00"),
            payment_method="cash",
            recorded_by=cashier_user,
        )
        order.refresh_from_db()
        assert not order.is_paid

    def test_multiple_payments_mark_paid(self, order, cashier_user):
        """Test that multiple payments totaling net amount mark order as paid."""
        half = order.net_amount / 2
        Payment.objects.create(
            order=order, amount=half, payment_method="cash", recorded_by=cashier_user
        )
        order.refresh_from_db()
        assert not order.is_paid

        Payment.objects.create(
            order=order, amount=half, payment_method="card", recorded_by=cashier_user
        )
        order.refresh_from_db()
        assert order.is_paid


@pytest.mark.django_db
class TestPaymentViewSet:
    """Tests for the Payment ViewSet."""

    def test_list_payments(self, authenticated_client, payment):
        """Test listing payments."""
        response = authenticated_client.get("/api/v1/payments/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_payment(self, api_client, cashier_user, order):
        """Test creating a payment."""
        api_client.force_authenticate(user=cashier_user)
        response = api_client.post(
            "/api/v1/payments/",
            {"order": order.id, "amount": "800.00", "payment_method": "cash"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["recorded_by"] == cashier_user.id

    def test_filter_payments_by_order(self, authenticated_client, payment):
        """Test filtering payments by order."""
        response = authenticated_client.get(
            "/api/v1/payments/", {"order": payment.order.id}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_payments_by_method(self, authenticated_client, payment):
        """Test filtering payments by payment method."""
        response = authenticated_client.get(
            "/api/v1/payments/", {"payment_method": "cash"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_receipt_generation(self, authenticated_client, payment):
        """Test generating payment receipt PDF."""
        response = authenticated_client.get(f"/api/v1/payments/{payment.id}/receipt/")
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        assert "Receipt" in response["Content-Disposition"]
        # FileResponse is a streaming response, verify it's set up correctly
        assert hasattr(response, 'streaming_content') or hasattr(response, 'file')

        content = b"".join(response.streaming_content)
        assert content[:4] == b"%PDF"
    
    def test_receipt_with_lab_info(self, authenticated_client, payment):
        """Test receipt generation with lab information."""
        response = authenticated_client.get(
            f"/api/v1/payments/{payment.id}/receipt/",
            {
                "lab_name": "Test Lab",
                "lab_address": "123 Test St",
                "lab_phone": "123-456-7890",
                "lab_email": "test@lab.com",
            }
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        # Verify PDF content exists
        content = b"".join(response.streaming_content)
        assert b"Test Lab" in content
        content = b''.join(response.streaming_content) if hasattr(response, 'streaming_content') else getattr(response, 'content', b'')
        assert len(content) > 0
    
    def test_receipt_with_discount(self, authenticated_client, order, cashier_user):
        """Test receipt generation with discount."""
        order.discount = Decimal("100.00")
        order.save()
        payment = Payment.objects.create(
            order=order,
            amount=order.net_amount,
            payment_method="cash",
            recorded_by=cashier_user,
        )
        response = authenticated_client.get(f"/api/v1/payments/{payment.id}/receipt/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_receipt_with_transaction_id(self, authenticated_client, order, cashier_user):
        """Test receipt generation with transaction ID."""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("500.00"),
            payment_method="card",
            transaction_id="TXN123456",
            recorded_by=cashier_user,
        )
        response = authenticated_client.get(f"/api/v1/payments/{payment.id}/receipt/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_receipt_with_notes(self, authenticated_client, order, cashier_user):
        """Test receipt generation with payment notes."""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("500.00"),
            payment_method="cash",
            notes="Payment received in full",
            recorded_by=cashier_user,
        )
        response = authenticated_client.get(f"/api/v1/payments/{payment.id}/receipt/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_receipt_partial_payment(self, authenticated_client, order, cashier_user):
        """Test receipt generation for partial payment."""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("300.00"),  # Less than net amount
            payment_method="cash",
            recorded_by=cashier_user,
        )
        response = authenticated_client.get(f"/api/v1/payments/{payment.id}/receipt/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_receipt_full_payment(self, authenticated_client, order, cashier_user):
        """Test receipt generation for full payment."""
        payment = Payment.objects.create(
            order=order,
            amount=order.net_amount,  # Full payment
            payment_method="cash",
            recorded_by=cashier_user,
        )
        response = authenticated_client.get(f"/api/v1/payments/{payment.id}/receipt/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_receipt_multiple_payments(self, authenticated_client, order, cashier_user):
        """Test receipt generation when order has multiple payments."""
        # Create first payment
        Payment.objects.create(
            order=order,
            amount=Decimal("300.00"),
            payment_method="cash",
            recorded_by=cashier_user,
        )
        # Create second payment
        payment2 = Payment.objects.create(
            order=order,
            amount=Decimal("500.00"),
            payment_method="card",
            recorded_by=cashier_user,
        )
        response = authenticated_client.get(f"/api/v1/payments/{payment2.id}/receipt/")
        assert response.status_code == status.HTTP_200_OK
