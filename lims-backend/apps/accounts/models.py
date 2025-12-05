"""
Custom User model for the LIMS with role-based access control.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Represents a user in the LIMS.

    This custom User model replaces the default Django User model to include
    role-based access control. It uses a username for authentication.

    Attributes:
        username (str): The unique username for the user.
        email (str): The user's unique email address.
        full_name (str): The user's full name.
        role (str): The user's role, chosen from ROLE_CHOICES.
        is_active (bool): Designates whether this user should be treated as active.
        is_staff (bool): Designates whether the user can log into the admin site.
        is_superuser (bool): Designates that this user has all permissions.
        date_joined (datetime): The date and time the user account was created.
        last_login (datetime): The last login date and time for the user.
    """

    ROLE_CHOICES = [
        ('Admin', 'Administrator'),
        ('Receptionist', 'Receptionist'),
        ('Cashier', 'Cashier'),
        ('Phlebotomist', 'Phlebotomist'),
        ('Lab Technician', 'Lab Technician'),
        ('Pathologist', 'Pathologist'),
        ('Manager', 'Manager'),
    ]

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Receptionist')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        """
        Return a string representation of the user.

        Returns:
            str: A string in the format "full_name (role)".
        """
        return f"{self.full_name} ({self.role})"

    @property
    def is_admin(self):
        """
        Check if the user is an administrator.

        Returns:
            bool: True if the user has the 'Admin' role or is a superuser, False otherwise.
        """
        return self.role == 'Admin' or self.is_superuser

    @property
    def is_receptionist(self):
        """
        Check if the user is a receptionist.

        Returns:
            bool: True if the user has the 'Receptionist' role, False otherwise.
        """
        return self.role == 'Receptionist'

    @property
    def is_cashier(self):
        """
        Check if the user is a cashier.

        Returns:
            bool: True if the user has the 'Cashier' role, False otherwise.
        """
        return self.role == 'Cashier'

    @property
    def is_phlebotomist(self):
        """
        Check if the user is a phlebotomist.

        Returns:
            bool: True if the user has the 'Phlebotomist' role, False otherwise.
        """
        return self.role == 'Phlebotomist'

    @property
    def is_lab_technician(self):
        """
        Check if the user is a lab technician.

        Returns:
            bool: True if the user has the 'Lab Technician' role, False otherwise.
        """
        return self.role == 'Lab Technician'

    @property
    def is_pathologist(self):
        """
        Check if the user is a pathologist.

        Returns:
            bool: True if the user has the 'Pathologist' role, False otherwise.
        """
        return self.role == 'Pathologist'

    @property
    def is_manager(self):
        """
        Check if the user is a manager.

        Returns:
            bool: True if the user has the 'Manager' role, False otherwise.
        """
        return self.role == 'Manager'
