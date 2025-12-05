"""Patient serializers."""

from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers

from .models import Patient
from .services import allocate_patient_mrn


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Patient model.

    Handles the serialization and deserialization of Patient objects, including
    validation of patient data and support for offline registration.
    """

    origin_terminal_code = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Terminal code for offline registration",
    )
    offline = serializers.BooleanField(
        write_only=True,
        default=False,
        help_text="True if this is an offline registration",
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "mrn",
            "full_name",
            "father_name",
            "dob",
            "sex",
            "phone",
            "cnic",
            "address",
            "age_years",
            "age_months",
            "age_days",
            "origin_terminal",
            "is_offline_entry",
            "synced_at",
            "created_at",
            "updated_at",
            "origin_terminal_code",
            "offline",
        ]
        read_only_fields = [
            "id",
            "mrn",
            "origin_terminal",
            "is_offline_entry",
            "synced_at",
            "created_at",
            "updated_at",
        ]

    def validate_dob(self, value):
        """
        Validates that the date of birth is not in the future.

        Args:
            value (date): The date of birth to validate.

        Returns:
            date: The validated date of birth.
        """
        if value and value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate_phone(self, value):
        """
        Normalizes and validates the phone number.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The normalized phone number.
        """
        phone = value.replace(" ", "").replace("-", "")
        if not phone.startswith(("+92", "0")):
            raise serializers.ValidationError("Phone must start with +92 or 0.")
        return phone

    def validate_cnic(self, value):
        """
        Validates the CNIC format.

        Args:
            value (str): The CNIC to validate.

        Returns:
            str: The validated CNIC.
        """
        import re

        if not value:
            return None

        if not re.match(r"^\d{5}-\d{7}-\d$", value):
            raise serializers.ValidationError("CNIC must be in format #####-#######-#")
        return value

    def validate(self, attrs):
        """
        Ensures that either a date of birth or age is provided.

        If age is provided instead of DOB, it calculates the DOB.
        If DOB is provided, it calculates the age.

        Args:
            attrs (dict): The attributes to validate.

        Returns:
            dict: The validated attributes.
        """
        dob = attrs.get("dob")
        age_years = attrs.get("age_years")
        age_months = attrs.get("age_months")
        age_days = attrs.get("age_days")

        has_dob = dob is not None
        has_age = any(
            [age_years is not None, age_months is not None, age_days is not None]
        )

        if not has_dob and not has_age:
            raise serializers.ValidationError(
                "Either date of birth or at least one age field "
                "(years, months, days) must be provided."
            )

        if has_age and not has_dob:
            years = age_years or 0
            months = age_months or 0
            days = age_days or 0

            today = date.today()
            try:
                attrs["dob"] = today - relativedelta(
                    years=years, months=months, days=days
                )
            except Exception as e:
                raise serializers.ValidationError(
                    f"Invalid age values: {str(e)}"
                ) from e

        if has_dob and not has_age:
            dob_date = attrs["dob"]
            today = date.today()

            delta = relativedelta(today, dob_date)
            attrs["age_years"] = delta.years
            attrs["age_months"] = delta.months
            attrs["age_days"] = delta.days

        return attrs

    def create(self, validated_data):
        """
        Creates a patient, handling both online and offline registration.

        This method allocates a Medical Record Number (MRN) using the
        `allocate_patient_mrn` service, which supports offline MRN generation
        from a terminal's range.

        Args:
            validated_data (dict): The validated data for the patient.

        Returns:
            Patient: The newly created patient instance.
        """
        origin_terminal_code = validated_data.pop("origin_terminal_code", None)
        offline = validated_data.pop("offline", False)

        try:
            mrn, origin_terminal, is_offline_entry = allocate_patient_mrn(
                origin_terminal_code=origin_terminal_code,
                offline=offline,
            )
        except ValidationError as e:
            error_messages = e.messages if hasattr(e, "messages") else [str(e)]
            for msg in error_messages:
                msg_lower = msg.lower()
                if "required" in msg_lower and "terminal" in msg_lower:
                    raise serializers.ValidationError(
                        {
                            "detail": (
                                "Terminal code is required for offline " "registration."
                            )
                        }
                    ) from e
                elif "not found" in msg_lower or "not active" in msg_lower:
                    raise serializers.ValidationError(
                        {"detail": "Invalid or inactive terminal."}
                    ) from e
                elif "exhausted" in msg_lower:
                    raise serializers.ValidationError(
                        {
                            "detail": (
                                "Terminal has exhausted its offline "
                                "registration range."
                            )
                        }
                    ) from e
            raise serializers.ValidationError(
                {"detail": "Invalid registration parameters."}
            ) from e

        if mrn is not None:
            validated_data["mrn"] = mrn
        if origin_terminal is not None:
            validated_data["origin_terminal"] = origin_terminal
        validated_data["is_offline_entry"] = is_offline_entry

        if offline and is_offline_entry:
            validated_data["synced_at"] = timezone.now()

        try:
            patient = Patient.objects.create(**validated_data)
        except IntegrityError as e:
            if "mrn" in str(e).lower() or "unique" in str(e).lower():
                raise serializers.ValidationError(
                    {"detail": "Registration number already exists."}
                ) from e
            raise

        return patient
