"""Catalog serializers."""

from rest_framework import serializers

from core.validators import validate_alphanumeric_code

from .models import (
    Parameter,
    ParameterQuickText,
    ReferenceRange,
    Test,
    TestCatalog,
    TestParameter,
)


class TestCatalogSerializer(serializers.ModelSerializer):
    """
    Serializer for the TestCatalog model.

    Handles the serialization and deserialization of TestCatalog objects,
    validating the input data.
    """

    class Meta:
        model = TestCatalog
        fields = [
            "id",
            "code",
            "name",
            "description",
            "category",
            "sample_type",
            "price",
            "turnaround_time_hours",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        """
        Validate that the test code is alphanumeric.

        Args:
            value (str): The test code to validate.

        Returns:
            str: The validated test code.
        """
        return validate_alphanumeric_code(value, "test code")

    def validate_price(self, value):
        """
        Validate that the price is a positive number.

        Args:
            value (Decimal): The price to validate.

        Returns:
            Decimal: The validated price.

        Raises:
            serializers.ValidationError: If the price is not greater than 0.
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value


class ParameterSerializer(serializers.ModelSerializer):
    """
    Serializer for the Parameter model.
    """

    class Meta:
        model = Parameter
        fields = [
            "id",
            "code",
            "name",
            "short_name",
            "unit",
            "data_type",
            "editor_type",
            "decimal_places",
            "allowed_values",
            "is_calculated",
            "calculation_formula",
            "flag_direction",
            "has_quick_text",
            "external_code_type",
            "external_code_value",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        """Validate that the parameter code is alphanumeric."""
        return validate_alphanumeric_code(value, "parameter code")


class TestSerializer(serializers.ModelSerializer):
    """
    Serializer for the Test model.
    """

    class Meta:
        model = Test
        fields = [
            "id",
            "code",
            "name",
            "short_name",
            "test_type",
            "department",
            "specimen_type",
            "container_type",
            "result_scale",
            "default_method",
            "default_tat_minutes",
            "default_print_group",
            "default_report_template",
            "default_printer_code",
            "billing_code",
            "default_charge",
            "external_code_type",
            "external_code_value",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        """Validate that the test code is alphanumeric."""
        return validate_alphanumeric_code(value, "test code")

    def validate_default_charge(self, value):
        """Validate that the charge is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Charge cannot be negative.")
        return value


class TestParameterSerializer(serializers.ModelSerializer):
    """
    Serializer for the TestParameter model.
    """

    test_code = serializers.CharField(source="test.code", read_only=True)
    test_name = serializers.CharField(source="test.name", read_only=True)
    parameter_code = serializers.CharField(source="parameter.code", read_only=True)
    parameter_name = serializers.CharField(source="parameter.name", read_only=True)
    parameter_unit = serializers.CharField(source="parameter.unit", read_only=True)

    class Meta:
        model = TestParameter
        fields = [
            "id",
            "test",
            "test_code",
            "test_name",
            "parameter",
            "parameter_code",
            "parameter_name",
            "parameter_unit",
            "display_order",
            "section_header",
            "is_mandatory",
            "show_on_report",
            "default_reference_profile_id",
            "delta_check_enabled",
            "panic_low_override",
            "panic_high_override",
            "comment_template_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ReferenceRangeSerializer(serializers.ModelSerializer):
    """
    Serializer for the ReferenceRange model.
    """

    parameter_code = serializers.CharField(source="parameter.code", read_only=True)
    parameter_name = serializers.CharField(source="parameter.name", read_only=True)

    class Meta:
        model = ReferenceRange
        fields = [
            "id",
            "parameter",
            "parameter_code",
            "parameter_name",
            "method_code",
            "sex",
            "age_min",
            "age_max",
            "age_unit",
            "population_group",
            "unit",
            "normal_low",
            "normal_high",
            "critical_low",
            "critical_high",
            "reference_text",
            "effective_from",
            "effective_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ParameterQuickTextSerializer(serializers.ModelSerializer):
    """
    Serializer for the ParameterQuickText model.
    """

    parameter_code = serializers.CharField(source="parameter.code", read_only=True)
    parameter_name = serializers.CharField(source="parameter.name", read_only=True)

    class Meta:
        model = ParameterQuickText
        fields = [
            "id",
            "parameter",
            "parameter_code",
            "parameter_name",
            "template_title",
            "template_body",
            "language",
            "is_default",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
