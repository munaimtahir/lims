"""Order serializers."""

from django.utils import timezone
from rest_framework import serializers

from catalog.serializers import TestCatalogSerializer
from patients.serializers import PatientSerializer
from results.models import Result, ResultStatus
from samples.models import Sample, SampleStatus
from settings.utils import should_skip_sample_collection, should_skip_sample_receive

from .models import Order, OrderItem, OrderStatus


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the OrderItem model.
    """

    test_detail = TestCatalogSerializer(source="test", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "test", "test_detail", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Order model.

    Handles the serialization and deserialization of Order objects, including
    the creation of associated OrderItems and Samples.
    """

    items = OrderItemSerializer(many=True, read_only=True)
    patient_detail = PatientSerializer(source="patient", read_only=True)
    test_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "patient",
            "patient_detail",
            "priority",
            "status",
            "notes",
            "items",
            "test_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "order_no", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        """
        Creates an order with its associated order items and samples.

        This method also handles the automatic creation of samples and sets their
        status based on the current workflow settings (e.g., skipping sample
        collection or reception). When both collection and reception are skipped,
        Result objects are also created to enable immediate result entry.

        Args:
            validated_data (dict): The validated data for the order.

        Returns:
            Order: The newly created order instance.
        """
        test_ids = validated_data.pop("test_ids")

        # Get workflow settings
        skip_collection = should_skip_sample_collection()
        skip_receive = should_skip_sample_receive()

        # Determine initial order status based on workflow settings
        initial_order_status = OrderStatus.NEW
        if skip_collection and skip_receive:
            # If both are skipped, order is ready for result entry
            initial_order_status = OrderStatus.IN_PROCESS
        elif skip_collection:
            # If only collection is skipped, order is in collected state
            initial_order_status = OrderStatus.COLLECTED

        order = Order.objects.create(**validated_data, status=initial_order_status)

        # Create order items and samples
        for test_id in test_ids:
            # Determine order item status
            item_status = OrderStatus.NEW
            if skip_collection and skip_receive:
                item_status = OrderStatus.IN_PROCESS
            elif skip_collection:
                item_status = OrderStatus.COLLECTED

            order_item = OrderItem.objects.create(
                order=order, test_id=test_id, status=item_status
            )

            # Auto-create sample for this order item
            sample_status = SampleStatus.PENDING
            collected_at = None
            received_at = None

            # If collection is disabled, mark as collected automatically
            if skip_collection:
                sample_status = SampleStatus.COLLECTED
                collected_at = timezone.now()

            # If both collection and receive are disabled, mark as received
            if skip_collection and skip_receive:
                sample_status = SampleStatus.RECEIVED
                received_at = timezone.now()

            Sample.objects.create(
                order_item=order_item,
                sample_type=order_item.test.sample_type,
                status=sample_status,
                collected_at=collected_at,
                received_at=received_at,
            )

            # If sample is marked as received (both steps skipped),
            # create a Result object for immediate result entry
            if skip_collection and skip_receive:
                Result.objects.create(
                    order_item=order_item,
                    value="",
                    status=ResultStatus.DRAFT,
                )

        return order
