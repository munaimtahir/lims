import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.laboratory.catalog_io import export_catalog_workbook, import_catalog_from_excel
from apps.laboratory.models import TestCategory, Test, Parameter, TestParameter, ReferenceRange


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_catalog",
        email="admin_catalog@test.com",
        password="adminpass123",
        full_name="Admin User",
        role="Admin",
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def catalog_data(db):
    category = TestCategory.objects.create(name="Hematology")
    test = Test.objects.create(
        test_id=100,
        test_code="CBC",
        test_name="Complete Blood Count",
        category=category,
        sample_type="Blood",
        price=Decimal("500.00"),
        turnaround_time=24,
    )
    param = Parameter.objects.create(
        parameter_id="p1",
        parameter_name="Hemoglobin",
        unit="g/dL",
    )
    mapping = TestParameter.objects.create(
        test=test,
        parameter=param,
        display_order=1,
        reportable=True,
    )
    ReferenceRange.objects.create(
        parameter=mapping,
        gender="Both",
        age_min=18,
        age_max=65,
        reference_min=Decimal("12.0"),
        reference_max=Decimal("16.0"),
        version=1,
        is_active=True,
    )
    return test


def test_export_import_round_trip_noop(catalog_data):
    workbook = export_catalog_workbook()
    buffer = __import__("io").BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    result = import_catalog_from_excel(
        buffer,
        strict=True,
        allow_defaults=False,
        mode="upsert",
        dry_run=True,
    )

    assert result["errors"] == []
    for counts in result["counts"].values():
        assert counts["created"] == 0
        assert counts["updated"] == 0


def test_audit_endpoint(authenticated_client, catalog_data):
    response = authenticated_client.get("/api/v1/laboratory/catalog/audit/")
    assert response.status_code == 200
    assert "duplicates" in response.data
    assert "tests_without_parameters" in response.data
