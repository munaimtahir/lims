"""Core models for configuration and infrastructure."""

from django.db import models
from django.conf import settings


class LabTerminal(models.Model):
    """
    Model representing a laboratory terminal/workstation.
    Used for tracking offline entries and synchronization.
    """
    name = models.CharField(max_length=255, help_text="Terminal name or identifier")
    location = models.CharField(max_length=255, blank=True, help_text="Physical location of terminal")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "core_labterminal"
        verbose_name = "Lab Terminal"
        verbose_name_plural = "Lab Terminals"
    
    def __str__(self):
        return self.name


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
    lab_display_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Display name for UI header and login (defaults to lab_name if not set)",
    )
    lab_address = models.TextField(blank=True, null=True)
    lab_phone = models.CharField(max_length=50, blank=True, null=True)
    lab_email = models.EmailField(blank=True, null=True)
    lab_logo = models.ImageField(
        upload_to="settings/logos/",
        blank=True,
        null=True,
        help_text="Laboratory logo for reports and UI",
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
    report_header_image = models.ImageField(
        upload_to="settings/report_headers/",
        blank=True,
        null=True,
        help_text="Optional header image for reports and receipts",
    )
    report_footer_image = models.ImageField(
        upload_to="settings/report_footers/",
        blank=True,
        null=True,
        help_text="Optional footer image for reports and receipts",
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
