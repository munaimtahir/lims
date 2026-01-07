"""
Comprehensive tests for notifications app.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationType, NotificationStatus
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.billing.models import Payment
from apps.reports.models import Report
from apps.laboratory.models import TestCategory, Test, TestParameter
from apps.results.models import TestResult


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
    
    def test_notification_cancelled_status(self):
        """Test notification with CANCELLED status."""
        notification = Notification.objects.create(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email="test@example.com",
            subject="Test Subject",
            message="Test message",
            status=NotificationStatus.CANCELLED,
        )
        assert notification.status == NotificationStatus.CANCELLED
        assert "CANCELLED" in str(notification)


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
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        # Mock email sending
        from unittest.mock import patch
        with patch('apps.notifications.utils.send_mail') as mock_send:
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
        from apps.notifications.utils import send_critical_value_alert
        from apps.results.models import TestResult
        from apps.orders.models import OrderItem
        from apps.laboratory.models import TestCategory, Test, TestParameter
        
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
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="GLU",
            test_name="Glucose",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="Glucose",
            unit="mg/dL",
            critical_high=250.00,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=param,
            result_value="300",
            flag="critical_high",
            status="pending",
        )
        
        # Mock email sending
        from unittest.mock import patch
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.return_value = True
            send_critical_value_alert(
                result=result,
                recipient_email=patient.email,
            )
            
            # Check notification was created
            notification = Notification.objects.filter(
                notification_type=NotificationType.CRITICAL_VALUE,
                recipient_email=patient.email,
            ).first()
            assert notification is not None
    
    def test_send_notification_with_html_message(self):
        """Test send_notification with HTML message."""
        from apps.notifications.utils import send_notification
        from unittest.mock import patch
        
        with patch('apps.notifications.utils.EmailMessage') as mock_email:
            mock_email_instance = mock_email.return_value
            mock_email_instance.send.return_value = True
            
            notification = send_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                recipient_email="test@example.com",
                subject="Test",
                message="Plain text",
                html_message="<html><body>HTML content</body></html>",
            )
            
            assert notification is not None
            assert notification.status == NotificationStatus.SENT
            mock_email.assert_called_once()
    
    def test_send_notification_email_failure(self):
        """Test send_notification when email sending fails."""
        from apps.notifications.utils import send_notification
        from unittest.mock import patch
        
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.side_effect = Exception("SMTP Error")
            
            notification = send_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                recipient_email="test@example.com",
                subject="Test",
                message="Test message",
            )
            
            assert notification is not None
            assert notification.status == NotificationStatus.FAILED
            assert notification.error_message is not None
    
    def test_send_order_complete_notification_no_email(self):
        """Test send_order_complete_notification when patient has no email."""
        from apps.notifications.utils import send_order_complete_notification
        
        patient = Patient.objects.create(
            patient_id="PAT-002",
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="Female",
            phone="1234567890",
            # No email
        )
        order = Order.objects.create(
            order_id="ORD-002",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        result = send_order_complete_notification(order)
        assert result is None
    
    def test_send_critical_value_alert_no_recipient(self):
        """Test send_critical_value_alert without recipient_email, defaults to admin."""
        from apps.notifications.utils import send_critical_value_alert
        from unittest.mock import patch
        
        admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass",
            full_name="Admin User",
            role="Admin",
        )
        
        patient = Patient.objects.create(
            patient_id="PAT-003",
            first_name="Test",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
        )
        order = Order.objects.create(
            order_id="ORD-003",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="GLU",
            test_name="Glucose",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="Glucose",
            unit="mg/dL",
        )
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=param,
            result_value="300",
            flag="critical_high",
            status="pending",
        )
        
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.return_value = True
            notification = send_critical_value_alert(result)
            
            assert notification is not None
            assert notification.recipient_email == admin.email
    
    def test_send_critical_value_alert_no_admins(self):
        """Test send_critical_value_alert when no admins exist."""
        from apps.notifications.utils import send_critical_value_alert
        
        patient = Patient.objects.create(
            patient_id="PAT-004",
            first_name="Test",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
        )
        order = Order.objects.create(
            order_id="ORD-004",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="GLU",
            test_name="Glucose",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="Glucose",
            unit="mg/dL",
        )
        order_item = OrderItem.objects.create(
            order=order,
            test=test,
            price=Decimal("50.00"),
        )
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=param,
            result_value="300",
            flag="critical_high",
            status="pending",
        )
        
        # No admins exist
        notification = send_critical_value_alert(result)
        assert notification is None
    
    def test_send_payment_receipt_notification(self):
        """Test send_payment_receipt_notification."""
        from apps.notifications.utils import send_payment_receipt_notification
        from unittest.mock import patch
        
        patient = Patient.objects.create(
            patient_id="PAT-005",
            first_name="Test",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
            email="patient@example.com",
        )
        order = Order.objects.create(
            order_id="ORD-005",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        user = User.objects.create_user(
            username="cashier",
            email="cashier@example.com",
            password="testpass",
            full_name="Cashier",
            role="Cashier",
        )
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("100.00"),
            payment_method="cash",
            recorded_by=user,
        )
        
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.return_value = True
            notification = send_payment_receipt_notification(payment)
            
            assert notification is not None
            assert notification.notification_type == NotificationType.PAYMENT_RECEIPT
            assert notification.related_payment == payment
    
    def test_send_payment_receipt_notification_no_email(self):
        """Test send_payment_receipt_notification when patient has no email."""
        from apps.notifications.utils import send_payment_receipt_notification
        
        patient = Patient.objects.create(
            patient_id="PAT-006",
            first_name="Test",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
            # No email
        )
        order = Order.objects.create(
            order_id="ORD-006",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        user = User.objects.create_user(
            username="cashier",
            email="cashier@example.com",
            password="testpass",
            full_name="Cashier",
            role="Cashier",
        )
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("100.00"),
            payment_method="cash",
            recorded_by=user,
        )
        
        result = send_payment_receipt_notification(payment)
        assert result is None
    
    def test_send_report_ready_notification(self):
        """Test send_report_ready_notification."""
        from apps.notifications.utils import send_report_ready_notification
        from unittest.mock import patch
        
        patient = Patient.objects.create(
            patient_id="PAT-007",
            first_name="Test",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
            email="patient@example.com",
        )
        order = Order.objects.create(
            order_id="ORD-007",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        report = Report.objects.create(
            order=order,
            report_number="RPT-20240101-0001",
            status="final",
        )
        
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.return_value = True
            notification = send_report_ready_notification(report)
            
            assert notification is not None
            assert notification.notification_type == NotificationType.REPORT_READY
            assert notification.related_report == report
    
    def test_send_report_ready_notification_no_email(self):
        """Test send_report_ready_notification when patient has no email."""
        from apps.notifications.utils import send_report_ready_notification
        
        patient = Patient.objects.create(
            patient_id="PAT-008",
            first_name="Test",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="1234567890",
            # No email
        )
        order = Order.objects.create(
            order_id="ORD-008",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        report = Report.objects.create(
            order=order,
            report_number="RPT-20240101-0002",
            status="final",
        )
        
        result = send_report_ready_notification(report)
        assert result is None
    
    def test_send_system_alert(self):
        """Test send_system_alert."""
        from apps.notifications.utils import send_system_alert
        from unittest.mock import patch
        
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.return_value = True
            notification = send_system_alert(
                recipient_email="admin@example.com",
                subject="System Alert",
                message="System is down",
            )
            
            assert notification is not None
            assert notification.notification_type == NotificationType.SYSTEM_ALERT
            assert notification.subject == "System Alert"
    
    def test_send_notification_with_system_settings(self):
        """Test send_notification uses system settings for email_from."""
        from apps.notifications.utils import send_notification
        from apps.core.models import SystemSettings
        from unittest.mock import patch
        
        # Create system settings with email_from
        SystemSettings.objects.create(
            lab_name="Test Lab",
            email_from="lab@example.com",
        )
        
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.return_value = True
            notification = send_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                recipient_email="test@example.com",
                subject="Test",
                message="Test message",
            )
            
            assert notification is not None
            # Verify send_mail was called with email_from from settings
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['from_email'] == "lab@example.com"
    
    def test_send_notification_system_settings_exception(self):
        """Test send_notification handles SystemSettings exception gracefully."""
        from apps.notifications.utils import send_notification
        from unittest.mock import patch, MagicMock
        
        # Mock SystemSettings.get_settings to raise exception
        # SystemSettings is imported inside the function, so patch it at the source
        with patch('apps.core.models.SystemSettings.get_settings') as mock_get_settings:
            mock_get_settings.side_effect = Exception("Settings error")
            
            with patch('apps.notifications.utils.send_mail') as mock_send:
                mock_send.return_value = True
                
                # Should not raise exception, should continue with default email
                notification = send_notification(
                    notification_type=NotificationType.SYSTEM_ALERT,
                    recipient_email="test@example.com",
                    subject="Test",
                    message="Test message",
                )
                
                assert notification is not None
                assert notification.status == NotificationStatus.SENT
    
    def test_send_notification_email_from_exception(self):
        """Test send_notification handles email_from exception gracefully."""
        from apps.notifications.utils import send_notification
        from unittest.mock import patch, MagicMock, PropertyMock
        
        with patch('apps.notifications.utils.send_mail') as mock_send:
            mock_send.return_value = True
            
            # Mock SystemSettings.get_settings to return an instance that raises exception when accessing email_from
            mock_settings_instance = MagicMock()
            type(mock_settings_instance).email_from = PropertyMock(side_effect=Exception("Email from error"))
            
            with patch('apps.core.models.SystemSettings.get_settings', return_value=mock_settings_instance):
                # Should not raise exception, should use default
                notification = send_notification(
                    notification_type=NotificationType.SYSTEM_ALERT,
                    recipient_email="test@example.com",
                    subject="Test",
                    message="Test message",
                )
                
                assert notification is not None
                assert notification.status == NotificationStatus.SENT


