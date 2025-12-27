"""Permission classes for patients app."""

from rest_framework import permissions

from users.models import UserRole


class IsAdminOrReception(permissions.BasePermission):
    """Allow access only to Admin and Reception roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [UserRole.ADMIN, UserRole.RECEPTION]
        )
