from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem
from apps.laboratory.models import Test, TestPanel
from apps.patients.models import Patient


class MinimalPatientSerializer(serializers.ModelSerializer):
    """
    Minimal patient serializer for nested use.
    """

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = Patient
        fields = ["id", "full_name", "mrn", "age", "gender"]


class MinimalOrderSerializer(serializers.ModelSerializer):
    """
    Minimal order serializer for nested use in items.
    """

    patient = MinimalPatientSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "order_id", "patient", "priority"]


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the OrderItem model.
    """

    test_name = serializers.CharField(source="test.test_name", read_only=True)
    panel_name = serializers.CharField(source="panel.panel_name", read_only=True)
    test_code = serializers.CharField(source="test.test_code", read_only=True)
    panel_code = serializers.CharField(source="panel.panel_code", read_only=True)
    order = MinimalOrderSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "test",
            "panel",
            "price",
            "status",
            "test_name",
            "panel_name",
            "test_code",
            "panel_code",
        ]
        read_only_fields = ["price", "status"]


class OrderListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing orders.
    """

    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    patient_id_display = serializers.CharField(
        source="patient.patient_id", read_only=True
    )
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "patient",
            "patient_name",
            "patient_id_display",
            "created_at",
            "status",
            "total_amount",
            "net_amount",
            "is_paid",
            "referred_by",
            "item_count",
            "lab_number",
            "collection_center",
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        """Return the number of items in the order."""
        return obj.items.count()


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Order model.

    Includes nested serialization for order items and write-only fields for creating orders with tests and panels.
    """

    items = OrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    ordered_by_name = serializers.CharField(
        source="ordered_by.full_name", read_only=True
    )

    # Write-only fields for creating items
    test_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    panel_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "patient",
            "patient_name",
            "ordered_by",
            "ordered_by_name",
            "created_at",
            "updated_at",
            "status",
            "notes",
            "referred_by",
            "total_amount",
            "discount",
            "discount_percent",
            "net_amount",
            "paid_amount",
            "due_amount",
            "is_paid",
            "items",
            "test_ids",
            "panel_ids",
            "lab_number",
            "lab_date",
            "daily_serial",
            "collection_center",
        ]
        read_only_fields = [
            "order_id",
            "lab_number",
            "lab_date",
            "daily_serial",
            "created_at",
            "updated_at",
            "total_amount",
            "net_amount",
            "due_amount",
            "is_paid",
            "ordered_by",
        ]

    def create(self, validated_data):
        """
        Create a new order with its associated items.

        The `ordered_by` field is automatically set to the current user.
        The total amount is calculated based on the prices of the tests and panels.

        Args:
            validated_data (dict): The data to create the order with.

        Returns:
            Order: The newly created order instance.
        """
        test_ids = validated_data.pop("test_ids", [])
        panel_ids = validated_data.pop("panel_ids", [])

        # Get current user from context
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["ordered_by"] = request.user

        with transaction.atomic():
            order = Order.objects.create(**validated_data)

            # Add tests
            for test_id in test_ids:
                try:
                    test = Test.objects.get(pk=test_id)
                    OrderItem.objects.create(order=order, test=test, price=test.price)
                except Test.DoesNotExist:
                    pass

            # Add panels
            for panel_id in panel_ids:
                try:
                    panel = TestPanel.objects.get(pk=panel_id)
                    OrderItem.objects.create(
                        order=order, panel=panel, price=panel.price
                    )
                except TestPanel.DoesNotExist:
                    pass

            # Calculate total
            order.calculate_total()

            # Create samples for each order item
            # We need to collect the items before the transaction is complete
            # because order.items.all() needs the transaction to be committed
            from apps.samples.models import Sample, SampleStatus
            
            # Refresh from DB to get all related order items
            order_items = OrderItem.objects.filter(order=order)
            
            for item in order_items:
                # Determine sample type from test or panel
                sample_type = "Blood"  # Default
                if item.test:
                    sample_type = item.test.sample_type or "Blood"
                elif item.panel:
                    # For panels, use panel's sample_type or first test's sample type
                    sample_type = item.panel.sample_type or "Blood"
                    if not sample_type or sample_type == "Blood":
                        first_test = item.panel.tests.first()
                        if first_test:
                            sample_type = first_test.sample_type or "Blood"
                
                # Create sample for this order item
                Sample.objects.create(
                    order_item=item,
                    sample_type=sample_type,
                    status=SampleStatus.PENDING
                )

        return order
