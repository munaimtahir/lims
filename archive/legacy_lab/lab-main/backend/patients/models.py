"""Patient models."""

from django.core.validators import RegexValidator
from django.db import models

from core.models import LabTerminal


class Patient(models.Model):
    """
    Represents a patient's demographic and contact information.

    Attributes:
        SEX_CHOICES (list): Choices for the sex field.
        cnic_validator (RegexValidator): Validator for the CNIC field.
        phone_validator (RegexValidator): Validator for the phone field.
        mrn (CharField): Medical Record Number, auto-generated and unique.
        full_name (CharField): The patient's full name.
        father_name (CharField): The patient's father's name.
        dob (DateField): The patient's date of birth.
        sex (CharField): The patient's sex.
        phone (CharField): The patient's phone number.
        cnic (CharField): The patient's Computerized National Identity Card number.
        address (TextField): The patient's address.
        age_years (IntegerField): The patient's age in years (alternative to DOB).
        age_months (IntegerField): The patient's age in months (alternative to DOB).
        age_days (IntegerField): The patient's age in days (alternative to DOB).
        origin_terminal (ForeignKey): The terminal where the patient was registered.
        is_offline_entry (BooleanField): Flag for offline registrations.
        synced_at (DateTimeField): Timestamp for when an offline record was synced.
        created_at (DateTimeField): The timestamp when the patient was created.
        updated_at (DateTimeField): The timestamp when the patient was last updated.
    """

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

    mrn = models.CharField(
        max_length=20,
        unique=True,
        help_text="Medical Record Number (auto-generated)",
    )
    full_name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255, blank=True, default="")
    dob = models.DateField(help_text="Date of birth", null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    cnic = models.CharField(
        max_length=15,
        validators=[cnic_validator],
        unique=True,
        null=True,
        blank=True,
        help_text="National ID in format #####-#######-#",
    )
    address = models.TextField(blank=True, default="")

    # Age fields (alternative to DOB)
    age_years = models.IntegerField(null=True, blank=True, help_text="Age in years")
    age_months = models.IntegerField(null=True, blank=True, help_text="Age in months")
    age_days = models.IntegerField(null=True, blank=True, help_text="Age in days")

    # Offline registration support
    origin_terminal = models.ForeignKey(
        LabTerminal,
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patients"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mrn"]),
            models.Index(fields=["cnic"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        """Returns a string representation of the patient."""
        return f"{self.mrn} - {self.full_name}"

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to generate a Medical Record Number (MRN).

        The MRN is generated based on the current date and a sequential number.
        """
        if not self.mrn:
            # Generate MRN: PAT-YYYYMMDD-NNNN
            from django.utils import timezone

            today = timezone.now().strftime("%Y%m%d")
            # Get the last patient created today
            last_patient = (
                Patient.objects.filter(mrn__startswith=f"PAT-{today}")
                .order_by("mrn")
                .last()
            )
            if last_patient:
                last_num = int(last_patient.mrn.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.mrn = f"PAT-{today}-{new_num:04d}"
        super().save(*args, **kwargs)
