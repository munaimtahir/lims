"""Catalog views."""

from rest_framework import generics

from core.permissions import IsAdminOrReadOnly

from .models import (
    Parameter,
    ParameterQuickText,
    ReferenceRange,
    Test,
    TestCatalog,
    TestParameter,
)
from .serializers import (
    ParameterQuickTextSerializer,
    ParameterSerializer,
    ReferenceRangeSerializer,
    TestCatalogSerializer,
    TestParameterSerializer,
    TestSerializer,
)


class TestCatalogListCreateView(generics.ListCreateAPIView):
    """
    List all tests or create a new test.

    Allows for the retrieval of a list of all test catalog items and the
    creation of new test catalog items. Creation is restricted to admin users.

    Filtering:
    - `is_active` (boolean): Filters tests based on their active status.
    """

    queryset = TestCatalog.objects.all().order_by("code")
    serializer_class = TestCatalogSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """
        Optionally filters the queryset by `is_active` status.

        Returns:
            QuerySet: The filtered queryset of `TestCatalog` objects.
        """
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class TestCatalogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a test.

    Provides endpoints for retrieving the details of a specific test, as well as
    updating or deleting it. Update and delete operations are restricted to admin
    users.
    """

    queryset = TestCatalog.objects.all()
    serializer_class = TestCatalogSerializer
    permission_classes = [IsAdminOrReadOnly]


# New LIMS Test Management Views
class TestListCreateView(generics.ListCreateAPIView):
    """
    List all tests or create a new test.
    """

    queryset = Test.objects.all().order_by("code")
    serializer_class = TestSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Optionally filters the queryset by active status."""
        queryset = super().get_queryset()
        active = self.request.query_params.get("active")
        if active is not None:
            queryset = queryset.filter(active=active.lower() == "true")
        return queryset


class TestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a test.
    """

    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsAdminOrReadOnly]


# Parameter Management Views
class ParameterListCreateView(generics.ListCreateAPIView):
    """
    List all parameters or create a new parameter.
    """

    queryset = Parameter.objects.all().order_by("code")
    serializer_class = ParameterSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Optionally filters the queryset by active status."""
        queryset = super().get_queryset()
        active = self.request.query_params.get("active")
        if active is not None:
            queryset = queryset.filter(active=active.lower() == "true")
        return queryset


class ParameterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a parameter.
    """

    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    permission_classes = [IsAdminOrReadOnly]


# TestParameter Relationship Views
class TestParameterListCreateView(generics.ListCreateAPIView):
    """
    List all test-parameter relationships or create a new one.
    """

    queryset = TestParameter.objects.all().select_related("test", "parameter")
    serializer_class = TestParameterSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Optionally filters by test ID."""
        queryset = super().get_queryset()
        test_id = self.request.query_params.get("test")
        if test_id:
            queryset = queryset.filter(test_id=test_id)
        return queryset


class TestParameterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a test-parameter relationship.
    """

    queryset = TestParameter.objects.all().select_related("test", "parameter")
    serializer_class = TestParameterSerializer
    permission_classes = [IsAdminOrReadOnly]


# Reference Range Management Views
class ReferenceRangeListCreateView(generics.ListCreateAPIView):
    """
    List all reference ranges or create a new one.
    """

    queryset = ReferenceRange.objects.all().select_related("parameter")
    serializer_class = ReferenceRangeSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Optionally filters by parameter ID."""
        queryset = super().get_queryset()
        parameter_id = self.request.query_params.get("parameter")
        if parameter_id:
            queryset = queryset.filter(parameter_id=parameter_id)
        return queryset


class ReferenceRangeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a reference range.
    """

    queryset = ReferenceRange.objects.all().select_related("parameter")
    serializer_class = ReferenceRangeSerializer
    permission_classes = [IsAdminOrReadOnly]


# Parameter Quick Text Views
class ParameterQuickTextListCreateView(generics.ListCreateAPIView):
    """
    List all parameter quick texts or create a new one.
    """

    queryset = ParameterQuickText.objects.all().select_related("parameter")
    serializer_class = ParameterQuickTextSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Optionally filters by parameter ID."""
        queryset = super().get_queryset()
        parameter_id = self.request.query_params.get("parameter")
        if parameter_id:
            queryset = queryset.filter(parameter_id=parameter_id)
        return queryset


class ParameterQuickTextDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a parameter quick text.
    """

    queryset = ParameterQuickText.objects.all().select_related("parameter")
    serializer_class = ParameterQuickTextSerializer
    permission_classes = [IsAdminOrReadOnly]
