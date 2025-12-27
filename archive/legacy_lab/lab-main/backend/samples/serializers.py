"""Sample serializers."""

from rest_framework import serializers

from .models import Sample


class SampleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Sample model.
    """

    class Meta:
        model = Sample
        fields = [
            "id",
            "order_item",
            "sample_type",
            "barcode",
            "collected_at",
            "collected_by",
            "received_at",
            "received_by",
            "status",
            "rejection_reason",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "barcode",
            "created_at",
            "updated_at",
        ]
