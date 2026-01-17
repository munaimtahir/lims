from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.export_utils import export_to_csv, export_to_excel
from .models import TestResult
from .serializers import TestResultSerializer
from .filters import TestResultFilter
from apps.orders.models import OrderItem
from apps.laboratory.models import TestParameter
from .services.expected_results import (
    ensure_test_results,
    get_orderitem_expected_parameters,
)


class TestResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Results.

    Provides actions for verifying and rejecting results.
    """

    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TestResultFilter
    ordering_fields = ["test_parameter__display_order", "entered_at"]
    
    @action(detail=False, methods=["get"])
    def export(self, request):
        """
        Export result search results to CSV or Excel.
        
        Query params:
            - format: 'csv' or 'excel' (default: 'csv')
            - All other result filter params are supported
        
        Returns:
            Response: CSV or Excel file download
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        format_type = request.query_params.get("format", "csv").lower()
        filename = f"results_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        data = serializer.data
        headers = [
            "Parameter", "Test", "Result Value", "Unit", "Flag",
            "Status", "Order ID", "Entered At", "Verified At"
        ]
        
        export_data = []
        for item in data:
            export_data.append([
                (item.get("test_parameter", {}).get("parameter_name", "")
                 if isinstance(item.get("test_parameter"), dict) else ""),
                (item.get("test_parameter", {}).get("test", {}).get("test_name", "")
                 if isinstance(item.get("test_parameter"), dict) else ""),
                item.get("result_value", ""),
                (item.get("test_parameter", {}).get("unit", "")
                 if isinstance(item.get("test_parameter"), dict) else ""),
                item.get("flag", ""),
                item.get("status", ""),
                (item.get("order_item", {}).get("order", {}).get("order_id", "")
                 if isinstance(item.get("order_item"), dict) else ""),
                item.get("entered_at", ""),
                item.get("verified_at", ""),
            ])

        if format_type == "excel":
            return export_to_excel(export_data, f"{filename}.xlsx", headers, "Results")
        else:
            return export_to_csv(export_data, f"{filename}.csv", headers)

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

        # Also include order items with pending results (ENTERED status means pending verification)
        pending_results = (
            self.queryset.filter(status="ENTERED")
            .values_list("order_item_id", flat=True)
            .distinct()
        )
        order_items_with_pending = OrderItem.objects.filter(
            id__in=pending_results
        ).select_related("order", "order__patient", "test", "panel").distinct()

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

    def _get_order_item_from_request(self, request):
        """
        Extract and validate order_item_id from request, fetch OrderItem instance.
        
        Args:
            request: DRF request object
            
        Returns:
            OrderItem: The fetched order item with related data
            
        Raises:
            Response: Returns error response for invalid requests (to be caught by caller)
        """
        order_item_id = request.query_params.get("order_item_id") or request.data.get("order_item_id")
        if not order_item_id:
            raise ValidationError({"order_item_id": "This field is required"})
        
        try:
            from django.db.models import Prefetch
            from apps.laboratory.models import ReferenceRange
            
            # Prefetch active reference ranges for all parameters to avoid N+1 queries
            reference_ranges_prefetch = Prefetch(
                'reference_ranges',
                queryset=ReferenceRange.objects.filter(is_active=True).order_by('-version', '-id'),
                to_attr='active_reference_ranges'
            )
            
            order_item = (
                OrderItem.objects.select_related("order", "order__patient", "test", "panel")
                .prefetch_related(
                    "panel__tests",
                    Prefetch("test__parameters", queryset=TestParameter.objects.prefetch_related(reference_ranges_prefetch)),
                    Prefetch("panel__tests__parameters", queryset=TestParameter.objects.prefetch_related(reference_ranges_prefetch)),
                )
                .get(id=order_item_id)
            )
        except (OrderItem.DoesNotExist, ValueError):
            raise ValidationError({"order_item_id": "Order item not found"})
        
        # Explicitly check for missing patient (select_related ensures these are loaded)
        if not order_item.order.patient:
            raise ValidationError({"error": "Order item has no associated patient"})
        
        return order_item

    @action(detail=False, methods=["get"])
    def expected(self, request):
        """Return expected result rows for an order item without writing."""
        order_item = self._get_order_item_from_request(request)
        
        expected = get_orderitem_expected_parameters(
            order_item, order_item.order.patient
        )
        return Response({"results": expected})

    @action(detail=False, methods=["post"])
    def ensure(self, request):
        """Ensure result rows exist for an order item."""
        order_item = self._get_order_item_from_request(request)
        
        results = ensure_test_results(order_item)
        serializer = self.get_serializer(results, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=["get"])
    def verification_queue(self, request):
        """
        Get queue of results pending verification (for pathologists).

        Returns:
            Response: A paginated list of results pending verification.
        """
        pending_results = (
            self.queryset.filter(status="ENTERED")
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
                        "entered_at": timezone.now(),
                        "status": "ENTERED",  # Set to ENTERED status on creation
                    },
                )

                if not created:
                    # Update existing result
                    result.result_value = result_value
                    result.remarks = result_data.get("remarks", "")
                    result.entered_by = request.user
                    result.entered_at = timezone.now()
                    result.status = "ENTERED"  # Set to ENTERED status when updating
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
        result.status = "VERIFIED"
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

        result.status = "REJECTED"
        result.verified_by = request.user  # Track who rejected
        result.verified_at = timezone.now()
        result.save()

        return Response({"status": "result rejected"})
