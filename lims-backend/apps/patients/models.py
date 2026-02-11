"""
Patient model for LIMS.

Supports patient registration with MRN generation.
"""

from datetime import date

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.models import CollectionCenter, Tenant
from apps.core.numbering import generate_registration_number, generate_tenant_mrn
from apps.core.validators import validate_registration_number


class Patient(models.Model):
    """
    Represents a patient in the LIMS.

    Stores demographic information, contact details, and a unique,
    auto-generated patient ID.

    Attributes:
        patient_id (str): The unique identifier for the patient in the format P-YYYY-NNNNN.
        first_name (str): The patient's first name.
        last_name (str): The patient's last name.
        date_of_birth (date): The patient's date of birth.
        gender (str): The patient's gender (Male, Female, or Other).
        phone (str): The patient's primary phone number.
        email (str, optional): The patient's email address. Defaults to None.
        national_id (str, optional): The patient's national identification number. Defaults to None.
        address (str, optional): The patient's physical address. Defaults to None.
        created_at (datetime): The timestamp of when the record was created.
        updated_at (datetime): The timestamp of the last update.
        created_by (User): The user who created the patient record.
    """

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    # Validators
    cnic_validator = RegexValidator(
        regex=r"^\d{5}-\d{7}-\d$",
        message="CNIC must be in format #####-#######-#",
    )
    phone_validator = RegexValidator(
        regex=r"^(\+92|0)?3\d{9}$",
        message="Phone must be a valid Pakistani mobile number",
    )

    # Auto-generated unique ID (MRN - Medical Record Number)
    # Also keep patient_id for backward compatibility
    patient_id = models.CharField(
        max_length=20, unique=True, editable=False, db_index=True, null=True, blank=True
    )
    mrn = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text="Medical Record Number (auto-generated, unique per tenant)",
    )

    # New Numbering System Fields (V2)
    registration_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        validators=[validate_registration_number],
        help_text="Official Registration Number (YYMM-CC-SSSS)",
    )
    registration_center = models.ForeignKey(
        CollectionCenter,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="patients",
    )
    registration_datetime = models.DateTimeField(null=True, blank=True)

    # Demographics - support both first_name/last_name and full_name
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Full name (alternative to first_name/last_name)",
    )
    father_name = models.CharField(max_length=255, blank=True, default="")
    father_husband_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Father/Husband name",
    )
    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of birth")
    dob = models.DateField(
        null=True, blank=True, help_text="Date of birth (legacy field)"
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    sex = models.CharField(
        max_length=1, choices=SEX_CHOICES, blank=True, help_text="Sex (M/F/O)"
    )

    # Age fields (alternative to DOB) - for cases where exact DOB is unknown
    age_years = models.IntegerField(null=True, blank=True, help_text="Age in years")
    age_months = models.IntegerField(null=True, blank=True, help_text="Age in months")
    age_days = models.IntegerField(null=True, blank=True, help_text="Age in days")

    # Contact Information
    phone = models.CharField(max_length=20, validators=[phone_validator])
    whatsapp_number = models.CharField(
        max_length=20,
        validators=[phone_validator],
        blank=True,
        null=True,
        help_text="Whatsapp number if different from phone"
    )
    email = models.EmailField(blank=True, null=True)

    default_referred_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Default referred by for future orders",
    )

    # Identification
    national_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    cnic = models.CharField(
        max_length=15,
        validators=[cnic_validator],
        unique=True,
        null=True,
        blank=True,
        help_text="National ID in format #####-#######-#",
    )

    # Address
    address = models.TextField(blank=True, null=True)

    # Multi-tenant
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="patients",
        help_text="Owning tenant (lab).",
    )

    # Offline/sync fields
    is_offline_entry = models.BooleanField(
        default=False, help_text="True if originally created while offline"
    )
    origin_terminal = models.ForeignKey(
        "core.LabTerminal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients",
        help_text="Terminal that created this registration (if known)",
    )
    synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when this record was synced to central server",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="patients_created",
    )

    class Meta:
        db_table = "patients"
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mrn"]),
            models.Index(fields=["patient_id"]),
            models.Index(fields=["registration_number"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["cnic"]),
            models.Index(fields=["national_id"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "mrn"], name="unique_patient_mrn_per_tenant"
            )
        ]

    def __str__(self):
        """
        Return a string representation of the patient.

        Returns:
            str: A string in the format "patient_id - full_name".
        """
        return f"{self.patient_id} - {self.get_full_name()}"

    def save(self, *args, **kwargs):
        """
        Override the save method to generate MRN/patient_id if they don't exist.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        # V2 Numbering System (Branch-aware now uses tenant MRN)
        if not self.registration_number:
            # Ensure center exists - fallback to Head Office (00)
            if not self.registration_center:
                center_00, _ = CollectionCenter.objects.get_or_create(
                    code="00", defaults={"name": "Head Office", "is_active": True}
                )
                self.registration_center = center_00

            if not self.registration_datetime:
                self.registration_datetime = timezone.now()

            # Generate the legacy center-based number for backward compatibility
            self.registration_number = generate_registration_number(
                self.registration_center, self.registration_datetime
            )

        # Tenant MRN for new patients (preserve existing if set)
        if not self.tenant:
            # Best-effort: derive tenant from center if available
            self.tenant = getattr(self.registration_center, "tenant", None)

        if not self.mrn:
            if self.tenant:
                self.mrn = generate_tenant_mrn(self.tenant, self.registration_datetime)
            else:
                # Fallback to legacy registration_number if tenant missing
                self.mrn = self.registration_number

        # Keep patient_id aligned to MRN for compatibility
        if not self.patient_id:
            self.patient_id = self.mrn

        # Set full_name from first_name/last_name if not provided
        if not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name} {self.last_name}".strip()

        # Set first_name/last_name from full_name if not provided
        if not self.first_name and not self.last_name and self.full_name:
            parts = self.full_name.split(maxsplit=1)
            self.first_name = parts[0] if parts else ""
            self.last_name = parts[1] if len(parts) > 1 else ""

        # Map gender to sex if sex not set
        if not self.sex and self.gender:
            gender_to_sex = {"Male": "M", "Female": "F", "Other": "O"}
            self.sex = gender_to_sex.get(self.gender, "O")

        # Map sex to gender if gender not set
        if not self.gender and self.sex:
            sex_to_gender = {"M": "Male", "F": "Female", "O": "Other"}
            self.gender = sex_to_gender.get(self.sex, "Other")

        # Use dob if date_of_birth not set
        if not self.date_of_birth and self.dob:
            self.date_of_birth = self.dob

        # Use cnic if national_id not set
        if not self.national_id and self.cnic:
            self.national_id = self.cnic

        if not self.father_husband_name and self.father_name:
            self.father_husband_name = self.father_name

        if not self.father_name and self.father_husband_name:
            self.father_name = self.father_husband_name

        super().save(*args, **kwargs)

    def generate_mrn(self):
        """
        Generate a unique Medical Record Number in the format PAT-YYYYMMDD-NNNN.

        Uses the standard daily sequence.

        Returns:
            str: The generated MRN.
        """
        # Standard MRN generation
        today = timezone.now().strftime("%Y%m%d")
        prefix = f"PAT-{today}-"

        last_patient = (
            Patient.objects.filter(mrn__startswith=prefix).order_by("mrn").last()
        )

        if last_patient:
            try:
                last_num = int(last_patient.mrn.split("-")[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def get_full_name(self):
        """
        Return the patient's full name.

        Returns:
            str: The patient's full name (from full_name field or first_name + last_name).
        """
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        """
        Calculate the patient's current age based on their date of birth or age fields.

        Returns:
            int: The patient's age in years.
        """
        # If age_years is provided, use it
        if self.age_years is not None:
            return self.age_years

        # Otherwise calculate from DOB
        dob = self.date_of_birth or self.dob
        if dob:
            today = date.today()
            age = today.year - dob.year
            if today.month < dob.month or (
                today.month == dob.month and today.day < dob.day
            ):
                age -= 1
            return age

        return None

    @property
    def total_orders(self):
        """
        Calculate the total number of orders associated with the patient.

        Returns:
            int: The total count of orders for this patient.
        """
        return self.orders.count()

    @property
    def last_visit(self):
        """
        Get the date of the patient's last visit based on their most recent order.

        Returns:
            date: The date of the last order, or None if the patient has no orders.
        """
        last_order = self.orders.order_by("-created_at").first()
        return last_order.created_at if last_order else None
