"""Tests for reports app."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import TestCatalog
from orders.models import Order, OrderItem
from patients.models import Patient
from results.models import Result

from .models import Report

User = get_user_model()


@pytest.mark.django_db
class TestReportModel:
    """Test Report model."""

    def test_create_report(self):
        """Test creating a report."""
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
        user = User.objects.create_user(
            username="path", password="path123", role="PATHOLOGIST"
        )

        report = Report.objects.create(order=order, generated_by=user)

        assert report.order == order
        assert report.generated_by == user
        assert str(report) == f"Report for {order.order_no}"


@pytest.mark.django_db
class TestReportAPI:
    """Test Report API endpoints."""

    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.pathologist_user = User.objects.create_user(
            username="path", password="path123", role="PATHOLOGIST"
        )
        self.tech_user = User.objects.create_user(
            username="tech", password="tech123", role="TECHNOLOGIST"
        )
        self.admin_user = User.objects.create_user(
            username="admin", password="admin123", role="ADMIN"
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
        self.result = Result.objects.create(
            order_item=self.order_item,
            value="12.5",
            unit="g/dL",
            status="PUBLISHED",
        )

    @patch("reports.views.generate_report_pdf")
    def test_generate_report_as_pathologist(self, mock_pdf):
        """Test generating a report as pathologist."""
        mock_pdf.return_value = MagicMock(read=lambda: b"PDF content")

        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.post(f"/api/reports/generate/{self.order.id}/")

        assert response.status_code == status.HTTP_201_CREATED
        assert Report.objects.filter(order=self.order).exists()

    @patch("reports.views.generate_report_pdf")
    def test_generate_report_as_admin(self, mock_pdf):
        """Test generating a report as admin."""
        mock_pdf.return_value = MagicMock(read=lambda: b"PDF content")

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f"/api/reports/generate/{self.order.id}/")

        assert response.status_code == status.HTTP_201_CREATED

    def test_generate_report_as_tech_forbidden(self):
        """Test that tech cannot generate reports."""
        self.client.force_authenticate(user=self.tech_user)
        response = self.client.post(f"/api/reports/generate/{self.order.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_report_nonexistent_order(self):
        """Test generating report for non-existent order."""
        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.post("/api/reports/generate/99999/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_generate_report_without_published_results(self):
        """Test that report generation fails without published results."""
        # Create order without published results
        order2 = Order.objects.create(patient=self.patient, priority="ROUTINE")
        order_item2 = OrderItem.objects.create(order=order2, test=self.test)
        Result.objects.create(
            order_item=order_item2,
            value="12.5",
            unit="g/dL",
            status="ENTERED",  # Not published
        )

        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.post(f"/api/reports/generate/{order2.id}/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports(self):
        """Test listing reports."""
        Report.objects.create(order=self.order, generated_by=self.pathologist_user)

        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.get("/api/reports/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_get_report_detail(self):
        """Test getting report detail."""
        report = Report.objects.create(
            order=self.order, generated_by=self.pathologist_user
        )

        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.get(f"/api/reports/{report.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["order"] == self.order.id

    def test_download_report(self):
        """Test downloading report PDF."""
        report = Report.objects.create(
            order=self.order, generated_by=self.pathologist_user
        )
        report.pdf_file.save("test.pdf", ContentFile(b"PDF content"))

        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.get(f"/api/reports/{report.id}/download/")

        assert response.status_code == status.HTTP_200_OK

    def test_download_nonexistent_report(self):
        """Test downloading non-existent report."""
        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.get("/api/reports/99999/download/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_report_without_pdf(self):
        """Test downloading report without PDF file."""
        report = Report.objects.create(
            order=self.order, generated_by=self.pathologist_user
        )

        self.client.force_authenticate(user=self.pathologist_user)
        response = self.client.get(f"/api/reports/{report.id}/download/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pdf_generation_integration(self):
        """Test actual PDF generation (integration test)."""
        from .pdf_generator import generate_report_pdf

        # Use the order with published result
        pdf_buffer = generate_report_pdf(self.order)

        assert pdf_buffer is not None
        pdf_content = pdf_buffer.read()
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b"%PDF")  # PDF header

        # Check for deterministic content
        pdf_buffer.seek(0)
        # PDFs should have consistent structure (though timestamps may vary)
        assert len(pdf_content) > 1000  # Reasonable PDF size
