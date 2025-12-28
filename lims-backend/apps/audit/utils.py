"""
Utility functions for audit logging.
"""
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.files import FieldFile
from .models import AuditLog


def get_client_ip(request):
    """
    Extract the client IP address from the request.

    Args:
        request: The HTTP request object.

    Returns:
        str: The client IP address, or None if not available.
    """
    if request is None:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_agent(request):
    """
    Extract the user agent from the request.

    Args:
        request: The HTTP request object.

    Returns:
        str: The user agent string, or None if not available.
    """
    if request is None:
        return None
    return request.META.get("HTTP_USER_AGENT", "")


def log_action(
    user, action, instance, old_data=None, new_data=None, request=None, notes=None
):
    """
    Create an audit log entry for an action.

    Args:
        user: The user performing the action.
        action (str): The type of action (CREATE, UPDATE, DELETE, etc.).
        instance: The model instance being acted upon.
        old_data (dict, optional): The previous state of the object.
        new_data (dict, optional): The new state of the object.
        request: The HTTP request object (for IP and user agent).
        notes (str, optional): Additional notes about the action.

    Returns:
        AuditLog: The created audit log entry.
    """
    content_type = ContentType.objects.get_for_model(instance)

    # Don't log ContentType or Migration changes to avoid loops during migration
    if content_type.model in ['contenttype', 'migration', 'logentry']:
        return None

    audit_log = AuditLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=str(instance.pk),
        table_name=instance._meta.db_table,
        old_value=old_data,
        new_value=new_data,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        notes=notes,
    )
    return audit_log


def log_create(user, instance, request=None, notes=None):
    """
    Log a create action.

    Args:
        user: The user who created the object.
        instance: The created model instance.
        request: The HTTP request object.
        notes (str, optional): Additional notes.

    Returns:
        AuditLog: The created audit log entry.
    """
    new_data = model_to_dict_safe(instance)
    return log_action(
        user, "CREATE", instance, new_data=new_data, request=request, notes=notes
    )


def log_update(user, instance, old_data, request=None, notes=None):
    """
    Log an update action.

    Args:
        user: The user who updated the object.
        instance: The updated model instance.
        old_data (dict): The previous state of the object.
        request: The HTTP request object.
        notes (str, optional): Additional notes.

    Returns:
        AuditLog: The created audit log entry.
    """
    new_data = model_to_dict_safe(instance)
    return log_action(
        user,
        "UPDATE",
        instance,
        old_data=old_data,
        new_data=new_data,
        request=request,
        notes=notes,
    )


def log_delete(user, instance, request=None, notes=None):
    """
    Log a delete action.

    Args:
        user: The user who deleted the object.
        instance: The deleted model instance.
        request: The HTTP request object.
        notes (str, optional): Additional notes.

    Returns:
        AuditLog: The created audit log entry.
    """
    old_data = model_to_dict_safe(instance)
    return log_action(
        user, "DELETE", instance, old_data=old_data, request=request, notes=notes
    )


def model_to_dict_safe(instance):
    """
    Convert a model instance to a JSON-serializable dictionary.

    Handles common field types like datetime, Decimal, foreign keys, and files.

    Args:
        instance: The model instance to convert.

    Returns:
        dict: A dictionary representation of the instance.
    """
    from decimal import Decimal
    from datetime import datetime, date

    result = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)

        # Convert non-JSON-serializable types
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = str(value)
        elif isinstance(value, FieldFile):
            try:
                value = value.url
            except ValueError:
                value = str(value) if value else None
        elif hasattr(value, "pk"):  # Foreign key
            value = value.pk

        result[field.name] = value

    return result
