"""Services for patient registration number allocation."""

from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import LabTerminal


@transaction.atomic
def allocate_patient_mrn(
    *, origin_terminal_code: str | None = None, offline: bool = False
) -> tuple[str | None, LabTerminal | None, bool]:
    """
    Decide and allocate the MRN for a new patient registration.

    This function handles both online and offline registration scenarios:
    - Online: Uses the normal date-based MRN generation (PAT-YYYYMMDD-NNNN)
    - Offline: Uses a terminal's reserved numeric range

    Args:
        origin_terminal_code: Short code of the terminal (e.g. 'LAB1-PC').
                            Required when offline=True.
        offline: True when the record was created offline or is being synced.
                False for normal online operation (default).

    Returns:
        Tuple of (mrn, origin_terminal, is_offline_entry):
        - mrn: The allocated MRN string, or None to use normal generation
        - origin_terminal: The LabTerminal instance if offline, else None
        - is_offline_entry: Boolean indicating if this is an offline entry

    Raises:
        ValidationError: If offline=True but origin_terminal_code is missing,
                        or if terminal not found, or range exhausted.
    """
    if not offline:
        # Online mode: use existing auto-generation in Patient.save()
        return None, None, False

    # Offline mode: allocate from terminal range
    if not origin_terminal_code:
        raise ValidationError("origin_terminal_code is required when offline=True")

    try:
        # Use select_for_update to prevent race conditions
        terminal = LabTerminal.objects.select_for_update().get(
            code=origin_terminal_code, is_active=True
        )
    except LabTerminal.DoesNotExist as err:
        raise ValidationError(
            f"Terminal '{origin_terminal_code}' not found or not active"
        ) from err

    # Get next MRN number from terminal's range
    mrn_number = terminal.get_next_offline_mrn()

    # Format as string (numeric only for offline to distinguish from online format)
    # Online format: PAT-YYYYMMDD-NNNN (date-based with prefix)
    # Offline format: Pure numeric (e.g., "710000") from terminal range
    # This allows easy identification of offline vs online registrations
    mrn = str(mrn_number)

    return mrn, terminal, True
