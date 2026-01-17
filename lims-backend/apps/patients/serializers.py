"""
Serializers for the Patient model.
"""

from rest_framework import serializers
from .models import Patient
from datetime import date, timedelta
import calendar


def calculate_age_parts(dob, today=None):
    """Calculate age in years, months, and days from date of birth."""
    if not dob:
        return None, None, None
    today = today or date.today()
    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day

    if days < 0:
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    return years, months, days


def calculate_dob_from_age(years, months=0, days=0, today=None):
    """Calculate date of birth from age components."""
    if years is None:
        return None
    today = today or date.today()
    year = today.year - years
    month = today.month - (months or 0)
    while month <= 0:
        year -= 1
        month += 12
    day = min(today.day, calendar.monthrange(year, month)[1])
    dob = date(year, month, day)
    if days:
        dob -= timedelta(days=days)
    return dob


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Patient model.

    Includes all patient fields and computed properties like age, full_name,
    total_orders, and last_visit. Used for detailed patient views.
    """

    age = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    total_orders = serializers.ReadOnlyField()
    last_visit = serializers.ReadOnlyField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age_years",
            "age_months",
            "age_days",
            "age",
            "gender",
            "phone",
            "email",
            "national_id",
            "address",
            "cnic",
            "father_husband_name",
            "default_referred_by",
            "created_at",
            "updated_at",
            "total_orders",
            "last_visit",
        ]
        read_only_fields = ["id", "patient_id", "created_at", "updated_at"]

    def get_full_name(self, obj):
        """
        Return the patient's full name.

        Args:
            obj (Patient): The patient instance.

        Returns:
            str: The concatenated first and last name.
        """
        return obj.get_full_name()

    def validate_phone(self, value):
        """
        Validate the phone number format.

        Ensures the phone number is not empty and has a minimum length.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            serializers.ValidationError: If the phone number is invalid.
        """
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if len(value) < 10:
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits."
            )
        return value

    def validate_date_of_birth(self, value):
        """
        Validate that the date of birth is not in the future.

        Args:
            value (date): The date of birth to validate.

        Returns:
            date: The validated date of birth.

        Raises:
            serializers.ValidationError: If the date of birth is in the future.
        """
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate(self, attrs):
        """Validate patient data for required fields and DOB/age rules."""
        instance = getattr(self, "instance", None)
        dob = attrs.get("date_of_birth", getattr(instance, "date_of_birth", None))
        age_years = attrs.get("age_years", getattr(instance, "age_years", None))
        age_months = attrs.get("age_months", getattr(instance, "age_months", None)) or 0
        age_days = attrs.get("age_days", getattr(instance, "age_days", None)) or 0
        first_name = attrs.get("first_name", getattr(instance, "first_name", None))
        last_name = attrs.get("last_name", getattr(instance, "last_name", None))
        full_name = attrs.get("full_name", getattr(instance, "full_name", None))
        phone = attrs.get("phone", getattr(instance, "phone", None))
        gender = attrs.get("gender", getattr(instance, "gender", None))

        if not phone:
            raise serializers.ValidationError({"phone": "Mobile number is required."})
        if not gender:
            raise serializers.ValidationError({"gender": "Gender is required."})
        if not full_name and not (first_name or last_name):
            raise serializers.ValidationError({"full_name": "Patient name is required."})

        if dob is None and age_years is None:
            raise serializers.ValidationError(
                {"date_of_birth": "Provide date of birth or age in years."}
            )

        if dob and age_years is not None:
            expected_dob = calculate_dob_from_age(age_years, age_months, age_days)
            if expected_dob and abs((dob - expected_dob).days) > 1:
                raise serializers.ValidationError(
                    {"date_of_birth": "Date of birth does not match provided age."}
                )

        if dob and age_years is None:
            years, months, days = calculate_age_parts(dob)
            attrs["age_years"] = years
            attrs["age_months"] = months
            attrs["age_days"] = days

        return attrs


class PatientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new patient records.

    This serializer includes only the fields required for creating a new patient.
    """

    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age_years",
            "age_months",
            "age_days",
            "gender",
            "phone",
            "email",
            "national_id",
            "cnic",
            "father_husband_name",
            "default_referred_by",
            "address",
        ]

    def validate_phone(self, value):
        """
        Validate the phone number format.

        Ensures the phone number is not empty and has a minimum length.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            serializers.ValidationError: If the phone number is invalid.
        """
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if len(value) < 10:
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits."
            )
        return value

    def validate_date_of_birth(self, value):
        """
        Validate that the date of birth is not in the future.

        Args:
            value (date): The date of birth to validate.

        Returns:
            date: The validated date of birth.

        Raises:
            serializers.ValidationError: If the date of birth is in the future.
        """
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate(self, attrs):
        """Validate patient data for required fields and DOB/age rules."""
        dob = attrs.get("date_of_birth")
        age_years = attrs.get("age_years")
        age_months = attrs.get("age_months") or 0
        age_days = attrs.get("age_days") or 0
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")
        full_name = attrs.get("full_name")
        phone = attrs.get("phone")
        gender = attrs.get("gender")

        if not phone:
            raise serializers.ValidationError({"phone": "Mobile number is required."})
        if not gender:
            raise serializers.ValidationError({"gender": "Gender is required."})
        if not full_name and not (first_name or last_name):
            raise serializers.ValidationError({"full_name": "Patient name is required."})

        if dob is None and age_years is None:
            raise serializers.ValidationError(
                {"date_of_birth": "Provide date of birth or age in years."}
            )

        if dob and age_years is not None:
            expected_dob = calculate_dob_from_age(age_years, age_months, age_days)
            if expected_dob and abs((dob - expected_dob).days) > 1:
                raise serializers.ValidationError(
                    {"date_of_birth": "Date of birth does not match provided age."}
                )

        if dob and age_years is None:
            years, months, days = calculate_age_parts(dob)
            attrs["age_years"] = years
            attrs["age_months"] = months
            attrs["age_days"] = days

        return attrs


class PatientListSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for listing patients.

    This serializer includes a subset of patient fields for efficient display
    in lists and search results.
    """

    age = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    last_order_referred_by = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age",
            "gender",
            "phone",
            "default_referred_by",
            "last_order_referred_by",
            "created_at",
        ]

    def get_full_name(self, obj):
        """
        Return the patient's full name.

        Args:
            obj (Patient): The patient instance.

        Returns:
            str: The concatenated first and last name.
        """
        return obj.get_full_name()

    def get_last_order_referred_by(self, obj):
        last_order = obj.orders.order_by("-created_at").first()
        return last_order.referred_by if last_order else None
