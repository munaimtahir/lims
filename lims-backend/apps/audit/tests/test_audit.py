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
        username='admin',
        email='admin@test.com',
        password='adminpass123',
        full_name='Admin User',
        role='Admin'
    )


@pytest.fixture
def manager_user(db):
    """Create and return a manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@test.com',
        password='managerpass123',
        full_name='Manager User',
        role='Manager'
    )


@pytest.fixture
def receptionist_user(db):
    """Create and return a receptionist user."""
    return User.objects.create_user(
        username='receptionist',
        email='receptionist@test.com',
        password='receppass123',
        full_name='Reception User',
        role='Receptionist'
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
        first_name='John',
        last_name='Doe',
        date_of_birth=date(1990, 5, 15),
        gender='Male',
        phone='03001234567',
        created_by=receptionist_user
    )


@pytest.fixture
def audit_log(db, admin_user, patient):
    """Create and return an audit log entry."""
    return AuditLog.objects.create(
        user=admin_user,
        action='CREATE',
        table_name='patients',
        object_id=str(patient.id),
        new_value={'first_name': 'John', 'last_name': 'Doe'}
    )


@pytest.mark.django_db
class TestAuditLogModel:
    """Tests for the AuditLog model."""

    def test_create_audit_log(self, admin_user, patient):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            user=admin_user,
            action='CREATE',
            table_name='patients',
            object_id=str(patient.id),
            new_value={'first_name': 'John'}
        )
        assert log.action == 'CREATE'
        assert log.table_name == 'patients'

    def test_audit_log_str(self, audit_log):
        """Test audit log string representation."""
        assert 'Admin User' in str(audit_log)
        assert 'CREATE' in str(audit_log)
        assert 'patients' in str(audit_log)


@pytest.mark.django_db
class TestAuditUtils:
    """Tests for audit utility functions."""

    def test_log_create(self, admin_user, patient):
        """Test log_create utility."""
        log = log_create(admin_user, patient)
        assert log.action == 'CREATE'
        assert log.table_name == 'patients'
        assert log.new_value is not None

    def test_log_update(self, admin_user, patient):
        """Test log_update utility."""
        old_data = model_to_dict_safe(patient)
        patient.first_name = 'Jane'
        patient.save()
        log = log_update(admin_user, patient, old_data)
        assert log.action == 'UPDATE'
        assert log.old_value['first_name'] == 'John'
        assert log.new_value['first_name'] == 'Jane'

    def test_log_delete(self, admin_user, patient):
        """Test log_delete utility."""
        log = log_delete(admin_user, patient)
        assert log.action == 'DELETE'
        assert log.old_value is not None

    def test_model_to_dict_safe_handles_datetime(self, patient):
        """Test that model_to_dict_safe handles datetime fields."""
        data = model_to_dict_safe(patient)
        assert 'created_at' in data
        # Should be converted to ISO format string
        assert isinstance(data['created_at'], str)

    def test_model_to_dict_safe_handles_decimal(self, db):
        """Test that model_to_dict_safe handles Decimal fields."""
        from apps.laboratory.models import TestCategory, Test
        category = TestCategory.objects.create(name='Test')
        test = Test.objects.create(
            category=category,
            test_code='TST',
            test_name='Test',
            sample_type='Blood',
            price=Decimal('100.50'),
            turnaround_time=4
        )
        data = model_to_dict_safe(test)
        assert 'price' in data
        assert isinstance(data['price'], str)
        assert data['price'] == '100.50'


@pytest.mark.django_db
class TestAuditLogViewSet:
    """Tests for the AuditLog ViewSet."""

    def test_list_audit_logs_admin(self, authenticated_admin_client, audit_log):
        """Test listing audit logs as admin."""
        response = authenticated_admin_client.get('/api/v1/audit/logs/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_audit_logs_manager(self, authenticated_manager_client, audit_log):
        """Test listing audit logs as manager."""
        response = authenticated_manager_client.get('/api/v1/audit/logs/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_audit_logs_unauthorized(self, api_client, receptionist_user, audit_log):
        """Test that non-admin/non-manager cannot access audit logs."""
        api_client.force_authenticate(user=receptionist_user)
        response = api_client.get('/api/v1/audit/logs/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_audit_logs_by_action(self, authenticated_admin_client, audit_log):
        """Test filtering audit logs by action."""
        response = authenticated_admin_client.get('/api/v1/audit/logs/', {
            'action': 'CREATE'
        })
        assert response.status_code == status.HTTP_200_OK

    def test_filter_audit_logs_by_table(self, authenticated_admin_client, audit_log):
        """Test filtering audit logs by table name."""
        response = authenticated_admin_client.get('/api/v1/audit/logs/', {
            'table_name': 'patients'
        })
        assert response.status_code == status.HTTP_200_OK

    def test_audit_logs_read_only(self, authenticated_admin_client, patient):
        """Test that audit logs cannot be created via API."""
        response = authenticated_admin_client.post('/api/v1/audit/logs/', {
            'action': 'CREATE',
            'table_name': 'patients',
            'object_id': str(patient.id)
        })
        # ReadOnlyModelViewSet should return 405 Method Not Allowed
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
