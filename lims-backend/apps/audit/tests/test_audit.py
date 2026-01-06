"""
Tests for the audit app.
"""
import pytest
from datetime import date
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.audit.models import AuditLog
from apps.audit.utils import log_create, log_update, log_delete, model_to_dict_safe


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
def manager_user(db):
    """Create and return a manager user."""
    return User.objects.create_user(
        username="manager",
        email="manager@test.com",
        password="managerpass123",
        full_name="Manager User",
        role="Manager",
    )


@pytest.fixture
def receptionist_user(db):
    """Create and return a receptionist user."""
    return User.objects.create_user(
        username="receptionist",
        email="receptionist@test.com",
        password="receppass123",
        full_name="Reception User",
        role="Receptionist",
    )


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Return an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_manager_client(api_client, manager_user):
    """Return an authenticated API client with manager user."""
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def patient(db, receptionist_user):
    """Create and return a patient."""
    return Patient.objects.create(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
        gender="Male",
        phone="03001234567",
        created_by=receptionist_user,
    )


@pytest.fixture
def audit_log(db, admin_user, patient):
    """Create and return an audit log entry."""
    return AuditLog.objects.create(
        user=admin_user,
        action="CREATE",
        table_name="patients",
        object_id=str(patient.id),
        new_value={"first_name": "John", "last_name": "Doe"},
    )


@pytest.mark.django_db
class TestAuditLogModel:
    """Tests for the AuditLog model."""

    def test_create_audit_log(self, admin_user, patient):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            user=admin_user,
            action="CREATE",
            table_name="patients",
            object_id=str(patient.id),
            new_value={"first_name": "John"},
        )
        assert log.action == "CREATE"
        assert log.table_name == "patients"

    def test_audit_log_str(self, audit_log):
        """Test audit log string representation."""
        assert "Admin User" in str(audit_log)
        assert "CREATE" in str(audit_log)
        assert "patients" in str(audit_log)
    
    def test_audit_log_str_no_user(self, patient):
        """Test audit log string representation when user is None."""
        log = AuditLog.objects.create(
            user=None,
            action="CREATE",
            table_name="patients",
            object_id=str(patient.id),
            new_value={"first_name": "John"},
        )
        assert "System" in str(log)
        assert "CREATE" in str(log)
    
    def test_audit_log_with_content_type(self, admin_user, patient):
        """Test audit log with content_type and GenericForeignKey."""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(patient)
        log = AuditLog.objects.create(
            user=admin_user,
            action="UPDATE",
            content_type=content_type,
            object_id=str(patient.id),
            table_name="patients",
            old_value={"first_name": "John"},
            new_value={"first_name": "Jane"},
        )
        assert log.content_type == content_type
        assert log.content_object == patient


@pytest.mark.django_db
class TestAuditUtils:
    """Tests for audit utility functions."""

    def test_log_create(self, admin_user, patient):
        """Test log_create utility."""
        log = log_create(admin_user, patient)
        assert log.action == "CREATE"
        assert log.table_name == "patients"
        assert log.new_value is not None

    def test_log_update(self, admin_user, patient):
        """Test log_update utility."""
        old_data = model_to_dict_safe(patient)
        patient.first_name = "Jane"
        patient.save()
        log = log_update(admin_user, patient, old_data)
        assert log.action == "UPDATE"
        assert log.old_value["first_name"] == "John"
        assert log.new_value["first_name"] == "Jane"

    def test_log_delete(self, admin_user, patient):
        """Test log_delete utility."""
        log = log_delete(admin_user, patient)
        assert log.action == "DELETE"
        assert log.old_value is not None

    def test_model_to_dict_safe_handles_datetime(self, patient):
        """Test that model_to_dict_safe handles datetime fields."""
        data = model_to_dict_safe(patient)
        assert "created_at" in data
        # Should be converted to ISO format string
        assert isinstance(data["created_at"], str)

    def test_model_to_dict_safe_handles_decimal(self, db):
        """Test that model_to_dict_safe handles Decimal fields."""
        from apps.laboratory.models import TestCategory, Test

        category = TestCategory.objects.create(name="Test")
        test = Test.objects.create(
            category=category,
            test_code="TST",
            test_name="Test",
            sample_type="Blood",
            price=Decimal("100.50"),
            turnaround_time=4,
        )
        data = model_to_dict_safe(test)
        assert "price" in data
        assert isinstance(data["price"], str)
        assert data["price"] == "100.50"
    
    def test_get_client_ip_with_x_forwarded_for(self):
        """Test get_client_ip with X-Forwarded-For header."""
        from apps.audit.utils import get_client_ip
        from unittest.mock import Mock
        
        request = Mock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "192.168.1.1, 10.0.0.1",
            "REMOTE_ADDR": "127.0.0.1",
        }
        
        ip = get_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_without_x_forwarded_for(self):
        """Test get_client_ip without X-Forwarded-For header."""
        from apps.audit.utils import get_client_ip
        from unittest.mock import Mock
        
        request = Mock()
        request.META = {"REMOTE_ADDR": "127.0.0.1"}
        
        ip = get_client_ip(request)
        assert ip == "127.0.0.1"
    
    def test_get_client_ip_none_request(self):
        """Test get_client_ip with None request."""
        from apps.audit.utils import get_client_ip
        
        ip = get_client_ip(None)
        assert ip is None
    
    def test_get_user_agent(self):
        """Test get_user_agent."""
        from apps.audit.utils import get_user_agent
        from unittest.mock import Mock
        
        request = Mock()
        request.META = {"HTTP_USER_AGENT": "Mozilla/5.0"}
        
        ua = get_user_agent(request)
        assert ua == "Mozilla/5.0"
    
    def test_get_user_agent_none_request(self):
        """Test get_user_agent with None request."""
        from apps.audit.utils import get_user_agent
        
        ua = get_user_agent(None)
        assert ua is None
    
    def test_log_action_with_request(self, admin_user, patient):
        """Test log_action with request object."""
        from apps.audit.utils import log_action
        from unittest.mock import Mock
        
        request = Mock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "192.168.1.1",
            "HTTP_USER_AGENT": "Test Agent",
            "REMOTE_ADDR": "127.0.0.1",
        }
        
        log = log_action(
            admin_user,
            "UPDATE",
            patient,
            old_data={"first_name": "John"},
            new_data={"first_name": "Jane"},
            request=request,
            notes="Test update",
        )
        
        assert log is not None
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Test Agent"
        assert log.notes == "Test update"
    
    def test_log_action_skip_contenttype(self, admin_user):
        """Test log_action skips ContentType logging."""
        from apps.audit.utils import log_action
        from django.contrib.contenttypes.models import ContentType
        
        log = log_action(admin_user, "UPDATE", ContentType.objects.first())
        assert log is None


@pytest.mark.django_db
class TestAuditLogViewSet:
    """Tests for the AuditLog ViewSet."""

    def test_list_audit_logs_admin(self, authenticated_admin_client, audit_log):
        """Test listing audit logs as admin."""
        response = authenticated_admin_client.get("/api/v1/audit/logs/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_audit_logs_manager(self, authenticated_manager_client, audit_log):
        """Test listing audit logs as manager."""
        response = authenticated_manager_client.get("/api/v1/audit/logs/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_audit_logs_unauthorized(
        self, api_client, receptionist_user, audit_log
    ):
        """Test that non-admin/non-manager cannot access audit logs."""
        api_client.force_authenticate(user=receptionist_user)
        response = api_client.get("/api/v1/audit/logs/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_audit_logs_by_action(self, authenticated_admin_client, audit_log):
        """Test filtering audit logs by action."""
        response = authenticated_admin_client.get(
            "/api/v1/audit/logs/", {"action": "CREATE"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_audit_logs_by_table(self, authenticated_admin_client, audit_log):
        """Test filtering audit logs by table name."""
        response = authenticated_admin_client.get(
            "/api/v1/audit/logs/", {"table_name": "patients"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_audit_logs_read_only(self, authenticated_admin_client, patient):
        """Test that audit logs cannot be created via API."""
        response = authenticated_admin_client.post(
            "/api/v1/audit/logs/",
            {
                "action": "CREATE",
                "table_name": "patients",
                "object_id": str(patient.id),
            },
        )
        # ReadOnlyModelViewSet should return 405 Method Not Allowed
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
