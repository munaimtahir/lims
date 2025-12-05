"""
Role-based permission classes for the LIMS API.

These classes are used to grant or deny access to different API endpoints
based on the user's role.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access an endpoint.
    """
    def has_permission(self, request, view):
        """
        Check if the user is authenticated and is an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsReceptionist(permissions.BasePermission):
    """
    Custom permission to allow receptionist and admin users.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a receptionist or an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is a receptionist or admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and (
            request.user.is_receptionist or request.user.is_admin
        )


class IsCashier(permissions.BasePermission):
    """
    Custom permission to allow cashier and admin users.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a cashier or an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is a cashier or admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and (
            request.user.is_cashier or request.user.is_admin
        )


class IsPhlebotomist(permissions.BasePermission):
    """
    Custom permission to allow phlebotomist and admin users.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a phlebotomist or an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is a phlebotomist or admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and (
            request.user.is_phlebotomist or request.user.is_admin
        )


class IsLabTechnician(permissions.BasePermission):
    """
    Custom permission to allow lab technician and admin users.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a lab technician or an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is a lab technician or admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and (
            request.user.is_lab_technician or request.user.is_admin
        )


class IsPathologist(permissions.BasePermission):
    """
    Custom permission to allow pathologist and admin users.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a pathologist or an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is a pathologist or admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and (
            request.user.is_pathologist or request.user.is_admin
        )


class IsManager(permissions.BasePermission):
    """
    Custom permission to allow manager and admin users.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a manager or an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is a manager or admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and (
            request.user.is_manager or request.user.is_admin
        )


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow manager and admin users.
    Combined class for use where OR operator is needed.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a manager or an admin.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is a manager or admin, False otherwise.
        """
        return request.user and request.user.is_authenticated and (
            request.user.is_manager or request.user.is_admin
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access for authenticated users,
    but write access only for admin users.
    """
    def has_permission(self, request, view):
        """
        Check permissions for read-only or write access.

        - SAFE_METHODS (GET, HEAD, OPTIONS) are allowed for any authenticated user.
        - Other methods (POST, PUT, DELETE, etc.) are only allowed for admin users.

        Args:
            request (Request): The request object.
            view (View): The view being accessed.

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_admin
