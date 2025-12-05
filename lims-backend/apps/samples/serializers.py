from rest_framework import serializers
from django.utils import timezone
from .models import SampleCollection


class SampleCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for the SampleCollection model.

    Includes read-only fields for collected_by_name, patient_name, and order_id.
    """
    collected_by_name = serializers.CharField(source='collected_by.full_name', read_only=True)
    patient_name = serializers.CharField(source='order.patient.get_full_name', read_only=True)
    order_id = serializers.CharField(source='order.order_id', read_only=True)

    class Meta:
        model = SampleCollection
        fields = [
            'id', 'order', 'order_id', 'patient_name', 'order_items',
            'sample_type', 'barcode', 'status',
            'collected_at', 'collected_by', 'collected_by_name', 'notes'
        ]
        read_only_fields = ['collected_at', 'collected_by']

    def update(self, instance, validated_data):
        """
        Override the update method to auto-set collected_at and collected_by
        when the status is changed to 'collected'.

        Args:
            instance (SampleCollection): The sample collection instance to update.
            validated_data (dict): The data to update the instance with.

        Returns:
            SampleCollection: The updated sample collection instance.
        """
        if validated_data.get('status') == 'collected' and instance.status != 'collected':
            validated_data['collected_at'] = timezone.now()
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                validated_data['collected_by'] = request.user

        return super().update(instance, validated_data)
