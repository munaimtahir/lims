from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count, Prefetch, Q
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
from apps.core.services.settings import get_tenant_settings
from apps.laboratory.models import ReferenceRange, TestParameter
from apps.orders.models import Order, OrderItem
# from apps.reports.models import Report, ReportStatus
# from apps.reports.utils import generate_pdf_report

from .filters import TestResultFilter
from .models import TestResult
from .serializers import TestResultSerializer
from .services.expected_results import (
    ensure_order_item_results,
    get_orderitem_expected_parameters,
)
from .services.transitions import transition_result_state
from .services.formulas import recompute_formulas_for_order_item
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
        When sample_workflow_enabled is False: paid orders are eligible immediately.
        When sample_workflow_enabled is True: order items must have collected/received samples.
        """
        tenant = user_tenant(request.user)
        tenant_settings = get_tenant_settings(tenant)
        sample_workflow_enabled = getattr(tenant_settings, "sample_workflow_enabled", True)

        if sample_workflow_enabled:
            # Original logic: order items with collected/received samples
            from apps.samples.models import Sample, SampleStatus
            collected_samples = Sample.objects.filter(
                status__in=[SampleStatus.COLLECTED, SampleStatus.RECEIVED]
            ).values_list("order_item_id", flat=True)
            base = OrderItem.objects.filter(id__in=collected_samples)
        else:
            # Sample workflow off: paid orders are eligible for result entry immediately
            base = OrderItem.objects.filter(
                order__tenant=tenant,
                order__is_paid=True,
                order__status__in=["NEW", "COLLECTED", "IN_PROCESS"],
            ).exclude(order__status="CANCELLED")
            if not is_tenant_admin(request.user):
                base = filter_queryset_for_branches(
                    base, "order__collection_branch", request.user
                )

        # Annotate with parameter counts to determine completion status
        # We need F expression for comparison
        from django.db.models import F

        # Annotate with parameter counts to determine completion status
        order_items_needing_results = (
            base.annotate(
                # Count results that are verified or finalized (item is beyond entry phase)
                verified_params=Count(
                    "results",
                    filter=Q(results__status__in=["VERIFIED", "FINAL"]),
                    distinct=True
                ),
                
                # Count total parameters that are required for verification
                required_total=Count(
                    "test__test_parameters",
                    filter=Q(test__test_parameters__is_required_for_verification=True),
                    distinct=True
                ) + Count(
                    "panel__tests__test_parameters",
                    filter=Q(panel__tests__test_parameters__is_required_for_verification=True),
                    distinct=True
                ),

                # Count required parameters that have a value
                required_entered=Count(
                    "results",
                    filter=Q(
                        results__test_parameter__is_required_for_verification=True,
                        results__result_value__isnull=False
                    ) & ~Q(results__result_value=""),
                    distinct=True
                ),

                # Count total parameters expected (Test or Panel)
                total_params=Count("test__test_parameters", distinct=True)
                + Count("panel__tests__test_parameters", distinct=True),
                
                # Count results entered (have a value)
                entered_with_value=Count(
                    "results",
                    filter=Q(results__result_value__isnull=False) & ~Q(results__result_value=""),
                    distinct=True
                ),
                
                # Count draft results (active work in progress)
                draft_params=Count(
                    "results",
                    filter=Q(results__status="DRAFT"),
                    distinct=True
                )
            )
            .filter(
                # Keep visible if:
                # 1. Has draft results (currently being worked on)
                # 2. OR Has missing required parameters
                # 3. OR Item is not fully verified
                Q(draft_params__gt=0) | 
                Q(required_entered__lt=F("required_total")) |
                Q(verified_params__lt=F("total_params"))
            )
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

        results = ensure_order_item_results(order_item)

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
        Get queue of results pending verification, grouped by Order.
        Returns a list of orders that have pending results.
        """
        tenant = user_tenant(request.user)
        base_qs = self.queryset.filter(status__in=["DRAFT", "ENTERED"]).order_by("order_item__order__created_at", "order_item__order__id")

        # Group by order items -> orders
        # We need: Order details, Patient details, Test count, Verified count, Pending count.
        
        # Get all pending results with related data
        results = base_qs.select_related(
            "order_item__order",
            "order_item__order__patient",
            "order_item__test",
            "order_item__panel",
        )

        # Dictionary to group by order_item_id (or order_id if we want full order grouping)
        # The UI request says "Verification queue shows PATIENT + ORDER context first, then tests within."
        # Group by Order ID first.
        
        orders_map = {}
        
        for res in results:
            order = res.order_item.order
            oid = order.id
            if oid not in orders_map:
                orders_map[oid] = {
                    "order_internal_id": order.id,
                    "order_id": order.order_id,
                    "lab_number": order.lab_number or order.order_id,
                    "patient_name": order.patient.get_full_name() if order.patient else "Unknown",
                    "mrn": getattr(order.patient, "mrn", "") if order.patient else "",
                    "age_gender": f"{getattr(order.patient, 'age', '')}/{getattr(order.patient, 'gender', '')}",
                    "created_at": order.created_at,
                    "priority": order.priority,
                    "status": order.status,
                    "items": {} # Map of order_item_id -> details
                }
            
            oi_id = res.order_item.id
            if oi_id not in orders_map[oid]["items"]:
                 orders_map[oid]["items"][oi_id] = {
                     "id": oi_id,
                     "test_name": res.order_item.test.test_name if res.order_item.test else (res.order_item.panel.panel_name if res.order_item.panel else "Unknown"),
                     "total_results": 0,
                     "pending_results": 0,
                     "verified_results": 0, # We might need to query verified ones too?
                     # Wait, if we only query pending results, we won't know verified count unless we query separate.
                     # For performance, maybe just showing "Pending inputs" count is enough for the queue?
                     # Let's keep it simple: Show pending results count.
                 }
            
            orders_map[oid]["items"][oi_id]["total_results"] += 1
            orders_map[oid]["items"][oi_id]["pending_results"] += 1
            # Note: Total count here is only "Total PENDING/ENTERED". 
            # If we want true total, we need a separate aggregate query.
            # But the queue is "Works requiring verification". 

        # Flatten structure
        response_data = []
        for order_info in orders_map.values():
            # Summarize item info string
            tests_summary = ", ".join([i["test_name"] for i in order_info["items"].values()])
            total_pending = sum([i["pending_results"] for i in order_info["items"].values()])
            
            response_data.append({
                "order_id": order_info["order_id"],
                "lab_number": order_info.get("lab_number"),
                "patient_name": order_info["patient_name"],
                "mrn": order_info["mrn"],
                "details": f"{order_info['age_gender']} | {order_info['priority']}",
                "tests": tests_summary,
                "pending_count": total_pending,
                "order_internal_id": order_info["order_internal_id"], # For linking
                "items": list(order_info["items"].values())
            })

        return Response({"queue": response_data})

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

        # Track modified order items to update status later
        modified_order_items = set()

        with transaction.atomic():
            for result_data in results_data:
                order_item_id = result_data.get("order_item")
                test_parameter_id = result_data.get("test_parameter")
                result_value = result_data.get("result_value")
                if result_value is not None and str(result_value).strip() == "":
                    result_value = None

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
                            status="ENTERED",
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

                        before_val = result.result_value
                        result.result_value = result_value
                        result.remarks = result_data.get("remarks", "")
                        result.entered_by = request.user
                        result.entered_at = timezone.now()
                        result.status = "ENTERED"
                        result.save()
                        emit_audit_event(
                            actor=request.user,
                            entity_type="result",
                            entity_id=result.pk,
                            action="RESULT_VALUE_UPDATED",
                            before={"result_value": before_val},
                            after={"result_value": result.result_value},
                            metadata={"order_item_id": result.order_item_id},
                            source="api",
                        )

                    created_results.append(self.get_serializer(result).data)
                    modified_order_items.add(result.order_item_id)
                except Exception as e:
                    logger.error(
                        f"Bulk entry failed for item {order_item_id}: {str(e)}",
                        exc_info=True,
                        extra={"user": request.user.username, "data": result_data},
                    )
                    errors.append({"data": result_data, "detail": str(e)})

            # Update statuses for affected order items
            if modified_order_items:
                from .services.transitions import update_order_item_status
                for item in OrderItem.objects.filter(id__in=modified_order_items):
                    # Recompute formulas BEFORE updating overall status
                    recompute_formulas_for_order_item(item)
                    update_order_item_status(item)

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
    def reject(self, request, pk=None):
        """
        Return a verified result to entry (VERFIED/DRAFT -> ENTERED).
        Also known as 'Unverify' or 'Return to Entry'.
        Requires 'reason'.
        """
        reason = request.data.get("reason", "").strip()
        if not reason:
             return Response({"detail": "Reason is required to return results."}, status=400)

        with transaction.atomic():
            result = (
                TestResult.objects.select_for_update()
                .select_related("order_item")
                .get(pk=pk)
            )
            try:
                # Transition to ENTERED
                transition_result_state(result, "ENTERED", request.user, source="api", reason=reason)
                self._check_and_update_status(result.order_item, reverting=True)
            except Exception as exc:
                logger.error(
                    f"Result rejection failed for result {pk}: {str(exc)}",
                    exc_info=True,
                    extra={"user": request.user.username, "result_id": pk},
                )
                return Response(
                    {"detail": str(exc), "code": "rejection_failed"},
                    status=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
                )
        
        serializer = self.get_serializer(result)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-reject")
    def bulk_reject(self, request):
        """
        Return multiple results to entry.
        """
        result_ids = request.data.get("result_ids", [])
        reason = request.data.get("reason", "").strip()

        if not result_ids:
            return Response({"detail": "result_ids required"}, status=400)
        if not reason:
            return Response({"detail": "Reason is required"}, status=400)
            
        success = 0
        errors = []
        with transaction.atomic():
            results = TestResult.objects.select_for_update().filter(id__in=result_ids).select_related("order_item")
            for result in results:
                try:
                    transition_result_state(result, "ENTERED", request.user, source="api", reason=reason)
                    self._check_and_update_status(result.order_item, reverting=True)
                    success += 1
                except Exception as exc:
                    errors.append(f"Result {result.id}: {str(exc)}")
        
        if errors:
            return Response({"detail": "Some results failed to return.", "errors": errors, "processed": success}, status=409)
        return Response({"detail": "Results returned to entry.", "processed": success})

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
                self._check_and_update_status(result.order_item)
            except Exception as exc:
                logger.error(
                    f"Result verification failed for result {pk}: {str(exc)}",
                    exc_info=True,
                    extra={"user": request.user.username, "result_id": pk},
                )
                return Response(
                    {"detail": str(exc), "code": "verification_failed"},
                    status=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
                )

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
                logger.error(
                    f"Result finalization failed for result {pk}: {str(exc)}",
                    exc_info=True,
                    extra={"user": request.user.username, "result_id": pk},
                )
                return Response(
                    {"detail": str(exc), "code": "finalization_failed"},
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
