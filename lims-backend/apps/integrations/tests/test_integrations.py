"""
Comprehensive tests for integrations app.
"""
import pytest
from decimal import Decimal
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
        response = api_client.post("/api/v1/integrations/analyzers/", data, format='json')
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
    
    @pytest.fixture
    def patient(self):
        """Create test patient."""
        return Patient.objects.create(
            patient_id="PAT-001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
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
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
        # Should create import record with FAILED status
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert AnalyzerResultImport.objects.filter(status="FAILED").exists()
    
    def test_import_hl7_successful_match(self, api_client, user, analyzer, patient):
        """Test HL7 import with successful order matching."""
        from apps.orders.models import Order, OrderItem
        
        # Create order with matching order_id
        order = Order.objects.create(
            order_id="ORD-HL7-001",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="WBC",
            unit="10*3/uL",
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        # Valid HL7 message with matching order
        hl7_message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||ORD-HL7-001|CBC^Complete Blood Count
OBX|1|NM|WBC^White Blood Count|5.0|10*3/uL|4.0-11.0|N|||F"""
        
        api_client.force_authenticate(user=user)
        data = {
            "analyzer_id": analyzer.id,
            "message": hl7_message,
        }
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] in ["success", "pending_review"]
    
    def test_import_hl7_manual_review(self, api_client, user, analyzer):
        """Test HL7 import that requires manual review (no order match)."""
        # Valid HL7 message but no matching order
        hl7_message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||NONEXISTENT-ORDER|CBC^Complete Blood Count
OBX|1|NM|WBC^White Blood Count|5.0|10*3/uL|4.0-11.0|N|||F"""
        
        api_client.force_authenticate(user=user)
        data = {
            "analyzer_id": analyzer.id,
            "message": hl7_message,
        }
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "pending_review"
    
    def test_match_order_action(self, api_client, user, analyzer, patient):
        """Test match_order action."""
        from apps.orders.models import Order, OrderItem
        
        order = Order.objects.create(
            order_id="ORD-MATCH-001",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        # Create import record
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={
                "results": [
                    {"parameter_name": "WBC", "value": "5.0", "flag": "normal"}
                ]
            },
            status="MANUAL_REVIEW",
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/v1/integrations/imports/{import_record.id}/match_order/",
            {"order_item_id": order_item.id},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        import_record.refresh_from_db()
        assert import_record.order_item == order_item
    
    def test_match_order_invalid_order_item(self, api_client, user, analyzer):
        """Test match_order with invalid order_item_id."""
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={},
            status="MANUAL_REVIEW",
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/v1/integrations/imports/{import_record.id}/match_order/",
            {"order_item_id": 99999},
            format='json'
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_match_order_missing_order_item_id(self, api_client, user, analyzer):
        """Test match_order without order_item_id."""
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={},
            status="MANUAL_REVIEW",
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/v1/integrations/imports/{import_record.id}/match_order/",
            {},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_import_hl7_parsing_exception(self, api_client, user, analyzer):
        """Test import_hl7 handles parsing exception."""
        from unittest.mock import patch
        
        api_client.force_authenticate(user=user)
        
        # Mock parse_hl7_message to raise exception
        with patch('apps.integrations.views.parse_hl7_message') as mock_parse:
            mock_parse.side_effect = Exception("Parsing failed")
            
            data = {
                "analyzer_id": analyzer.id,
                "message": "Test message",
            }
            response = api_client.post(
                "/api/v1/integrations/imports/import_hl7/",
                data,
                format='json'
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "status" in response.data
            assert response.data["status"] == "failed"
            # Check import record was created with FAILED status
            assert AnalyzerResultImport.objects.filter(status="FAILED").exists()
    
    def test_import_hl7_order_matching_exception(self, api_client, user, analyzer, patient):
        """Test import_hl7 handles order matching exception."""
        from apps.orders.models import Order
        from unittest.mock import patch
        
        # Create order
        order = Order.objects.create(
            order_id="ORD-HL7-002",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        hl7_message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||ORD-HL7-002|CBC^Complete Blood Count"""
        
        api_client.force_authenticate(user=user)
        
        # Mock Order.objects.filter to raise exception
        # Order is imported locally in the view, so patch at source
        with patch('apps.orders.models.Order.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception("DB error")
            
            data = {
                "analyzer_id": analyzer.id,
                "message": hl7_message,
            }
            response = api_client.post(
                "/api/v1/integrations/imports/import_hl7/",
                data,
                format='json'
            )
            
            # Should still create import record, just without order match
            assert response.status_code == status.HTTP_201_CREATED
    
    def test_import_hl7_result_creation_exception(self, api_client, user, analyzer, patient):
        """Test import_hl7 handles result creation exception."""
        from apps.orders.models import Order, OrderItem
        from apps.laboratory.models import TestCategory, Test, TestParameter
        from unittest.mock import patch
        
        # Create order with matching order_id
        order = Order.objects.create(
            order_id="ORD-HL7-003",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="WBC",
            unit="10*3/uL",
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        hl7_message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||ORD-HL7-003|CBC^Complete Blood Count
OBX|1|NM|WBC^White Blood Count|5.0|10*3/uL|4.0-11.0|N|||F"""
        
        api_client.force_authenticate(user=user)
        
        # Mock TestResult.objects.get_or_create to raise exception
        with patch('apps.integrations.views.TestResult') as mock_result:
            mock_result.objects.get_or_create.side_effect = Exception("Result creation failed")
            
            data = {
                "analyzer_id": analyzer.id,
                "message": hl7_message,
            }
            response = api_client.post(
                "/api/v1/integrations/imports/import_hl7/",
                data,
                format='json'
            )
            
            # Should return error response
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "status" in response.data
            assert response.data["status"] == "failed"
    
    def test_match_order_result_creation_exception(self, api_client, user, analyzer, patient):
        """Test match_order handles result creation exception."""
        from apps.orders.models import Order, OrderItem
        from apps.laboratory.models import TestCategory, Test, TestParameter
        from unittest.mock import patch
        
        order = Order.objects.create(
            order_id="ORD-MATCH-002",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="WBC",
            unit="10*3/uL",
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        # Create import record
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={
                "results": [
                    {"parameter_name": "WBC", "value": "5.0", "flag": "normal"}
                ]
            },
            status="MANUAL_REVIEW",
        )
        
        api_client.force_authenticate(user=user)
        
        # Mock TestResult.objects.get_or_create to raise exception
        with patch('apps.integrations.views.TestResult') as mock_result:
            mock_result.objects.get_or_create.side_effect = Exception("Result creation failed")
            
            response = api_client.post(
                f"/api/v1/integrations/imports/{import_record.id}/match_order/",
                {"order_item_id": order_item.id},
                format='json'
            )
            
            # Should still return 200, but import status should be FAILED
            assert response.status_code == status.HTTP_200_OK
            import_record.refresh_from_db()
            assert import_record.status == "FAILED"
            assert import_record.error_message is not None


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


@pytest.mark.django_db
class TestAnalyzerResultImportViewSetAdditional:
    """Additional tests for AnalyzerResultImportViewSet."""
    
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
    
    @pytest.fixture
    def patient(self):
        """Create test patient."""
        return Patient.objects.create(
            patient_id="PAT-001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
        )
    
    def test_import_hl7_exception_handling(self, api_client, user, analyzer):
        """Test import_hl7 handles exceptions during parsing."""
        api_client.force_authenticate(user=user)
        # This will trigger exception handling in import_hl7
        data = {
            "analyzer_id": analyzer.id,
            "message": "Invalid message that causes exception",
        }
        # Mock parse_hl7_message to raise exception
        from unittest.mock import patch
        with patch('apps.integrations.views.parse_hl7_message') as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert AnalyzerResultImport.objects.filter(status="FAILED").exists()
    
    def test_import_hl7_no_message_type_or_order(self, api_client, user, analyzer):
        """Test import_hl7 with parsed data missing message_type, order, and results."""
        api_client.force_authenticate(user=user)
        from unittest.mock import patch
        with patch('apps.integrations.views.parse_hl7_message') as mock_parse:
            mock_parse.return_value = {}  # Empty parsed data
            data = {
                "analyzer_id": analyzer.id,
                "message": "Test message",
            }
            response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert AnalyzerResultImport.objects.filter(status="FAILED").exists()
    
    def test_import_hl7_match_by_placer_order(self, api_client, user, analyzer, patient):
        """Test import_hl7 matches order by placer_order_number."""
        from apps.orders.models import Order, OrderItem
        from apps.laboratory.models import TestCategory, Test
        
        order = Order.objects.create(
            order_id="ORD-HL7-002",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        hl7_message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||ORD-HL7-002|CBC^Complete Blood Count"""
        
        api_client.force_authenticate(user=user)
        data = {
            "analyzer_id": analyzer.id,
            "message": hl7_message,
        }
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_import_hl7_create_results_on_match(self, api_client, user, analyzer, patient):
        """Test import_hl7 creates test results when order is matched."""
        from apps.orders.models import Order, OrderItem
        from apps.laboratory.models import TestCategory, Test, TestParameter
        
        order = Order.objects.create(
            order_id="ORD-HL7-003",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="WBC",
            unit="10*3/uL",
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        hl7_message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||ORD-HL7-003|CBC^Complete Blood Count
OBX|1|NM|WBC^White Blood Count|5.0|10*3/uL|4.0-11.0|N|||F"""
        
        api_client.force_authenticate(user=user)
        data = {
            "analyzer_id": analyzer.id,
            "message": hl7_message,
        }
        response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check test result was created
        from apps.results.models import TestResult
        assert TestResult.objects.filter(order_item=order_item, test_parameter=param).exists()
    
    def test_import_hl7_result_creation_exception(self, api_client, user, analyzer, patient):
        """Test import_hl7 handles exception during result creation."""
        from apps.orders.models import Order, OrderItem
        from apps.laboratory.models import TestCategory, Test
        
        order = Order.objects.create(
            order_id="ORD-HL7-004",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        
        # Create test parameter so it can be matched
        param = TestParameter.objects.create(
            test=test,
            parameter_name="WBC",
            unit="10*3/uL",
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        hl7_message = """MSH|^~\\&|LAB|HOSPITAL|LAB|HOSPITAL|20240101120000||ORU^R01|12345|P|2.5
PID|1||12345||DOE^JOHN||19900101|M
OBR|1||ORD-HL7-004|CBC^Complete Blood Count
OBX|1|NM|WBC^White Blood Count|5.0|10*3/uL|4.0-11.0|N|||F"""
        
        api_client.force_authenticate(user=user)
        data = {
            "analyzer_id": analyzer.id,
            "message": hl7_message,
        }
        
        # Mock TestResult.objects.get_or_create to raise exception
        # Need to patch where it's actually used - in the view module after import
        from unittest.mock import patch
        with patch('apps.integrations.views.TestResult.objects.get_or_create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            response = api_client.post("/api/v1/integrations/imports/import_hl7/", data, format='json')
            # The exception should be caught and return 500, but if parameter not found, returns 201
            # So we need to ensure parameter exists - it does (WBC parameter created above)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, f"Expected 500, got {response.status_code}. Response: {response.data}"
            import_record = AnalyzerResultImport.objects.filter(analyzer=analyzer).order_by('-id').first()
            assert import_record.status == "FAILED", f"Expected FAILED, got {import_record.status}"
    
    def test_match_order_creates_results(self, api_client, user, analyzer, patient):
        """Test match_order action creates test results."""
        from apps.orders.models import Order, OrderItem
        from apps.laboratory.models import TestCategory, Test, TestParameter
        
        order = Order.objects.create(
            order_id="ORD-MATCH-002",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="WBC",
            unit="10*3/uL",
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={
                "results": [
                    {"parameter_name": "WBC", "value": "5.0", "flag": "normal"}
                ]
            },
            status="MANUAL_REVIEW",
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/v1/integrations/imports/{import_record.id}/match_order/",
            {"order_item_id": order_item.id},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        import_record.refresh_from_db()
        assert import_record.order_item == order_item
        
        # Check test result was created
        from apps.results.models import TestResult
        assert TestResult.objects.filter(order_item=order_item, test_parameter=param).exists()
    
    def test_match_order_result_creation_exception(self, api_client, user, analyzer, patient):
        """Test match_order handles exception during result creation."""
        from apps.orders.models import Order, OrderItem
        from apps.laboratory.models import TestCategory, Test, TestParameter
        
        order = Order.objects.create(
            order_id="ORD-EXCEPTION",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        
        # Create test parameter so it can be matched
        param = TestParameter.objects.create(
            test=test,
            parameter_name="WBC",
            unit="10*3/uL",
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message="Test message",
            parsed_data={
                "results": [
                    {"parameter_name": "WBC", "value": "5.0", "flag": "normal"}
                ]
            },
            status="MANUAL_REVIEW",
        )
        
        api_client.force_authenticate(user=user)
        
        # Mock TestResult.objects.get_or_create to raise exception
        from unittest.mock import patch
        # Patch at the source module where it's used
        with patch('apps.results.models.TestResult.objects.get_or_create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            response = api_client.post(
                f"/api/v1/integrations/imports/{import_record.id}/match_order/",
                {"order_item_id": order_item.id},
                format='json'
            )
            assert response.status_code == status.HTTP_200_OK  # Still returns 200 but status is FAILED
            import_record.refresh_from_db()
            assert import_record.status == "FAILED"


