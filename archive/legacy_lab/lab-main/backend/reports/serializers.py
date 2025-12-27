"""Report serializers."""

from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for the Report model.
    """

    class Meta:
        model = Report
        fields = [
            "id",
            "order",
            "pdf_file",
            "generated_at",
            "generated_by",
        ]
        read_only_fields = ["id", "generated_at", "generated_by"]
