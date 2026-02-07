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
                "put": "list",  # Route PUT to list which handles update
                "patch": "list",  # Route PATCH to list which handles partial_update
            }
        ),
        name="settings-list",
    ),
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
