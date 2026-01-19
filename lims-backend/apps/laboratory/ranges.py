from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import math
from typing import Any, Optional

from django.utils import timezone

from apps.laboratory.models import ReferenceRange, TestParameter


# Common qualitative abnormal result indicators
ABNORMAL_QUALITATIVE_INDICATORS = [
    "POSITIVE", "REACTIVE", "DETECTED", "ABNORMAL", 
    "PRESENT", "HIGH", "LOW", "CRITICAL"
]


def get_patient_age_years(patient, at_date: Optional[date] = None) -> Optional[float]:
    """Return patient age in years, using DOB when available."""
    if not patient:
        return None
    dob = getattr(patient, "date_of_birth", None) or getattr(patient, "dob", None)
    if not dob:
        return None
    if at_date is None:
        at_date = timezone.now().date()
    if dob > at_date:
        return None
    delta_days = (at_date - dob).days
    return delta_days / 365.25


def format_reference_display(ref_min: Optional[Decimal], ref_max: Optional[Decimal]) -> str:
    """Format the reference range for display."""
    if ref_min is not None and ref_max is not None:
        return f"{ref_min} - {ref_max}"
    if ref_min is not None:
        return f">= {ref_min}"
    if ref_max is not None:
        return f"<= {ref_max}"
    return ""


def _fallback_parameter_range(
    parameter_mapping: TestParameter, gender: Optional[str]
) -> dict[str, Any]:
    """Fallback logic when no age-specific ReferenceRange exists."""
    # In the new global parameter model, fallbacks are looked up from the Parameter model.
    # Note: If Parameter model doesn't have these fields, we return None.
    param = parameter_mapping.parameter
    
    # We check if these fields exist on the Parameter model (they were moved from TestParameter)
    ref_min = None
    ref_max = None
    critical_low = getattr(param, "critical_low", None)
    critical_high = getattr(param, "critical_high", None)

    if gender == "Male":
        ref_min = getattr(param, "reference_min_male", None)
        ref_max = getattr(param, "reference_max_male", None)
    elif gender == "Female":
        ref_min = getattr(param, "reference_min_female", None)
        ref_max = getattr(param, "reference_max_female", None)
    
    # Fallback to male if both are missing
    if ref_min is None: ref_min = getattr(param, "reference_min_male", None)
    if ref_max is None: ref_max = getattr(param, "reference_max_male", None)

    return {
        "ref_min": ref_min,
        "ref_max": ref_max,
        "display": format_reference_display(ref_min, ref_max),
        "source": "parameter_fallback",
        "critical_low": critical_low,
        "critical_high": critical_high,
    }


def pick_reference_range(
    parameter: TestParameter, patient, at_date: Optional[date] = None
) -> dict[str, Any]:
    """Select the best reference range for a parameter and patient."""
    if not parameter:
        return {
            "ref_min": None,
            "ref_max": None,
            "display": "",
            "source": "none",
            "critical_low": None,
            "critical_high": None,
        }

    gender = getattr(patient, "gender", None) if patient else None
    age_years = get_patient_age_years(patient, at_date=at_date)

    if gender not in {"Male", "Female"} or age_years is None:
        return _fallback_parameter_range(parameter, gender)

    ranges = ReferenceRange.objects.filter(
        parameter=parameter,
        is_active=True,
        gender__in=[gender, "Both"],
    )

    candidates = []
    for ref_range in ranges:
        min_ok = ref_range.age_min is None or age_years >= ref_range.age_min
        max_ok = ref_range.age_max is None or age_years <= ref_range.age_max
        if min_ok and max_ok:
            candidates.append(ref_range)

    if not candidates:
        return _fallback_parameter_range(parameter, gender)

    def age_window(ref_range: ReferenceRange) -> float:
        if ref_range.age_min is None or ref_range.age_max is None:
            return math.inf
        return float(ref_range.age_max - ref_range.age_min)

    def sort_key(ref_range: ReferenceRange) -> tuple[int, float, int, int]:
        gender_priority = 0 if ref_range.gender == gender else 1
        return (
            gender_priority,
            age_window(ref_range),
            -ref_range.version,
            -ref_range.id,
        )

    best_range = sorted(candidates, key=sort_key)[0]
    ref_min = best_range.reference_min
    ref_max = best_range.reference_max

    return {
        "ref_min": ref_min,
        "ref_max": ref_max,
        "display": format_reference_display(ref_min, ref_max),
        "source": "reference_range",
        "critical_low": best_range.critical_low,
        "critical_high": best_range.critical_high,
    }


def compute_flag(
    result_value: Any,
    ref_min: Optional[Decimal],
    ref_max: Optional[Decimal],
    critical_low: Optional[Decimal],
    critical_high: Optional[Decimal],
) -> str:
    """
    Compute the flag for a result value (numeric or qualitative).
    
    For numeric values, checks against reference ranges.
    For non-numeric qualitative values, recognizes common abnormal indicators.
    """
    if result_value is None:
        return ""
    
    # Try to parse as numeric value
    try:
        cleaned_value = str(result_value).strip().replace(",", "").replace(" ", "")
        value = Decimal(cleaned_value)
    except (InvalidOperation, ValueError, TypeError):
        # Non-numeric value - check for common qualitative abnormal results
        value_upper = str(result_value).strip().upper()
        
        if any(indicator in value_upper for indicator in ABNORMAL_QUALITATIVE_INDICATORS):
            return "A"
        
        # Normal qualitative results or unrecognized text
        return ""

    # Numeric value - apply range checking
    if critical_low is not None and value <= critical_low:
        return "C"
    if critical_high is not None and value >= critical_high:
        return "C"

    if ref_min is not None and value < ref_min:
        return "L"
    if ref_max is not None and value > ref_max:
        return "H"

    return ""
