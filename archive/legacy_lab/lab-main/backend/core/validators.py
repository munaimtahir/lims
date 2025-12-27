"""Shared validation utilities."""

from rest_framework import serializers


def validate_alphanumeric_code(value: str, field_name: str = "code") -> str:
    """
    Validates that a code is alphanumeric, allowing dashes and underscores.

    Args:
        value: The code string to validate.
        field_name: The name of the field being validated, used in the error message.

    Returns:
        The validated code, converted to uppercase.

    Raises:
        serializers.ValidationError: If the code contains characters other than
            alphanumerics, dashes, or underscores.
    """
    if not value.replace("-", "").replace("_", "").isalnum():
        raise serializers.ValidationError(
            f"{field_name.replace('_', ' ').capitalize()} must be alphanumeric "
            "(dashes and underscores allowed)."
        )
    return value.upper()
