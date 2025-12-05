"""
Patient model for LIMS.
"""

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

    # Auto-generated unique ID
    patient_id = models.CharField(
        max_length=20, unique=True, editable=False, db_index=True
    )

    # Demographics
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    # Identification
    national_id = models.CharField(max_length=20, blank=True, null=True, unique=True)

    # Address
    address = models.TextField(blank=True, null=True)

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
            models.Index(fields=["phone"]),
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
        Override the save method to generate a patient ID if it doesn't exist.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        if not self.patient_id:
            self.patient_id = self.generate_patient_id()
        super().save(*args, **kwargs)

    def generate_patient_id(self):
        """
        Generate a unique patient ID in the format P-YYYY-NNNNN.

        The numeric part of the ID is sequential and resets each year.
        For example, the first patient of 2024 would be P-2024-00001.

        Returns:
            str: The generated patient ID.
        """
        current_year = timezone.now().year
        prefix = f"P-{current_year}-"

        # Get the last patient ID for this year
        last_patient = (
            Patient.objects.filter(patient_id__startswith=prefix)
            .order_by("patient_id")
            .last()
        )

        if last_patient:
            last_number = int(last_patient.patient_id.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{new_number:05d}"

    def get_full_name(self):
        """
        Return the patient's full name.

        Returns:
            str: The patient's first name and last name concatenated with a space.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        """
        Calculate the patient's current age based on their date of birth.

        Returns:
            int: The patient's age in years.
        """
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (
            today.month == self.date_of_birth.month
            and today.day < self.date_of_birth.day
        ):
            age -= 1
        return age

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
