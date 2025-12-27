"""Core models for configuration and infrastructure."""

from django.core.exceptions import ValidationError
from django.db import models, transaction


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
