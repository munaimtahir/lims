"""
Comprehensive tests for integrations app.
"""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.integrations.models import Analyzer, AnalyzerResultImport
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.laboratory.models import TestCategory, Test, TestParameter
from apps.integrations.hl7_parser import parse_hl7_message


@pytest.mark.django_db
class TestAnalyzerModel:
    """Test Analyzer model."""
    
    def test_create_analyzer(self):
        """Test creating an analyzer."""
        analyzer = Analyzer.objects.create(
            name="CBC Analyzer",
            model="ABC-123",
            manufacturer="Test Corp",
            connection_type="HL7",
            connection_config={"host": "localhost", "port": 8080},
        )
        assert analyzer.name == "CBC Analyzer"
        assert analyzer.model == "ABC-123"
        assert analyzer.connection_type == "HL7"
        assert analyzer.is_active is True
    
    def test_analyzer_str(self):
        """Test analyzer string representation."""
        analyzer = Analyzer.objects.create(
            name="Test Analyzer",
            model="MODEL-1",
        )
        assert "Test Analyzer" in str(analyzer)
        assert "MODEL-1" in str(analyzer)


@pytest.mark.django_db
class TestAnalyzerResultImportModel:
    """Test AnalyzerResultImport model."""
    
    @pytest.fixture
    def analyzer(self):
        """Create test analyzer."""
        return Analyzer.objects.create(
            name="Test Analyzer",
            model="TEST-1",
        )
    
    def test_create_import(self, analyzer):
        """Test creating an import record."""
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="MSH|^~\\&|...",
            parsed_data={"test": "data"},
            status="PENDING",
        )
        assert import_record.analyzer == analyzer
        assert import_record.status == "PENDING"
        assert import_record.raw_message == "MSH|^~\\&|..."
    
    def test_import_str(self, analyzer):
        """Test import string representation."""
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={},
        )
        assert analyzer.name in str(import_record)
        assert import_record.status in str(import_record)


@pytest.mark.django_db
class TestAnalyzerViewSet:
    """Test AnalyzerViewSet API."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
            role="Admin",
        )
    
    def test_list_analyzers(self, api_client, user):
        """Test listing analyzers."""
        Analyzer.objects.create(
            name="Test Analyzer",
            model="TEST-1",
        )
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/integrations/analyzers/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
    
    def test_create_analyzer(self, api_client, user):
        """Test creating an analyzer."""
        api_client.force_authenticate(user=user)
        data = {
            "name": "New Analyzer",
            "model": "NEW-1",
            "manufacturer": "Test Corp",
            "connection_type": "HL7",
            "connection_config": {"host": "localhost"},
        }
        response = api_client.post("/api/v1/integrations/analyzers/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Analyzer"


@pytest.mark.django_db
class TestAnalyzerResultImportViewSet:
    """Test AnalyzerResultImportViewSet API."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
            role="Admin",
        )
    
    @pytest.fixture
    def analyzer(self):
        """Create test analyzer."""
        return Analyzer.objects.create(
            name="Test Analyzer",
            model="TEST-1",
        )
    
    def test_list_imports(self, api_client, user, analyzer):
        """Test listing import records."""
        AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={},
        )
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/integrations/imports/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
    
    def test_import_hl7_missing_params(self, api_client, user, analyzer):
        """Test HL7 import with missing parameters."""
        api_client.force_authenticate(user=user)
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_import_hl7_invalid_analyzer(self, api_client, user):
        """Test HL7 import with invalid analyzer."""
        api_client.force_authenticate(user=user)
        data = {
            "analyzer_id": 999,
            "message": "MSH|^~\\&|...",
        }
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_import_hl7_invalid_message(self, api_client, user, analyzer):
        """Test HL7 import with invalid message."""
        api_client.force_authenticate(user=user)
        data = {
            "analyzer_id": analyzer.id,
            "message": "Invalid HL7 message",
        }
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", data)
        # Should create import record with FAILED status
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert AnalyzerResultImport.objects.filter(status="FAILED").exists()


@pytest.mark.django_db
class TestHL7Parser:
    """Test HL7 parser."""
    
    def test_parse_hl7_message(self):
        """Test parsing HL7 message."""
        message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||ORD-001|CBC^Complete Blood Count
OBX|1|NM|WBC^White Blood Count|100|10*3/uL|4.0-11.0|N|||F"""
        
        parsed = parse_hl7_message(message)
        assert "order" in parsed
        assert "results" in parsed
        assert len(parsed["results"]) > 0
    
    def test_parse_hl7_invalid_message(self):
        """Test parsing invalid HL7 message."""
        message = "Invalid message"
        # Should not raise exception, but return empty or minimal structure
        parsed = parse_hl7_message(message)
        assert isinstance(parsed, dict)
    
    def test_parse_hl7_empty_message(self):
        """Test parsing empty message."""
        message = ""
        parsed = parse_hl7_message(message)
        assert isinstance(parsed, dict)


