"""Core models for configuration and infrastructure."""

import os

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils import timezone


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
        "show_ordering_provider": True,
        "show_verified_by_line": True,
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


class Tenant(models.Model):
    """Tenant represents a logical lab organization sharing the same DB."""

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Short stable tenant code used in IDs (e.g., LAB).",
    )
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_tenants"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


def get_default_tenant():
    """Return the default tenant, creating it if missing."""
    tenant, _ = Tenant.objects.get_or_create(code="LAB", defaults={"name": "Default Lab"})
    return tenant


class BranchCapability(models.TextChoices):
    COLLECT_ONLY = "COLLECT_ONLY", "Collection Only"
    COLLECT_AND_PROCESS = "COLLECT_AND_PROCESS", "Collect & Process"
    HQ_PROCESSING = "HQ_PROCESSING", "HQ / Processing"


class Branch(models.Model):
    """Branch / collection site tied to a tenant."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="branches", null=True, blank=True
    )
    code = models.CharField(
        max_length=2,
        validators=[RegexValidator(r"^\d{2}$", "Code must be 2 digits (00-99)")],
        help_text="Numeric branch code (00-99).",
    )
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    capability_mode = models.CharField(
        max_length=32,
        choices=BranchCapability.choices,
        default=BranchCapability.COLLECT_ONLY,
    )
    is_hq = models.BooleanField(
        default=False,
        help_text="True when branch is HQ; enforced for code 00",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_branches"
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="unique_branch_per_tenant"
            )
        ]
        ordering = ["tenant_id", "code"]

    def save(self, *args, **kwargs):
        # Ensure HQ flag mirrors code; only code 00 may be HQ
        self.is_hq = self.code == "00"
        super().save(*args, **kwargs)

    def __str__(self):
        tenant_code = self.tenant.code if self.tenant else "?"
        return f"{tenant_code}:{self.code} - {self.name}"


class TenantMrnSequence(models.Model):
    """Atomic counter for tenant-wide MRN per year (YY)."""

    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="mrn_sequences")
    year_suffix = models.CharField(max_length=2, help_text="YY format")
    last_seq = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_tenant_mrn_sequences"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "year_suffix"], name="unique_tenant_year_mrn_seq"
            )
        ]
        indexes = [models.Index(fields=["tenant", "year_suffix"])]


class OrderIdSequence(models.Model):
    """Atomic counter for per-branch-per-day Order IDs."""

    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="order_sequences")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="order_sequences")
    date = models.DateField()
    last_seq = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_order_id_sequences"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "branch", "date"],
                name="unique_order_seq_per_branch_date",
            )
        ]
        indexes = [models.Index(fields=["tenant", "branch", "date"])]

    @classmethod
    def next_sequence(cls, tenant, branch, for_date=None):
        if for_date is None:
            for_date = timezone.now().date()
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(
                tenant=tenant, branch=branch, date=for_date, defaults={"last_seq": 0}
            )
            seq.last_seq += 1
            seq.save(update_fields=["last_seq", "updated_at"])
            return seq.last_seq


class TenantSettings(models.Model):
    """
    Tenant-scoped settings for branch/collection center and sample workflow behavior.
    When flags are False, corresponding APIs return 404 and UI hides those modules.
    """

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="settings",
        primary_key=True,
    )
    enable_branches = models.BooleanField(
        default=False,
        help_text="When True, branch and dispatch APIs and UI are enabled. When False, branches are hidden and orders do not require a branch.",
    )
    enable_collection_centers = models.BooleanField(
        default=False,
        help_text="When True, registration/order flows may require or use collection center.",
    )
    sample_workflow_enabled = models.BooleanField(
        default=False,
        help_text="When True, sample collection/receiving is required before result entry. When False, orders go directly to result entry after receipt/payment.",
    )
    default_branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Default branch for order collection when user has no branch (e.g. HQ).",
    )
    default_collection_center = models.ForeignKey(
        CollectionCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Default collection center for patient registration when centers enabled.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="User who last updated these settings.",
    )

    class Meta:
        db_table = "core_tenant_settings"
        verbose_name = "Tenant settings"
        verbose_name_plural = "Tenant settings"

    def __str__(self):
        return f"Settings for {self.tenant}"
