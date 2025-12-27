"""
API views for Patient management.
"""

from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.export_utils import export_to_csv, export_to_excel

from .models import Patient
from .serializers import (
    PatientSerializer,
    PatientCreateSerializer,
    PatientListSerializer,
)
from .filters import PatientFilter


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
    search_fields = ["patient_id", "first_name", "last_name", "phone", "national_id", "full_name"]
    ordering_fields = ["created_at", "patient_id", "last_name"]
    ordering = ["-created_at"]

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
            Response: A paginated or full list of patients.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(
                {"success": True, "data": serializer.data}
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
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
        from django.db.models import Q, Max, Min
        from apps.orders.serializers import OrderListSerializer
        from apps.results.models import TestResult
        from apps.laboratory.models import TestParameter
        
        patient = self.get_object()
        limit = int(request.query_params.get("limit", 5))
        parameter_id = request.query_params.get("parameter_id")
        
        # Get recent orders
        orders = patient.orders.all().order_by("-created_at")[:10]
        
        # Get all test results for this patient
        results_query = TestResult.objects.filter(
            order_item__order__patient=patient
        ).select_related(
            "test_parameter",
            "test_parameter__test",
            "order_item__order"
        ).order_by("-entered_at")
        
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
                numeric_value = float(result.result_value.replace(',', '').strip())
            except (ValueError, AttributeError):
                numeric_value = None
            
            result_data = {
                "id": result.id,
                "order_id": result.order_item.order.order_id,
                "order_date": result.order_item.order.created_at.isoformat(),
                "result_value": result.result_value,
                "numeric_value": numeric_value,
                "flag": result.flag,
                "entered_at": result.entered_at.isoformat() if result.entered_at else None,
                "verified_at": result.verified_at.isoformat() if result.verified_at else None,
            }
            
            test_history[param_id]["results"].append(result_data)
            test_history[param_id]["trend"].append({
                "date": result.order_item.order.created_at.isoformat(),
                "value": numeric_value,
                "flag": result.flag,
            })
        
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
                    
                    if prev_result["numeric_value"] is not None and curr_result["numeric_value"] is not None:
                        prev_val = prev_result["numeric_value"]
                        curr_val = curr_result["numeric_value"]
                        
                        # Calculate percentage change
                        if prev_val != 0:
                            percent_change = abs((curr_val - prev_val) / prev_val) * 100
                            
                            # Alert if change is > 20% or crosses critical thresholds
                            if percent_change > 20:
                                delta_alerts.append({
                                    "type": "significant_change",
                                    "message": f"Value changed by {percent_change:.1f}% from previous test",
                                    "previous_value": prev_val,
                                    "current_value": curr_val,
                                    "percent_change": percent_change,
                                    "previous_date": prev_result["order_date"],
                                    "current_date": curr_result["order_date"],
                                })
                            
                            # Check if flag changed to critical
                            if prev_result["flag"] not in ["critical_low", "critical_high"] and \
                               curr_result["flag"] in ["critical_low", "critical_high"]:
                                delta_alerts.append({
                                    "type": "critical_change",
                                    "message": f"Result changed to {curr_result['flag']} from {prev_result['flag']}",
                                    "previous_flag": prev_result["flag"],
                                    "current_flag": curr_result["flag"],
                                    "previous_date": prev_result["order_date"],
                                    "current_date": curr_result["order_date"],
                                })
                
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
        from apps.results.models import TestResult
        from apps.laboratory.models import TestParameter
        
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
        results = TestResult.objects.filter(
            order_item__order__patient=patient,
            test_parameter=parameter
        ).select_related(
            "order_item__order"
        ).order_by("-entered_at")[:limit]
        
        comparison_data = []
        for result in results:
            try:
                numeric_value = float(result.result_value.replace(',', '').strip())
            except (ValueError, AttributeError):
                numeric_value = None
            
            comparison_data.append({
                "order_id": result.order_item.order.order_id,
                "order_date": result.order_item.order.created_at.isoformat(),
                "result_value": result.result_value,
                "numeric_value": numeric_value,
                "unit": parameter.unit,
                "flag": result.flag,
                "entered_at": result.entered_at.isoformat() if result.entered_at else None,
            })
        
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
                        "male": {
                            "min": float(parameter.reference_min_male) if parameter.reference_min_male else None,
                            "max": float(parameter.reference_max_male) if parameter.reference_max_male else None,
                        },
                        "female": {
                            "min": float(parameter.reference_min_female) if parameter.reference_min_female else None,
                            "max": float(parameter.reference_max_female) if parameter.reference_max_female else None,
                        },
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
