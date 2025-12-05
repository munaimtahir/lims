"""User models for authentication and authorization."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    """
    Enumeration for user roles.
    """

    ADMIN = "ADMIN", "Admin"
    RECEPTION = "RECEPTION", "Reception"
    PHLEBOTOMY = "PHLEBOTOMY", "Phlebotomy"
    TECHNOLOGIST = "TECHNOLOGIST", "Technologist"
    PATHOLOGIST = "PATHOLOGIST", "Pathologist"


class User(AbstractUser):
    """
    Custom user model with role-based access control.

    Attributes:
        role (CharField): The user's role, which determines their permissions.
        phone (CharField): The user's phone number.
    """

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.RECEPTION,
    )
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "users"
        ordering = ["id"]

    def __str__(self):
        """Returns a string representation of the user."""
        return f"{self.username} ({self.get_role_display()})"
