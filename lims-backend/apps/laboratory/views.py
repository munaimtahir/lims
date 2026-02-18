from django.db import models
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsManager

from .catalog_io import (
    IMPORT_LOGIC_VERSION,
    IMPORT_LOGIC_FEATURES,
    export_catalog_workbook,
    import_catalog_from_excel,
)
from .models import (
    CatalogImportJob,
    Parameter,
    ReferenceRange,
    Test,
    TestCategory,
    TestPanel,
    TestParameter,
)
from .serializers import (
    CatalogImportJobSerializer,
    ParameterSerializer,
    ReferenceRangeSerializer,
    TestCategorySerializer,
    TestPanelSerializer,
    TestParameterSerializer,
    TestSerializer,
)


class BulkImportViewSet(viewsets.ViewSet):
    """
    ViewSet for bulk importing laboratory data from Excel.

    Supports dry-run mode for validation without writing to database.
    """

    permission_classes = [IsAdmin]

    @action(detail=False, methods=["get"])
    def version(self, request):
        """Return the import logic version and features for deployment verification."""
        import os
        import sys
        
        return Response(
            {
                "version": IMPORT_LOGIC_VERSION,
                "features": IMPORT_LOGIC_FEATURES,
                "python_path": sys.executable,
                "catalog_io_path": os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__), "catalog_io.py"
                    )
                ),
                "catalog_io_exists": os.path.exists(
                    os.path.join(
                        os.path.dirname(__file__), "catalog_io.py"
                    )
                ),
            }
        )

    def create(self, request):
        """
        Import data from an uploaded Excel file.

        Query params:
            - strict: If 'true', missing required values are errors (default true)
            - allow_defaults: If 'true', apply defaults for optional fields (default false)
            - mode: Only 'upsert' is supported (default upsert)
            - dry_run: If 'true', validates the file without writing to database (default true)
        """
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        def parse_bool(value, default):
            if value is None:
                return default
            return str(value).lower() in ["true", "1", "yes"]

        strict = parse_bool(request.query_params.get("strict"), True)
        allow_defaults = parse_bool(request.query_params.get("allow_defaults"), False)
        mode = request.query_params.get("mode", "upsert")
        dry_run = parse_bool(request.query_params.get("dry_run"), True)

        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Import request received: file={getattr(file, 'name', 'Unknown')}, "
                f"strict={strict}, allow_defaults={allow_defaults}, mode={mode}, dry_run={dry_run}"
            )
            
            summary = import_catalog_from_excel(
                file,
                strict=strict,
                allow_defaults=allow_defaults,
                mode=mode,
                dry_run=dry_run,
            )
            
            logger.info(
                f"Import completed: version={summary.get('version')}, "
                f"errors={len(summary.get('errors', []))}, "
                f"warnings={len(summary.get('warnings', []))}"
            )

            job = CatalogImportJob.objects.create(
                created_by=request.user if request.user.is_authenticated else None,
                strict=strict,
                allow_defaults=allow_defaults,
                mode=mode,
                dry_run=dry_run,
                summary_json=summary,
                errors_json=summary.get("errors", []),
                warnings_json=summary.get("warnings", []),
                source_filename=getattr(file, "name", ""),
            )

            # If there are validation errors, return 400
            if summary.get("errors"):
                return Response(
                    {
                        "success": False,
                        "message": "Import validation failed. Please fix the errors and try again.",
                        "summary": summary,
                        "job_id": job.id,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "success": True,
                    "message": "Import completed successfully"
                    if not dry_run
                    else "Dry-run validation completed",
                    "summary": summary,
                    "job_id": job.id,
                },
                status=(status.HTTP_201_CREATED if not dry_run else status.HTTP_200_OK),
            )
        except Exception as e:
            # Check for invalid file format errors
            if "does not support the old .xls file format" in str(
                e
            ) or "is not a valid Zip file" in str(e):
                return Response(
                    {
                        "error": (
                            "Invalid Excel file format. " "Please use .xlsx format."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"], url_path="download-template")
    def download_template(self, request):
        """
        Download the Excel template for bulk import.
        """
        from .utils import generate_import_template

        workbook = generate_import_template()

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response[
            "Content-Disposition"
        ] = 'attachment; filename="LIMS_Import_Template.xlsx"'

        workbook.save(response)
        return response


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
        Fast search for tests AND panels by name or code for order entry.

        Query params:
            - q: Search query (searches test_name, test_code, panel_name, panel_code)
            - limit: Maximum results to return (default: 20)

        Returns:
            Response: List of matching tests and panels with essential info.
        """
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 20))

        if not query or len(query) < 2:
            return Response(
                {
                    "success": True,
                    "data": [],
                    "message": "Enter at least 2 characters to search",
                },
                status=status.HTTP_200_OK,
            )

        # Search for tests by name or code (case-insensitive)
        tests = (
            Test.objects.filter(
                models.Q(test_name__icontains=query)
                | models.Q(test_code__icontains=query),
                is_active=True,
            )
            .select_related("category")
            .order_by("test_code")[:limit]
        )

        # Search for panels by name or code (case-insensitive)
        panels = (
            TestPanel.objects.filter(
                models.Q(panel_name__icontains=query)
                | models.Q(panel_code__icontains=query),
                is_active=True,
            )
            .select_related("category")
            .prefetch_related("tests")[:limit]
        )

        results = []

        # Add tests to results
        for test in tests:
            results.append(
                {
                    "id": test.test_id,
                    "test_id": test.test_id,
                    "test_code": test.test_code,
                    "test_name": test.test_name,
                    "category_name": test.category.name if test.category else "",
                    "sample_type": test.sample_type,
                    "price": str(test.price),
                    "type": "test",
                }
            )

        # Add panels to results
        for panel in panels:
            results.append(
                {
                    "id": panel.id,
                    "panel_id": panel.id,
                    "test_code": panel.panel_code,  # For compatibility with frontend
                    "test_name": panel.panel_name,  # For compatibility with frontend
                    "panel_code": panel.panel_code,
                    "panel_name": panel.panel_name,
                    "category_name": panel.category.name if panel.category else "",
                    "sample_type": panel.sample_type,
                    "price": str(panel.price),
                    "type": "panel",
                    "test_count": panel.tests.count(),
                }
            )

        # Sort results: panels first, then tests, both alphabetically
        results.sort(key=lambda x: (x["type"] != "panel", x["test_name"]))

        # Limit total results
        results = results[:limit]

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
    search_fields = [
        "parameter__parameter_id",
        "parameter__parameter_name",
        "parameter_name",
    ]
    ordering_fields = ["parameter__parameter_id", "display_order"]


class ParameterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Global Parameters (Analytes).
    """

    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer  # Needs to be imported or available
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["parameter_id", "parameter_name"]
    ordering_fields = ["parameter_id", "parameter_name"]


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
    search_fields = [
        "parameter__parameter__parameter_name",
        "parameter__test__test_name",
    ]
    ordering_fields = [
        "parameter__parameter__parameter_id",
        "age_min",
        "gender",
        "version",
        "effective_date",
    ]

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


class CatalogImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CatalogImportJob.objects.all()
    serializer_class = CatalogImportJobSerializer
    permission_classes = [IsAdmin]


class CatalogExportView(viewsets.ViewSet):
    permission_classes = [IsAdmin]

    def list(self, request):
        workbook = export_catalog_workbook()
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response[
            "Content-Disposition"
        ] = 'attachment; filename="LIMS_Catalog_Export.xlsx"'
        workbook.save(response)
        return response


class CatalogAuditView(viewsets.ViewSet):
    permission_classes = [IsManager]

    def list(self, request):
        duplicate_test_codes = (
            Test.objects.values("test_code")
            .annotate(count=models.Count("test_id"))
            .filter(count__gt=1)
        )
        duplicate_param_codes = (
            Parameter.objects.values("parameter_id")
            .annotate(count=models.Count("parameter_id"))
            .filter(count__gt=1)
        )
        tests_without_parameters = Test.objects.filter(
            test_parameters__isnull=True
        ).values("test_id", "test_code", "test_name")[:10]
        orphan_mappings = TestParameter.objects.filter(
            models.Q(test__isnull=True) | models.Q(parameter__isnull=True)
        )
        missing_ranges = TestParameter.objects.filter(
            reference_ranges__isnull=True
        ).values("test_id", "parameter_id")[:10]
        invalid_ranges = ReferenceRange.objects.filter(
            models.Q(reference_min__isnull=True, reference_max__isnull=True)
            | models.Q(age_min__gte=models.F("age_max"))
        )
        serum_defaults = Test.objects.filter(sample_type__iexact="Serum")
        zero_price = Test.objects.filter(price=0)
        default_tat = Test.objects.filter(turnaround_time=24)
        panels_without_tests = TestPanel.objects.filter(tests__isnull=True)

        return Response(
            {
                "duplicates": {
                    "test_code": {
                        "count": duplicate_test_codes.count(),
                        "samples": list(duplicate_test_codes[:10]),
                    },
                    "parameter_code": {
                        "count": duplicate_param_codes.count(),
                        "samples": list(duplicate_param_codes[:10]),
                    },
                },
                "orphans": {
                    "mappings": {
                        "count": orphan_mappings.count(),
                        "samples": list(
                            orphan_mappings.values("id", "test_id", "parameter_id")[:10]
                        ),
                    },
                },
                "tests_without_parameters": {
                    "count": Test.objects.filter(test_parameters__isnull=True).count(),
                    "samples": list(tests_without_parameters),
                },
                "reference_ranges": {
                    "missing": {
                        "count": TestParameter.objects.filter(
                            reference_ranges__isnull=True
                        ).count(),
                        "samples": list(missing_ranges),
                    },
                    "invalid": {
                        "count": invalid_ranges.count(),
                        "samples": list(
                            invalid_ranges.values("id", "parameter_id", "gender")[:10]
                        ),
                    },
                },
                "suspicious_defaults": {
                    "sample_type_serum": {
                        "count": serum_defaults.count(),
                        "samples": list(
                            serum_defaults.values("test_id", "test_code")[:10]
                        ),
                    },
                    "price_zero": {
                        "count": zero_price.count(),
                        "samples": list(zero_price.values("test_id", "test_code")[:10]),
                    },
                    "turnaround_time_24": {
                        "count": default_tat.count(),
                        "samples": list(
                            default_tat.values("test_id", "test_code")[:10]
                        ),
                    },
                },
                "panels_without_tests": {
                    "count": panels_without_tests.count(),
                    "samples": list(
                        panels_without_tests.values("panel_code", "panel_name")[:10]
                    ),
                },
            }
        )
