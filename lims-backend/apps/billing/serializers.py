from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model.

    Includes a read-only field for the name of the user who recorded the payment.
    """
    recorded_by_name = serializers.CharField(source='recorded_by.full_name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'amount', 'payment_method',
            'transaction_id', 'payment_date', 'recorded_by',
            'recorded_by_name', 'notes'
        ]
        read_only_fields = ['payment_date', 'recorded_by']

    def create(self, validated_data):
        """
        Create a new payment and set the `recorded_by` field to the current user.

        Args:
            validated_data (dict): The data to create the payment with.

        Returns:
            Payment: The newly created payment instance.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['recorded_by'] = request.user
        return super().create(validated_data)
