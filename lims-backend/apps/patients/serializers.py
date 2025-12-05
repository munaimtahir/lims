"""
Serializers for the Patient model.
"""

from rest_framework import serializers
from .models import Patient
from datetime import date


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
            "age",
            "gender",
            "phone",
            "email",
            "national_id",
            "address",
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
            "date_of_birth",
            "gender",
            "phone",
            "email",
            "national_id",
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


class PatientListSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for listing patients.

    This serializer includes a subset of patient fields for efficient display
    in lists and search results.
    """

    age = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()

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
