"""Tests for results app."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import TestCatalog
from orders.models import Order, OrderItem
from patients.models import Patient
from settings.permissions import TEMPORARY_FULL_ACCESS_MODE

from .models import Result

User = get_user_model()


@pytest.mark.django_db
class TestResultModel:
    """Test Result model."""

    def test_create_result(self):
        """Test creating a result."""
        patient = Patient.objects.create(
            full_name="John Doe",
            father_name="James Doe",
            dob=date(1990, 1, 1),
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="123 Main St",
        )
        order = Order.objects.create(patient=patient, priority="ROUTINE")
        test = TestCatalog.objects.create(
            code="CBC",
            name="Complete Blood Count",
            category="Hematology",
            sample_type="Blood",
            price=500.00,
            turnaround_time_hours=24,
        )
        order_item = OrderItem.objects.create(order=order, test=test)

        result = Result.objects.create(
            order_item=order_item,
            value="12.5",
            unit="g/dL",
            reference_range="12-16",
            flags="N",
        )

        assert result.value == "12.5"
        assert result.unit == "g/dL"
        assert result.status == "DRAFT"


@pytest.mark.django_db
class TestResultAPI:
    """Test Result API endpoints."""

    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin", password="admin123", role="ADMIN"
        )
        self.tech_user = User.objects.create_user(
            username="tech", password="tech123", role="TECHNOLOGIST"
        )
        self.pathologist_user = User.objects.create_user(
            username="path", password="path123", role="PATHOLOGIST"
        )
        self.reception_user = User.objects.create_user(
            username="reception", password="reception123", role="RECEPTION"
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
        self.order = Order.objects.create(patient=self.patient, priority="ROUTINE")
        self.test = TestCatalog.objects.create(
            code="CBC",
            name="Complete Blood Count",
            category="Hematology",
            sample_type="Blood",
            price=500.00,
            turnaround_time_hours=24,
        )
        self.order_item = OrderItem.objects.create(order=self.order, test=self.test)

    def test_create_result(self):
        """Test creating a result."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "order_item": self.order_item.id,
            "value": "12.5",
            "unit": "g/dL",
            "reference_range": "12-16",
            "flags": "N",
        }
        response = self.client.post("/api/results/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["value"] == "12.5"

    def test_list_results(self):
        """Test listing results."""
        self.client.force_authenticate(user=self.admin_user)
        Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
        )

        response = self.client.get("/api/results/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_enter_result_as_tech(self):
        """Test entering a result as technologist."""
        self.client.force_authenticate(user=self.tech_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
        )

        response = self.client.post(f"/api/results/{result.id}/enter/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ENTERED"
        assert response.data["entered_by"] == self.tech_user.id

    @pytest.mark.skipif(
        TEMPORARY_FULL_ACCESS_MODE,
        reason="Test skipped when TEMPORARY_FULL_ACCESS_MODE is enabled",
    )
    def test_enter_result_as_reception_forbidden(self):
        """Test that reception cannot enter results."""
        self.client.force_authenticate(user=self.reception_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
        )

        response = self.client.post(f"/api/results/{result.id}/enter/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verify_result_as_pathologist(self):
        """Test verifying a result as pathologist."""
        self.client.force_authenticate(user=self.pathologist_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
            status="ENTERED",
        )

        response = self.client.post(f"/api/results/{result.id}/verify/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "VERIFIED"
        assert response.data["verified_by"] == self.pathologist_user.id

    def test_verify_result_not_entered_fails(self):
        """Test verifying a result that is not entered fails."""
        self.client.force_authenticate(user=self.pathologist_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
            status="DRAFT",
        )

        response = self.client.post(f"/api/results/{result.id}/verify/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.skipif(
        TEMPORARY_FULL_ACCESS_MODE,
        reason="Test skipped when TEMPORARY_FULL_ACCESS_MODE is enabled",
    )
    def test_verify_result_as_tech_forbidden(self):
        """Test that tech cannot verify results."""
        self.client.force_authenticate(user=self.tech_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
            status="ENTERED",
        )

        response = self.client.post(f"/api/results/{result.id}/verify/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_publish_result_as_pathologist(self):
        """Test publishing a result as pathologist."""
        self.client.force_authenticate(user=self.pathologist_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
            status="VERIFIED",
        )

        response = self.client.post(f"/api/results/{result.id}/publish/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "PUBLISHED"

    def test_publish_result_not_verified_fails(self):
        """Test publishing a result that is not verified fails."""
        self.client.force_authenticate(user=self.pathologist_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
            status="ENTERED",
        )

        response = self.client.post(f"/api/results/{result.id}/publish/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_result_detail(self):
        """Test getting result detail."""
        self.client.force_authenticate(user=self.admin_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
        )

        response = self.client.get(f"/api/results/{result.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["value"] == "12.5"

    def test_enter_nonexistent_result(self):
        """Test entering a non-existent result returns 404."""
        self.client.force_authenticate(user=self.tech_user)
        response = self.client.post("/api/results/99999/enter/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_verify_nonexistent_result(self):
        """Test verifying a non-existent result returns 404."""
        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.post("/api/results/99999/verify/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_publish_nonexistent_result(self):
        """Test publishing a non-existent result returns 404."""
        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.post("/api/results/99999/publish/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.skipif(
        TEMPORARY_FULL_ACCESS_MODE,
        reason="Test skipped when TEMPORARY_FULL_ACCESS_MODE is enabled",
    )
    def test_publish_result_as_tech_forbidden(self):
        """Test that tech cannot publish results."""
        self.client.force_authenticate(user=self.tech_user)
        result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
            status="VERIFIED",
        )

        response = self.client.post(f"/api/results/{result.id}/publish/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
