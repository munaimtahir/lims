"""
URL configuration for core app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HealthCheckView, PrintTemplateViewSet, SystemSettingsViewSet

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
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
