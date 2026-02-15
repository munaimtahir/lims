"""
URL configuration for core app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BranchViewSet,
    CollectionCenterViewSet,
    HealthCheckView,
    PrintTemplateViewSet,
    SystemSettingsViewSet,
    TenantSettingsView,
)

router = DefaultRouter()
router.register("print-templates", PrintTemplateViewSet, basename="print-template")
router.register("branches", BranchViewSet, basename="branch")
router.register("collection-centers", CollectionCenterViewSet, basename="collection-center")

urlpatterns = [
    path("", include(router.urls)),
    # Manual route for settings (singleton pattern - no pk needed)
    path(
        "settings/",
        SystemSettingsViewSet.as_view(
            {
                "get": "list",
                "put": "list",
                "patch": "list",
            }
        ),
        name="settings-list",
    ),
    path(
        "settings/report-header-image/",
        SystemSettingsViewSet.as_view(
            {"post": "report_header_image", "delete": "report_header_image"}
        ),
        name="settings-report-header-image",
    ),
    path(
        "settings/report-footer-image/",
        SystemSettingsViewSet.as_view(
            {"post": "report_footer_image", "delete": "report_footer_image"}
        ),
        name="settings-report-footer-image",
    ),
    # Tenant-scoped settings (branch/collection center feature flag and defaults)
    path(
        "settings/tenant/",
        TenantSettingsView.as_view(),
        name="settings-tenant",
    ),
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
