from rest_framework import serializers

from .models import TestResult


class TestResultSerializer(serializers.ModelSerializer):
    """
    Serializer for the TestResult model.

    Includes read-only fields for parameter details and user names.
    """

    parameter_name = serializers.CharField(
        source="test_parameter.effective_parameter_name", read_only=True
    )
    unit = serializers.CharField(source="test_parameter.unit", read_only=True)
    entered_by_name = serializers.CharField(
        source="entered_by.full_name", read_only=True
    )
    verified_by_name = serializers.CharField(
        source="verified_by.full_name", read_only=True
    )
    reference_range = serializers.SerializerMethodField()
    is_abnormal = serializers.SerializerMethodField()
    is_critical = serializers.SerializerMethodField()

    def get_is_abnormal(self, obj):
        """Return true if the result flag indicates abnormality."""
        return obj.flag in ["L", "H", "C", "A"]

    def get_is_critical(self, obj):
        """Return true if the result flag is critical."""
        return obj.flag == "C"

    def get_reference_range(self, obj):
        """Get the reference range display string for this result."""
        from apps.laboratory.ranges import pick_reference_range

        patient = None
        try:
            patient = obj.order_item.order.patient
        except AttributeError:
            pass
        range_info = pick_reference_range(obj.test_parameter, patient)
        return range_info.get("display", "")

    def to_representation(self, instance):
        """Convert status to lowercase for frontend compatibility."""
        data = super().to_representation(instance)
        # Normalize placeholder empty values for frontend display
        if data.get("result_value") == "*":
            data["result_value"] = ""
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
            "is_abnormal",
            "is_critical",
            "status",
            "remarks",
            "entered_by",
            "entered_by_name",
            "entered_at",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "reference_range",
        ]
        read_only_fields = [
            "flag",
            "entered_by",
            "entered_at",
            "verified_by",
            "verified_at",
        ]

    def validate(self, attrs):
        """Enforce status transitions and data completeness before verify/final."""
        instance = self.instance
        request = self.context.get("request")
        user = getattr(request, "user", None)

        new_status = attrs.get("status") or (instance.status if instance else "DRAFT")
        result_value = attrs.get("result_value") or (instance.result_value if instance else "")

        if instance:
            if new_status != instance.status:
                if not instance.can_transition_to(new_status, user):
                    raise serializers.ValidationError("Invalid status transition.")

        if new_status in ["VERIFIED", "FINAL"]:
            is_empty = not result_value or str(result_value).strip() in {"", "*"}
            
            # Check if parameter is required
            test_parameter = getattr(instance, "test_parameter", None)
            # If creating a new instance, we might need to fetch it from attrs (not easily available here without DB hit)
            # But usually we update existing results for verification.
            
            if is_empty and instance:
                if instance.test_parameter.is_required:
                    raise serializers.ValidationError(
                        f"Result value is required for {instance.test_parameter.effective_parameter_name} before verification."
                    )
            elif is_empty and not instance:
                # Creation time verification? Unlikely but possible.
                pass

        return attrs

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

    def update(self, instance, validated_data):
        """
        Update a test result, but prevent editing of verified results.
        """
        new_status = validated_data.get("status", instance.status)
        if instance.status == "FINAL":
            raise serializers.ValidationError("Cannot edit a final result.")
        if instance.status == "VERIFIED" and new_status == "VERIFIED":
            raise serializers.ValidationError("Cannot edit a verified result.")
        return super().update(instance, validated_data)
