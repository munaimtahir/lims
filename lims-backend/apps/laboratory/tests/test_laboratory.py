"""
Tests for the laboratory app.
"""
import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.laboratory.models import TestCategory, Test, TestParameter, TestPanel, Parameter


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
def authenticated_client(api_client, admin_user):
    """Return an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def test_category(db):
    """Create and return a test category."""
    return TestCategory.objects.create(name="Hematology", description="Blood tests")


@pytest.fixture
def test_instance(db, test_category):
    """Create and return a test."""
    return Test.objects.create(
        category=test_category,
        test_code="CBC",
        test_name="Complete Blood Count",
        loinc_code="58410-2",
        sample_type="EDTA Blood",
        sample_volume="3-5 mL",
        price=Decimal("800.00"),
        turnaround_time=4,
    )


@pytest.fixture
def parameter(db):
    """Create a parameter."""
    return Parameter.objects.create(
        parameter_id="p1",
        parameter_name="Hemoglobin",
        unit="g/dL",
    )


@pytest.fixture
def test_parameter(db, test_instance, parameter):
    """Create and return a test parameter."""
    return TestParameter.objects.create(
        test=test_instance,
        parameter=parameter,
        display_order=1,
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


@pytest.mark.django_db
class TestTestCategoryModel:
    """Tests for the TestCategory model."""

    def test_create_category(self):
        """Test creating a test category."""
        category = TestCategory.objects.create(
            name="Chemistry", description="Chemical tests"
        )
        assert category.name == "Chemistry"
        assert str(category) == "Chemistry"


@pytest.mark.django_db
class TestTestModel:
    """Tests for the Test model."""

    def test_create_test(self, test_category):
        """Test creating a test."""
        test = Test.objects.create(
            category=test_category,
            test_code="LFT",
            test_name="Liver Function Test",
            sample_type="Serum",
            price=Decimal("1200.00"),
            turnaround_time=4,
        )
        assert test.test_code == "LFT"
        assert test.price == Decimal("1200.00")
        assert "LFT" in str(test)


@pytest.mark.django_db
class TestTestParameterModel:
    """Tests for the TestParameter model."""

    def test_create_parameter(self, test_instance):
        """Test creating a test parameter."""
        parameter = Parameter.objects.create(
            parameter_id="p2",
            parameter_name="WBC",
            unit="x10^9/L",
        )
        param = TestParameter.objects.create(
            test=test_instance,
            parameter=parameter,
        )
        assert param.parameter.parameter_name == "WBC"
        assert param.test == test_instance


@pytest.mark.django_db
class TestTestPanelModel:
    """Tests for the TestPanel model."""

    def test_create_panel(self, test_category, test_instance):
        """Test creating a test panel."""
        panel = TestPanel.objects.create(
            panel_code="LFT_PANEL",
            panel_name="LFT Panel",
            category=test_category,
            sample_type="Serum",
            price=Decimal("1000.00"),
            turnaround_time=4,
        )
        panel.tests.add(test_instance)
        assert panel.panel_code == "LFT_PANEL"
        assert panel.tests.count() == 1


@pytest.mark.django_db
class TestTestCategoryViewSet:
    """Tests for the TestCategory ViewSet."""

    def test_list_categories(self, authenticated_client, test_category):
        """Test listing test categories."""
        response = authenticated_client.get("/api/v1/laboratory/categories/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_category(self, authenticated_client):
        """Test creating a test category."""
        response = authenticated_client.post(
            "/api/v1/laboratory/categories/",
            {"name": "Microbiology", "description": "Microbiology tests"},
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestTestViewSet:
    """Tests for the Test ViewSet."""

    def test_list_tests(self, authenticated_client, test_instance):
        """Test listing tests."""
        response = authenticated_client.get("/api/v1/laboratory/tests/")
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_test_with_parameters(
        self, authenticated_client, test_instance, test_parameter
    ):
        """Test retrieving a test with its parameters."""
        response = authenticated_client.get(
            f"/api/v1/laboratory/tests/{test_instance.test_id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "parameters" in response.data

    def test_create_test(self, authenticated_client, test_category):
        """Test creating a test."""
        response = authenticated_client.post(
            "/api/v1/laboratory/tests/",
            {
                "category": test_category.id,
                "test_code": "GLU",
                "test_name": "Glucose",
                "sample_type": "Serum",
                "price": "250.00",
                "turnaround_time": 2,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestTestPanelViewSet:
    """Tests for the TestPanel ViewSet."""

    def test_list_panels(self, authenticated_client, test_panel):
        """Test listing test panels."""
        response = authenticated_client.get("/api/v1/laboratory/panels/")
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_panel_with_tests(self, authenticated_client, test_panel):
        """Test retrieving a panel with its tests."""
        response = authenticated_client.get(
            f"/api/v1/laboratory/panels/{test_panel.id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "tests" in response.data


@pytest.mark.django_db
class TestImportTestsViewSet:
    """Tests for ImportTests ViewSet."""
    
    @pytest.fixture
    def api_client(self):
        """Return an API client for making requests."""
        return APIClient()
    
    @pytest.fixture
    def admin_user(self, db):
        """Create and return an admin user."""
        return User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            full_name="Admin User",
            role="Admin",
        )
    
    def test_import_tests_no_file(self, api_client, admin_user):
        """Test import_tests without file."""
        api_client.force_authenticate(user=admin_user)
        # The router registers it as "import", so URL is /api/v1/laboratory/import/
        response = api_client.post("/api/v1/laboratory/import/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No file uploaded" in response.data.get("error", "")
    
    def test_import_tests_success(self, api_client, admin_user):
        """Test successful import of tests from Excel."""
        from io import BytesIO
        from openpyxl import Workbook
        
        # Create Excel file
        wb = Workbook()
        ws = wb.create_sheet("Tests")
        ws.append(["Code", "Name", "Category", "SampleType", "Price", "TAT"])
        ws.append(["TEST1", "Test One", "Hematology", "Blood", 100.00, 24])
        
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        file_obj.name = "tests.xlsx"
        
        api_client.force_authenticate(user=admin_user)
        # The router registers it as "import", so URL is /api/v1/laboratory/import/
        response = api_client.post(
            "/api/v1/laboratory/import/?dry_run=false",
            {"file": file_obj},
            format="multipart",
        )
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        assert response.data["success"] is True
    
    def test_import_tests_invalid_file_format(self, api_client, admin_user):
        """Test import_tests with invalid file format."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        invalid_file = SimpleUploadedFile("test.txt", b"Not an Excel file")
        
        api_client.force_authenticate(user=admin_user)
        # The router registers it as "import", so URL is /api/v1/laboratory/import/
        response = api_client.post(
            "/api/v1/laboratory/import/",
            {"file": invalid_file},
            format="multipart",
        )
        # Should return error (either 400 or 500 depending on error handling)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_import_tests_exception_handling(self, api_client, admin_user):
        """Test import_tests handles exceptions."""
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_obj = SimpleUploadedFile("test.xlsx", b"fake excel content")
        
        api_client.force_authenticate(user=admin_user)
        
        # Mock import_catalog_from_excel to raise exception
        with patch('apps.laboratory.views.import_catalog_from_excel') as mock_import:
            mock_import.side_effect = Exception("Import failed")
            
            # The router registers it as "import", so URL is /api/v1/laboratory/import/
            response = api_client.post(
                "/api/v1/laboratory/import/",
                {"file": file_obj},
                format="multipart",
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
