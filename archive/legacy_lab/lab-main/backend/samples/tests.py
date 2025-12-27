"""Tests for samples app."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import TestCatalog
from orders.models import Order, OrderItem
from patients.models import Patient
from settings.permissions import TEMPORARY_FULL_ACCESS_MODE

from .models import Sample

User = get_user_model()


@pytest.mark.django_db
class TestSampleModel:
    """Test Sample model."""

    def test_create_sample(self):
        """Test creating a sample."""
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

        sample = Sample.objects.create(order_item=order_item, sample_type="Blood")

        assert sample.barcode.startswith("SAM-")
        assert sample.status == "PENDING"
        assert sample.sample_type == "Blood"

    def test_sample_barcode_generation(self):
        """Test barcode auto-generation."""
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

        sample1 = Sample.objects.create(order_item=order_item, sample_type="Blood")
        sample2 = Sample.objects.create(order_item=order_item, sample_type="Serum")

        assert sample1.barcode != sample2.barcode
        assert sample1.barcode.startswith("SAM-")
        assert sample2.barcode.startswith("SAM-")


@pytest.mark.django_db
class TestSampleAPI:
    """Test Sample API endpoints."""

    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin", password="admin123", role="ADMIN"
        )
        self.phlebotomy_user = User.objects.create_user(
            username="phleb", password="phleb123", role="PHLEBOTOMY"
        )
        self.tech_user = User.objects.create_user(
            username="tech", password="tech123", role="TECHNOLOGIST"
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

    def test_create_sample(self):
        """Test creating a sample."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "order_item": self.order_item.id,
            "sample_type": "Blood",
        }
        response = self.client.post("/api/samples/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "barcode" in response.data
        assert response.data["sample_type"] == "Blood"

    def test_list_samples(self):
        """Test listing samples."""
        self.client.force_authenticate(user=self.admin_user)
        Sample.objects.create(order_item=self.order_item, sample_type="Blood")

        response = self.client.get("/api/samples/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_collect_sample_as_phlebotomy(self):
        """Test collecting a sample as phlebotomy user."""
        self.client.force_authenticate(user=self.phlebotomy_user)
        sample = Sample.objects.create(order_item=self.order_item, sample_type="Blood")

        response = self.client.post(f"/api/samples/{sample.id}/collect/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "COLLECTED"
        assert response.data["collected_by"] == self.phlebotomy_user.id

    def test_collect_sample_as_admin(self):
        """Test collecting a sample as admin."""
        self.client.force_authenticate(user=self.admin_user)
        sample = Sample.objects.create(order_item=self.order_item, sample_type="Blood")

        response = self.client.post(f"/api/samples/{sample.id}/collect/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "COLLECTED"

    @pytest.mark.skipif(
        TEMPORARY_FULL_ACCESS_MODE,
        reason="Test skipped when TEMPORARY_FULL_ACCESS_MODE is enabled",
    )
    def test_collect_sample_as_tech_forbidden(self):
        """Test that tech cannot collect samples."""
        self.client.force_authenticate(user=self.tech_user)
        sample = Sample.objects.create(order_item=self.order_item, sample_type="Blood")

        response = self.client.post(f"/api/samples/{sample.id}/collect/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_receive_sample_as_tech(self):
        """Test receiving a sample as tech user."""
        self.client.force_authenticate(user=self.tech_user)
        sample = Sample.objects.create(
            order_item=self.order_item,
            sample_type="Blood",
            status="COLLECTED",
        )

        response = self.client.post(f"/api/samples/{sample.id}/receive/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "RECEIVED"
        assert response.data["received_by"] == self.tech_user.id

    def test_receive_sample_as_phlebotomy(self):
        """Test that phlebotomy can receive samples."""
        self.client.force_authenticate(user=self.phlebotomy_user)
        sample = Sample.objects.create(
            order_item=self.order_item,
            sample_type="Blood",
            status="COLLECTED",
        )

        response = self.client.post(f"/api/samples/{sample.id}/receive/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "RECEIVED"
        assert response.data["received_by"] == self.phlebotomy_user.id

    def test_get_sample_detail(self):
        """Test getting sample detail."""
        self.client.force_authenticate(user=self.admin_user)
        sample = Sample.objects.create(order_item=self.order_item, sample_type="Blood")

        response = self.client.get(f"/api/samples/{sample.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barcode"] == sample.barcode

    def test_collect_nonexistent_sample(self):
        """Test collecting a non-existent sample returns 404."""
        self.client.force_authenticate(user=self.phlebotomy_user)
        response = self.client.post("/api/samples/99999/collect/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_receive_nonexistent_sample(self):
        """Test receiving a non-existent sample returns 404."""
        self.client.force_authenticate(user=self.tech_user)
        response = self.client.post("/api/samples/99999/receive/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_reject_sample_as_tech(self):
        """Test rejecting a sample as tech user."""
        self.client.force_authenticate(user=self.tech_user)
        sample = Sample.objects.create(
            order_item=self.order_item,
            sample_type="Blood",
            status="RECEIVED",
        )

        response = self.client.post(
            f"/api/samples/{sample.id}/reject/",
            {"rejection_reason": "Hemolyzed sample"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "REJECTED"
        assert response.data["rejection_reason"] == "Hemolyzed sample"

    def test_reject_sample_without_reason(self):
        """Test that rejecting without a reason fails."""
        self.client.force_authenticate(user=self.tech_user)
        sample = Sample.objects.create(
            order_item=self.order_item,
            sample_type="Blood",
            status="RECEIVED",
        )

        response = self.client.post(f"/api/samples/{sample.id}/reject/", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rejection reason" in response.data["error"].lower()

    def test_reject_sample_with_invalid_status(self):
        """Test that rejecting a sample with invalid status fails."""
        self.client.force_authenticate(user=self.tech_user)
        sample = Sample.objects.create(
            order_item=self.order_item,
            sample_type="Blood",
            status="REJECTED",  # Already rejected
        )

        response = self.client.post(
            f"/api/samples/{sample.id}/reject/",
            {"rejection_reason": "Test rejection"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot reject sample with status" in response.data["error"]

    def test_reject_sample_as_phlebotomy(self):
        """Test that phlebotomy can reject samples."""
        self.client.force_authenticate(user=self.phlebotomy_user)
        sample = Sample.objects.create(
            order_item=self.order_item,
            sample_type="Blood",
            status="COLLECTED",
        )

        response = self.client.post(
            f"/api/samples/{sample.id}/reject/",
            {"rejection_reason": "Bad sample"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "REJECTED"
        assert response.data["rejection_reason"] == "Bad sample"

    def test_reject_nonexistent_sample(self):
        """Test rejecting a non-existent sample returns 404."""
        self.client.force_authenticate(user=self.tech_user)
        response = self.client.post(
            "/api/samples/99999/reject/",
            {"rejection_reason": "Bad sample"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
