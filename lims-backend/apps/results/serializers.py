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

    def to_representation(self, instance):
        """Convert status to lowercase for frontend compatibility."""
        data = super().to_representation(instance)
        # Map backend status to frontend status
        status_map = {
            "DRAFT": "pending",
            "ENTERED": "pending",
            "VERIFIED": "verified",
            "PUBLISHED": "verified",
            "REJECTED": "rejected",
        }
        if "status" in data and data["status"]:
            data["status"] = status_map.get(data["status"], data["status"].lower())
        return data

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
            "status",
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
        from django.utils import timezone
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["entered_by"] = request.user
        # Set entered_at if not provided
        if "entered_at" not in validated_data:
            validated_data["entered_at"] = timezone.now()
        # Set status to ENTERED when creating (pending verification)
        if "status" not in validated_data:
            validated_data["status"] = "ENTERED"
        return super().create(validated_data)
