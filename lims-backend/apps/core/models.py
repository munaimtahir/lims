"""Core models for configuration and infrastructure."""

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.conf import settings


class SystemSettingsManager(models.Manager):
    """Custom manager for SystemSettings to enforce singleton pattern."""
    
    def create(self, **kwargs):
        """Create or update the singleton settings instance."""
        if self.model.objects.exists():
            # Update existing instance
            existing = self.model.objects.first()
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.save()
            return existing
        return super().create(**kwargs)


class LabTerminal(models.Model):
    """
    Represents a physical workstation or terminal within the laboratory.

    Each terminal is assigned a reserved numeric range for offline patient
    registrations. When a terminal is operating offline, it can allocate
    Medical Record Numbers (MRNs) from this range without needing to contact
    the central server, ensuring uninterrupted service.

    Attributes:
        code (CharField): A short, unique identifier (e.g., 'RECEP-1').
        name (CharField): A human-readable name for the terminal.
        offline_range_start (PositiveIntegerField): Inclusive start of
            the offline MRN range.
        offline_range_end (PositiveIntegerField): Inclusive end of the
            offline MRN range.
        offline_current (PositiveIntegerField): The last used MRN in
            the offline range.
        is_active (BooleanField): A flag indicating if the terminal is currently in use.
        created_at (DateTimeField): The timestamp of when the terminal was created.
        updated_at (DateTimeField): The timestamp of the last update to the terminal.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Short unique identifier (e.g., 'LAB1-PC', 'RECEP-1')",
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this terminal",
    )
    offline_range_start = models.PositiveIntegerField(
        help_text="Start of the offline MRN range (inclusive)"
    )
    offline_range_end = models.PositiveIntegerField(
        help_text="End of the offline MRN range (inclusive)"
    )
    offline_current = models.PositiveIntegerField(
        default=0,
        help_text="Current position in the offline range (0 = unused)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this terminal is currently active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lab_terminals"
        verbose_name = "Lab Terminal"
        verbose_name_plural = "Lab Terminals"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        """Returns a string representation of the lab terminal."""
        return f"{self.code} - {self.name}"

    def clean(self):
        """
        Validates the model's data.

        Ensures that `offline_range_start` is less than `offline_range_end`.
        """
        if self.offline_range_start >= self.offline_range_end:
            raise ValidationError(
                "offline_range_start must be less than offline_range_end"
            )

    @transaction.atomic
    def get_next_offline_mrn(self) -> int:
        """
        Atomically allocates and returns the next offline MRN from
        this terminal's range.

        This method uses a pessimistic lock (`select_for_update`) to
        prevent race conditions when multiple processes might be
        requesting an MRN simultaneously.

        Returns:
            int: The next available offline MRN.

        Raises:
            ValidationError: If the terminal has exhausted its allocated
            offline MRN range.
        """
        # Use select_for_update to prevent race conditions
        terminal = LabTerminal.objects.select_for_update().get(pk=self.pk)

        # Determine next number
        if terminal.offline_current == 0:
            next_mrn = terminal.offline_range_start
        else:
            next_mrn = terminal.offline_current + 1

        # Check if we've exhausted the range
        if next_mrn > terminal.offline_range_end:
            raise ValidationError(
                f"Terminal {terminal.code} has exhausted its offline MRN range "
                f"({terminal.offline_range_start}-{terminal.offline_range_end}). "
                f"Please contact administrator to configure a new range."
            )

        # Update the current position
        terminal.offline_current = next_mrn
        terminal.save(update_fields=["offline_current"])

        return next_mrn


class SystemSettings(models.Model):
    """
    System-wide configuration settings for the LIMS.
    
    Stores lab information, report customization, email settings, and other
    system-wide configurations. Uses a singleton pattern - only one settings
    instance should exist.
    
    Attributes:
        lab_name (str): Name of the laboratory.
        lab_address (str): Address of the laboratory.
        lab_phone (str): Phone number of the laboratory.
        lab_email (str): Email address of the laboratory.
        lab_logo (FileField, optional): Logo image for reports.
        report_header (str, optional): Custom header text for reports.
        report_footer (str, optional): Custom footer text for reports.
        currency (str): Currency code (default: PKR).
        tax_rate (Decimal): Tax rate as percentage.
        email_host (str): SMTP host for email.
        email_port (int): SMTP port.
        email_use_tls (bool): Use TLS for email.
        email_use_ssl (bool): Use SSL for email.
        email_host_user (str): SMTP username.
        email_host_password (str): SMTP password (encrypted).
        email_from (str): Default from email address.
        backup_enabled (bool): Whether automated backups are enabled.
        backup_frequency (str): Backup frequency (daily, weekly, monthly).
        updated_at (datetime): Last update timestamp.
        updated_by (User, optional): User who last updated settings.
    """
    
    objects = SystemSettingsManager()
    
    # Lab Information
    lab_name = models.CharField(max_length=255, default="Laboratory")
    lab_address = models.TextField(blank=True, null=True)
    lab_phone = models.CharField(max_length=50, blank=True, null=True)
    lab_email = models.EmailField(blank=True, null=True)
    lab_logo = models.ImageField(
        upload_to="settings/logos/",
        blank=True,
        null=True,
        help_text="Laboratory logo for reports",
    )
    
    # Report Customization
    report_header = models.TextField(
        blank=True,
        null=True,
        help_text="Custom header text for reports",
    )
    report_footer = models.TextField(
        blank=True,
        null=True,
        help_text="Custom footer text for reports",
    )
    
    # Financial Settings
    currency = models.CharField(max_length=10, default="PKR")
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tax rate as percentage",
    )
    
    # Email Configuration
    email_host = models.CharField(max_length=255, blank=True, null=True)
    email_port = models.IntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_use_ssl = models.BooleanField(default=False)
    email_host_user = models.CharField(max_length=255, blank=True, null=True)
    email_host_password = models.CharField(max_length=255, blank=True, null=True)
    email_from = models.EmailField(blank=True, null=True)
    
    # Backup Settings
    backup_enabled = models.BooleanField(default=False)
    backup_frequency = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        default="daily",
    )
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="settings_updated",
    )
    
    class Meta:
        db_table = "system_settings"
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        """Return string representation."""
        return f"System Settings - {self.lab_name}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure singleton pattern."""
        # Ensure only one settings instance exists
        if not self.pk:
            # Check if settings already exist
            if SystemSettings.objects.exists():
                # Update existing instance instead of creating new one
                existing = SystemSettings.objects.first()
                for field in self._meta.fields:
                    if field.name not in ['id', 'updated_at', 'updated_by']:
                        setattr(existing, field.name, getattr(self, field.name))
                # Remove force_insert from kwargs to allow update
                kwargs.pop('force_insert', None)
                existing.save(*args, **kwargs)
                # Update self to match existing instance
                self.pk = existing.pk
                return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """
        Get the system settings instance (singleton pattern).
        
        Returns:
            SystemSettings: The settings instance, creating one if it doesn't exist.
        """
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
