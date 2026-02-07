from decimal import Decimal
from io import BytesIO

import pandas as pd
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.laboratory.catalog_io import (
    export_catalog_workbook,
    import_catalog_from_excel,
)
from apps.laboratory.models import (
    Parameter,
    ReferenceRange,
    Test,
    TestCategory,
    TestParameter,
)


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
def minimal_catalog_excel_file():
    """Creates an in-memory Excel file with minimal catalog data for testing."""
    df = pd.DataFrame(
        {
            "Test ID": [999],
            "Test Code": ["MINTST"],
            "Test Name": ["Minimal Test"],
            "Category": ["General"],
            "Sample Type": ["Blood"],
            "Price": [100.00],
            "Turnaround Time (hours)": [24],
            "Parameter ID": ["p999"],
            "Parameter Name": ["Minimal Param"],
            "Unit": ["g/dL"],
            "Display Order": [1],
            "Reportable": [True],
            "Gender": ["Both"],
            "Age Min (years)": [0],
            "Age Max (years)": [99],
            "Reference Min": [10.0],
            "Reference Max": [20.0],
        }
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="LIMS Test Catalog", index=False)
    buffer.seek(0)
    return buffer


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


def test_import_creates_expected_records(db, minimal_catalog_excel_file):
    """Verify that importing a minimal catalog creates the correct DB records."""
    assert Test.objects.count() == 0  # Ensure DB is empty before import

    result = import_catalog_from_excel(
        minimal_catalog_excel_file,
        strict=True,
        allow_defaults=False,
        mode="upsert",
        dry_run=False,  # Perform a real import
    )

    assert not result["errors"]
    assert result["counts"]["tests"]["created"] == 1
    assert result["counts"]["parameters"]["created"] == 1
    assert result["counts"]["test_parameters"]["created"] == 1
    assert result["counts"]["reference_ranges"]["created"] == 1

    assert Test.objects.count() == 1
    assert Parameter.objects.count() == 1
    assert TestParameter.objects.count() == 1
    assert ReferenceRange.objects.count() == 1

    test = Test.objects.get(test_code="MINTST")
    assert test.test_name == "Minimal Test"
    assert test.price == Decimal("100.00")


def test_export_endpoint_returns_file(authenticated_client, catalog_data):
    """Verify the catalog export endpoint returns a valid Excel file."""
    response = authenticated_client.get("/api/v1/laboratory/catalog/export/")

    assert response.status_code == 200
    assert response.has_header("Content-Disposition")
    assert "attachment; filename=" in response["Content-Disposition"]
    assert ".xlsx" in response["Content-Disposition"]
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Verify the content is a valid excel file
    buffer = BytesIO(response.content)
    df = pd.read_excel(buffer)
    assert "Test ID" in df.columns
    assert "Test Name" in df.columns
    assert len(df) > 0
