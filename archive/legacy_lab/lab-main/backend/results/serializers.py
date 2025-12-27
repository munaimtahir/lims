"""Result serializers."""

from rest_framework import serializers

from .models import Result


class ResultSerializer(serializers.ModelSerializer):
    """
    Serializer for the Result model.
    """

    class Meta:
        model = Result
        fields = [
            "id",
            "order_item",
            "value",
            "unit",
            "reference_range",
            "flags",
            "status",
            "entered_by",
            "entered_at",
            "verified_by",
            "verified_at",
            "published_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "entered_by",
            "entered_at",
            "verified_by",
            "verified_at",
            "published_at",
            "created_at",
            "updated_at",
        ]
