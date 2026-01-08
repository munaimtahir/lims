"""
URL configuration for core app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabTerminalViewSet, SystemSettingsViewSet, HealthCheckView

router = DefaultRouter()
router.register(r"terminals", LabTerminalViewSet, basename="terminal")
# Don't register settings in router - handle manually for singleton pattern

urlpatterns = [
    path("", include(router.urls)),
    # Manual route for settings (singleton pattern - no pk needed)
    path("settings/", SystemSettingsViewSet.as_view({
        'get': 'list',
        'put': 'list',  # Route PUT to list which handles update
        'patch': 'list',  # Route PATCH to list which handles partial_update
    }), name="settings-list"),
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name="health-check"),
]

