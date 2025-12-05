from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for the Report model.

    Includes a read-only field for the name of the user who generated the report.
    """
    generated_by_name = serializers.CharField(source='generated_by.full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)
    order_id_display = serializers.CharField(source='order.order_id', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'order', 'order_id_display', 'report_file', 
            'generated_at', 'generated_by', 'generated_by_name',
            'is_final', 'pathologist_signature', 'technician_signature',
            'verified_by', 'verified_by_name', 'verified_at'
        ]
        read_only_fields = ['report_file', 'generated_at', 'generated_by', 'verified_by', 'verified_at']
