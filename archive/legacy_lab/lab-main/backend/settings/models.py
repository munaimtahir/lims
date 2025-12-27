"""Settings models for system configuration."""

from django.db import models


class WorkflowSettings(models.Model):
    """
    Singleton model for workflow configuration settings.

    This model controls which steps are enabled in the laboratory workflow.

    Attributes:
        enable_sample_collection (BooleanField): If true, manual sample
            collection is required.
        enable_sample_receive (BooleanField): If true, manual sample
            reception is required.
        enable_verification (BooleanField): If true, result verification
            is required before publishing.
        updated_at (DateTimeField): The timestamp of the last update.
    """

    enable_sample_collection = models.BooleanField(
        default=True,
        help_text="Enable manual sample collection step",
    )
    enable_sample_receive = models.BooleanField(
        default=True,
        help_text="Enable manual sample receive step in lab",
    )
    enable_verification = models.BooleanField(
        default=True,
        help_text="Require verification before publishing results",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_settings"
        verbose_name = "Workflow Settings"
        verbose_name_plural = "Workflow Settings"

    def __str__(self):
        """Returns a string representation of the workflow settings."""
        return "Workflow Settings"

    def save(self, *args, **kwargs):
        """
        Overrides the save method to ensure only one instance of this model exists.
        """
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """
        Loads the singleton instance of the workflow settings.

        Returns:
            WorkflowSettings: The singleton instance.
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class RolePermission(models.Model):
    """
    Defines the permissions for each user role in the system.

    Attributes:
        ROLE_CHOICES (list): Choices for the user roles.
        role (CharField): The user role.
        can_register (BooleanField): Permission to register new patients.
        can_collect (BooleanField): Permission to collect samples.
        can_enter_result (BooleanField): Permission to enter test results.
        can_verify (BooleanField): Permission to verify test results.
        can_publish (BooleanField): Permission to publish test results.
        can_edit_catalog (BooleanField): Permission to edit the test catalog.
        can_edit_settings (BooleanField): Permission to edit system settings.
        updated_at (DateTimeField): The timestamp of the last update.
    """

    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("RECEPTION", "Reception"),
        ("PHLEBOTOMY", "Phlebotomy"),
        ("TECHNOLOGIST", "Technologist"),
        ("PATHOLOGIST", "Pathologist"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        unique=True,
        help_text="User role",
    )
    can_register = models.BooleanField(
        default=False,
        help_text="Can register new patients",
    )
    can_collect = models.BooleanField(
        default=False,
        help_text="Can collect samples",
    )
    can_enter_result = models.BooleanField(
        default=False,
        help_text="Can enter test results",
    )
    can_verify = models.BooleanField(
        default=False,
        help_text="Can verify test results",
    )
    can_publish = models.BooleanField(
        default=False,
        help_text="Can publish test results",
    )
    can_edit_catalog = models.BooleanField(
        default=False,
        help_text="Can edit test catalog",
    )
    can_edit_settings = models.BooleanField(
        default=False,
        help_text="Can edit system settings",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role_permissions"
        ordering = ["role"]

    def __str__(self):
        """Returns a string representation of the role permissions."""
        return f"{self.get_role_display()} Permissions"
