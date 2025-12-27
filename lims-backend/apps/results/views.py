from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import TestResult
from .serializers import TestResultSerializer
from apps.orders.models import OrderItem


class TestResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Results.

    Provides actions for verifying and rejecting results.
    """

    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["order_item", "flag", "status"]
    ordering_fields = ["test_parameter__display_order"]

    @action(detail=False, methods=["get"])
    def worklist(self, request):
        """
        Get worklist of pending results for entry (for lab technicians).

        Returns order items that have samples collected but no results entered yet,
        or results that are pending entry.

        Returns:
            Response: A paginated list of order items needing result entry.
        """
        # Get order items with collected samples but no results
        from apps.samples.models import Sample, SampleStatus

        # Find order items that have collected samples but missing results
        collected_samples = Sample.objects.filter(
            status__in=[SampleStatus.COLLECTED, SampleStatus.RECEIVED]
        ).values_list("order_item_id", flat=True)

        # Get order items that need results
        order_items_needing_results = (
            OrderItem.objects.filter(id__in=collected_samples)
            .exclude(results__isnull=False)
            .select_related("order", "order__patient", "test", "panel")
            .distinct()
        )

        # Also include order items with pending results
        pending_results = (
            self.queryset.filter(status="pending")
            .values_list("order_item_id", flat=True)
            .distinct()
        )
        order_items_with_pending = OrderItem.objects.filter(
            id__in=pending_results
        ).select_related("order", "order__patient", "test", "panel")

        # Combine and deduplicate
        all_items = (order_items_needing_results | order_items_with_pending).distinct()

        # Serialize the data with order information
        from apps.orders.serializers import OrderItemSerializer, OrderSerializer

        # Create a custom response structure
        worklist_data = []
        for item in all_items:
            item_data = OrderItemSerializer(item, context={"request": request}).data
            # Add order information
            order_data = OrderSerializer(item.order, context={"request": request}).data
            item_data["order"] = order_data
            worklist_data.append(item_data)

        page = self.paginate_queryset(all_items)
        if page is not None:
            # Re-serialize paginated items
            paginated_data = []
            for item in page:
                item_data = OrderItemSerializer(item, context={"request": request}).data
                order_data = OrderSerializer(
                    item.order, context={"request": request}
                ).data
                item_data["order"] = order_data
                paginated_data.append(item_data)
            return self.get_paginated_response(paginated_data)

        return Response(worklist_data)

    @action(detail=False, methods=["get"])
    def verification_queue(self, request):
        """
        Get queue of results pending verification (for pathologists).

        Returns:
            Response: A paginated list of results pending verification.
        """
        pending_results = (
            self.queryset.filter(status="pending")
            .select_related(
                "order_item",
                "order_item__order",
                "order_item__order__patient",
                "test_parameter",
                "entered_by",
            )
            .order_by("entered_at")
        )

        page = self.paginate_queryset(pending_results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending_results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_entry(self, request):
        """
        Bulk create or update test results.

        Expected payload:
        {
            "results": [
                {
                    "order_item": 1,
                    "test_parameter": 1,
                    "result_value": "5.2",
                    "remarks": ""
                },
                ...
            ]
        }

        Returns:
            Response: Created/updated results.
        """
        results_data = request.data.get("results", [])
        if not results_data:
            return Response(
                {"error": "results array is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_results = []
        errors = []

        for result_data in results_data:
            order_item_id = result_data.get("order_item")
            test_parameter_id = result_data.get("test_parameter")
            result_value = result_data.get("result_value")

            if not all([order_item_id, test_parameter_id, result_value]):
                errors.append(
                    {
                        "data": result_data,
                        "error": "Missing required fields: order_item, test_parameter, result_value",
                    }
                )
                continue

            try:
                # Check if result already exists
                result, created = TestResult.objects.get_or_create(
                    order_item_id=order_item_id,
                    test_parameter_id=test_parameter_id,
                    defaults={
                        "result_value": result_value,
                        "remarks": result_data.get("remarks", ""),
                        "entered_by": request.user,
                    },
                )

                if not created:
                    # Update existing result
                    result.result_value = result_value
                    result.remarks = result_data.get("remarks", "")
                    result.status = "pending"  # Reset to pending if updating
                    result.save()

                created_results.append(self.get_serializer(result).data)
            except Exception as e:
                errors.append({"data": result_data, "error": str(e)})

        response_data = {
            "created": len(created_results),
            "errors": len(errors),
            "results": created_results,
        }

        if errors:
            response_data["error_details"] = errors

        return Response(
            response_data,
            status=status.HTTP_201_CREATED
            if created_results
            else status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """
        Verify a test result.

        This action can only be performed by pathologists and admins.

        Args:
            request (Request): The request object.
            pk (int, optional): The primary key of the test result. Defaults to None.

        Returns:
            Response: A response object with a status message.
        """
        result = self.get_object()

        # Check permission (should be Pathologist)
        if not request.user.is_pathologist and not request.user.is_admin:
            return Response(
                {"error": "Only pathologists can verify results"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Handle digital signature if provided
        digital_signature = request.data.get("digital_signature")
        if digital_signature:
            # Store signature (implementation depends on signature storage method)
            # For now, we'll add it to the remarks or create a separate model
            pass

        result.verified_by = request.user
        result.verified_at = timezone.now()
        result.status = "verified"
        result.save()

        return Response({"status": "result verified"})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """
        Reject a test result.

        This action can only be performed by pathologists and admins.

        Args:
            request (Request): The request object.
            pk (int, optional): The primary key of the test result. Defaults to None.

        Returns:
            Response: A response object with a status message.
        """
        result = self.get_object()

        # Check permission
        if not request.user.is_pathologist and not request.user.is_admin:
            return Response(
                {"error": "Only pathologists can reject results"},
                status=status.HTTP_403_FORBIDDEN,
            )

        rejection_reason = request.data.get("reason", "")
        if rejection_reason:
            result.remarks = f"Rejected: {rejection_reason}. {result.remarks or ''}"

        result.status = "rejected"
        result.verified_by = request.user  # Track who rejected
        result.verified_at = timezone.now()
        result.save()

        return Response({"status": "result rejected"})
