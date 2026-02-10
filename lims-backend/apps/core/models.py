"""Core models for configuration and infrastructure."""

import os

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


def default_print_template_config():
    return {
        "paper_size": "A4",
        "margins": {
            "top": 1.0,
            "right": 1.0,
            "bottom": 1.0,
            "left": 1.0,
        },
        "font_scale": 1.0,
        "show_logo": True,
        "show_header_image": True,
        "show_footer_image": True,
        "show_disclaimer": True,
        "show_signatures": True,
        "show_qr": False,
        "show_barcode": False,
        # Report compliance toggles
        "show_patient_dob": False,
        "repeat_patient_id_on_pages": False,
        "show_specimen_details": False,
        "show_ordering_provider": False,
        "show_verified_by_line": False,
        "show_method_info": False,
        "show_decision_limits": False,
        "show_critical_annotations": False,
        "show_qc_statement": False,
        "show_confidentiality_statement": False,
        "show_revision_banner": False,
    }


def default_print_signatories():
    return []


class LabTerminal(models.Model):
    """
    Model representing a laboratory terminal/workstation.
    Used for tracking offline entries and synchronization.
    """

    name = models.CharField(max_length=255, help_text="Terminal name or identifier")
    location = models.CharField(
        max_length=255, blank=True, help_text="Physical location of terminal"
    )
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
                    if field.name not in ["id", "updated_at", "updated_by"]:
                        setattr(existing, field.name, getattr(self, field.name))
                # Remove force_insert from kwargs to allow update
                kwargs.pop("force_insert", None)
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
        settings = cls.objects.first()
        if settings:
            return settings
        return cls.objects.create(lab_name=os.environ.get("LAB_NAME", "Laboratory"))


class PrintTemplate(models.Model):
    """
    Configurable print template for reports and receipts.
    """

    TYPE_REPORT = "REPORT"
    TYPE_RECEIPT = "RECEIPT"

    TYPE_CHOICES = [
        (TYPE_REPORT, "Report"),
        (TYPE_RECEIPT, "Receipt"),
    ]

    template_key = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    config = models.JSONField(default=default_print_template_config)
    disclaimer_text = models.TextField(blank=True)
    signatories = models.JSONField(default=default_print_signatories)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "print_templates"
        verbose_name = "Print Template"
        verbose_name_plural = "Print Templates"
        ordering = ["type", "name"]

    def save(self, *args, **kwargs):
        """Ensure only one active template per type."""
        super().save(*args, **kwargs)
        if self.is_active:
            PrintTemplate.objects.filter(type=self.type).exclude(pk=self.pk).update(
                is_active=False
            )

    @classmethod
    def get_active(cls, template_type):
        return cls.objects.filter(type=template_type, is_active=True).first()

    def __str__(self):
        return f"{self.type} - {self.name}"


class CollectionCenter(models.Model):
    """
    Represents a collection/reception center for the lab.
    Used for scoping numbering sequences (Registration and Lab numbers).
    """

    code = models.CharField(
        max_length=2,
        unique=True,
        validators=[RegexValidator(r"^\d{2}$", "Code must be 2 digits (00-99)")],
        help_text="2-digit unique code (e.g., '00' for Head Office)",
    )
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_collection_centers"
        verbose_name = "Collection Center"
        verbose_name_plural = "Collection Centers"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class RegistrationCounter(models.Model):
    """
    Atomic counter for Patient Registration Numbers (MRN).
    Scope: (YYMM, Center)
    Format: YYMM-CC-SSSS
    Resets monthly per center.
    """

    yymm = models.CharField(max_length=4, help_text="Year-Month string (e.g., '2602')")
    center = models.ForeignKey(CollectionCenter, on_delete=models.PROTECT)
    last_value = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_registration_counters"
        unique_together = ["yymm", "center"]
        indexes = [
            models.Index(fields=["yymm", "center"]),
        ]


class LabDailyCounter(models.Model):
    """
    Atomic counter for Lab/Visit Numbers (Tube Label).
    Scope: (Date, Center)
    Format: MDD-XXX
    Resets daily per center.
    """

    date = models.DateField(help_text="Date of processing")
    center = models.ForeignKey(CollectionCenter, on_delete=models.PROTECT)
    last_value = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_lab_daily_counters"
        unique_together = ["date", "center"]
        indexes = [
            models.Index(fields=["date", "center"]),
        ]
