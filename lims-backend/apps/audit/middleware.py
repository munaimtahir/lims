"""
Django middleware for automatic audit logging.

This middleware automatically logs all model changes (create, update, delete)
using Django signals. Uses contextvars to store request information for signal handlers.
"""

import logging
import sys
from contextvars import ContextVar

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import AuditLog
from .utils import get_client_ip, get_user_agent, model_to_dict_safe

logger = logging.getLogger(__name__)

# Context variables for storing request and user in async/signal context
_request_context: ContextVar = ContextVar("request", default=None)
_user_context: ContextVar = ContextVar("user", default=None)

# Track old values for update operations
_old_instances = {}


@receiver(pre_save)
def pre_save_handler(sender, instance, **kwargs):
    """
    Store the old instance state before saving for update operations.
    """
    # Skip if this is AuditLog itself to avoid recursion
    if sender == AuditLog:
        return

    # Check if we are running migrations or raw SQL that might fail
    if "migrate" in sys.argv or "makemigrations" in sys.argv:
        return

    # Only track if instance has a primary key (i.e., it's an update, not a create)
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_instances[id(instance)] = model_to_dict_safe(old_instance)
        except (sender.DoesNotExist, Exception):
            # Catch OperationalError if table doesn't exist yet
            pass


@receiver(post_save)
def post_save_handler(sender, instance, created, **kwargs):
    """
    Log create and update operations.
    """
    # Skip if this is AuditLog itself to avoid recursion
    if sender == AuditLog:
        return

    # Check if we are running migrations
    if "migrate" in sys.argv or "makemigrations" in sys.argv:
        return

    # Skip if model is not in INSTALLED_APPS or doesn't have a pk
    if not instance.pk:
        return

    # Get user and request from context
    try:
        request = _request_context.get()
        user = _user_context.get()
        if (
            not user
            and request
            and hasattr(request, "user")
            and request.user.is_authenticated
        ):
            user = request.user
    except LookupError:
        request = None
        user = None

    # Determine action
    action = "CREATE" if created else "UPDATE"

    # Get old data for updates
    old_data = None
    if not created:
        old_data = _old_instances.pop(id(instance), None)

    # Get new data
    new_data = model_to_dict_safe(instance)

    # Create audit log entry
    try:
        content_type = ContentType.objects.get_for_model(instance)

        # Don't log ContentType or Migration changes to avoid loops during migration
        if content_type.model in ["contenttype", "migration", "logentry"]:
            return

        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=str(instance.pk),
            table_name=instance._meta.db_table,
            old_value=old_data,
            new_value=new_data,
            ip_address=get_client_ip(request) if request else None,
            user_agent=get_user_agent(request) if request else None,
        )
    except Exception as e:
        # Log error but don't break the save operation
        logger.error(f"Failed to create audit log for {sender.__name__}: {e}")


@receiver(pre_delete)
def pre_delete_handler(sender, instance, **kwargs):
    """
    Log delete operations.
    """
    # Skip if this is AuditLog itself to avoid recursion
    if sender == AuditLog:
        return

    # Get user and request from context
    try:
        request = _request_context.get()
        user = _user_context.get()
        if (
            not user
            and request
            and hasattr(request, "user")
            and request.user.is_authenticated
        ):
            user = request.user
    except LookupError:
        request = None
        user = None

    # Get old data
    old_data = model_to_dict_safe(instance)

    # Create audit log entry
    try:
        content_type = ContentType.objects.get_for_model(instance)

        AuditLog.objects.create(
            user=user,
            action="DELETE",
            content_type=content_type,
            object_id=str(instance.pk),
            table_name=instance._meta.db_table,
            old_value=old_data,
            new_value=None,
            ip_address=get_client_ip(request) if request else None,
            user_agent=get_user_agent(request) if request else None,
        )
    except Exception as e:
        # Log error but don't break the delete operation
        logger.error(f"Failed to create audit log for {sender.__name__}: {e}")


class AuditLoggingMiddleware:
    """
    Middleware to store request and user in context for audit logging.

    This middleware stores the current request and user in context variables
    so that signal handlers can access them for audit logging.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the request and store user/request in context.
        """
        # Store request and user in context for signal handlers
        _request_context.set(request)
        if hasattr(request, "user") and request.user.is_authenticated:
            _user_context.set(request.user)
        else:
            _user_context.set(None)

        response = self.get_response(request)

        # Clean up context
        _request_context.set(None)
        _user_context.set(None)

        return response
