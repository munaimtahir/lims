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
from apps.reports.models import Report, ReportStatus
from apps.billing.models import Payment


@pytest.fixture
def api_client():
    """Return an API client for making requests."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    user = User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="adminpass123",
        full_name="Admin User",
        role="Admin",
    )
    return user


@pytest.fixture
def receptionist_user(db):
    """Create and return a receptionist user."""
    user = User.objects.create_user(
        username="receptionist",
        email="receptionist@test.com",
        password="receppass123",
        full_name="Reception User",
        role="Receptionist",
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
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
        gender="Male",
        phone="03001234567",
        created_by=receptionist_user,
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
def test_panel(db, test_category, test_instance):
    """Create and return a test panel."""
    panel = TestPanel.objects.create(
        panel_code="CBC_PANEL",
        panel_name="CBC Panel",
        category=test_category,
        sample_type="EDTA Blood",
        price=Decimal("700.00"),
        turnaround_time=4,
    )
    panel.tests.add(test_instance)
    return panel


@pytest.fixture
def order(db, patient, receptionist_user, test_instance):
    """Create and return an order."""
    order = Order.objects.create(
        patient=patient, ordered_by=receptionist_user, status="NEW"
    )
    OrderItem.objects.create(order=order, test=test_instance, price=test_instance.price)
    order.calculate_total()
    return order


@pytest.mark.django_db
class TestOrderModel:
    """Tests for the Order model."""

    def test_create_order(self, patient, receptionist_user):
        """Test creating an order."""
        order = Order.objects.create(patient=patient, ordered_by=receptionist_user)
        assert order.order_id is not None
        assert order.order_id.startswith("ORD-")
        assert order.status == "NEW"

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
            patient=patient, ordered_by=receptionist_user, discount=Decimal("100.00")
        )
        OrderItem.objects.create(
            order=order, test=test_instance, price=test_instance.price
        )
        order.calculate_total()

        assert order.total_amount == Decimal("800.00")
        assert order.net_amount == Decimal("700.00")


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
        order = Order.objects.create(patient=patient, ordered_by=receptionist_user)
        item = OrderItem.objects.create(
            order=order, panel=test_panel, price=test_panel.price
        )
        assert item.panel == test_panel
        assert item.price == test_panel.price


@pytest.mark.django_db
class TestOrderViewSet:
    """Tests for the Order ViewSet."""

    def test_list_orders(self, authenticated_client, order):
        """Test listing orders."""
        response = authenticated_client.get("/api/v1/orders/orders/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_order_with_tests(
        self, authenticated_client, patient, test_instance
    ):
        """Test creating an order with tests."""
        response = authenticated_client.post(
            "/api/v1/orders/orders/",
            {
                "patient": patient.id,
                "test_ids": [test_instance.id],
                "notes": "Test order",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["order_id"] is not None

    def test_create_order_with_panel(self, authenticated_client, patient, test_panel):
        """Test creating an order with a panel."""
        response = authenticated_client.post(
            "/api/v1/orders/orders/",
            {"patient": patient.id, "panel_ids": [test_panel.id]},
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_worklist_can_reprint_flags(authenticated_client, order, admin_user):
    """Worklist should enable receipt when payment exists and report when published."""
    # Add payment -> receipt available
    Payment.objects.create(order=order, amount=order.net_amount, payment_method="cash", recorded_by=admin_user)

    # Add published report
    Report.objects.create(
        order=order,
        report_file="reports/test.pdf",
        report_number="RPT-TEST",
        status=ReportStatus.FINAL,
        generated_by=admin_user,
    )

    response = authenticated_client.get("/api/v1/worklist/patients/")
    assert response.status_code == status.HTTP_200_OK
    result = response.data["results"][0]

    assert result["can_reprint_receipt"] is True
    assert result["can_reprint_report"] is True

    def test_create_order_with_referred_by(self, authenticated_client, patient, test_instance):
        """Test creating an order with referred_by."""
        response = authenticated_client.post(
            "/api/v1/orders/orders/",
            {
                "patient": patient.id,
                "test_ids": [test_instance.id],
                "referred_by": "Dr. Smith",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["referred_by"] == "Dr. Smith"

    def test_update_order_referred_by(self, authenticated_client, order):
        """Test updating referred_by on an order."""
        response = authenticated_client.patch(
            f"/api/v1/orders/orders/{order.id}/",
            {"referred_by": "Clinic A"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["referred_by"] == "Clinic A"

    def test_retrieve_order(self, authenticated_client, order):
        """Test retrieving an order."""
        response = authenticated_client.get(f"/api/v1/orders/orders/{order.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert "items" in response.data

    def test_cancel_order(self, authenticated_client, order):
        """Test canceling an order."""
        # Ensure initial status is allowed to transition to CANCELLED
        order.status = "NEW"
        order.save()

        response = authenticated_client.post(
            f"/api/v1/orders/orders/{order.id}/cancel/"
        )
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == "CANCELLED"



    def test_worklist_reprint_eligibility(self, authenticated_client, order, admin_user):
        Payment.objects.create(order=order, amount=Decimal('100.00'), payment_method='cash', recorded_by=admin_user)
        order.status = 'PUBLISHED'
        order.save(update_fields=['status'])
        report_file = SimpleUploadedFile('report.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        Report.objects.create(
            order=order,
            report_file=report_file,
            status=ReportStatus.FINAL,
            generated_by=admin_user,
        )

        response = authenticated_client.get('/api/v1/worklist/patients/')
        assert response.status_code == status.HTTP_200_OK
        row = response.data['results'][0]
        assert row['can_reprint_receipt'] is True
        assert row['can_reprint_report'] is True
        assert row['receipt_pdf_url']
        assert row['report_pdf_url']

    def test_cancel_completed_order_fails(self, authenticated_client, order):
        """Test that canceling a completed order fails."""
        # Use PUBLISHED status as 'completed' equivalent
        # Bypass validation for test setup using update
        Order.objects.filter(pk=order.pk).update(status="PUBLISHED")

        response = authenticated_client.post(
            f"/api/v1/orders/orders/{order.id}/cancel/"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOrderModelMethods:
    """Test Order model methods."""
    
    def test_validate_status_transition_valid(self, patient, receptionist_user):
        """Test valid status transitions."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="NEW",
        )
        
        # Valid transition: NEW -> COLLECTED
        order.validate_status_transition("NEW", "COLLECTED")
        order.status = "COLLECTED"
        order.save()
        assert order.status == "COLLECTED"
    
    def test_validate_status_transition_invalid(self, patient, receptionist_user):
        """Test invalid status transitions."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="NEW",
        )
        
        # Invalid transition: NEW -> VERIFIED (must go through COLLECTED, IN_PROCESS first)
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            order.validate_status_transition("NEW", "VERIFIED")
    
    def test_can_transition_to_valid(self, patient, receptionist_user):
        """Test can_transition_to returns True for valid transitions."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="NEW",
        )
        
        assert order.can_transition_to("COLLECTED") is True
        assert order.can_transition_to("CANCELLED") is True
    
    def test_can_transition_to_invalid(self, patient, receptionist_user):
        """Test can_transition_to returns False for invalid transitions."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="NEW",
        )
        
        assert order.can_transition_to("VERIFIED") is False
        assert order.can_transition_to("PUBLISHED") is False
    
    def test_transition_to_valid(self, patient, receptionist_user):
        """Test transition_to method with valid transition."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="NEW",
        )
        
        order.transition_to("COLLECTED", receptionist_user)
        order.refresh_from_db()
        assert order.status == "COLLECTED"
    
    def test_transition_to_invalid(self, patient, receptionist_user):
        """Test transition_to method with invalid transition."""
        order = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="NEW",
        )
        
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            order.transition_to("VERIFIED", receptionist_user)
    
    def test_status_final_states_no_transitions(self, patient, receptionist_user):
        """Test that PUBLISHED and CANCELLED are final states."""
        # Test PUBLISHED
        order1 = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="PUBLISHED",
        )
        assert order1.can_transition_to("COLLECTED") is False
        
        # Test CANCELLED
        order2 = Order.objects.create(
            patient=patient,
            ordered_by=receptionist_user,
            status="CANCELLED",
        )
        assert order2.can_transition_to("COLLECTED") is False
