import pytest
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.orders.models import Order
from apps.patients.models import Patient
from apps.reports.models import Report


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def pathologist(db):
    return User.objects.create_user(
        username="phase2_report_path",
        email="phase2_report_path@test.com",
        password="pass1234",
        full_name="Phase2 Report Pathologist",
        role="Pathologist",
    )


@pytest.fixture
def final_report(db, pathologist):
    patient = Patient.objects.create(
        first_name="Report",
        last_name="Phase2",
        gender="Female",
        created_by=pathologist,
    )
    order = Order.objects.create(patient=patient, ordered_by=pathologist)
    report = Report.objects.create(order=order, generated_by=pathologist, status="DRAFT")
    report.report_file.save("phase2.pdf", ContentFile(b"PDF content"))
    report.status = "FINAL"
    report.save()
    return report


@pytest.mark.django_db
def test_report_regeneration_of_final_blocked(api_client, pathologist, final_report):
    api_client.force_authenticate(pathologist)
    response = api_client.post(
        "/api/v1/reports/generate/",
        {"order_id": final_report.order_id, "regenerate": True},
        format="json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "detail" in response.data
