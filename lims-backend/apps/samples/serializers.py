from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .models import Sample, SampleStatus


class SampleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Sample model.

    Includes read-only fields for collected_by_name, patient_name, and order_id.
    """

    collected_by_name = serializers.CharField(
        source="collected_by.full_name", read_only=True
    )
    received_by_name = serializers.CharField(
        source="received_by.full_name", read_only=True
    )
    patient_name = serializers.CharField(
        source="order_item.order.patient.get_full_name", read_only=True
    )
    order_id = serializers.CharField(source="order_item.order.order_id", read_only=True)

    class Meta:
        model = Sample
        fields = [
            "id",
            "order_item",
            "order_id",
            "patient_name",
            "sample_type",
            "barcode",
            "status",
            "collected_at",
            "collected_by",
            "collected_by_name",
            "received_at",
            "received_by",
            "received_by_name",
            "rejection_reason",
            "postponement_reason",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "collected_at", "collected_by", "received_at",
            "received_by", "created_at", "updated_at"
        ]

    def validate_status(self, value):
        """Restrict status transitions to Collected/Received/Postponed for now."""
        allowed = {
            SampleStatus.PENDING,
            SampleStatus.COLLECTED,
            SampleStatus.RECEIVED,
            SampleStatus.POSTPONED,
        }
        if value not in allowed:
            raise serializers.ValidationError("Status not allowed.")
        return value

    def update(self, instance, validated_data):
        """
        Override the update method to auto-set collected_at and collected_by
        when the status is changed to 'collected', and received_at/received_by
        when status is changed to 'received'.

        Args:
            instance (Sample): The sample instance to update.
            validated_data (dict): The data to update the instance with.

        Returns:
            Sample: The updated sample instance.
        """
        new_status = validated_data.get("status")
        if new_status:
            if new_status == SampleStatus.COLLECTED and instance.status != SampleStatus.COLLECTED:
                validated_data["collected_at"] = timezone.now()
                request = self.context.get("request")
                if request and hasattr(request, "user"):
                    validated_data["collected_by"] = request.user
            elif new_status == SampleStatus.RECEIVED and instance.status != SampleStatus.RECEIVED:
                validated_data["received_at"] = timezone.now()
                request = self.context.get("request")
                if request and hasattr(request, "user"):
                    validated_data["received_by"] = request.user

        # Handle barcode: if provided, use it; otherwise, let model auto-generate if missing
        barcode = validated_data.get("barcode")
        if barcode:
            # Use provided barcode (model will validate uniqueness)
            validated_data["barcode"] = barcode
        elif not instance.barcode:
            # No barcode provided and instance doesn't have one - let model auto-generate
            # Remove from validated_data so model's save() method handles it
            validated_data.pop("barcode", None)

        return super().update(instance, validated_data)
