"""
URL configuration for core app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BranchListView,
    CollectionCenterListView,
    HealthCheckView,
    PrintTemplateViewSet,
    SystemSettingsViewSet,
    TenantSettingsView,
)

router = DefaultRouter()
router.register("print-templates", PrintTemplateViewSet, basename="print-template")

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
    # Lists for tenant settings dropdowns (admin/manage without Django admin)
    path("branches/", BranchListView.as_view(), name="branch-list"),
    path("collection-centers/", CollectionCenterListView.as_view(), name="collection-center-list"),
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
