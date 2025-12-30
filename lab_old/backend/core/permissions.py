"""Shared permission classes."""

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow users with the 'ADMIN' role.
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated and has the 'ADMIN' role.

        Args:
            request: The request object.
            view: The view being accessed.

        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access for authenticated users,
    and write access only for users with the 'ADMIN' role.
    """

    def has_permission(self, request, view):
        """
        Check permissions based on the request method.

        Allows GET, HEAD, OPTIONS for any authenticated user.
        Restricts other methods (POST, PUT, DELETE, PATCH) to admin users.

        Args:
            request: The request object.
            view: The view being accessed.

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user.role == "ADMIN"
