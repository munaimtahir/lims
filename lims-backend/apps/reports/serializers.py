from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for the Report model.

    Includes read-only fields for user names and related data.
    """

    generated_by_name = serializers.CharField(
        source="generated_by.full_name", read_only=True
    )
    verified_by_name = serializers.CharField(
        source="verified_by.full_name", read_only=True
    )
    delivered_by_name = serializers.CharField(
        source="delivered_by.full_name", read_only=True
    )
    order_id_display = serializers.CharField(source="order.order_id", read_only=True)
    patient_name = serializers.CharField(
        source="order.patient.get_full_name", read_only=True
    )
    amended_from_number = serializers.CharField(
        source="amended_from.report_number", read_only=True
    )

    class Meta:
        model = Report
        fields = [
            "id",
            "order",
            "order_id_display",
            "patient_name",
            "report_number",
            "report_file",
            "status",
            "template_name",
            "generated_at",
            "generated_by",
            "generated_by_name",
            "is_final",
            "pathologist_signature",
            "technician_signature",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "amended_from",
            "amended_from_number",
            "amendment_reason",
            "delivered_at",
            "delivered_by",
            "delivered_by_name",
            "delivery_method",
            "reprint_count",
            "last_reprinted_at",
        ]
        read_only_fields = [
            "report_file",
            "report_number",
            "generated_at",
            "generated_by",
            "verified_by",
            "verified_at",
            "reprint_count",
            "last_reprinted_at",
        ]
