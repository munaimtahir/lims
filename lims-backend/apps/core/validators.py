"""Validators for V2 numbering system."""
import re
from django.core.exceptions import ValidationError


def validate_registration_number(value):
    """
    Validate Patient Registration Number format: YYMM-CC-SSSS
    Example: 2602-00-0001
    """
    if not value:
        return
    
    pattern = r'^\d{4}-\d{2}-\d{4}$'
    if not re.match(pattern, value):
        raise ValidationError(
            f"Registration number must match format YYMM-CC-SSSS (e.g., 2602-00-0001). Got: {value}"
        )


def validate_lab_number(value):
    """
    Validate Lab Number (Tube Label) format: MDD-XXX
    Example: B07-001
    M = Month letter (A-L)
    DD = Day (01-31)
    XXX = Serial (001-999)
    """
    if not value:
        return
    
    pattern = r'^[A-L]\d{2}-\d{3}$'
    if not re.match(pattern, value):
        raise ValidationError(
            f"Lab number must match format MDD-XXX where M is A-L, DD is 01-31, XXX is 001-999. Got: {value}"
        )
