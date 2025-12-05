"""Patient views."""

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Patient
from .permissions import IsAdminOrReception
from .serializers import PatientSerializer


class PatientListCreateView(generics.ListCreateAPIView):
    """
    Lists and creates patients.

    Provides endpoints for listing patients with optional search functionality,
    and for creating new patients. Access is restricted to admin and reception users.

    Filtering:
    - `query` (string): Searches for patients by name, phone, or CNIC prefix.
    """

    serializer_class = PatientSerializer
    permission_classes = [IsAdminOrReception]

    def get_queryset(self):
        """
        Optionally filters the queryset by a search `query`.

        The query searches against the `full_name`, `phone`, and `cnic` fields.

        Returns:
            QuerySet: The filtered queryset of `Patient` objects.
        """
        queryset = Patient.objects.all()
        query = self.request.query_params.get("query", "").strip()

        if query:
            queryset = queryset.filter(
                Q(full_name__icontains=query)
                | Q(phone__icontains=query)
                | Q(cnic__startswith=query)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Creates a new patient.

        Args:
            request: The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The response object with the created patient data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class PatientDetailView(generics.RetrieveAPIView):
    """
    Retrieves the details of a specific patient.
    """

    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAdminOrReception]
