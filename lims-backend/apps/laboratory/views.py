from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from .models import TestCategory, Test, TestPanel, TestParameter, ReferenceRange
from .serializers import (
    TestCategorySerializer,
    TestSerializer,
    TestPanelSerializer,
    TestParameterSerializer,
    ReferenceRangeSerializer,
)
from .utils import import_tests_from_excel


class BulkImportViewSet(viewsets.ViewSet):
    """
    ViewSet for bulk importing laboratory data from Excel.
    
    Supports dry-run mode for validation without writing to database.
    """

    def create(self, request):
        """
        Import data from an uploaded Excel file.
        
        Query params:
            - dry_run: If 'true', validates the file without writing to database
        """
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for dry_run parameter
        dry_run = request.query_params.get("dry_run", "").lower() == "true"

        try:
            summary = import_tests_from_excel(file, dry_run=dry_run)
            
            # If there are validation errors, return 400
            if not summary.get("validation_passed", True):
                return Response(
                    {
                        "success": False,
                        "message": "Import validation failed. Please fix the errors and try again.",
                        "summary": summary
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {
                    "success": True,
                    "message": summary.get(
                        "message", "Import completed successfully"
                    ),
                    "summary": summary
                },
                status=(
                    status.HTTP_201_CREATED if not dry_run
                    else status.HTTP_200_OK
                )
            )
        except Exception as e:
            # Check for invalid file format errors
            if ("does not support the old .xls file format" in str(e) or
                    "is not a valid Zip file" in str(e)):
                return Response(
                    {
                        "error": (
                            "Invalid Excel file format. "
                            "Please use .xlsx format."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Categories.
    """

    queryset = TestCategory.objects.all()
    serializer_class = TestCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name"]


class TestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Tests.
    """

    queryset = Test.objects.all()
    serializer_class = TestSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "is_active"]
    search_fields = ["test_name", "test_code", "loinc_code"]
    ordering_fields = ["test_code", "test_name", "price"]
    
    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Fast search for tests by name or code for order entry.
        
        Query params:
            - q: Search query (searches test_name and test_code)
            - limit: Maximum results to return (default: 20)
        
        Returns:
            Response: List of matching tests with essential info.
        """
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 20))
        
        if not query or len(query) < 2:
            return Response(
                {
                    "success": True,
                    "data": [],
                    "message": "Enter at least 2 characters to search"
                },
                status=status.HTTP_200_OK,
            )
        
        # Search for tests by name or code (case-insensitive)
        tests = Test.objects.filter(
            models.Q(test_name__icontains=query) | models.Q(test_code__icontains=query),
            is_active=True
        ).select_related("category").order_by("test_code")[:limit]
        
        results = []
        for test in tests:
            results.append({
                "id": test.id,
                "test_code": test.test_code,
                "test_name": test.test_name,
                "category_name": test.category.name if test.category else "",
                "sample_type": test.sample_type,
                "price": str(test.price),
                "type": "test",  # To distinguish from panels
            })
        
        return Response(
            {
                "success": True,
                "data": results,
            },
            status=status.HTTP_200_OK,
        )


class TestPanelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Panels.
    """

    queryset = TestPanel.objects.all()
    serializer_class = TestPanelSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "is_active"]
    search_fields = ["panel_name", "panel_code"]
    ordering_fields = ["panel_code", "panel_name", "price"]


class TestParameterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Parameters.
    """

    queryset = TestParameter.objects.all()
    serializer_class = TestParameterSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["test", "test__category"]
    search_fields = ["parameter__parameter_id", "parameter__parameter_name", "parameter_name"]
    ordering_fields = ["parameter__parameter_id", "display_order"]


class ReferenceRangeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Reference Ranges.
    
    Supports age-specific and gender-specific reference ranges with versioning.
    """

    queryset = ReferenceRange.objects.all()
    serializer_class = ReferenceRangeSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["parameter", "parameter__test", "gender", "is_active"]
    search_fields = ["parameter__parameter__parameter_name", "parameter__test__test_name"]
    ordering_fields = ["parameter__parameter__parameter_id", "age_min", "gender", "version", "effective_date"]
    
    @action(detail=False, methods=["get"])
    def for_parameter(self, request):
        """
        Get all reference ranges for a specific parameter.
        
        Query params:
            - parameter_id: The ID of the parameter
            - age: Optional age in years to filter by
            - gender: Optional gender (Male/Female) to filter by
        """
        parameter_id = request.query_params.get("parameter_id")
        if not parameter_id:
            return Response(
                {"error": "parameter_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        queryset = self.queryset.filter(parameter_id=parameter_id, is_active=True)
        
        # Filter by age if provided
        age = request.query_params.get("age")
        if age:
            try:
                age_int = int(age)
                queryset = queryset.filter(
                    models.Q(age_min__isnull=True) | models.Q(age_min__lte=age_int),
                    models.Q(age_max__isnull=True) | models.Q(age_max__gte=age_int),
                )
            except ValueError:
                return Response(
                    {"error": "age must be a valid integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Filter by gender if provided
        gender = request.query_params.get("gender")
        if gender:
            queryset = queryset.filter(
                models.Q(gender="Both") | models.Q(gender=gender)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """
        Deactivate a reference range (creates a new version if needed).
        """
        reference_range = self.get_object()
        reference_range.is_active = False
        reference_range.save()
        return Response(
            {"status": "Reference range deactivated"},
            status=status.HTTP_200_OK,
        )
