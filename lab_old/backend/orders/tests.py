"""Tests for orders app."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import TestCatalog
from patients.models import Patient

from .models import Order

User = get_user_model()


@pytest.mark.django_db
class TestOrderAPI:
    """Test order API endpoints."""

    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="reception",
            password="testpass123",
            role="RECEPTION",
        )
        self.patient = Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )
        self.test1 = TestCatalog.objects.create(
            code="CBC",
            name="Complete Blood Count",
            category="Hematology",
            sample_type="Blood",
            price=500.00,
            turnaround_time_hours=24,
        )
        self.test2 = TestCatalog.objects.create(
            code="LFT",
            name="Liver Function Test",
            category="Biochemistry",
            sample_type="Blood",
            price=800.00,
            turnaround_time_hours=48,
        )

    def test_create_order(self):
        """Test creating an order."""
        self.client.force_authenticate(user=self.user)
        data = {
            "patient": self.patient.id,
            "priority": "ROUTINE",
            "test_ids": [self.test1.id, self.test2.id],
            "notes": "Test order",
        }
        response = self.client.post("/api/orders/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "order_no" in response.data
        assert response.data["order_no"].startswith("ORD-")
        assert len(response.data["items"]) == 2

    def test_get_order_detail(self):
        """Test getting order detail."""
        self.client.force_authenticate(user=self.user)
        # Create order first
        order = Order.objects.create(
            patient=self.patient,
            priority="ROUTINE",
        )

        response = self.client.get(f"/api/orders/{order.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["order_no"] == order.order_no

    def test_list_orders(self):
        """Test listing orders."""
        self.client.force_authenticate(user=self.user)
        Order.objects.create(patient=self.patient, priority="ROUTINE")
        Order.objects.create(patient=self.patient, priority="URGENT")

        response = self.client.get("/api/orders/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_filter_orders_by_patient(self):
        """Test filtering orders by patient."""
        self.client.force_authenticate(user=self.user)
        patient2 = Patient.objects.create(
            full_name="Jane Doe",
            father_name="James Doe",
            dob=date(1992, 1, 1),
            sex="F",
            phone="03001234568",
            cnic="12345-1234567-2",
            address="124 Main St",
        )
        Order.objects.create(patient=self.patient, priority="ROUTINE")
        Order.objects.create(patient=patient2, priority="URGENT")

        response = self.client.get(f"/api/orders/?patient={self.patient.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_cancel_order_success(self):
        """Test cancelling an order with no collected samples."""
        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")

        response = self.client.post(f"/api/orders/{order.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "CANCELLED"

        # Verify order is cancelled in database
        order.refresh_from_db()
        assert order.status == "CANCELLED"

    def test_cancel_order_with_collected_samples(self):
        """Test that order cannot be cancelled after samples are collected."""
        from orders.models import OrderItem
        from samples.models import Sample

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        order_item = OrderItem.objects.create(order=order, test=self.test1)
        Sample.objects.create(
            order_item=order_item, sample_type="Blood", status="COLLECTED"
        )

        response = self.client.post(f"/api/orders/{order.id}/cancel/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "collected" in response.data["error"].lower()

    def test_cancel_already_cancelled_order(self):
        """Test that already cancelled order cannot be cancelled again."""
        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(
            patient=self.patient, priority="ROUTINE", status="CANCELLED"
        )

        response = self.client.post(f"/api/orders/{order.id}/cancel/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already cancelled" in response.data["error"].lower()

    def test_cancel_nonexistent_order(self):
        """Test cancelling a non-existent order returns 404."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/orders/99999/cancel/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_edit_order_tests_add_tests(self):
        """Test adding tests to an order."""
        from orders.models import OrderItem

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        OrderItem.objects.create(order=order, test=self.test1)

        test3 = TestCatalog.objects.create(
            code="RFT",
            name="Renal Function Test",
            category="Biochemistry",
            sample_type="Blood",
            price=700.00,
            turnaround_time_hours=48,
        )

        data = {"tests_to_add": [test3.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) == 2

        # Verify test was added
        order.refresh_from_db()
        test_ids = [item.test_id for item in order.items.all()]
        assert test3.id in test_ids

    def test_edit_order_tests_remove_tests(self):
        """Test removing tests from an order."""
        from orders.models import OrderItem

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        OrderItem.objects.create(order=order, test=self.test1)
        OrderItem.objects.create(order=order, test=self.test2)

        data = {"tests_to_remove": [self.test2.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) == 1

        # Verify test was removed
        order.refresh_from_db()
        test_ids = [item.test_id for item in order.items.all()]
        assert self.test2.id not in test_ids
        assert self.test1.id in test_ids

    def test_edit_order_tests_add_and_remove(self):
        """Test adding and removing tests in the same request."""
        from orders.models import OrderItem

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        OrderItem.objects.create(order=order, test=self.test1)
        OrderItem.objects.create(order=order, test=self.test2)

        test3 = TestCatalog.objects.create(
            code="RFT",
            name="Renal Function Test",
            category="Biochemistry",
            sample_type="Blood",
            price=700.00,
            turnaround_time_hours=48,
        )

        data = {"tests_to_add": [test3.id], "tests_to_remove": [self.test2.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) == 2

        # Verify correct tests remain
        order.refresh_from_db()
        test_ids = [item.test_id for item in order.items.all()]
        assert self.test1.id in test_ids
        assert test3.id in test_ids
        assert self.test2.id not in test_ids

    def test_edit_order_tests_with_samples_forbidden(self):
        """Test that order with samples cannot be edited."""
        from orders.models import OrderItem
        from samples.models import Sample

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        order_item = OrderItem.objects.create(order=order, test=self.test1)
        Sample.objects.create(
            order_item=order_item, sample_type="Blood", status="PENDING"
        )

        data = {"tests_to_add": [self.test2.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "samples" in response.data["error"].lower()

    def test_edit_order_tests_with_results_forbidden(self):
        """Test that order with results cannot be edited."""
        from orders.models import OrderItem
        from results.models import Result

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        order_item = OrderItem.objects.create(order=order, test=self.test1)
        Result.objects.create(
            order_item=order_item, value="10.5", unit="mg/dL", status="DRAFT"
        )

        data = {"tests_to_add": [self.test2.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "results" in response.data["error"].lower()

    def test_edit_cancelled_order_forbidden(self):
        """Test that cancelled order cannot be edited."""
        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(
            patient=self.patient, priority="ROUTINE", status="CANCELLED"
        )

        data = {"tests_to_add": [self.test2.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cancelled" in response.data["error"].lower()

    def test_edit_order_tests_no_changes_specified(self):
        """Test that request with no changes returns error."""
        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")

        data = {}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no tests specified" in response.data["error"].lower()

    def test_edit_order_tests_cannot_remove_all_tests(self):
        """Test that removing all tests without adding any is forbidden."""
        from orders.models import OrderItem

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        OrderItem.objects.create(order=order, test=self.test1)

        data = {"tests_to_remove": [self.test1.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot remove all tests" in response.data["error"].lower()

    def test_edit_order_tests_duplicate_test_not_added(self):
        """Test that adding a duplicate test is idempotent."""
        from orders.models import OrderItem

        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        OrderItem.objects.create(order=order, test=self.test1)

        # Try to add test1 again
        data = {"tests_to_add": [self.test1.id]}
        response = self.client.patch(
            f"/api/orders/{order.id}/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) == 1  # Still only 1 test

    def test_edit_nonexistent_order(self):
        """Test editing a non-existent order returns 404."""
        self.client.force_authenticate(user=self.user)
        data = {"tests_to_add": [self.test2.id]}
        response = self.client.patch(
            "/api/orders/99999/edit-tests/", data, format="json"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
