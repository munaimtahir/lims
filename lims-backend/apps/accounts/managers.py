"""
Custom User Manager for the LIMS User model.
"""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom user manager for the User model.

    This manager provides methods to create regular users and superusers.
    It uses the username as a natural key for authentication.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and save a regular User with the given username, email, and password.

        Args:
            username (str): The user's username.
            email (str): The user's email address.
            password (str, optional): The user's password. Defaults to None.
            **extra_fields: Additional fields to be saved with the user model.

        Returns:
            User: The newly created user instance.

        Raises:
            ValueError: If the username or email is not provided.
        """
        if not username:
            raise ValueError("The Username field must be set")
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given username, email, and password.

        Superusers are automatically assigned the 'Admin' role and granted
        staff and superuser privileges.

        Args:
            username (str): The superuser's username.
            email (str): The superuser's email address.
            password (str, optional): The superuser's password. Defaults to None.
            **extra_fields: Additional fields to be saved with the user model.

        Returns:
            User: The newly created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser is not set to True.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "Admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)
