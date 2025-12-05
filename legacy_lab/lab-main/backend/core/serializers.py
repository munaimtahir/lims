"""Serializers for core models."""

from rest_framework import serializers

from core.validators import validate_alphanumeric_code

from .models import LabTerminal


class LabTerminalSerializer(serializers.ModelSerializer):
    """
    Serializer for the LabTerminal model.

    Handles the serialization and deserialization of LabTerminal objects,
    validating the input data, including checking for overlapping offline MRN ranges.
    """

    class Meta:
        model = LabTerminal
        fields = [
            "id",
            "code",
            "name",
            "offline_range_start",
            "offline_range_end",
            "offline_current",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "offline_current", "created_at", "updated_at"]

    def validate_code(self, value):
        """
        Validate that the terminal code is alphanumeric.

        Args:
            value (str): The terminal code to validate.

        Returns:
            str: The validated terminal code.
        """
        return validate_alphanumeric_code(value, "terminal code")

    def validate(self, data):
        """
        Validate the offline MRN range and check for overlaps.

        Args:
            data (dict): The data to validate.

        Returns:
            dict: The validated data.

        Raises:
            serializers.ValidationError: If the range is invalid or
            overlaps with another terminal.
        """
        start = data.get("offline_range_start")
        end = data.get("offline_range_end")

        # Get existing values from instance if updating
        if self.instance:
            if start is None:
                start = self.instance.offline_range_start
            if end is None:
                end = self.instance.offline_range_end

        if start is not None and end is not None and start >= end:
            raise serializers.ValidationError(
                {"offline_range_start": "Start must be less than end."}
            )

        # Check for overlapping ranges with other terminals only if we have both values
        if start is not None and end is not None:
            instance = self.instance
            overlapping = LabTerminal.objects.filter(
                offline_range_start__lt=end, offline_range_end__gt=start
            )

            if instance:
                overlapping = overlapping.exclude(pk=instance.pk)

            if overlapping.exists():
                # Safe to call first() since exists() confirms at least one record
                overlap_code = overlapping.first().code
                raise serializers.ValidationError(
                    f"MRN range overlaps with existing terminal: {overlap_code}"
                )

        return data
