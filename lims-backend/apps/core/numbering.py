from django.db import transaction
from django.utils import timezone

from django.conf import settings


def generate_registration_number(center, dt=None):
    """
    Generate a formatted Patient Registration Number (MRN).
    Format: YYMM-CC-SSSS
    Example: 2602-00-0001

    Args:
        center (CollectionCenter): The registration center.
        dt (datetime): The registration datetime (default: now).

    Returns:
        str: The generated registration number.
    """
    from apps.core.models import CollectionCenter, RegistrationCounter
    if dt is None:
        dt = timezone.now()

    if center is None:
        # Fallback for when collection centers feature is disabled
        center, _ = CollectionCenter.objects.get_or_create(
            code="00", defaults={"name": "Head Office", "is_active": True}
        )

    yymm = dt.strftime("%y%m")  # e.g., '2602'

    # Atomic increment
    with transaction.atomic():
        # Lock the row for update
        (
            counter,
            created,
        ) = RegistrationCounter.objects.select_for_update().get_or_create(
            yymm=yymm, center=center, defaults={"last_value": 0}
        )

        counter.last_value += 1
        counter.save()

        serial = counter.last_value

    # Formatting
    reg_number = f"{yymm}-{center.code}-{serial:04d}"
    return reg_number


def generate_tenant_mrn(tenant: "Tenant", dt=None):
    """
    Generate tenant-wide MRN.

    Format: TENANTCODE-YY-###### (sequence resets annually per tenant).
    """
    from apps.core.models import TenantMrnSequence
    if dt is None:
        dt = timezone.now()

    year_suffix = dt.strftime("%y")

    with transaction.atomic():
        seq, _ = TenantMrnSequence.objects.select_for_update().get_or_create(
            tenant=tenant, year_suffix=year_suffix, defaults={"last_seq": 0}
        )
        seq.last_seq += 1
        seq.save(update_fields=["last_seq", "updated_at"])
        serial = seq.last_seq

    return f"{tenant.code}-{year_suffix}-{serial:06d}"


def generate_branch_order_id(tenant: "Tenant", branch: "Branch", dt=None):
    """Generate Order ID: BC-YYMMDD-#### per (tenant, branch, date)."""
    from apps.core.models import OrderIdSequence
    if dt is None:
        dt = timezone.now()
    date_part = dt.strftime("%y%m%d")
    seq = OrderIdSequence.next_sequence(tenant=tenant, branch=branch, for_date=dt.date())
    return f"{branch.code}-{date_part}-{seq:04d}"


def generate_lab_number(center, dt=None):
    """
    Generate a formatted Lab/Visit Number (Tube Label).
    Format: MDD-XXX
    Example: B07-001 (Feb 07, #001)

    Args:
        center (CollectionCenter): The collection center.
        dt (datetime): The order datetime (default: now).

    Returns:
        tuple: (lab_number_str, daily_serial_int)
    """
    from apps.core.models import CollectionCenter, LabDailyCounter
    if dt is None:
        dt = timezone.now()

    date_obj = dt.date()

    # Month letter mapping
    month_map = {
        1: "A",
        2: "B",
        3: "C",
        4: "D",
        5: "E",
        6: "F",
        7: "G",
        8: "H",
        9: "I",
        10: "J",
        11: "K",
        12: "L",
    }
    month_letter = month_map[dt.month]
    dd = dt.strftime("%d")  # 01-31

    if center is None:
        # Fallback for when collection centers feature is disabled
        center, _ = CollectionCenter.objects.get_or_create(
            code="00", defaults={"name": "Head Office", "is_active": True}
        )

    # Atomic increment
    with transaction.atomic():
        # Lock the row for update
        counter, created = LabDailyCounter.objects.select_for_update().get_or_create(
            date=date_obj, center=center, defaults={"last_value": 0}
        )

        if counter.last_value >= 999:
            raise ValueError("Daily serial limit (999) reached for this center/date.")

        counter.last_value += 1
        counter.save()

        serial = counter.last_value

    # Formatting
    lab_number = f"{month_letter}{dd}-{serial:03d}"
    return lab_number, serial
