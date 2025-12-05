from rest_framework import serializers
from .models import TestResult


class TestResultSerializer(serializers.ModelSerializer):
    """
    Serializer for the TestResult model.

    Includes read-only fields for parameter details and user names.
    """

    parameter_name = serializers.CharField(
        source="test_parameter.parameter_name", read_only=True
    )
    unit = serializers.CharField(source="test_parameter.unit", read_only=True)
    entered_by_name = serializers.CharField(
        source="entered_by.full_name", read_only=True
    )
    verified_by_name = serializers.CharField(
        source="verified_by.full_name", read_only=True
    )

    class Meta:
        model = TestResult
        fields = [
            "id",
            "order_item",
            "test_parameter",
            "parameter_name",
            "unit",
            "result_value",
            "flag",
            "remarks",
            "entered_by",
            "entered_by_name",
            "entered_at",
            "verified_by",
            "verified_by_name",
            "verified_at",
        ]
        read_only_fields = [
            "flag",
            "entered_by",
            "entered_at",
            "verified_by",
            "verified_at",
        ]

    def create(self, validated_data):
        """
        Create a new test result and set the `entered_by` field to the current user.

        Args:
            validated_data (dict): The data to create the test result with.

        Returns:
            TestResult: The newly created test result instance.
        """
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["entered_by"] = request.user
        return super().create(validated_data)
