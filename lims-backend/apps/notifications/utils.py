"""
Utility functions for sending email notifications.
"""

import logging
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notification, NotificationType, NotificationStatus

logger = logging.getLogger(__name__)


def send_notification(
    notification_type,
    recipient_email,
    subject,
    message,
    recipient_user=None,
    related_order=None,
    related_payment=None,
    related_report=None,
    html_message=None,
):
    """
    Send an email notification and create a notification record.
    
    Args:
        notification_type (str): Type of notification.
        recipient_email (str): Email address of recipient.
        subject (str): Email subject.
        message (str): Plain text message.
        recipient_user (User, optional): User recipient.
        related_order (Order, optional): Related order.
        related_payment (Payment, optional): Related payment.
        related_report (Report, optional): Related report.
        html_message (str, optional): HTML message content.
    
    Returns:
        Notification: The created notification record.
    """
    # Get email settings from system settings
    try:
        from apps.core.models import SystemSettings
        sys_settings = SystemSettings.get_settings()
        
        # Configure email backend if settings exist
        if sys_settings.email_host:
            # Email will be sent using configured SMTP settings
            pass
    except Exception as e:
        logger.warning(f"Could not load system settings for email: {e}")
    
    # Create notification record
    notification = Notification.objects.create(
        notification_type=notification_type,
        recipient_email=recipient_email,
        recipient_user=recipient_user,
        subject=subject,
        message=message,
        status=NotificationStatus.PENDING,
        related_order=related_order,
        related_payment=related_payment,
        related_report=related_report,
    )
    
    # Try to send email
    try:
        # Use default email backend or system settings
        email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lims.local')
        
        # Try to get from system settings
        try:
            from apps.core.models import SystemSettings
            sys_settings = SystemSettings.get_settings()
            if sys_settings.email_from:
                email_from = sys_settings.email_from
        except:
            pass
        
        if html_message:
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=email_from,
                to=[recipient_email],
            )
            email.content_subtype = "html"
            email.send()
        else:
            send_mail(
                subject=subject,
                message=message,
                from_email=email_from,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
        
        # Mark as sent
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save()
        
        logger.info(f"Notification sent successfully: {notification.id}")
        
    except Exception as e:
        # Mark as failed
        notification.status = NotificationStatus.FAILED
        notification.error_message = str(e)
        notification.save()
        
        logger.error(f"Failed to send notification {notification.id}: {e}")
    
    return notification


def send_order_complete_notification(order):
    """
    Send notification when an order is completed.
    
    Args:
        order (Order): The completed order.
    
    Returns:
        Notification: The created notification.
    """
    patient = order.patient
    subject = f"Order {order.order_id} - Results Ready"
    
    message = f"""
Dear {patient.get_full_name()},

Your laboratory test results for Order {order.order_id} are now ready.

You can view and download your report from the patient portal or visit our laboratory.

Thank you for choosing our services.

Best regards,
Laboratory Team
    """.strip()
    
    if patient.email:
        return send_notification(
            notification_type=NotificationType.ORDER_COMPLETE,
            recipient_email=patient.email,
            subject=subject,
            message=message,
            related_order=order,
        )
    return None


def send_critical_value_alert(result, recipient_email=None):
    """
    Send alert when a critical value is detected.
    
    Args:
        result (TestResult): The result with critical value.
        recipient_email (str, optional): Email to send alert to.
    
    Returns:
        Notification: The created notification.
    """
    if not recipient_email:
        # Default to pathologist/admin emails
        from apps.accounts.models import User
        admins = User.objects.filter(role__in=["Admin", "Pathologist"], is_active=True)
        if admins.exists():
            recipient_email = admins.first().email
        else:
            logger.warning("No recipient email for critical value alert")
            return None
    
    order = result.order_item.order
    patient = order.patient
    param = result.test_parameter
    
    subject = f"CRITICAL ALERT: {param.parameter_name} - {patient.get_full_name()}"
    
    message = f"""
CRITICAL VALUE ALERT

Patient: {patient.get_full_name()} ({patient.patient_id})
Order: {order.order_id}
Test: {param.test.test_name}
Parameter: {param.parameter_name}
Result: {result.result_value} {param.unit}
Flag: {result.get_flag_display()}

This result requires immediate attention.

Please review and verify this result as soon as possible.

Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
    """.strip()
    
    return send_notification(
        notification_type=NotificationType.CRITICAL_VALUE,
        recipient_email=recipient_email,
        subject=subject,
        message=message,
        related_order=order,
    )


def send_payment_receipt_notification(payment):
    """
    Send payment receipt via email.
    
    Args:
        payment (Payment): The payment record.
    
    Returns:
        Notification: The created notification.
    """
    order = payment.order
    patient = order.patient
    
    if not patient.email:
        return None
    
    subject = f"Payment Receipt - Order {order.order_id}"
    
    message = f"""
Dear {patient.get_full_name()},

Thank you for your payment.

Receipt Number: REC-{payment.id:06d}
Order ID: {order.order_id}
Amount Paid: {payment.amount} {payment.order.patient.currency if hasattr(payment.order.patient, 'currency') else 'PKR'}
Payment Method: {payment.get_payment_method_display()}
Payment Date: {payment.payment_date.strftime('%Y-%m-%d %H:%M:%S')}

Please keep this receipt for your records.

Best regards,
Laboratory Team
    """.strip()
    
    return send_notification(
        notification_type=NotificationType.PAYMENT_RECEIPT,
        recipient_email=patient.email,
        subject=subject,
        message=message,
        related_payment=payment,
    )


def send_report_ready_notification(report):
    """
    Send notification when a report is ready.
    
    Args:
        report (Report): The generated report.
    
    Returns:
        Notification: The created notification.
    """
    order = report.order
    patient = order.patient
    
    if not patient.email:
        return None
    
    subject = f"Laboratory Report Ready - Order {order.order_id}"
    
    message = f"""
Dear {patient.get_full_name()},

Your laboratory report for Order {order.order_id} is now ready.

Report Number: {report.report_number}
Generated Date: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

You can download your report from the patient portal or visit our laboratory to collect a printed copy.

Thank you for choosing our services.

Best regards,
Laboratory Team
    """.strip()
    
    return send_notification(
        notification_type=NotificationType.REPORT_READY,
        recipient_email=patient.email,
        subject=subject,
        message=message,
        related_report=report,
    )


def send_system_alert(recipient_email, subject, message):
    """
    Send a system alert to administrators.
    
    Args:
        recipient_email (str): Email address of recipient.
        subject (str): Alert subject.
        message (str): Alert message.
    
    Returns:
        Notification: The created notification.
    """
    return send_notification(
        notification_type=NotificationType.SYSTEM_ALERT,
        recipient_email=recipient_email,
        subject=subject,
        message=message,
    )

