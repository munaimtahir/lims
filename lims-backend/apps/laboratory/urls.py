from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BulkImportViewSet,
    CatalogAuditView,
    CatalogExportView,
    CatalogImportJobViewSet,
    ParameterViewSet,
    ReferenceRangeViewSet,
    TestCategoryViewSet,
    TestPanelViewSet,
    TestParameterViewSet,
    TestViewSet,
)

router = DefaultRouter()
router.register(r"import", BulkImportViewSet, basename="import")
router.register(r"import/jobs", CatalogImportJobViewSet, basename="import-jobs")
router.register(r"categories", TestCategoryViewSet)
router.register(r"tests", TestViewSet)
router.register(r"panels", TestPanelViewSet)
router.register(r"parameters", TestParameterViewSet)
router.register(r"analytes", ParameterViewSet)
router.register(r"reference-ranges", ReferenceRangeViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "catalog/export/",
        CatalogExportView.as_view({"get": "list"}),
        name="catalog-export",
    ),
    path(
        "catalog/audit/",
        CatalogAuditView.as_view({"get": "list"}),
        name="catalog-audit",
    ),
]
