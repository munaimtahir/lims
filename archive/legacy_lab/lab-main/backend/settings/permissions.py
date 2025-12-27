"""Permission checking utilities for role-based access control."""

import os

from .models import RolePermission

# TEMPORARY FULL PERMISSION OVERRIDE — REMOVE LATER WHEN FINE-GRAINED PERMISSIONS ARE ACTIVATED.
# Set this to False to enable role-based permission checking
# Can also be controlled via TEMPORARY_FULL_ACCESS_MODE environment variable
TEMPORARY_FULL_ACCESS_MODE = (
    os.environ.get("TEMPORARY_FULL_ACCESS_MODE", "True").lower() == "true"
)


def check_permission(user, permission_field: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: The user object with a 'role' attribute
        permission_field: The permission field to check
            (e.g., 'can_register', 'can_collect')

    Returns:
        bool: True if user has the permission, False otherwise
    """
    if not user or not user.is_authenticated:
        return False

    # TEMPORARY FULL PERMISSION OVERRIDE — REMOVE LATER WHEN FINE-GRAINED PERMISSIONS ARE ACTIVATED.
    if TEMPORARY_FULL_ACCESS_MODE:
        return True

    # Admin always has all permissions
    if user.role == "ADMIN":
        return True

    try:
        role_perm = RolePermission.objects.get(role=user.role)
        return getattr(role_perm, permission_field, False)
    except RolePermission.DoesNotExist:
        return False


def user_can_register(user) -> bool:
    """Check if user can register patients."""
    return check_permission(user, "can_register")


def user_can_collect(user) -> bool:
    """Check if user can collect samples."""
    return check_permission(user, "can_collect")


def user_can_enter_result(user) -> bool:
    """Check if user can enter test results."""
    return check_permission(user, "can_enter_result")


def user_can_verify(user) -> bool:
    """Check if user can verify test results."""
    return check_permission(user, "can_verify")


def user_can_publish(user) -> bool:
    """Check if user can publish test results."""
    return check_permission(user, "can_publish")


def user_can_edit_catalog(user) -> bool:
    """Check if user can edit test catalog."""
    return check_permission(user, "can_edit_catalog")


def user_can_edit_settings(user) -> bool:
    """Check if user can edit system settings."""
    return check_permission(user, "can_edit_settings")
