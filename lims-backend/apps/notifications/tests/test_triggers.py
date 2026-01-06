"""
Trigger-based integration tests for notifications.
Tests that notifications are created when specific events occur.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult
from apps.billing.models import Payment
from apps.reports.models import Report, ReportStatus
from apps.notifications.models import Notification, NotificationType, NotificationStatus
from apps.laboratory.models import TestCategory, Test, TestParameter


@pytest.mark.django_db
class TestResultCriticalFlagNotification:
    """Test that critical result flags trigger notifications."""
    
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
            email="patient@example.com",
        )
    
    @pytest.fixture
    def order(self, patient):
        """Create test order."""
        return Order.objects.create(
            order_id="ORD-001",
            patient=patient,
            status="in_progress",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
    
    @pytest.fixture
    def test_parameter(self):
        """Create test parameter."""
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="GLU",
            test_name="Glucose",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        return TestParameter.objects.create(
            test=test,
            parameter_name="Glucose",
            unit="mg/dL",
            critical_high=Decimal("250.00"),
        )
    
    @patch('apps.notifications.utils.send_email')
    def test_critical_high_result_creates_notification(
        self, mock_send_email, patient, order, test_parameter
    ):
        """Test that critical high result creates notification."""
        mock_send_email.return_value = True
        
        # Create order item
        order_item = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        
        # Create critical result
        result = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="300",  # Above critical high
            flag="critical_high",
            status="pending",
        )
        
        # Trigger notification (simulate signal or manual trigger)
        from apps.notifications.utils import send_critical_value_alert
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
        assert notification.status in [NotificationStatus.PENDING, NotificationStatus.SENT]
        assert "Glucose" in notification.subject or "Glucose" in notification.message


@pytest.mark.django_db
class TestPaymentReceiptNotification:
    """Test that payment creation triggers receipt notification."""
    
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
            email="patient@example.com",
        )
    
    @pytest.fixture
    def order(self, patient):
        """Create test order."""
        return Order.objects.create(
            order_id="ORD-001",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
    
    @patch('apps.notifications.utils.send_email')
    def test_payment_creates_receipt_notification(self, mock_send_email, patient, order):
        """Test that payment creation triggers receipt notification."""
        mock_send_email.return_value = True
        
        user = User.objects.create_user(
            username="cashier",
            email="cashier@example.com",
            password="testpass123",
            full_name="Cashier User",
            role="Cashier",
        )
        
        # Create payment
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("100.00"),
            payment_method="cash",
            payment_date=timezone.now().date(),
            recorded_by=user,
        )
        
        # Trigger notification
        from apps.notifications.utils import send_payment_receipt_notification
        send_payment_receipt_notification(payment)
        
        # Check notification was created
        notification = Notification.objects.filter(
            notification_type=NotificationType.PAYMENT_RECEIPT,
            related_payment=payment,
        ).first()
        
        assert notification is not None
        assert notification.recipient_email == patient.email
        assert notification.status in [NotificationStatus.PENDING, NotificationStatus.SENT]


@pytest.mark.django_db
class TestReportReadyNotification:
    """Test that report publication triggers ready notification."""
    
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
            email="patient@example.com",
        )
    
    @pytest.fixture
    def order(self, patient):
        """Create test order."""
        return Order.objects.create(
            order_id="ORD-001",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
    
    @patch('apps.notifications.utils.send_email')
    def test_report_ready_creates_notification(self, mock_send_email, patient, order):
        """Test that report ready status triggers notification."""
        mock_send_email.return_value = True
        
        user = User.objects.create_user(
            username="pathologist",
            email="pathologist@example.com",
            password="testpass123",
            full_name="Pathologist User",
            role="Pathologist",
        )
        
        # Create report
        report = Report.objects.create(
            order=order,
            report_number="RPT-20240101-0001",
            status=ReportStatus.FINAL,
            generated_by=user,
        )
        
        # Trigger notification
        from apps.notifications.utils import send_report_ready_notification
        send_report_ready_notification(report)
        
        # Check notification was created
        notification = Notification.objects.filter(
            notification_type=NotificationType.REPORT_READY,
            related_report=report,
        ).first()
        
        assert notification is not None
        assert notification.recipient_email == patient.email
        assert notification.status in [NotificationStatus.PENDING, NotificationStatus.SENT]
        assert "report" in notification.subject.lower() or "report" in notification.message.lower()


@pytest.mark.django_db
class TestOrderCompleteNotification:
    """Test that order completion triggers notification."""
    
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
            email="patient@example.com",
        )
    
    @patch('apps.notifications.utils.send_email')
    def test_order_complete_creates_notification(self, mock_send_email, patient):
        """Test that order completion triggers notification."""
        mock_send_email.return_value = True
        
        # Create completed order
        order = Order.objects.create(
            order_id="ORD-001",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        
        # Trigger notification
        from apps.notifications.utils import send_order_complete_notification
        send_order_complete_notification(order)
        
        # Check notification was created
        notification = Notification.objects.filter(
            notification_type=NotificationType.ORDER_COMPLETE,
            related_order=order,
        ).first()
        
        assert notification is not None
        assert notification.recipient_email == patient.email
        assert notification.status in [NotificationStatus.PENDING, NotificationStatus.SENT]

