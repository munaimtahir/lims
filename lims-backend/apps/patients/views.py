"""
API views for Patient management.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Patient
from .serializers import (
    PatientSerializer,
    PatientCreateSerializer,
    PatientListSerializer,
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
    search_fields = ["patient_id", "first_name", "last_name", "phone", "national_id"]
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
        Retrieve a patient's order history.

        This endpoint provides a summary of the patient's recent orders.
        Test comparisons are planned for a future phase.

        Args:
            request (Request): The request object.
            pk (int, optional): The primary key of the patient. Defaults to None.

        Returns:
            Response: A response object containing the patient's details, recent orders,
                      and a placeholder for test comparisons.
        """
        patient = self.get_object()
        from apps.orders.serializers import OrderListSerializer

        orders = patient.orders.all().order_by("-created_at")[:10]

        # Note: Test comparisons feature will be implemented in Phase 2
        # This will include comparing current test results with previous results
        # for the same patient to track trends and changes over time
        return Response(
            {
                "success": True,
                "data": {
                    "patient": PatientSerializer(patient).data,
                    "orders": OrderListSerializer(orders, many=True).data,
                    "test_comparisons": {},  # Will be implemented in Phase 2
                },
            },
            status=status.HTTP_200_OK,
        )
