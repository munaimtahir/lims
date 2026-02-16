"""
API views for Patient management.
"""

from django.db import models
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.export_utils import export_to_csv, export_to_excel
from apps.core.authz import user_tenant
import logging

logger = logging.getLogger(__name__)

from .filters import PatientFilter
from .models import Patient
from .serializers import (
    PatientCreateSerializer,
    PatientListSerializer,
    PatientSerializer,
)


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for patients.

    Provides endpoints for creating, retrieving, updating, and listing patients.
    Includes functionality for searching, filtering, and ordering.
    """

    queryset = Patient.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PatientFilter
    search_fields = [
        "patient_id",
        "first_name",
        "last_name",
        "phone",
        "national_id",
        "full_name",
    ]
    ordering_fields = ["created_at", "patient_id", "last_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Optimize queryset with prefetching for list action.

        For list action, prefetch the latest order to avoid N+1 queries
        when accessing last_order_referred_by in PatientListSerializer.
        """
        queryset = super().get_queryset()
        # Tenant scoping
        tenant = user_tenant(self.request.user)
        queryset = queryset.filter(tenant=tenant)
        if self.action == "list":
            # Prefetch only the latest order for each patient
            from django.db.models import Prefetch, Q

            from apps.orders.models import Order

            latest_order = Order.objects.filter(patient=models.OuterRef("pk")).order_by(
                "-created_at"
            )[:1]

            queryset = queryset.prefetch_related(
                Prefetch(
                    "orders",
                    queryset=Order.objects.order_by("-created_at")[:1],
                    to_attr="latest_orders",
                )
            )
        return queryset

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request action.

        - For `list` action, `PatientListSerializer` is used.
        - For `create` action, `PatientCreateSerializer` is used.
        - For all other actions, `PatientSerializer` is used.

        Returns:
            Serializer: The serializer class for the current action.
        """
        if self.action == "list":
            return PatientListSerializer
        elif self.action == "create":
            return PatientCreateSerializer
        return PatientSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new patient record.

        The `created_by` field is automatically set to the current authenticated user.

        Args:
            request (Request): The request object containing patient data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: A response object with the created patient data and a success message.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save(created_by=request.user)
        logger.info(
            f"Patient registered: {patient.full_name} (MRN: {patient.mrn}) by {request.user.username}",
            extra={
                "patient_id": patient.id,
                "mrn": patient.mrn,
                "user": request.user.username,
                "tenant": user_tenant(request.user).id if request.user.is_authenticated else None
            }
        )

        return Response(
            {
                "success": True,
                "data": PatientSerializer(patient).data,
                "message": "Patient registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single patient's details.

        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments containing the patient's primary key.

        Returns:
            Response: A response object with the patient's data.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        """
        Update a patient's details.

        Supports both partial and full updates.

        Args:
            request (Request): The request object with the updated data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments containing the patient's primary key.

        Returns:
            Response: A response object with the updated patient data and a success message.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()

        return Response(
            {
                "success": True,
                "data": PatientSerializer(patient).data,
                "message": "Patient updated successfully",
            },
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """
        List all patients with optional filtering, searching, and pagination.

        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: A paginated or full list of patients (standard DRF pagination).
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Return standard DRF pagination: {count, next, previous, results: [...]}
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        # For non-paginated responses, return plain array
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Global patient search with refined matching.
        """
        q = request.query_params.get("q", "").strip()
        if not q:
             return Response({"success": True, "data": []})

        # Base filter
        qs = Patient.objects.filter(tenant=user_tenant(request.user))
        
        # Build complex query
        from django.db.models import Q
        
        # Determine if query looks like a phone number (digits only, > 7 chars)
        import re
        is_phone = re.match(r'^[0-9+]{8,}$', q)
        
        if is_phone:
             # If it looks like a phone number, prioritize phone search
             qs = qs.filter(Q(phone__icontains=q) | Q(whatsapp_number__icontains=q))
        else:
             # General search
             qs = qs.filter(
                 Q(mrn__icontains=q) |
                 Q(registration_number__icontains=q) |
                 Q(patient_id__icontains=q) |
                 Q(full_name__icontains=q) |
                 Q(phone__icontains=q) |
                 Q(cnic__icontains=q) |
                 Q(national_id__icontains=q)
             )

        # distinct() is important if joins were involved, but here we are filtering on flat fields mostly.
        # However, if we joined orders it would be needed.
        
        patients = qs.distinct().order_by("-created_at")[:20]
        
        results = []
        for p in patients:
             # For last visit info, we need to look at orders
             
             last_order = p.orders.order_by("-created_at").first()
             
             last_branch_code = None
             if last_order:
                 # Check if order has collection_branch
                 if hasattr(last_order, 'collection_branch') and last_order.collection_branch:
                     last_branch_code = last_order.collection_branch.code
                 elif hasattr(last_order, 'branch') and last_order.branch:
                     last_branch_code = last_order.branch.code

             results.append({
                 "id": p.id,
                 "mrn": p.mrn or p.registration_number or p.patient_id,
                 "name": p.get_full_name(),
                 "dob": p.date_of_birth,
                 "age": p.age,
                 "gender": p.gender,
                 "mobile": p.phone,
                 "last_visit_branch_code": last_branch_code,
                 "last_visit_date": p.last_visit,
             })
        
        return Response({"success": True, "data": results})

    @action(detail=False, methods=["get"])
    def lookup(self, request):
        """
        Lookup patients by mobile number for quick registration search.

        Query params:
            - mobile: Mobile number to search (partial match supported)

        Returns:
            Response: List of matching patients with summary info.
        """
        mobile = request.query_params.get("mobile", "").strip()
        mrn = request.query_params.get("mrn", "").strip()
        name = request.query_params.get("name", "").strip()
        cnic = request.query_params.get("cnic", "").strip()

        if not any([mobile, mrn, name, cnic]):
            return Response(
                {
                    "success": True,
                    "data": [],
                    "message": "Provide mobile/mrn/name/cnic to search",
                },
                status=status.HTTP_200_OK,
            )

        qs = Patient.objects.filter(tenant=user_tenant(request.user))
        if mobile:
            qs = qs.filter(phone__icontains=mobile)
        if mrn:
            qs = qs.filter(mrn__icontains=mrn)
        if name:
            qs = qs.filter(full_name__icontains=name)
        if cnic:
            qs = qs.filter(cnic__icontains=cnic)

        patients = qs.order_by("-created_at")[:20]

        results = []
        for patient in patients:
            results.append(
                {
                    "id": patient.id,
                    "patient_id": patient.patient_id,
                    "registration_number": patient.registration_number,
                    "full_name": patient.get_full_name(),
                    "phone": patient.phone,
                    "age": patient.age,
                    "gender": patient.gender,
                    "last_visit": patient.last_visit.isoformat()
                    if patient.last_visit
                    else None,
                    "last_branch_code": (
                        patient.orders.order_by("-created_at")
                        .values_list("collection_branch__code", flat=True)
                        .first()
                    ),
                    "total_orders": patient.total_orders,
                }
            )

        return Response(
            {
                "success": True,
                "data": results,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """
        Retrieve a patient's complete test history with comparisons and trends.

        Provides:
        - Recent orders
        - Test result history grouped by parameter
        - Comparison of last 5 values for each parameter
        - Delta checks (significant changes detection)
        - Trend data for visualization

        Query params:
            - limit: Number of recent results to include (default: 5)
            - parameter_id: Filter by specific parameter ID

        Args:
            request (Request): The request object.
            pk (int, optional): The primary key of the patient. Defaults to None.

        Returns:
            Response: A response object containing patient history with test comparisons.
        """
        from decimal import Decimal

        from django.db.models import Max, Min, Q

        from apps.laboratory.models import TestParameter
        from apps.orders.serializers import OrderListSerializer
        from apps.results.models import TestResult

        patient = self.get_object()
        limit = int(request.query_params.get("limit", 5))
        parameter_id = request.query_params.get("parameter_id")

        # Get recent orders
        orders = patient.orders.all().order_by("-created_at")[:10]

        # Get all test results for this patient
        results_query = (
            TestResult.objects.filter(order_item__order__patient=patient)
            .select_related(
                "test_parameter", "test_parameter__test", "order_item__order"
            )
            .order_by("-entered_at")
        )

        if parameter_id:
            results_query = results_query.filter(test_parameter_id=parameter_id)

        # Group results by parameter
        test_history = {}
        all_results = list(results_query)

        for result in all_results:
            param_id = result.test_parameter.id
            param_name = result.test_parameter.parameter_name

            if param_id not in test_history:
                test_history[param_id] = {
                    "parameter_id": param_id,
                    "parameter_name": param_name,
                    "unit": result.test_parameter.unit,
                    "test_name": result.test_parameter.test.test_name,
                    "test_code": result.test_parameter.test.test_code,
                    "results": [],
                    "comparison": [],
                    "trend": [],
                    "delta_alerts": [],
                }

            # Try to parse numeric value
            try:
                numeric_value = float(result.result_value.replace(",", "").strip())
            except (ValueError, AttributeError):
                numeric_value = None

            result_data = {
                "id": result.id,
                "order_id": result.order_item.order.order_id,
                "order_date": result.order_item.order.created_at.isoformat(),
                "result_value": result.result_value,
                "numeric_value": numeric_value,
                "flag": result.flag,
                "entered_at": result.entered_at.isoformat()
                if result.entered_at
                else None,
                "verified_at": result.verified_at.isoformat()
                if result.verified_at
                else None,
            }

            test_history[param_id]["results"].append(result_data)
            test_history[param_id]["trend"].append(
                {
                    "date": result.order_item.order.created_at.isoformat(),
                    "value": numeric_value,
                    "flag": result.flag,
                }
            )

        # Generate comparisons and delta checks for each parameter
        for param_id, history_data in test_history.items():
            results = history_data["results"]

            # Get last N results for comparison
            recent_results = results[:limit]
            history_data["comparison"] = recent_results

            # Delta check: detect significant changes
            if len(recent_results) >= 2:
                delta_alerts = []
                for i in range(1, len(recent_results)):
                    prev_result = recent_results[i]
                    curr_result = recent_results[0]

                    if (
                        prev_result["numeric_value"] is not None
                        and curr_result["numeric_value"] is not None
                    ):
                        prev_val = prev_result["numeric_value"]
                        curr_val = curr_result["numeric_value"]

                        # Calculate percentage change
                        if prev_val != 0:
                            percent_change = abs((curr_val - prev_val) / prev_val) * 100

                            # Alert if change is > 20% or crosses critical thresholds
                            if percent_change > 20:
                                delta_alerts.append(
                                    {
                                        "type": "significant_change",
                                        "message": f"Value changed by {percent_change:.1f}% from previous test",
                                        "previous_value": prev_val,
                                        "current_value": curr_val,
                                        "percent_change": percent_change,
                                        "previous_date": prev_result["order_date"],
                                        "current_date": curr_result["order_date"],
                                    }
                                )

                            # Check if flag changed to critical
                            critical_flags = {"C", "critical_low", "critical_high"}
                            if (
                                prev_result["flag"] not in critical_flags
                                and curr_result["flag"] in critical_flags
                            ):
                                delta_alerts.append(
                                    {
                                        "type": "critical_change",
                                        "message": f"Result changed to {curr_result['flag']} from {prev_result['flag']}",
                                        "previous_flag": prev_result["flag"],
                                        "current_flag": curr_result["flag"],
                                        "previous_date": prev_result["order_date"],
                                        "current_date": curr_result["order_date"],
                                    }
                                )

                history_data["delta_alerts"] = delta_alerts

        return Response(
            {
                "success": True,
                "data": {
                    "patient": PatientSerializer(patient).data,
                    "orders": OrderListSerializer(orders, many=True).data,
                    "test_history": list(test_history.values()),
                    "summary": {
                        "total_orders": patient.orders.count(),
                        "total_tests": len(test_history),
                        "total_results": len(all_results),
                    },
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def test_comparison(self, request, pk=None):
        """
        Get comparison view for last N test values for a specific parameter.

        Query params:
            - parameter_id: The parameter ID to compare (required)
            - limit: Number of previous values to compare (default: 5)

        Returns:
            Response: Comparison data for the specified parameter.
        """
        from apps.laboratory.models import TestParameter
        from apps.results.models import TestResult

        patient = self.get_object()
        parameter_id = request.query_params.get("parameter_id")
        limit = int(request.query_params.get("limit", 5))

        if not parameter_id:
            return Response(
                {"error": "parameter_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parameter = TestParameter.objects.get(id=parameter_id)
        except TestParameter.DoesNotExist:
            return Response(
                {"error": "Parameter not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get last N results for this parameter
        results = (
            TestResult.objects.filter(
                order_item__order__patient=patient, test_parameter=parameter
            )
            .select_related("order_item__order")
            .order_by("-entered_at")[:limit]
        )

        comparison_data = []
        for result in results:
            try:
                numeric_value = float(result.result_value.replace(",", "").strip())
            except (ValueError, AttributeError):
                numeric_value = None

            comparison_data.append(
                {
                    "order_id": result.order_item.order.order_id,
                    "order_date": result.order_item.order.created_at.isoformat(),
                    "result_value": result.result_value,
                    "numeric_value": numeric_value,
                    "unit": parameter.unit,
                    "flag": result.flag,
                    "entered_at": result.entered_at.isoformat()
                    if result.entered_at
                    else None,
                }
            )

        # Get reference range for this specific patient
        from apps.laboratory.ranges import pick_reference_range
        range_info = pick_reference_range(parameter, patient)

        return Response(
            {
                "success": True,
                "data": {
                    "parameter": {
                        "id": parameter.id,
                        "name": parameter.parameter_name,
                        "unit": parameter.unit,
                        "test_name": parameter.test.test_name,
                    },
                    "comparison": comparison_data,
                    "reference_range": {
                        "min": float(range_info["ref_min"])
                        if range_info["ref_min"]
                        else None,
                        "max": float(range_info["ref_max"])
                        if range_info["ref_max"]
                        else None,
                        "display": range_info["display"],
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
