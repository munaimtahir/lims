from django.db import transaction
from rest_framework import serializers

from apps.core.authz import user_active_branches, user_tenant
from apps.core.models import Branch
from apps.core.services.settings import get_tenant_settings
from apps.laboratory.models import Test, TestPanel
from apps.patients.models import Patient

from .models import Dispatch, DispatchItem, Order, OrderItem


class MinimalPatientSerializer(serializers.ModelSerializer):
    """
    Minimal patient serializer for nested use.
    """

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = Patient
        fields = ["id", "full_name", "mrn", "age", "gender", "phone"]


class MinimalOrderSerializer(serializers.ModelSerializer):
    """
    Minimal order serializer for nested use in items.
    """

    patient = MinimalPatientSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "order_id", "lab_number", "patient", "priority"]


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
            "collection_branch_name",
        ]
        read_only_fields = fields

    collection_branch_name = serializers.SerializerMethodField()

    def get_collection_branch_name(self, obj):
        return getattr(obj.collection_branch, "name", None) if obj.collection_branch else None

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
            "tenant",
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
            "collection_branch",
            "processing_branch",
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
            "tenant",
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
            request = self.context.get("request")
            req_user = getattr(request, "user", None) if request else None

            # Tenant: always set from user (server is source of truth)
            if not validated_data.get("tenant") and req_user:
                validated_data["tenant"] = user_tenant(req_user)

            tenant = validated_data.get("tenant") or (user_tenant(req_user) if req_user else None)
            tenant_settings = get_tenant_settings(tenant) if tenant else None
            enable_branches = getattr(tenant_settings, "enable_branches", False) if tenant_settings else False

            # When enable_branches is False: leave collection_branch/processing_branch null (core workflow).
            # When True: resolve from body, else user branches, else tenant default, else HQ, else any branch.
            if enable_branches and not validated_data.get("collection_branch") and req_user:
                branches = user_active_branches(req_user)
                first_branch = branches.first()
                if not first_branch and tenant and tenant_settings and tenant_settings.default_branch_id:
                    first_branch = tenant_settings.default_branch
                if not first_branch and tenant:
                    first_branch = Branch.objects.filter(
                        tenant=tenant, is_hq=True, is_active=True
                    ).first()
                if not first_branch and tenant:
                    first_branch = Branch.objects.filter(
                        tenant=tenant, is_active=True
                    ).order_by("code").first()
                if not first_branch:
                    raise serializers.ValidationError(
                        {"collection_branch": "No branch assigned. Contact admin."}
                    )
                validated_data["collection_branch"] = first_branch

            if enable_branches and not validated_data.get("processing_branch"):
                validated_data["processing_branch"] = validated_data.get("collection_branch")

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
            import logging

            logger = logging.getLogger(__name__)

            # Refresh from DB to get all related order items
            order_items = OrderItem.objects.filter(order=order)

            for item in order_items:
                try:
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
                        status=SampleStatus.PENDING,
                    )
                except Exception as e:
                    logger.error(f"Failed to create sample for order item {item.id}: {str(e)}", exc_info=True)
                    # Don't fail the entire order creation if sample creation fails
                    # This allows the order to be created even if sample workflow has issues
                    pass

            # If order was created with paid_amount, create a Payment so receipt is available
            from decimal import Decimal
            from apps.billing.models import Payment

            paid = getattr(order, "paid_amount", None)
            if paid is not None and paid > Decimal("0.00"):
                Payment.objects.create(
                    order=order,
                    amount=paid,
                    payment_method="cash",
                    recorded_by=req_user,
                )

        return order


class DispatchItemSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    order_order_id = serializers.CharField(source="order.order_id", read_only=True)

    class Meta:
        model = DispatchItem
        fields = ["id", "order", "order_id", "order_order_id", "created_at"]
        read_only_fields = ["created_at"]


class DispatchSerializer(serializers.ModelSerializer):
    items = DispatchItemSerializer(many=True, read_only=True)
    from_branch_name = serializers.CharField(source="from_branch.name", read_only=True)
    to_branch_name = serializers.CharField(source="to_branch.name", read_only=True)

    class Meta:
        model = Dispatch
        fields = [
            "id",
            "tenant",
            "from_branch",
            "to_branch",
            "from_branch_name",
            "to_branch_name",
            "created_by",
            "created_at",
            "status",
            "sent_at",
            "received_at",
            "received_by",
            "items",
        ]
        read_only_fields = [
            "created_at",
            "status",
            "sent_at",
            "received_at",
            "received_by",
        ]


class DispatchCreateSerializer(serializers.Serializer):
    """Payload: from_branch, to_branch, order_ids (list of order ids)."""

    from_branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    to_branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    order_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
