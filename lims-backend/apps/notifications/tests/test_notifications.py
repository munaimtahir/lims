"""
Comprehensive tests for notifications app.
"""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationType, NotificationStatus
from apps.orders.models import Order
from apps.patients.models import Patient
from apps.billing.models import Payment
from apps.reports.models import Report


@pytest.mark.django_db
class TestNotificationModel:
    """Test Notification model."""
    
    def test_create_notification(self):
        """Test creating a notification."""
        notification = Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test@example.com",
            subject="Test Subject",
            message="Test message",
            status=NotificationStatus.PENDING,
        )
        assert notification.notification_type == NotificationType.ORDER_COMPLETE
        assert notification.recipient_email == "test@example.com"
        assert notification.status == NotificationStatus.PENDING
    
    def test_notification_str(self):
        """Test notification string representation."""
        notification = Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test@example.com",
            subject="Test Subject",
            message="Test message",
        )
        assert "ORDER_COMPLETE" in str(notification)
        assert "test@example.com" in str(notification)


@pytest.mark.django_db
class TestNotificationViewSet:
    """Test NotificationViewSet API."""
    
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
    def notification(self):
        """Create test notification."""
        return Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test@example.com",
            subject="Test Subject",
            message="Test message",
            status=NotificationStatus.SENT,
        )
    
    def test_list_notifications(self, api_client, user, notification):
        """Test listing notifications."""
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
    
    def test_filter_by_type(self, api_client, user):
        """Test filtering notifications by type."""
        Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test1@example.com",
            subject="Test 1",
            message="Message 1",
        )
        Notification.objects.create(
            notification_type=NotificationType.CRITICAL_VALUE,
            recipient_email="test2@example.com",
            subject="Test 2",
            message="Message 2",
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/notifications/?notification_type=ORDER_COMPLETE")
        assert response.status_code == status.HTTP_200_OK
        assert all(
            n["notification_type"] == "ORDER_COMPLETE"
            for n in response.data["results"]
        )
    
    def test_filter_by_status(self, api_client, user):
        """Test filtering notifications by status."""
        Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test1@example.com",
            subject="Test 1",
            message="Message 1",
            status=NotificationStatus.SENT,
        )
        Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test2@example.com",
            subject="Test 2",
            message="Message 2",
            status=NotificationStatus.PENDING,
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/notifications/?status=SENT")
        assert response.status_code == status.HTTP_200_OK
        assert all(n["status"] == "SENT" for n in response.data["results"])
    
    def test_search_notifications(self, api_client, user):
        """Test searching notifications."""
        Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test@example.com",
            subject="Order Complete",
            message="Your order is complete",
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/notifications/?search=complete")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
    
    def test_get_notification_detail(self, api_client, user, notification):
        """Test getting notification detail."""
        api_client.force_authenticate(user=user)
        response = api_client.get(f"/api/v1/notifications/{notification.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == notification.id
        assert response.data["subject"] == "Test Subject"


@pytest.mark.django_db
class TestNotificationUtils:
    """Test notification utility functions."""
    
    def test_send_order_complete_notification(self):
        """Test sending order complete notification."""
        from apps.notifications.utils import send_order_complete_notification
        
        patient = Patient.objects.create(
            patient_id="PAT-001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
            email="patient@example.com",
        )
        order = Order.objects.create(
            order_id="ORD-001",
            patient=patient,
            status="completed",
            total_amount=100.00,
            net_amount=100.00,
        )
        
        # Mock email sending
        with pytest.mock.patch('apps.notifications.utils.send_email') as mock_send:
            mock_send.return_value = True
            send_order_complete_notification(order)
            
            # Check notification was created
            notification = Notification.objects.filter(
                notification_type=NotificationType.ORDER_COMPLETE,
                related_order=order,
            ).first()
            assert notification is not None
            assert notification.recipient_email == patient.email
    
    def test_send_critical_value_notification(self):
        """Test sending critical value notification."""
        from apps.notifications.utils import send_critical_value_notification
        
        patient = Patient.objects.create(
            patient_id="PAT-001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
            email="patient@example.com",
        )
        
        # Mock email sending
        with pytest.mock.patch('apps.notifications.utils.send_email') as mock_send:
            mock_send.return_value = True
            send_critical_value_notification(
                patient_email=patient.email,
                parameter_name="Glucose",
                result_value="300",
                critical_value="250",
            )
            
            # Check notification was created
            notification = Notification.objects.filter(
                notification_type=NotificationType.CRITICAL_VALUE,
                recipient_email=patient.email,
            ).first()
            assert notification is not None


