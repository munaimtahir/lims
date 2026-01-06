"""
Tests for the reports app.
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
from apps.reports.models import Report
from apps.reports.utils import generate_pdf_report


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
        display_order=1,
    )


@pytest.fixture
def order_with_results(
    db, patient, admin_user, test_instance, test_parameter, technician_user
):
    """Create and return an order with results."""
    order = Order.objects.create(
        patient=patient, ordered_by=admin_user, status="pending"
    )
    order_item = OrderItem.objects.create(
        order=order, test=test_instance, price=test_instance.price
    )
    order.calculate_total()

    # Add a result
    TestResult.objects.create(
        order_item=order_item,
        test_parameter=test_parameter,
        result_value="14.5",
        entered_by=technician_user,
    )
    return order


@pytest.mark.django_db
class TestReportModel:
    """Tests for the Report model."""

    def test_report_str(self, order_with_results, pathologist_user):
        """Test report string representation."""
        from django.core.files.base import ContentFile

        report = Report(order=order_with_results, generated_by=pathologist_user)
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()

        assert order_with_results.order_id in str(report)


@pytest.mark.django_db
class TestPDFGeneration:
    """Tests for PDF report generation."""

    def test_generate_pdf_report(self, order_with_results):
        """Test that PDF generation returns bytes."""
        pdf_content = generate_pdf_report(order_with_results.id)
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        # Check PDF magic bytes
        assert pdf_content[:4] == b"%PDF"

    def test_generate_pdf_nonexistent_order(self):
        """Test that generating PDF for nonexistent order raises error."""
        with pytest.raises(ValueError):
            generate_pdf_report(99999)


@pytest.mark.django_db
class TestReportViewSet:
    """Tests for the Report ViewSet."""

    def test_list_reports(self, authenticated_client):
        """Test listing reports."""
        response = authenticated_client.get("/api/v1/reports/")
        assert response.status_code == status.HTTP_200_OK

    def test_generate_report(self, api_client, pathologist_user, order_with_results):
        """Test generating a report."""
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(
            "/api/v1/reports/generate/", {"order_id": order_with_results.id}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "report_file" in response.data

    def test_generate_report_missing_order_id(self, authenticated_client):
        """Test generating a report without order_id."""
        response = authenticated_client.post("/api/v1/reports/generate/", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_download_report(self, api_client, pathologist_user, order_with_results):
        """Test downloading a report PDF."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.get(f"/api/v1/reports/{report.id}/download/")
        assert response.status_code == status.HTTP_200_OK
        assert response.get("Content-Type", "") == "application/pdf"
    
    def test_download_report_no_file(self, api_client, pathologist_user, order_with_results):
        """Test downloading a report without file."""
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.get(f"/api/v1/reports/{report.id}/download/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_mark_delivered(self, api_client, pathologist_user, order_with_results):
        """Test marking a report as delivered."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(
            f"/api/v1/reports/{report.id}/mark_delivered/",
            {"method": "email"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.delivered_at is not None
    
    def test_reprint_report(self, api_client, pathologist_user, order_with_results):
        """Test reprinting a report."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        initial_count = report.reprint_count
        response = api_client.post(f"/api/v1/reports/{report.id}/reprint/")
        assert response.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.reprint_count == initial_count + 1
    
    def test_amend_report(self, api_client, pathologist_user, order_with_results):
        """Test amending a report."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(
            f"/api/v1/reports/{report.id}/amend/",
            {"reason": "Correction needed"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "amended_report" in response.data
    
    def test_amend_report_missing_reason(self, api_client, pathologist_user, order_with_results):
        """Test amending a report without reason."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(
            f"/api/v1/reports/{report.id}/amend/",
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_amend_report_non_pathologist(self, api_client, technician_user, order_with_results):
        """Test that non-pathologist cannot amend reports."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=technician_user)
        response = api_client.post(
            f"/api/v1/reports/{report.id}/amend/",
            {"reason": "Correction needed"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_patient_history(self, api_client, pathologist_user, order_with_results):
        """Test getting patient report history."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        patient_id = order_with_results.patient.id
        response = api_client.get(
            f"/api/v1/reports/patient_history/?patient_id={patient_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
    
    def test_patient_history_missing_patient_id(self, api_client, pathologist_user):
        """Test patient history without patient_id."""
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.get("/api/v1/reports/patient_history/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_amendments_list(self, api_client, pathologist_user, order_with_results):
        """Test getting amendments for a report."""
        from django.core.files.base import ContentFile
        original_report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        original_report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        original_report.save()
        
        # Create amendment
        amended_report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
            amended_from=original_report,
        )
        amended_report.report_file.save("amended.pdf", ContentFile(b"PDF content"))
        amended_report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.get(
            f"/api/v1/reports/amendments/?report_id={original_report.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "amendments" in response.data
        assert len(response.data["amendments"]) == 1
    
    def test_amendments_missing_report_id(self, api_client, pathologist_user):
        """Test amendments endpoint without report_id."""
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.get("/api/v1/reports/amendments/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_upload_signature_pathologist(self, api_client, pathologist_user, order_with_results):
        """Test uploading pathologist signature."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        signature_file = ContentFile(b"signature data")
        signature_file.name = "signature.png"
        
        response = api_client.post(
            f"/api/v1/reports/{report.id}/upload_signature/",
            {"signature": signature_file, "signature_type": "pathologist"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.pathologist_signature is not None
    
    def test_upload_signature_technician(self, api_client, technician_user, order_with_results):
        """Test uploading technician signature."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=technician_user)
        signature_file = ContentFile(b"signature data")
        signature_file.name = "signature.png"
        
        response = api_client.post(
            f"/api/v1/reports/{report.id}/upload_signature/",
            {"signature": signature_file, "signature_type": "technician"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.technician_signature is not None
    
    def test_upload_signature_missing_file(self, api_client, pathologist_user, order_with_results):
        """Test uploading signature without file."""
        from django.core.files.base import ContentFile
        report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(
            f"/api/v1/reports/{report.id}/upload_signature/",
            {"signature_type": "pathologist"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_generate_report_with_order_id_string(self, api_client, pathologist_user, order_with_results):
        """Test generating report with order_id as string."""
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(
            "/api/v1/reports/generate/",
            {"order_id": order_with_results.order_id},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_generate_report_existing_regenerate(self, api_client, pathologist_user, order_with_results):
        """Test regenerating an existing report."""
        from django.core.files.base import ContentFile
        existing_report = Report.objects.create(
            order=order_with_results,
            generated_by=pathologist_user,
            status="final",
        )
        existing_report.report_file.save("test.pdf", ContentFile(b"PDF content"))
        existing_report.save()
        
        api_client.force_authenticate(user=pathologist_user)
        response = api_client.post(
            "/api/v1/reports/generate/",
            {"order_id": order_with_results.id, "regenerate": True},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED