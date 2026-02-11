from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.export_utils import export_to_csv, export_to_excel
from apps.core.authz import (
    filter_queryset_for_branches,
    is_tenant_admin,
    user_has_branch_access,
    user_tenant,
)
from apps.core.models import BranchCapability
from apps.laboratory.models import ReferenceRange, TestParameter
from apps.orders.models import Order, OrderItem
# from apps.reports.models import Report, ReportStatus
# from apps.reports.utils import generate_pdf_report

from .filters import TestResultFilter
from .models import TestResult
from .serializers import TestResultSerializer
from .services.expected_results import (
    ensure_test_results,
    get_orderitem_expected_parameters,
)
from .services.transitions import transition_result_state
from apps.audit.utils import emit_audit_event


class TestResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Results.

    Provides actions for verifying and finalizing results.
    """

    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TestResultFilter
    ordering_fields = ["test_parameter__display_order", "entered_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = user_tenant(self.request.user)
        qs = qs.filter(order_item__order__tenant=tenant)
        if not is_tenant_admin(self.request.user):
            qs = filter_queryset_for_branches(
                qs, "order_item__order__collection_branch", self.request.user
            )
        return qs.select_related("order_item__order__collection_branch")

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
            "Parameter",
            "Test",
            "Result Value",
            "Unit",
            "Flag",
            "Status",
            "Order ID",
            "Entered At",
            "Verified At",
        ]

        export_data = []
        for item in data:
            export_data.append(
                [
                    (
                        item.get("test_parameter", {}).get("parameter_name", "")
                        if isinstance(item.get("test_parameter"), dict)
                        else ""
                    ),
                    (
                        item.get("test_parameter", {})
                        .get("test", {})
                        .get("test_name", "")
                        if isinstance(item.get("test_parameter"), dict)
                        else ""
                    ),
                    item.get("result_value", ""),
                    (
                        item.get("test_parameter", {}).get("unit", "")
                        if isinstance(item.get("test_parameter"), dict)
                        else ""
                    ),
                    item.get("flag", ""),
                    item.get("status", ""),
                    (
                        item.get("order_item", {}).get("order", {}).get("order_id", "")
                        if isinstance(item.get("order_item"), dict)
                        else ""
                    ),
                    item.get("entered_at", ""),
                    item.get("verified_at", ""),
                ]
            )

        if format_type == "excel":
            return export_to_excel(export_data, f"{filename}.xlsx", headers, "Results")
        else:
            return export_to_csv(export_data, f"{filename}.csv", headers)

    @action(detail=False, methods=["get"])
    def worklist(self, request):
        """
        Get worklist of pending results for entry (for lab technicians).

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

        # Also include order items with pending results (DRAFT)
        pending_results = (
            self.queryset.filter(status="DRAFT")
            .values_list("order_item_id", flat=True)
            .distinct()
        )
        order_items_with_pending = (
            OrderItem.objects.filter(id__in=pending_results)
            .select_related("order", "order__patient", "test", "panel")
            .distinct()
        )

        # Combine and deduplicate
        all_items = (order_items_needing_results | order_items_with_pending).distinct()

        # Serialize the data with order information
        from apps.orders.serializers import OrderItemSerializer

        def _serialize_item(item):
            """Keep patient fields from MinimalOrderSerializer and append timeline info."""
            item_data = OrderItemSerializer(item, context={"request": request}).data
            order_data = item_data.get("order", {}) or {}
            
            # Explicitly ensure patient is present in order_data
            from apps.orders.serializers import MinimalPatientSerializer
            if not order_data.get("patient") and item.order.patient:
                order_data["patient"] = MinimalPatientSerializer(item.order.patient).data

            # Append key fields required by the worklist UI
            order_data.update(
                {
                    "created_at": item.order.created_at,
                    "lab_number": getattr(item.order, "lab_number", None),
                    "status": item.order.status,
                }
            )
            item_data["order"] = order_data
            patient = getattr(item.order, "patient", None)
            if patient:
                patient_payload = order_data.get("patient") or {}
                patient_full_name = patient.get_full_name()
                patient_payload.update(
                    {
                        "id": patient.id,
                        "full_name": patient_full_name,
                        "age": getattr(patient, "age", None),
                        "gender": getattr(patient, "gender", None),
                        "mrn": getattr(patient, "mrn", None),
                    }
                )
                order_data["patient"] = patient_payload
                item_data["order"] = order_data
            # Flatten patient display fields for frontend fallbacks/search
            item_data["patient_name"] = patient.get_full_name() if patient else None
            item_data["patient_age"] = getattr(patient, "age", None)
            item_data["patient_gender"] = getattr(patient, "gender", None)
            return item_data

        # Create a custom response structure
        worklist_data = [_serialize_item(item) for item in all_items]

        page = self.paginate_queryset(all_items)
        if page is not None:
            # Re-serialize paginated items
            paginated_data = [_serialize_item(item) for item in page]
            return self.get_paginated_response(paginated_data)

        return Response(worklist_data)

    def _assert_branch_permissions(self, order_item, user):
        branch = (
            getattr(order_item.order, "processing_branch", None)
            or getattr(order_item.order, "collection_branch", None)
        )
        if branch and branch.capability_mode == BranchCapability.COLLECT_ONLY:
            raise ValidationError("Result entry not allowed for collection-only branch.")
        if branch and not user_has_branch_access(user, branch):
            raise ValidationError("You do not have access to this branch.")

    def _get_order_item_from_request(self, request):
        """
        Extract and validate order_item_id from request, fetch OrderItem instance.
        """
        order_item_id = request.query_params.get("order_item_id") or request.data.get(
            "order_item_id"
        )
        if not order_item_id:
            raise ValidationError({"detail": "order_item_id is required."})

        try:
            # Prefetch active reference ranges for all parameters to avoid N+1 queries
            reference_ranges_prefetch = Prefetch(
                "reference_ranges",
                queryset=ReferenceRange.objects.filter(is_active=True).order_by(
                    "-version", "-id"
                ),
                to_attr="active_reference_ranges",
            )

            order_item = (
                OrderItem.objects.select_related(
                    "order",
                    "order__patient",
                    "order__collection_branch",
                    "order__processing_branch",
                    "test",
                    "panel",
                )
                .prefetch_related(
                    "panel__tests",
                    Prefetch(
                        "test__test_parameters",
                        queryset=TestParameter.objects.prefetch_related(
                            reference_ranges_prefetch
                        ),
                    ),
                    Prefetch(
                        "panel__tests__test_parameters",
                        queryset=TestParameter.objects.prefetch_related(
                            reference_ranges_prefetch
                        ),
                    ),
                )
                .get(id=order_item_id)
            )
        except (OrderItem.DoesNotExist, ValueError):
            raise ValidationError({"detail": "Order item not found."})

        # Explicitly check for missing patient (select_related ensures these are loaded)
        if not order_item.order.patient:
            raise ValidationError({"detail": "Order item has no associated patient."})

        self._assert_branch_permissions(order_item, request.user)
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

        # Reload results with all related data for serialization
        result_ids = [r.id for r in results]
        results_with_relations = (
            TestResult.objects.filter(id__in=result_ids)
            .select_related(
                "test_parameter",
                "test_parameter__parameter",
                "test_parameter__test",
                "order_item",
                "order_item__order",
                "order_item__order__patient",
                "entered_by",
                "verified_by",
            )
            .prefetch_related(
                "test_parameter__reference_ranges",
            )
            .order_by("test_parameter__display_order")
        )

        serializer = self.get_serializer(results_with_relations, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=["get"])
    def verification_queue(self, request):
        """
        Get queue of results pending verification.
        """
        pending_results = (
            self.queryset.filter(status="DRAFT")
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
        """
        results_data = request.data.get("results", [])
        if not results_data:
            return Response(
                {"detail": "results array is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_results = []
        errors = []

        with transaction.atomic():
            for result_data in results_data:
                order_item_id = result_data.get("order_item")
                test_parameter_id = result_data.get("test_parameter")
                result_value = result_data.get("result_value", "")
                if result_value is None or str(result_value).strip() == "":
                    result_value = "*"

                if not order_item_id or not test_parameter_id:
                    errors.append(
                        {
                            "data": result_data,
                            "detail": "Missing required fields: order_item, test_parameter.",
                        }
                    )
                    continue

                try:
                    try:
                        result = (
                            TestResult.objects.select_for_update()
                            .get(
                                order_item_id=order_item_id,
                                test_parameter_id=test_parameter_id,
                            )
                        )
                        created = False
                    except TestResult.DoesNotExist:
                        result = None
                        created = True

                    if created:
                        result = TestResult.objects.create(
                            order_item_id=order_item_id,
                            test_parameter_id=test_parameter_id,
                            result_value=result_value,
                            remarks=result_data.get("remarks", ""),
                            entered_by=request.user,
                            entered_at=timezone.now(),
                            status="DRAFT",
                        )
                        emit_audit_event(
                            actor=request.user,
                            entity_type="result",
                            entity_id=result.pk,
                            action="RESULT_VALUE_UPDATED",
                            before=None,
                            after={"result_value": result.result_value, "status": result.status},
                            metadata={"order_item_id": result.order_item_id},
                            source="api",
                        )
                    else:
                        if not result.can_edit(request.user):
                            errors.append(
                                {
                                    "data": result_data,
                                    "detail": "Result cannot be edited after verification/finalization.",
                                }
                            )
                            continue

                        before_value = result.result_value
                        result.result_value = result_value
                        result.remarks = result_data.get("remarks", "")
                        result.entered_by = request.user
                        result.entered_at = timezone.now()
                        result.status = "DRAFT"
                        result.save()
                        emit_audit_event(
                            actor=request.user,
                            entity_type="result",
                            entity_id=result.pk,
                            action="RESULT_VALUE_UPDATED",
                            before={"result_value": before_value},
                            after={"result_value": result.result_value},
                            metadata={"order_item_id": result.order_item_id},
                            source="api",
                        )

                    created_results.append(self.get_serializer(result).data)
                except Exception as e:
                    errors.append({"data": result_data, "detail": str(e)})

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

    def _check_and_update_status(self, order_item):
        """
        Check if all results for an order item are verified using strict logic.
        """
        all_results = order_item.results.all()
        if not all_results.exists():
            return

        # Check if all existing results are VERIFIED or FINAL
        # We only auto-verify the OrderItem if all results are processed.
        verified_count = all_results.filter(status__in=["VERIFIED", "FINAL"]).count()
        if verified_count == all_results.count():
            # All results for this item are verified.
            if order_item.status != "VERIFIED":
                order_item.status = "VERIFIED"
                order_item.save(update_fields=["status"])
        
        # We removed auto-finalization and auto-report generation 
        # to strictly follow "VERIFIED -> FINAL requires permission".

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """
        Verify a test result (DRAFT -> VERIFIED).
        """
        with transaction.atomic():
            result = (
                TestResult.objects.select_for_update()
                .select_related("order_item")
                .get(pk=pk)
            )

        try:
            result = transition_result_state(result, "VERIFIED", request.user, source="api")
        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
            )

        # Update OrderItem status
        self._check_and_update_status(result.order_item)

        serializer = self.get_serializer(result)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-verify")
    def bulk_verify(self, request):
        """
        Verify a list of test results.
        """
        result_ids = request.data.get("result_ids", [])
        if not result_ids:
            return Response(
                {"detail": "result_ids list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        errors = []
        success = 0

        with transaction.atomic():
            results = (
                TestResult.objects.select_for_update()
                .filter(id__in=result_ids)
                .select_related("order_item")
            )
            for result in results:
                try:
                    transition_result_state(result, "VERIFIED", request.user, source="api")
                    self._check_and_update_status(result.order_item)
                    success += 1
                except Exception as exc:
                    errors.append(f"Result {result.id}: {str(exc)}")

        if errors:
             return Response(
                 {"detail": "Some results could not be verified.", "errors": errors, "processed": success},
                 status=status.HTTP_409_CONFLICT,
             )
        
        return Response({"detail": "Results verified successfully.", "processed": success})

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        """
        Finalize a test result (VERIFIED -> FINAL).
        """
        with transaction.atomic():
            result = TestResult.objects.select_for_update().get(pk=pk)

        try:
            result = transition_result_state(result, "FINAL", request.user, source="api")
        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
            )

        serializer = self.get_serializer(result)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-finalize")
    def bulk_finalize(self, request):
        """
        Finalize a list of test results.
        """
        result_ids = request.data.get("result_ids", [])
        if not result_ids:
             return Response({"detail": "result_ids is required."}, status=400)

        errors = []
        success = 0
        
        with transaction.atomic():
            results = TestResult.objects.select_for_update().filter(id__in=result_ids)
            for result in results:
                try:
                    transition_result_state(result, "FINAL", request.user, source="api")
                    success += 1
                except Exception as exc:
                    errors.append(f"Result {result.id}: {str(exc)}")

        if errors:
             return Response(
                 {"detail": "Some results could not be finalized.", "errors": errors, "processed": success},
                 status=status.HTTP_409_CONFLICT,
             )

        return Response({"detail": "Results finalized.", "processed": success})
