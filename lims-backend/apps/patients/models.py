"""
Patient model for LIMS.

Supports both online and offline registration with MRN generation.
"""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from datetime import date


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
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Medical Record Number (auto-generated)",
    )

    # Demographics - support both first_name/last_name and full_name
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    full_name = models.CharField(max_length=255, blank=True, help_text="Full name (alternative to first_name/last_name)")
    father_name = models.CharField(max_length=255, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of birth")
    dob = models.DateField(null=True, blank=True, help_text="Date of birth (legacy field)")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, blank=True, help_text="Sex (M/F/O)")

    # Age fields (alternative to DOB) - for cases where exact DOB is unknown
    age_years = models.IntegerField(null=True, blank=True, help_text="Age in years")
    age_months = models.IntegerField(null=True, blank=True, help_text="Age in months")
    age_days = models.IntegerField(null=True, blank=True, help_text="Age in days")

    # Contact Information
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True, null=True)

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

    # Offline registration support
    origin_terminal = models.ForeignKey(
        "core.LabTerminal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients",
        help_text="Terminal that created this registration (if known)",
    )
    is_offline_entry = models.BooleanField(
        default=False,
        help_text="True if originally created while offline",
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
            models.Index(fields=["phone"]),
            models.Index(fields=["cnic"]),
            models.Index(fields=["national_id"]),
            models.Index(fields=["created_at"]),
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
        # Generate MRN if not provided (legacy format: PAT-YYYYMMDD-NNNN)
        if not self.mrn:
            self.mrn = self.generate_mrn()
        
        # Generate patient_id for backward compatibility if not set
        if not self.patient_id:
            self.patient_id = self.mrn  # Use MRN as patient_id for compatibility
        
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
        
        super().save(*args, **kwargs)

    def generate_mrn(self):
        """
        Generate a unique Medical Record Number in the format PAT-YYYYMMDD-NNNN.

        For offline entries, uses the terminal's offline range.
        For online entries, uses the standard daily sequence.

        Returns:
            str: The generated MRN.
        """
        # Check if this is an offline entry with a terminal
        if self.is_offline_entry and self.origin_terminal:
            try:
                next_mrn = self.origin_terminal.get_next_offline_mrn()
                return f"PAT-OFFLINE-{next_mrn:06d}"
            except ValidationError:
                # Fall back to standard generation if offline range exhausted
                pass
        
        # Standard online MRN generation
        today = timezone.now().strftime("%Y%m%d")
        prefix = f"PAT-{today}-"
        
        last_patient = (
            Patient.objects.filter(mrn__startswith=prefix)
            .order_by("mrn")
            .last()
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
